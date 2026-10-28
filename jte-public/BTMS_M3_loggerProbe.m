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
 stage='SYNTHETIC_FIRST_COMPLETED_MAJOR';processed=s.Time;step(s);q0=BTMS_M3_completed(s,processed);
 stage='T0_OPERATING_POINT';op0=get_param(m,'CurrentOperatingPoint');save(fullfile(root,'PROBE_T0_OPERATING_POINT.mat'),'op0','q0','-v7.3');
 assert(isa(op0,'Simulink.op.ModelOperatingPoint')&&op0.snapshotTime==0,'M3:OP','t0 operating point unavailable.');
 stage='SYNTHETIC_NATIVE_HORIZON';checkpoints={q0};
 while strcmp(s.Status,'paused')
  processed=s.Time;step(s);
  if strcmp(s.Status,'paused'),checkpoints{end+1}=BTMS_M3_completed(s,processed);end %#ok<AGROW>
 end
 BTMS_M3_events('close');
 for k=1:4
  d=load(files{k});ts=d.(['native' num2str(k)]);
  assert(isa(ts,'timeseries')&&numel(ts.Time)>2&&ts.Time(1)==0&&ts.Time(end)==.03,...
   'M3:Native','ToFile full stream was truncated or horizon missing.');
 end
 save(fullfile(root,'PROBE_CHECKPOINTS.mat'),'checkpoints','-v7.3');
 flags.status='M3_LOGGER_CLOCK_STATE_OP_QUALIFIED';
 flags.unboundedToFileWithBoundedDataset=true;flags.actualCompletedMajor=true;
 flags.discreteRoleClocks=true;flags.actualPhaseDState=true;flags.fullT0OperatingPoint=true;
catch err
 flags.stage=stage;flags.identifier=err.identifier;flags.reason=err.message;
 % Synthetic fixture only: an allowlisted identifier is safe if private delivery fails.
 if ~isempty(regexp(err.identifier,'^[A-Za-z][A-Za-z0-9_:]*
 if ~isempty(s),try,stop(s);catch,end,end
 try,BTMS_M3_events('close');catch,end
end
fid=fopen(fullfile(root,'PROBE_FLAGS.json'),'w');fprintf(fid,'%s',jsonencode(flags));fclose(fid);
diary off;
fprintf('M3_LOGGER_PROBE status=%s physicalRun=0 G5_ACCEPTED=false\n',flags.status);
end
,'once'))
  fprintf('M3_SYNTHETIC_INFRA_UNQUALIFIED stage=%s identifier=%s\n',stage,err.identifier);
 end
 if ~isempty(s),try,stop(s);catch,end,end
 try,BTMS_M3_events('close');catch,end
end
fid=fopen(fullfile(root,'PROBE_FLAGS.json'),'w');fprintf(fid,'%s',jsonencode(flags));fclose(fid);
diary off;
fprintf('M3_LOGGER_PROBE status=%s physicalRun=0 G5_ACCEPTED=false\n',flags.status);
end
