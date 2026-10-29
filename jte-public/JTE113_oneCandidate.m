function JTE113_oneCandidate()
% ONE conditional trajectory. No sim(), retry, original rerun or solver sweep.
root=pwd;priv=fullfile(root,'jte113-private');run=getenv('GITHUB_RUN_ID');
prefix=fullfile(priv,['JTE113_' run]);pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
model='JTE101Original';file=fullfile(priv,[model '.slx']);vendor=fullfile(root,'vendor-pack');
S=[];project=[];begun=false;finished=false;majorCount=0;trace=struct([]);out=[];
flags=struct('DECISION','UNQUALIFIED','SOURCE_PARITY',false,'ENVELOPE_FIRST_WINDOW_CONDITIONAL','UNAVAILABLE',...
 'EXCURSION_PERSISTS','UNAVAILABLE','ACCEPTED_STEP_PROVENANCE','UNAVAILABLE',...
 'THERMAL_COMPARISON_NOT_AUTHORIZED',true,'G5_ACCEPTED',false,'simulationStarted',false,'horizonComplete',false);
record=struct('schema','JTE113_ONE_NUMERICAL_DISCRIMINATOR_NOT_G5','run',run,'commit',getenv('GITHUB_SHA'),...
 'sourceProtocolCommit','37ad014883c49686a35c5c78d6611e65472efe0f','sourceSLXSHA256',pin,...
 'originalReferenceRun','40449421507','G5_ACCEPTED',false);
