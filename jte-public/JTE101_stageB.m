function JTE101_stageB(mode)
% Frozen bounded diagnostic, not a solver sweep or G5 acceptance.
P=paths();manifest=jsondecode(fileread(fullfile(P.private,'stage_b_manifest.json')));
assert(strcmp(JTE2026sha256(P.audit),manifest.audit.sha256),'JTE101:AuditSHA','Private Stage A audit changed.');
S=load(P.audit,'audit');A=S.audit;
assert(strcmp(A.run,getenv('JTE101_AUDIT_RUN')),'JTE101:AuditRun','Wrong accepted Stage A audit.');
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE101:Runtime','Wrong runtime.');
assert(strcmp(A.referenceSchema,'PASS')&&A.original340Required&&~A.referenceTFStateAvailable,'JTE101:StageAGate','No qualified authorization for paired original.');
assert(strcmp(JTE2026sha256(P.source),P.pin),'JTE101:Pin','Wrong source bytes.');
project=openProject(fullfile(P.vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()quietProject(project)); %#ok<NASGU>
if strcmp(mode,'prepare'),prepare(P,A);return;end
restoreWorkspace(P);
if strcmp(mode,'workspacecheck')
 for roleName={'original','constant'}
  label=roleName{1};model=['JTE101' upper(label(1)) label(2:end)];
  load_system(fullfile(P.generated,[model '.slx']));
  verifyConfig(model,A.primary.solver);
  set_param(model,'SimulationCommand','update');
  quietModel(model);
 end
 copyfile(fullfile(P.private,'prepared.mat'),fullfile(P.private,['JTE101_' P.run '_PREPARE_STATE.mat']));
 writeJSON(fullfile(P.private,['JTE101_' P.run '_PREPARE_FLAGS.json']),...
  struct('snapshotRestored',true,'bothRolesCompiled',true,'simulationRun',false,'G5_ACCEPTED',false));
 fprintf('JTE101_WORKSPACE_RESTORE_COMPILE_PASS bothRoles=1 originalFrozenValuesPreserved=1 simulationRun=0\n');
 return;
end
assert(any(strcmp(mode,{'original','constant'})),'JTE101:Role','Unknown role.');
role=upper([mode '340']);model=['JTE101' upper(mode(1)) mode(2:end)];
file=fullfile(P.generated,[model '.slx']);
Q=load(fullfile(P.private,'prepared.mat'),'prepared');prepared=Q.prepared;
assert(strcmp(JTE2026sha256(file),prepared.modelSHA.(mode)),'JTE101:ModelSHA','Prepared model changed.');
load_system(file);mg=onCleanup(@()quietModel(model)); %#ok<NASGU>
tf=[model '/Battery Control/sensor dynamics 1'];ctrl=[model '/Battery Control'];core=[ctrl '/FlwR_calc'];
verifyTF(tf);verifyConfig(model,A.primary.solver);
th=get_param(tf,'PortHandles');ch=get_param(core,'PortHandles');
if strcmp(mode,'constant')
 c=get_param([ctrl '/JTE101 TF Constant'],'PortHandles');
 assert(source(th.Inport(1))==c.Outport(1),'JTE101:ConstantWire','Constant not directly feeding TF.');
 assert(strcmp(get_param([ctrl '/JTE101 TF Constant'],'Value'),'0.25')&&strcmp(get_param([ctrl '/JTE101 TF Constant'],'SampleTime'),'0'),'JTE101:ConstantDefinition','Wrong diagnostic constant.');
else
 assert(source(th.Inport(1))==ch.Outport(1),'JTE101:ReferenceWire','Original TF input changed.');
end
command=get_param([ctrl '/JTE Command'],'PortHandles');
assert(source(command.Inport(1))==ch.Outport(1),'JTE101:CoreLogger','Authentic controller logger changed.');
startMarker=fullfile(P.private,[role '_MATLAB_ENTERED.json']);
assert(~isfile(startMarker),'JTE101:RepeatDenied','Role was already attempted in this run.');
writeJSON(startMarker,struct('role',role,'phase','SIM_CALL_ENTERED','run',P.run,'commit',P.commit));
input=Simulink.SimulationInput(model);
input=input.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
 'SaveState','on','StateSaveName','jte101XStates','SaveFormat','Dataset',...
 'SaveTime','on','TimeSaveName','tout','SignalLogging','on','SignalLoggingName','jte101InputLogs');
