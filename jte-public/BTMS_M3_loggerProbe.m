function BTMS_M3_loggerProbe()
% ONE tiny synthetic logging/API qualification, never the battery model.
root=fullfile(pwd,'actuator-review-private');diary(fullfile(root,'PROBE_CONSOLE.txt'));
m='M3InfrastructureProbe';s=[];stage='BUILD_SYNTHETIC';flags=struct('physicalRun',false,'G5Accepted',false,'status','UNQUALIFIED');
try
 assert(strcmp(version('-release'),'2024b')&&strcmp(version,'24.2.0.3361896 (R2024b) Update 10'),...
 'M3:Runtime','Exact R2024b U10 required.');
 new_system(m);c=onCleanup(@()close_system(m,0));
 set_param(m,'Solver','ode23t','MaxStep','.005','StopTime','.03','Refine','1');
 add_block('simulink/Sources/Constant',[m '/u'],'Value','.5');
 add_block('simulink/Discrete/Discrete State-Space',[m '/state'],'A','.5','B','.5','C','1','D','0','InitialCondition','.25','SampleTime','.01');
 add_block('simulink/Discrete/Zero-Order Hold',[m '/hold'],'SampleTime','.01');
 add_block('simulink/Sources/Clock',[m '/time']);
 add_block('simulink/Math Operations/Gain',[m '/vector'],'Gain','ones(312,1)');
 add_line(m,'u/1','hold/1');add_line(m,'hold/1','state/1');add_line(m,'time/1','vector/1');
 paths={'time','hold','state','vector'};ports=zeros(1,4);files=cell(1,4);
 for k=1:4
  ph=get_param([m '/' paths{k}],'PortHandles');ports(k)=ph.Outport(1);
  files{k}=fullfile(root,['PROBE_NATIVE_' num2str(k) '.mat']);
  add_block('simulink/Sinks/To File',[m '/file' num2str(k)],'FileName',files{k},...
   'MatrixName',['native' num2str(k)],'SaveFormat','Timeseries','SampleTime','-1','Decimation','1');
  add_line(m,[paths{k} '/1'],['file' num2str(k) '/1'],'autorouting','on');
 end
 % Core probe must have continuous clock, use Clock port for observational core.
 ph=get_param([m '/time'],'PortHandles');ports(1)=ph.Outport(1);
 stage='OBSERVATION_METADATA';BTMS_M3_instrument(m,ports,[m '/state'],root);
 stage='SYNTHETIC_INITIALIZE';s=simulation(m);initialize(s);
 stage='SYNTHETIC_FIRST_COMPLETED_MAJOR';processed=s.Time;finalstep=step(s);q0=BTMS_M3_completed(s,processed,finalstep,.03);
 stage='FIRST_PAUSED_OPERATING_POINT_NOT_T0';
 firstPausedTop=s.Time;
 op0=get_param(m,'CurrentOperatingPoint');
 assert(isa(op0,'Simulink.op.ModelOperatingPoint') && isfinite(op0.snapshotTime) && ...
   abs(op0.snapshotTime-firstPausedTop)<=32*eps(max(1,abs(firstPausedTop))), ...
   'M3:PausedOP','Operating point snapshot does not match actual paused top-of-step.');
 save(fullfile(root,'PROBE_FIRST_PAUSED_OPERATING_POINT.mat'),'op0','q0','firstPausedTop','-v7.3');
 stage='SYNTHETIC_NATIVE_HORIZON';checkpoints={q0};majorCount=1;loopClock=tic;
 lifecycle=struct('processedPriorTop',processed,'finalStepReturned',finalstep,...
  'returnedSimulationTime',s.Time,'simulationStatus',char(s.Status));
 while ~finalstep
  assert(strcmp(s.Status,'paused')&&majorCount<1000&&toc(loopClock)<30,...
   'M3:SyntheticTermination','Tiny probe failed bounded major-step progression.');
  processed=s.Time;finalstep=step(s);majorCount=majorCount+1;
  lifecycle=struct('processedPriorTop',processed,'finalStepReturned',finalstep,...
   'returnedSimulationTime',s.Time,'simulationStatus',char(s.Status));
  checkpoints{end+1}=BTMS_M3_completed(s,processed,finalstep,.03); %#ok<AGROW>
 end
 assert(processed==.03,'M3:SyntheticHorizon','Final processed major is not frozen synthetic horizon.');
 if ~strcmp(s.Status,'inactive'),stop(s);end % Final lifecycle may already be inactive.
 BTMS_M3_events('close');
 for k=1:4
  d=load(files{k});ts=d.(['native' num2str(k)]);
  assert(isa(ts,'timeseries')&&numel(ts.Time)>2&&ts.Time(1)==0&&...
   all(isfinite(ts.Time))&&all(diff(ts.Time)>=0)&&...
   abs(ts.Time(end)-.03)<=32*eps(1),...
   'M3:Native','ToFile full stream or independent native clock failed.');
  nativeClock{k}=ts.Time; %#ok<AGROW> private exact clock, no interpolation
 end
 save(fullfile(root,'PROBE_CHECKPOINTS.mat'),'checkpoints','nativeClock','lifecycle','-v7.3');
 flags.status='M3_LOGGER_CLOCK_STATE_FIRST_PAUSED_OP_ONLY';
 flags.unboundedToFileWithBoundedDataset=true;flags.actualCompletedMajor=true;
 flags.discreteRoleClocks=true;flags.actualPhaseDState=true;
 flags.firstPausedOperatingPoint=true;flags.fullT0OperatingPoint=false;