try
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for k=1:numel(M.files)
  z=M.files(k);assert(strcmp(JTE2026sha256(fullfile(priv,z.local)),z.sha256),'JTE113:Source','Input hash changed.');
 end
 assert(M.resource.repositoryPublicVerifiedFromGithubEvent&&~M.resource.paidServices,'JTE113:Resource','Public free entitlement absent.');
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE113:Resource','Pinned R2024bUpdate10 unavailable.');
 [ok,~]=license('checkout','Simulink');assert(ok,'JTE113:Resource','Included Simulink license unavailable.');
 assert(exist('simulation','file')~=0,'JTE113:Unqualified','Documented Simulation interface missing.');
 assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE113:Source','Vendor source pin changed.');
 record.runtime=version;record.includedLicenseCheckout=true;record.resourcePolicy=M.resource;
 O=load(fullfile(priv,'original_raw.mat'),'record');o=O.record;
 assert(strcmp(o.schema,'JTE101_TF_340_RAW_NOT_G5')&&strcmp(o.role,'ORIGINAL340')&&...
  strcmp(o.sourceSHA256,pin)&&strcmp(o.modelSHA256,JTE2026sha256(file)),'JTE113:Source','Wrong original reference.');
 assert(o.observed.initialStateMapAvailable,'JTE113:Unqualified','Original complete saved-state map unavailable.');
 ref=struct('initialMap',o.observed.initialStateMap,'T0',o.observed.trueTemperature(1,:),...
  'x0',o.observed.state(1),'y0',o.observed.output(1),'C',o.calibration.C,...
  'loadSHA',o.prepared.loadSHA256,'modelSHA',o.modelSHA256,'workspaceSHA',o.prepared.workspaceSHA256,...
  'originalNativeRows',numel(o.observed.outputTime));
 record.reference=ref;record.referenceSourceConfig=o.prepared.beforeGraph.config;
 clear O o
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 assert(strcmp(JTE2026sha256(fullfile(priv,'source_workspace.mat')),ref.workspaceSHA),'JTE113:Source','Original full workspace snapshot mismatch.');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),value=W.workspaceSnapshot.(names{k});assignin('base',names{k},value);
  assert(isequaln(evalin('base',names{k}),value),'JTE113:Source','Source initialization variable not restored.');
 end
 load_system(file);
 assert(strcmp(get_param(model,'LoadInitialState'),'off'),'JTE113:Unqualified','External state input would change initialization.');
 tf=[model '/Battery Control/sensor dynamics 1'];core=[model '/Battery Control/FlwR_calc'];
 assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),...
  'JTE113:Source','Original TransferFcn changed.');
 ph=get_param(tf,'PortHandles');ch=get_param(core,'PortHandles');
 assert(src(ph.Inport(1))==ch.Outport(1),'JTE113:Source','Authentic source controller disconnected.');
 amb=[model '/Constant3'];
 assert(slResolve(get_param(amb,'Value'),amb)==300,'JTE113:Source','Source controller reference not300K.');
 record.controllerReferenceK=300;
 loadPath=which(get_param([model '/Current demand'],'FileName'));
 assert(~isempty(loadPath)&&strcmp(JTE2026sha256(loadPath),ref.loadSHA),'JTE113:Source','Original load differs.');
 before=JTE096_modelAudit(model);
 % Observers on existing source ports only, no block/edge/physics change.
 observer(1)=mark(src(ph.Inport(1)),'JTE113ActualInput');
 observer(2)=mark(ph.Outport(1),'JTE113Postfilter');
 blocks=find_system(model,'BlockType','ToWorkspace');idx=[];
 for k=1:numel(blocks),if strcmp(get_param(blocks{k},'VariableName'),'jteTtrue'),idx(end+1)=k;end;end %#ok<AGROW>
 assert(numel(idx)==1,'JTE113:Unqualified','Original T312 observer unavailable.');
 th=get_param(blocks{idx},'PortHandles');observer(3)=mark(src(th.Inport(1)),'JTE113T312');
 record.observerDelta=observer;
 S=simulation(model);
 assert(ismethod(S,'step')&&isprop(S,'SimulationOutput'),'JTE113:Unqualified','Documented major-step output API unavailable.');
 S=setModelParameter(S,'Solver','ode23tb','MaxStep','0.005','StartTime','0','StopTime','340',...
  'SimulationMode','normal','SaveState','on','StateSaveName','jte113States','SaveFormat','Dataset',...
  'SaveTime','on','TimeSaveName','tout','SignalLogging','on','SignalLoggingName','jte113Signals','ReturnWorkspaceOutputs','on');
 % initialize executes the full physical source initialization at t0, not a temperature-only restart.
 initialize(S);
 assert(strcmp(get_param(model,'Solver'),'ode23tb')&&strcmp(get_param(model,'RelTol'),'1e-3')&&...
  strcmp(get_param(model,'AbsTol'),'1e-3')&&str2double(get_param(model,'MaxStep'))==.005,...
  'JTE113:Unqualified','Effective solver/tolerances do not match frozen candidate.');
 assert(strcmp(get_param(model,'ZeroCrossControl'),'UseLocalSettings')&&strcmp(get_param(model,'SolverResetMethod'),'Fast'),...
  'JTE113:Unqualified','Original zero-cross/local reset configuration drifted.');
 assert(strcmp(get_param(model,'Refine'),'1'),'JTE113:Unqualified','Output refinement would confound checkpoint attribution.');
 afterInit=JTE096_modelAudit(model);
 assert(isequal(before.blocks,afterInit.blocks),'JTE113:Source','Model blocks changed.');
 record.initializationPolicy='Entire unchanged source model initialized at0 from frozen source workspace; no external operating point or330s temperature restart.';
 record.effectiveConfig=afterInit.config;
 stateWidth=0;for k=1:numel(ref.initialMap),stateWidth=stateWidth+numel(ref.initialMap(k).value);end
 projectedLogs=3*double(M.resource.maximumNativeRows)*8*(double(stateWidth)+312+8);
 [avail,total]=ram();
 % Conservative logging planning reserve + current compiled-model footprint +2GiB OS headroom.
 diskObject=java.io.File(priv);diskNow=double(diskObject.getUsableSpace());
 assert(diskNow>max(4*1024^3,2*projectedLogs),'JTE113:Resource','Current disk logging reserve insufficient.');
 elapsedPreflight=posixtime(datetime('now','TimeZone','UTC'))-M.resource.preflightUnixEpoch;
 assert(M.resource.runtimeLimit_s-elapsedPreflight>M.resource.simulationWallStop_s+300,'JTE113:Resource','Remaining wall-clock allowance insufficient.');
 assert(avail>projectedLogs+2*1024^3,'JTE113:Resource','Available RAM does not cover source-state logging reserve.');
 assert(M.resource.drive.availableBytes>max(2*1024^3,projectedLogs),'JTE113:Resource','Private sink reserve insufficient.');
 record.resourcePreflight=struct('availableRAMAfterInitialize_bytes',avail,'totalRAM_bytes',total,...
  'sourceSavedStateWidth',stateWidth,'loggingReserve_bytes',projectedLogs,'diskFreeAfterInitialize_bytes',diskNow,...
  'remainingWorkflowWallProxy_s',M.resource.runtimeLimit_s-elapsedPreflight,...
  'planningMethod','Three numeric copies at200000-row safety cap; not a measured candidate peak. Runtime guards below stop rather than tune.',...
  'maximumRows',M.resource.maximumNativeRows,'wallStop_s',M.resource.simulationWallStop_s);
 record.acceptedLoggerContract=struct('publicAPI','Simulink.Simulation.step',...
  'scope','Completed-major-step output/state checkpoints in330–338 only, not callback/native-row equivalence or internal rejected-stage history.',...
  'documentation','https://www.mathworks.com/help/simulink/slref/simulink.simulation.step.html',...
  'timeRule','Capture the prior S.Time as processed major time; after step returns, last logged output/state time must equal that prior time. Current S.Time is next top-of-step.');
 marker=fullfile(priv,'ODE23TB_TIME_ADVANCEMENT_ENTERED.json');
 assert(~isfile(marker),'JTE113:Unqualified','Attempt already entered.');
 writeJSON(marker,struct('run',run,'phase','ONE_TIME_ADVANCEMENT_ATTEMPT','repeatAuthorized',false));
 begun=true;flags.simulationStarted=true;timer=tic;
 fprintf('JTE113_ONE_CANDIDATE_TIME_ADVANCEMENT_START noOriginalRerun=1 sourcePinned=1 sourceInitializationRestored=1 solver=ode23tb maxStep005=1\n');
 % First completed major-step record must establish the actual initial source state map.
 expectedTime=S.Time;finished=step(S);majorCount=majorCount+1;
 q=checkpoint(S,expectedTime,tf);
 ds=S.SimulationOutput.get('jte113States');currentMap=initialMap(ds);
 assert(mapsEqual(ref.initialMap,currentMap)&&isequal(q.T312,ref.T0)&&q.x==ref.x0&&q.y==ref.y0,...
  'JTE113:Unqualified','Complete saved initial-state map differs; no additional time advancement.');
 record.initialSavedStateMapExact=true;
 record.hiddenICScope='All original saved Dataset state keys/values and source initialization policy matched. Unrepresented algebraic states are not independently bitwise certified; not a G5 IC certificate.';
 flags.SOURCE_PARITY=true;
 tfIndex=q.stateIndex;trace=q;trace(1).phase='INITIAL_COMPLETED_MAJOR_STEP';
 firstRows=0;
 while ~finished
  assert(toc(timer)<M.resource.simulationWallStop_s,'JTE113:Resource','One-shot wall budget reached.');
  [avail,~]=ram();assert(avail>1024^3,'JTE113:Resource','RAM headroom exhausted.');
  expectedTime=S.Time;
  if expectedTime>=330&&expectedTime<=338
   finished=step(S);majorCount=majorCount+1;
   q=checkpoint(S,expectedTime,tf,tfIndex);q.phase='FIRST_WINDOW_COMPLETED_MAJOR_STEP';
   firstRows=firstRows+1;trace(end+1)=q; %#ok<AGROW>
  elseif expectedTime>=340
   finished=step(S);majorCount=majorCount+1;
  else
   target=min(340,expectedTime+5);
   if expectedTime<330,target=min(330,target);end
   finished=step(S,'PauseTime',target);
   % Bulk progression provides native logs; it is deliberately NOT labeled per-step accepted evidence.
  end
  partial=S.SimulationOutput;
  if any(strcmp(who(partial),'tout')),nt=numel(partial.get('tout'));assert(nt<=M.resource.maximumNativeRows,'JTE113:Resource','Native-row cap reached.');end
  if mod(firstRows,250)==0&&firstRows>0
   fprintf('JTE113_COMPLETED_MAJOR_CHECKPOINTS_PROGRESS scope=FIRST_WINDOW privacy=METADATA_ONLY\n');
  end
 end
 out=stop(S);record.wallTime_s=toc(timer);record.completedMajorCheckpoints=trace;
 record.majorStepFunctionCalls=majorCount;flags.horizonComplete=true;
 fprintf('JTE113_ONE_CANDIDATE_TIME_ADVANCEMENT_RETURNED horizon340=1 noRetry=1\n');