before=JTE096_modelAudit(model);
fprintf('JTE101_BOUNDED_SIM_CALL_START role=%s horizon340=1 sourcePinned=1 solverUnchanged=1 privacyRetentionRequired=1\n',role);
out=sim(input);
fprintf('JTE101_BOUNDED_SIM_RETURNED role=%s resultCaptured=1\n',role);
% Persist every captured field BEFORE any scientific/instrumentation qualification.
record=struct('schema','JTE101_TF_340_RAW_NOT_G5','role',role,'simulationOutput',out,...
 'sourceSHA256',P.pin,'modelSHA256',JTE2026sha256(file),'run',P.run,'commit',P.commit,...
 'inputOverrides',{input.ModelParameters},'sourceAuditRun',A.run,'sourceAuditInputManifest',A.inputManifest,...
 'prepared',prepared,'beforeConfig',{before.config},'acceptedStepCertification','UNAVAILABLE',...
 'diagnosticIntervention',strcmp(mode,'constant'),'G5_ACCEPTED',false);
raw=fullfile(P.private,['JTE101_' P.run '_' role '_RAW.mat']);
save(raw,'record','-v7.3');
copyfile(file,fullfile(P.private,['JTE101_' P.run '_' role '_MODEL.slx']));
after=JTE096_modelAudit(model);
assert(isequal(before.config,after.config),'JTE101:SolverDrift','Solver/model-IC declaration changed.');
assert(strcmp(JTE2026sha256(P.source),P.pin),'JTE101:SourceChanged','Vendor changed.');
data=extract(out,model);
record.observed=data;
if strcmp(mode,'original')
 record.qualification=qualifyOriginal(data,A);
 record.calibration=record.qualification.calibration;
 save(raw,'record','-v7.3');
 summary=struct('role',role,'executed',true,'qualified',record.qualification.qualified,...
  'eventReproduced',record.qualification.eventReproduced,'stateClockQualified',data.clocksQualified,...
  'G5','BLOCKED');
 writeJSON(fullfile(P.private,['JTE101_' P.run '_' role '_FLAGS.json']),summary);
 fprintf('JTE101_ORIGINAL340_RESULT executed=1 qualified=%d firstEventReproduced=%d nativeClocksQualified=%d stateOutputQualified=%d G5=BLOCKED\n',...
  summary.qualified,summary.eventReproduced,data.clocksQualified,record.qualification.stateOutputQualified);
 assert(summary.qualified,'JTE101:OriginalInconclusive','Original reference is not qualified; do not run constant or rerun original.');
else
 O=load(fullfile(P.private,['JTE101_' P.run '_ORIGINAL340_RAW.mat']),'record');
 record.comparison=compareConstant(O.record,data);
 save(raw,'record','-v7.3');
 c=record.comparison;
 summary=struct('CONSTANT_340',c.status,'EXCURSION',c.excursion,'LOCALIZATION',c.localization,...
  'RESET_ACTOR','UNAVAILABLE','SECOND_EVENT','NOT_COVERED','G5','BLOCKED',...
  'capturedInputConstant',c.inputConstant,'nativeClocksQualified',data.clocksQualified,...
  'initialStateQualified',c.initialQualified,'stateOutputQualified',c.stateOutputQualified);
 writeJSON(fullfile(P.private,['JTE101_' P.run '_' role '_FLAGS.json']),summary);
 fprintf('JTE101_CONSTANT340_RESULT CONSTANT_340=%s EXCURSION=%s LOCALIZATION=%s capturedInputConstant=%d nativeClocksQualified=%d initialStateQualified=%d stateOutputQualified=%d RESET_ACTOR=UNAVAILABLE SECOND_EVENT=NOT_COVERED G5=BLOCKED\n',...
 c.status,c.excursion,c.localization,c.inputConstant,data.clocksQualified,c.initialQualified,c.stateOutputQualified);
