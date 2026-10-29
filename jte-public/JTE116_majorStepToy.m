function JTE116_majorStepToy()
% NEW non-plant API/clock qualification, not a controller/filter/plant study.
root=pwd;priv=fullfile(root,'jte116-one-private');prefix=fullfile(priv,['JTE116ONE_' getenv('GITHUB_RUN_ID') '_TOY']);
m='JTE116_COMPLETED_MAJOR_TOY';S=[];out=[];trace=struct([]);flags=struct('LOGGER_QUALIFIED',false,'PHYSICAL_SIMULATION_STARTED',false,'G5_ACCEPTED',false);
r=struct('scope','Non-plant toy only','runtime',version,'physicalSimulation',false);finished=false;
try
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE116:Resource','Pinned runtime unavailable.');
 new_system(m);set_param(m,'Solver','ode23t','MaxStep','.0005','RelTol','1e-3','AbsTol','1e-3','Refine','1');
 add_block('simulink/Sources/Ramp',[m '/Drive'],'slope','.01','start','0','InitialOutput','.25');
 add_block('simulink/Continuous/Transfer Fcn',[m '/Filter'],'Numerator','[1]','Denominator','[.001 1]');
 add_block('simulink/Sources/Clock',[m '/Q']);
 add_block('simulink/Math Operations/Gain',[m '/QStar'],'Gain','1');
 add_block('simulink/Math Operations/Gain',[m '/Vector'],'Gain','ones(312,1)','Multiplication','Element-wise(K.*u)');
 add_block('simulink/Sinks/To Workspace',[m '/Core'],'VariableName','jteUcore','SaveFormat','Timeseries');
 add_block('simulink/Sinks/To Workspace',[m '/Y'],'VariableName','jteFlwR','SaveFormat','Timeseries');
 add_block('simulink/Sinks/To Workspace',[m '/T'],'VariableName','jteTtrue','SaveFormat','Timeseries');
 add_line(m,'Drive/1','Filter/1');add_line(m,'Drive/1','Core/1');
 add_line(m,'Filter/1','Vector/1');add_line(m,'Filter/1','Y/1');add_line(m,'Vector/1','T/1');add_line(m,'Q/1','QStar/1');
 blocks={'Drive','Filter','Q','QStar','Vector'};names={'JTE116ActualInput','JTE116Postfilter','JTE116Q','JTE116QStar','JTE116T312'};
 for k=1:5,h=get_param([m '/' blocks{k}],'PortHandles');mark(h.Outport(1),names{k});end
 save_system(m,[prefix '_MODEL.slx']); % Save-as changes root name: use actual loaded model below.
 [~,savedName]=fileparts([prefix '_MODEL.slx']);
 if bdIsLoaded(savedName),m=savedName;end
 S=simulation(m);S=setModelParameter(S,'StartTime','0','StopTime','.02','SimulationMode','normal',...
  'SaveState','on','StateSaveName','jte116States','SaveFormat','Dataset','SaveTime','on','TimeSaveName','tout',...
  'SignalLogging','on','SignalLoggingName','jte116Signals','ReturnWorkspaceOutputs','on');
 initialize(S);r.initializedTime=S.Time;r.preAdvanceOutputAvailable=false;
 try,JTE116_completedMajor(S,0,[m '/Filter']);r.preAdvanceOutputAvailable=true;catch,r.preAdvanceOutputScope='Not available/certified while initialized; first completed major0 is qualified separately.';end
 before=S.Time;assert(before==0,'JTE116:Logging','Toy initial top-of-step not0.');
 finished=step(S);q=JTE116_completedMajor(S,before,[m '/Filter']);q.phase='COMPLETED_INITIAL_MAJOR0';trace=q;
 finished=step(S,PauseTime=.005);
 r.bulkPause=struct('nextTop',S.Time,'scope','Bulk native progress only, not an individual accepted record.');
 while ~finished&&S.Time<=.008
  before=S.Time;finished=step(S);q=JTE116_completedMajor(S,before,[m '/Filter']);q.phase='COMPLETED_WINDOW_MAJOR';trace(end+1)=q; %#ok<AGROW>
  assert(numel(trace)<10000,'JTE116:Logging','Toy checkpoint limit.');
 end
 if ~finished,finished=step(S,PauseTime=.02);end
 if ~finished,before=S.Time;finished=step(S);q=JTE116_completedMajor(S,before,[m '/Filter']);q.phase='COMPLETED_FINAL_MAJOR';trace(end+1)=q;end
 assert(finished,'JTE116:Logging','Toy final step not completed.');
 out=stop(S);d=JTE116_nativeData(out,[m '/Filter'],m);
 assert(d.time(1)==0&&d.time(end)==.02&&d.clocksExact&&size(d.T312,2)==312&&numel(trace)>3,...
  'JTE116:Logging','Toy horizon/native clock/vector qualification failed.');
 assert(any([trace.time]>=.005&[trace.time]<=.008),'JTE116:Logging','Toy accepted window unavailable.');
 flags.LOGGER_QUALIFIED=true;r.observed=d;
catch ME
 r.failure=struct('identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
end
try,if ~isempty(S)&&isempty(out),out=stop(S);end;catch,try,out=S.SimulationOutput;catch,end;end
r.flags=flags;r.checkpoints=trace;r.simulationOutput=out;save([prefix '_RAW.mat'],'r','-v7.3');
writeJSON([prefix '_FLAGS.json'],flags);
summary=struct('flags',flags);if isfield(r,'failure'),summary.failure=r.failure;end
if isfield(r,'preAdvanceOutputAvailable'),summary.preAdvanceOutputAvailable=r.preAdvanceOutputAvailable;end
writeJSON([prefix '_SUMMARY.json'],summary);
try,if ~isempty(S)&&~strcmp(S.Status,'inactive'),terminate(S);end;catch,end
try,close_system(m,0);catch,end
end
function mark(p,n)
set_param(p,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName',n,'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'JTE116:Resource','Private toy write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