catch ME
 record.failure=struct('identifier',ME.identifier,'message',ME.message,'phaseTimeAdvancementEntered',begun);
 if startsWith(ME.identifier,'JTE113:Resource')||(~begun&&contains(lower(ME.message),'license'))
  flags.DECISION='BLOCKED_RESOURCE_NOT_QUALIFIED';
 else,flags.DECISION='UNQUALIFIED';end
end
% Persist original MATLAB output before any acceptance/scientific assertion.
try
 if ~isempty(S)&&isempty(out),out=stop(S);end
catch,try,out=S.SimulationOutput;catch,end;end
record.simulationOutput=out;record.completedMajorCheckpoints=trace;record.simulationStarted=begun;record.flags=flags;
raw=fullfile(priv,['JTE113_' run '_CANDIDATE_RAW.mat']);save(raw,'record','-v7.3');
try
 if begun&&finished&&flags.SOURCE_PARITY
  d=native(out,tf,ref.C);
  assert(d.time(1)==0&&d.time(end)==340&&size(d.T312,2)==312,'JTE113:Unqualified','Incomplete candidate native horizon/vector.');
  assert(d.clocksExact&&isequal(d.input,d.core),'JTE113:Unqualified','Native clock/actual-input coherence failed.');
  assert(all(abs(d.output-ref.C*d.state)<=1e-9),'JTE113:Unqualified','Saved native TF-state/output calibration mismatch.');
  assert(numel(trace)>1&&any([trace.time]>=330&[trace.time]<=334)&&any([trace.time]>334&[trace.time]<=338),...
   'JTE113:Unqualified','Documented completed-major checkpoints do not cover control and anomaly windows.');
  assert(strcmp(JTE2026sha256(file),ref.modelSHA)&&strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
   'JTE113:Source','Original/vendor model bytes changed.');
  e=envelope(d.time,d.output);w=d.time>=330&d.time<=338;nc=d.time>=330&d.time<=334;
  % Envelope uses actual time0 y0, including for window checkpoints.
  ey=envelopeAt([trace.time]',[trace.y]',d.output(1));
  gap=abs(d.output-d.core);
  flags.ENVELOPE_FIRST_WINDOW_CONDITIONAL=ternary(any(e.flag(w)),'FLAGGED_NATIVE','NOT_FLAGGED_NATIVE');
  flags.EXCURSION_PERSISTS=any(gap(w)>.005)||any(e.flag(w));
  flags.ACCEPTED_STEP_PROVENANCE='DOCUMENTED_COMPLETED_MAJOR_STEP_CHECKPOINTS_FIRST_WINDOW_ONLY';
  if any(e.flag)||flags.EXCURSION_PERSISTS
   flags.DECISION='DISCRIMINATOR_NEGATIVE';
  else,flags.DECISION='DISCRIMINATOR_POSITIVE_CONDITIONAL';end
  record.observed=d;record.conditionalEnvelope=e;record.checkpointEnvelope=ey;
  record.windowSummary=struct('globalOutside',any(e.flag),'firstOutside',any(e.flag(w)),...
   'negativeControlOutside',any(e.flag(nc)),'startupOutside',any(e.flag(d.time<330)),...
   'firstLocalizationExcursion',any(gap(w)>.005),'checkpointFirstOutside',any(ey.flag([trace.time]'>=330&[trace.time]'<=338)),...
   'marginRole','32ULP normalized interval localization ONLY, not solver/thermal acceptance tolerance',...
   'hiddenICScope',record.hiddenICScope,'G5_ACCEPTED',false);
 end