end
fprintf('JTE101_BOUNDED_RAW_RETAINED_LOCALLY role=%s nextRequired=PRIVATE_SHA_READBACK acceptedStepCertification=UNAVAILABLE\n',role);
end
function prepare(P,A)
assert(~isfolder(P.generated),'JTE101:Fresh','Fresh generated directory required.');
files=JTE056build(P.vendor,P.generated);
baselineHash=JTE2026sha256(files.baseline);
names={'JTE101Original','JTE101Constant'};
for k=1:2
 copyfile(files.baseline,fullfile(P.generated,[names{k} '.slx']));
 load_system(fullfile(P.generated,[names{k} '.slx']));
end
g=onCleanup(@()closePair(names)); %#ok<NASGU>
o=names{1};d=names{2};ot=[o '/Battery Control/sensor dynamics 1'];dt=[d '/Battery Control/sensor dynamics 1'];
verifyTF(ot);verifyTF(dt);verifyConfig(o,A.primary.solver);verifyConfig(d,A.primary.solver);
ctrl=[d '/Battery Control'];core=[ctrl '/FlwR_calc'];
dh=get_param(dt,'PortHandles');ch=get_param(core,'PortHandles');
assert(source(dh.Inport(1))==ch.Outport(1),'JTE101:OriginalGraph','Source TF is not connected directly to original core.');
originalEdges=JTE096_signalEdges([o '/Battery Control']);
cb=[ctrl '/JTE101 TF Constant'];
add_block('simulink/Sources/Constant',cb,'Value','0.25','SampleTime','0');
cp=get_param(cb,'PortHandles');
delete_line(ctrl,ch.Outport(1),dh.Inport(1));
add_line(ctrl,cp.Outport(1),dh.Inport(1),'autorouting','on');
newEdges=JTE096_signalEdges(ctrl);
old='FlwR_calc:1>sensor dynamics 1:1';new='JTE101 TF Constant:1>sensor dynamics 1:1';
assert(sum(strcmp(originalEdges,old))==1&&isequal(sort([setdiff(originalEdges,{old});{new}]),newEdges),'JTE101:EdgeDelta','More than intended one-edge substitution.');
oa=JTE096_modelAudit(o);da=JTE096_modelAudit(d,{cb});
assert(isequal(oa.blocks,da.blocks)&&isequal(oa.config,da.config),'JTE101:Parameters','Retained physical parameters/declared IC/solver differ.');
omit={'$ROOT/Battery Control/FlwR_calc','$ROOT/Battery Control/sensor dynamics 1'};
oc=oa.connectivity(~ismember(oa.connectivity(:,1),omit),:);
dc=da.connectivity(~ismember(da.connectivity(:,1),omit),:);
assert(isequal(oc,dc),'JTE101:OutsideGraph','External physical/control graph changed.');
% Only add observer metadata on the actual TF input source port; no observer edge.
for k=1:2
 m=names{k};tf=[m '/Battery Control/sensor dynamics 1'];h=get_param(tf,'PortHandles');src=source(h.Inport(1));
 loggingBefore.(m)=struct('DataLogging',get_param(src,'DataLogging'),...
  'NameMode',get_param(src,'DataLoggingNameMode'),'Name',get_param(src,'DataLoggingName')); %#ok<AGROW>
 set_param(src,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName','JTE101ActualTFInput',...
  'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
 assert(strcmp(get_param(src,'DataLogging'),'on'),'JTE101:InputLogging','Actual-input logging not enabled.');
 save_system(m,fullfile(P.generated,[m '.slx']));
end
loadPath=which(get_param([o '/Current demand'],'FileName'));
assert(~isempty(loadPath)&&strcmp(JTE2026sha256(loadPath),A.primary.load.SHA256),'JTE101:Load','Source load differs.');
assert(strcmp(JTE2026sha256(files.baseline),baselineHash)&&strcmp(JTE2026sha256(P.source),P.pin),'JTE101:SourceMutation','Pristine/vendor modified.');
prepared=struct('schema','JTE101_PREPARED_V1','sourceSHA256',P.pin,'baselineFileSHA256',baselineHash,...
 'modelSHA',struct('original',JTE2026sha256(fullfile(P.generated,[o '.slx'])),...
 'constant',JTE2026sha256(fullfile(P.generated,[d '.slx']))),...
 'beforeGraph',oa,'afterGraph',da,'exactEdgeSubstitution',true,'loggingBefore',loggingBefore,...
 'loadSHA256',A.primary.load.SHA256,'sourceAuditRun',A.run,...
 'constantValue',.25,'constantSampleTime',0,'eventTopologyEquivalence','NOT_PROVEN',...
 'solvedSimscapeICEquivalence','NOT_ESTABLISHED_BY_STATIC_AUDIT',...
 'calibrationPriorRun','40289697124','calibrationMethod','JTE089 aligned saved-state/output ratio method; old numeric gain not archived; no canary rerun');
% Preserve exact used base values from the source preload before ending this process.
workspaceSnapshot=struct();
for vi=1:numel(A.primary.resolvedVariables)
 entry=A.primary.resolvedVariables(vi);
 if strcmp(entry.sourceType,'base workspace')
  assert(isvarname(entry.name),'JTE101:WorkspaceName','Invalid recorded variable.');
  value=evalin('base',entry.name);
  assert(isequaln(value,entry.value),'JTE101:WorkspaceValue','Source workspace differs from the archived native run.');
  workspaceSnapshot.(entry.name)=value;
 end
end
assert(~isempty(fieldnames(workspaceSnapshot)),'JTE101:WorkspaceEmpty','No used source base values.');
prepared.workspaceFile=fullfile(P.private,['JTE101_' P.run '_PREPARE_WORKSPACE.mat']);
save(prepared.workspaceFile,'workspaceSnapshot','-v7.3');
prepared.workspaceSHA256=JTE2026sha256(prepared.workspaceFile);
prepared.workspaceProof='Exact source-preload values equal archived resolvedVariables; no defaults or tuning.';
save(fullfile(P.private,'prepared.mat'),'prepared','-v7.3');
fprintf('JTE101_PREPARE_PASS onePhysicalEdgeSubstitution=1 authenticCoreLoggerRetained=1 TF_SID197Unchanged=1 solverLoadDeclaredICUnchanged=1 simulationRun=0 eventTopologyEquivalence=NOT_PROVEN\n');
end
function restoreWorkspace(P)
S=load(fullfile(P.private,'prepared.mat'),'prepared');p=S.prepared;
assert(strcmp(JTE2026sha256(p.workspaceFile),p.workspaceSHA256),'JTE101:WorkspaceSHA','Frozen workspace changed.');
S=load(p.workspaceFile,'workspaceSnapshot');names=fieldnames(S.workspaceSnapshot);
for k=1:numel(names)
 name=names{k};value=S.workspaceSnapshot.(name);
 assignin('base',name,value);
 assert(isequaln(evalin('base',name),value),'JTE101:WorkspaceRestore','Exact workspace restoration failed.');
end
end
function d=extract(out,m)
[t,u]=JTE2026timeseries(out,'jteUcore');[ty,y]=JTE2026timeseries(out,'jteFlwR');
[tt,T]=JTE2026timeseries(out,'jteTtrue');
logs=out.get('jte101InputLogs');signal=logs.getElement('JTE101ActualTFInput');v=signal.Values;
[ti,input]=JTE056normalize(v.Time,v.Data,v.IsTimeFirst);
assert(size(T,2)==312&&t(1)==0&&t(end)==340&&ty(end)==340&&tt(end)==340,'JTE101:NativeHorizon','Incomplete native signal data.');
ds=out.get('jte101XStates');assert(isa(ds,'Simulink.SimulationData.Dataset'),'JTE101:Dataset','Missing xout Dataset.');
found=0;tx=[];x=[];initial=struct('key',{},'time',{},'value',{});initialAvailable=true;
for k=1:ds.numElements
 el=ds.getElement(k);paths={};
 try
  for z=1:el.BlockPath.getLength(),paths{z}=char(el.BlockPath.getBlock(z));end %#ok<AGROW>
 catch,initialAvailable=false;continue;end
 path=strjoin(paths,'::');
 if strcmp(path,[m '/Battery Control/sensor dynamics 1'])
  found=found+1;[tx,x]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
 end
 try
  [stime,svalue]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
  key=strrep([path '|' char(el.Name)],m,'$ROOT');
  initial(end+1)=struct('key',key,'time',stime(1),'value',svalue(1,:)); %#ok<AGROW>
 catch,initialAvailable=false;
 end
end
assert(found==1&&size(x,2)==1,'JTE101:TFState','Exact TF state missing/ambiguous.');
initialAvailable=initialAvailable&&numel(unique({initial.key}))==numel(initial);
d=struct('coreTime',t,'core',u,'outputTime',ty,'output',y,'inputTime',ti,'input',input,...
 'trueTime',tt,'trueTemperature',T,'stateTime',tx,'state',x,'fullStateDataset',ds,...
 'initialStateMap',initial,'initialStateMapAvailable',initialAvailable,'tout',out.get('tout'),...
 'clocksQualified',isequal(t,ty)&&isequal(tx,ty)&&isequal(ti,ty)&&isequal(tt,ty),...
 'acceptedStepCertification','UNAVAILABLE_NATIVE_RECORDING_ONLY');
end
function q=qualifyOriginal(d,A)
good=d.clocksQualified&&all(d.core(:)==.25)&&isequal(d.core,d.input);
cal=struct('C',NaN,'method','JTE089 saved Dataset/output ratio on pre-event source; numerical gain newly qualified','priorSyntheticRun','40289697124');
calibrated=false;
if good
 fit=d.outputTime>0&d.outputTime<300&abs(d.state)>1e-12;
 if any(fit)
  cal.C=median(d.output(fit)./d.state(fit));
  calibrated=isfinite(cal.C)&&all(abs(d.output-cal.C*d.state)<=1e-9);
 end
end
event=eventEvidence(d);
eventReproduced=event.present&&~isempty(A.firstBracket);
bracketAligned=false;
if eventReproduced
 a=A.firstBracket;b=event.bracket;
 gap=max(0,max(a(1),b(1))-min(a(2),b(2)));
 bracketAligned=gap<=max([diff(a),diff(b),1e-9]);
end
initialT=isequal(d.trueTemperature(1,:),A.primary.signalData.jteTtrue.values(1,:));
q=struct('qualified',good&&calibrated&&eventReproduced&&bracketAligned&&initialT,...
 'eventReproduced',eventReproduced,'bracketAligned',bracketAligned,'event',event,...
 'stateOutputQualified',calibrated,'initialTMatchesExisting',initialT,'calibration',cal,...
 'initialTFState',d.state(1),'initialTFOutput',d.output(1),'G5_ACCEPTED',false);
end
function c=compareConstant(original,d)
o=original.observed;C=original.calibration.C;
inputConstant=all(d.input(:)==.25)&&d.inputTime(1)==0&&d.inputTime(end)==340;
stateOutput=d.clocksQualified&&isfinite(C)&&all(abs(d.output-C*d.state)<=1e-9);
sameInitial=isequal(d.state(1,:),o.state(1,:))&&isequal(d.output(1,:),o.output(1,:))&&...
 isequal(d.trueTemperature(1,:),o.trueTemperature(1,:))&&initialMapsEqual(o,d);
e=eventEvidence(d);
qualified=original.qualification.qualified&&d.clocksQualified&&inputConstant&&stateOutput&&sameInitial;
c=struct('status','INCONCLUSIVE','excursion','INCONCLUSIVE','localization','INCONCLUSIVE_TOPOLOGY_OR_EVENT_CHANGE',...
 'inputConstant',inputConstant,'stateOutputQualified',stateOutput,'initialQualified',sameInitial,...
 'event',e,'calibrationC',C,'stateOutputResidualMax',max(abs(d.output-C*d.state)),...
 'eventTopologyEquivalence','NOT_PROVEN','crossTrajectoryClockExact',isequal(d.outputTime,o.outputTime),...
 'conditionalResetFreeLTIOnly',true,'G5_ACCEPTED',false);
if d.clocksQualified&&inputConstant
 if e.present,c.excursion='YES';else,c.excursion='NO';end
end
if qualified
 c.status='PASS'; % Executed/qualified localization, NOT causal repair or G5.
 if e.present
  c.localization='STATE_SOLVER_COUPLING_IMPLICATED_NOT_PHYSICAL_OUTPUT';
 else
  c.localization='UPSTREAM_INPUT_PATH_IMPLICATED_NOT_CAUSAL_ACTOR_PROVEN';
 end
end
end
function e=eventEvidence(d)
t=d.outputTime;y=d.output;
ix=find(t>=330&t<=338&abs(y-.25)>.005,1,'first');
e=struct('present',~isempty(ix),'bracket',[],'conditionalLTIResidual',NaN,'stateJump',NaN);
if ~isempty(ix)&&ix>1
 e.bracket=[t(ix-1),t(ix)];
 e.conditionalLTIResidual=y(ix)-(.25+(y(ix-1)-.25)*exp(-(t(ix)-t(ix-1))/.001));
 if d.clocksQualified,e.stateJump=d.state(ix)-d.state(ix-1);end
end
end
function ok=initialMapsEqual(a,b)
ok=false;if ~a.initialStateMapAvailable||~b.initialStateMapAvailable,return;end
x=a.initialStateMap;y=b.initialStateMap;
[kx,ix]=sort({x.key});[ky,iy]=sort({y.key});
if ~isequal(kx,ky),return;end
ok=true;
for k=1:numel(ix)
 if x(ix(k)).time~=0||y(iy(k)).time~=0||~isequaln(x(ix(k)).value,y(iy(k)).value),ok=false;return;end
end
end
function verifyConfig(m,s)
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','MinStep','InitialStep','FixedStep',...
 'ZeroCrossControl','LoadInitialState','InitialState','SimulationMode'};