catch err
 flags.stage=stage;
 flags.identifier=err.identifier;
 flags.reason=err.message; % Full diagnostic remains PRIVATE only.
 safeStage=regexprep(stage,'[^A-Za-z0-9_]','_');
 safeID=regexprep(err.identifier,'[^A-Za-z0-9_:]','_');
 if isempty(safeID),safeID='EMPTY_ERROR_IDENTIFIER';end
 fprintf('M3_SYNTHETIC_INFRA_UNQUALIFIED stage=%s identifier=%s\n',safeStage,safeID);
 % Preserve observed lifecycle BEFORE cleanup. Never infer a missing final flag.
 if ~isempty(s)
  try
   lifecycle=struct('returnedSimulationTime',s.Time,'simulationStatus',char(s.Status));
   if exist('processed','var'),lifecycle.processedPriorTop=processed;end
   if exist('finalstep','var'),lifecycle.finalStepReturned=finalstep;end
   if exist('majorCount','var'),lifecycle.majorCount=majorCount;end
   if ~exist('checkpoints','var'),checkpoints={};end
   save(fullfile(root,'PROBE_PARTIAL_LIFECYCLE.mat'),'lifecycle','checkpoints','-v7.3');
  catch evidenceErr
   flags.partialEvidenceIdentifier=evidenceErr.identifier;
  end
  try,if ~strcmp(s.Status,'inactive'),stop(s);end,catch,end
 end
 try
  nativeClock=cell(1,4);nativeLast=cell(1,4);
  for k=1:4
   if isfile(files{k})
    d=load(files{k});ts=d.(['native' num2str(k)]);
    nativeClock{k}=ts.Time;nativeLast{k}=ts.Data(end,:);
   end
  end
  save(fullfile(root,'PROBE_PARTIAL_NATIVE_CLOCKS.mat'),'nativeClock','nativeLast','-v7.3');
 catch evidenceErr
  flags.nativeEvidenceIdentifier=evidenceErr.identifier;
 end
 try,BTMS_M3_events('close');catch,end
end
fid=fopen(fullfile(root,'PROBE_FLAGS.json'),'w');
assert(fid>=0,'M3:PrivateFlags','Cannot preserve private diagnostic.');
fprintf(fid,'%s',jsonencode(flags));
fclose(fid);
diary off;
fprintf('M3_LOGGER_PROBE status=%s physicalRun=0 G5_ACCEPTED=false\n',flags.status);
end