catch ME
 record.qualificationFailure=struct('identifier',ME.identifier,'message',ME.message);flags.DECISION='UNQUALIFIED';
end
record.flags=flags;save(raw,'record','-v7.3');
writeJSON(fullfile(priv,['JTE113_' run '_PRIVATE_FLAGS.json']),flags);
summary=struct('flags',flags,'simulationStarted',begun,'horizonComplete',flags.horizonComplete,'G5_ACCEPTED',false);
if isfield(record,'resourcePreflight'),summary.resources=record.resourcePreflight;end
if isfield(record,'windowSummary'),summary.windowSummary=record.windowSummary;end
if isfield(record,'failure'),summary.failure=record.failure;end
if isfield(record,'qualificationFailure'),summary.qualificationFailure=record.qualificationFailure;end
writeJSON(fullfile(priv,['JTE113_' run '_PRIVATE_SUMMARY.json']),summary);
fprintf('JTE113_RESULT DECISION=%s SOURCE_PARITY=%d ENVELOPE_FIRST_WINDOW_CONDITIONAL=%s EXCURSION_PERSISTS=%s ACCEPTED_STEP_PROVENANCE=%s THERMAL_COMPARISON_NOT_AUTHORIZED=true simulationStarted=%d horizonComplete=%d G5_ACCEPTED=false\n',...
 flags.DECISION,flags.SOURCE_PARITY,flags.ENVELOPE_FIRST_WINDOW_CONDITIONAL,flagText(flags.EXCURSION_PERSISTS),flags.ACCEPTED_STEP_PROVENANCE,begun,flags.horizonComplete);