for k=1:numel(keys),assert(strcmp(get_param(m,keys{k}),s.(keys{k})),'JTE101:Config','Source solver/declared IC differs.');end
assert(strcmp(get_param(m,'Solver'),'ode23t')&&strcmp(get_param(m,'LoadInitialState'),'off'),'JTE101:SourceConfig','Unexpected source configuration.');
for name={'InitFcn','StartFcn','StopFcn','PostLoadFcn'}
 assert(isempty(get_param(m,name{1})),'JTE101:Callback','Unexpected runtime callback.');
end
end
function verifyTF(tf)
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'BlockType'),'TransferFcn')&&...
 strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE101:TFIdentity','TransferFcn changed.');
end
function p=source(dst)
h=get_param(dst,'Line');assert(h~=-1,'JTE101:Line','Missing line.');p=get_param(h,'SrcPortHandle');assert(p~=-1,'JTE101:SourcePort','Missing source.');
end
function P=paths()
P.root=pwd;P.vendor=fullfile(pwd,'vendor-pack');P.private=fullfile(pwd,'jte101-private');
P.generated=fullfile(pwd,'jte101-generated');P.audit=fullfile(P.private,'stage_a_audit.mat');
P.pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
P.source=fullfile(P.vendor,'Models','Battery_Pack_Thermal_Management.slx');
P.run=getenv('GITHUB_RUN_ID');P.commit=getenv('GITHUB_SHA');
end
function writeJSON(path,value)
f=fopen(path,'w');assert(f~=-1,'JTE101:PrivateJSON','Cannot write private JSON.');fprintf(f,'%s',jsonencode(value));fclose(f);
end
function closePair(names)
for k=1:numel(names),quietModel(names{k});end
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
function quietProject(p)
try,close(p);catch,end
end