try,if ~isempty(S)&&~strcmp(S.Status,'inactive'),terminate(S);end;catch,end
try,close_system(model,0);catch,end
try,if ~isempty(project),close(project);end;catch,end
end
function h=src(dst)
line=get_param(dst,'Line');assert(line~=-1,'JTE113:Source','Missing source edge.');h=get_param(line,'SrcPortHandle');
end
function o=mark(port,name)
o=struct('portParent',get_param(port,'Parent'),'beforeDataLogging',get_param(port,'DataLogging'),...
 'beforeName',get_param(port,'DataLoggingName'),'newName',name);
set_param(port,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName',name,...
 'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
end
function [t,v]=last(ts)
t=ts.Time(end);a=ts.Data;N=numel(ts.Time);
if ts.IsTimeFirst,a=reshape(a,N,[]);else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),N,[]);end
v=a(end,:);
end
function q=checkpoint(s,expected,tf,ix)
o=s.SimulationOutput;logs=o.get('jte113Signals');
sig=logs.getElement('JTE113ActualInput');[t,u]=last(sig.Values);
sig=logs.getElement('JTE113Postfilter');[ty,y]=last(sig.Values);
sig=logs.getElement('JTE113T312');[tt,T]=last(sig.Values);
ds=o.get('jte113States');
if nargin<4
 ix=[];for k=1:ds.numElements,el=ds.getElement(k);
  if el.BlockPath.getLength()==1&&strcmp(char(el.BlockPath.getBlock(1)),tf),ix(end+1)=k;end %#ok<AGROW>
 end
 assert(numel(ix)==1,'JTE113:Unqualified','Exact TF state not available at completed step.');
end
el=ds.getElement(ix);[tx,x]=last(el.Values);
assert(t==expected&&ty==expected&&tt==expected&&tx==expected&&numel(T)==312,...
 'JTE113:Unqualified','Completed-major output/state times do not match processed prior S.Time.');
q=struct('time',t,'nextTopOfStepTime',s.Time,'inputCore',u,'y',y,'x',x,'T312',T,'stateIndex',ix,'phase','');
end
function v=initialMap(ds)
v=struct('key',{},'time',{},'value',{});
for k=1:ds.numElements
 el=ds.getElement(k);paths={};for z=1:el.BlockPath.getLength(),paths{z}=char(el.BlockPath.getBlock(z));end %#ok<AGROW>
 ts=el.Values;a=ts.Data;N=numel(ts.Time);
 if ts.IsTimeFirst,a=reshape(a,N,[]);else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),N,[]);end
 key=strrep([strjoin(paths,'::') '|' char(el.Name)],'JTE101Original','$ROOT');
 v(end+1)=struct('key',key,'time',ts.Time(1),'value',a(1,:)); %#ok<AGROW>
end
end
function b=mapsEqual(a,c)
b=false;[ka,ia]=sort({a.key});[kc,ic]=sort({c.key});
if ~isequal(ka,kc),return;end
for k=1:numel(ia),if a(ia(k)).time~=0||c(ic(k)).time~=0||~isequaln(a(ia(k)).value,c(ic(k)).value),return;end;end
b=true;
end
function d=native(o,tf,C)
[t,u]=JTE2026timeseries(o,'jteUcore');[ty,y]=JTE2026timeseries(o,'jteFlwR');[tt,T]=JTE2026timeseries(o,'jteTtrue');
logs=o.get('jte113Signals');el=logs.getElement('JTE113ActualInput');v=el.Values;
[ti,a]=JTE056normalize(v.Time,v.Data,v.IsTimeFirst);
ds=o.get('jte113States');found=0;
for k=1:ds.numElements,el=ds.getElement(k);
 if el.BlockPath.getLength()==1&&strcmp(char(el.BlockPath.getBlock(1)),tf)
  found=found+1;[tx,x]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
 end
end
assert(found==1,'JTE113:Unqualified','Native TF state unavailable.');
d=struct('time',t,'core',u,'output',y,'input',a,'state',x,'T312',T,'stateOutputGain',C,...
 'clocksExact',isequal(t,ty)&&isequal(t,tt)&&isequal(t,ti)&&isequal(t,tx));
end
function e=envelope(t,y)
e=envelopeAt(t,y,y(1));
end
function e=envelopeAt(t,y,y0)
a=-expm1(-t/.001);lo=y0+(.25-y0)*a;hi=y0+(.75-y0)*a;
margin=32*eps(max([ones(size(t)),abs(y),abs(lo),abs(hi),abs(y0)*ones(size(t))],[],2));
ex=max([lo-y,y-hi,zeros(size(t))],[],2);
e=struct('time',t,'y0',y0,'lower',lo,'upper',hi,'margin32ULP',margin,'excess',ex,...
 'flag',y<lo-margin|y>hi+margin,'scope','Conditional exact LTI necessary envelope, not solver/thermal tolerance.');
end
function [a,b]=ram()
s=fileread('/proc/meminfo');a=str2double(regexp(s,'MemAvailable:\s+(\d+)','tokens','once'))*1024;
b=str2double(regexp(s,'MemTotal:\s+(\d+)','tokens','once'))*1024;
end
function t=flagText(x)
if islogical(x)||isnumeric(x),t=sprintf('%d',x);else,t=char(x);end
end
function t=ternary(b,a,c)
if b,t=a;else,t=c;end
end
function writeJSON(path,v)
f=fopen(path,'w');assert(f~=-1,'JTE113:Resource','Private write unavailable.');
fprintf(f,'%s',jsonencode(v));fclose(f);
end
