function JTE103_sourceProfile(mode)
% One owner-authorized original-source profiling, public R2024b API only.
P=paths();
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE103:Runtime','R2024bU10 required.');
if strcmp(mode,'readback'),readback(P);return;end
assert(strcmp(mode,'capture'),'JTE103:Mode','Unknown source profiling mode.');
M=jsondecode(fileread(fullfile(P.root,'source_manifest.json')));
for k=1:numel(M.files),v=M.files(k);assert(strcmp(JTE2026sha256(fullfile(P.root,v.local)),v.sha256),'JTE103:SHA','Private input changed.');end
C=jsondecode(fileread(fullfile(P.root,'cap_flags.json')));B=jsondecode(fileread(fullfile(P.root,'cap_readback.json')));
assert(C.canaryCaptured&&~C.priorSessionPresent&&B.SOURCE_PROFILE_ELIGIBLE,'JTE103:Capability','Capability/retention preconditions absent.');
A=jsondecode(fileread(fullfile(P.root,'accepted_audit.json')));
assert(strcmp(JTE2026sha256(P.vendorSource),P.pin),'JTE103:Vendor','Vendor bytes changed.');
assert(strcmp(JTE2026sha256(P.originalFile),A.cases.ORIGINAL340.metadata.modelSHA),'JTE103:Archive','Wrong source-model archive.');
project=openProject(fullfile(P.vendor,'batteryExamplesProjectSetup.prj'));pg=onCleanup(@()quietProject(project)); %#ok<NASGU>
W=load(fullfile(P.root,'source_workspace.mat'),'workspaceSnapshot');names=fieldnames(W.workspaceSnapshot);
for k=1:numel(names),value=W.workspaceSnapshot.(names{k});assignin('base',names{k},value);assert(isequaln(evalin('base',names{k}),value),'JTE103:Workspace','Frozen source workspace changed.');end
Q=load(fullfile(P.root,'C0_source_reference.mat'),'record');r=Q.record;
assert(strcmp(r.sourceSHA256,P.pin)&&r.ambient.valueK==300&&strcmp(r.caseName,'C0_original'),'JTE103:C0Reference','Wrong same-condition reference.');
expectedT0=r.signalData.jteTtrue.values(1,:);clear Q r;
assert(~isfolder(P.generated),'JTE103:Fresh','Fresh source profile directory required.');mkdir(P.generated);
copyfile(P.originalFile,P.modelFile);load_system(P.modelFile);mg=onCleanup(@()quietModel(P.model)); %#ok<NASGU>
tf=[P.model '/Battery Control/sensor dynamics 1'];core=[P.model '/Battery Control/FlwR_calc'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'BlockType'),'TransferFcn')&&...
 strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE103:TF','Original TransferFcn required.');
h=get_param(tf,'PortHandles');ch=get_param(core,'PortHandles');line=get_param(h.Inport(1),'Line');
assert(get_param(line,'SrcPortHandle')==ch.Outport(1),'JTE103:SourceWire','Authentic controller wire changed.');
s=A.cases.B0L_original.metadata.solver;
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','MinStep','InitialStep','FixedStep','ZeroCrossControl','LoadInitialState','InitialState','SimulationMode'};
for k=1:numel(keys),assert(strcmp(get_param(P.model,keys{k}),s.(keys{k})),'JTE103:Config','Original solver/declared IC differs.');end
for key={'InitFcn','StartFcn','StopFcn','PostLoadFcn'},assert(isempty(get_param(P.model,key{1})),'JTE103:Callback','Unexpected runtime callback.');end
loadFile=which(get_param([P.model '/Current demand'],'FileName'));
assert(strcmp(JTE2026sha256(loadFile),A.cases.B0L_original.metadata.loadSHA),'JTE103:Load','Load changed.');
controllerRef=slResolve(get_param([P.model '/Constant3'],'Value'),[P.model '/Constant3']);assert(controllerRef==300,'JTE103:Reference','Not original controller reference.');
before=JTE096_modelAudit(P.model);
% Observation/export settings only, explicit and archived. No graph/block/law/solver/IC change.
obsNames={'ReturnWorkspaceOutputs','SaveTime','TimeSaveName','SaveState','StateSaveName','SaveFormat','SignalLogging','SignalLoggingName'};
obsBefore=cellfun(@(x)get_param(P.model,x),obsNames,'UniformOutput',false);
set_param(P.model,'ReturnWorkspaceOutputs','off','SaveTime','on','TimeSaveName','tout',...
 'SaveState','on','StateSaveName','jte103XStates','SaveFormat','Dataset','SignalLogging','on','SignalLoggingName','jte103InputLogs');
obsAfter=cellfun(@(x)get_param(P.model,x),obsNames,'UniformOutput',false);
afterObservation=JTE096_modelAudit(P.model);
assert(isequal(before.blocks,afterObservation.blocks)&&isequal(before.connectivity,afterObservation.connectivity)&&isequal(before.config,afterObservation.config),'JTE103:ObservationDelta','Physical graph/controller/solver changed.');
save_system(P.model,P.modelFile);
sourceModelSHA=JTE2026sha256(P.modelFile);
% Clear only output names, not model parameters. Fresh invocation plus clear avoids stale data.
outNames={'jteTtrue','jteUcore','jteFlwR','jteAmbient','jteTmaxTrue','jteTminTrue','jte103XStates','jte103InputLogs','tout'};
assert(~any(ismember(names,outNames)),'JTE103:OutputNameCollision','Output clear would affect a physical parameter.');
for k=1:numel(outNames),evalin('base',['clear ' outNames{k}]);end
windows=struct('negativeControl_s',[330 334],'firstInspection_s',[330 338],'closeInspection_s',[334.8 335],...
 'previousNativeFirstBracket_s',A.cases.ORIGINAL340.events.FIRST.firstBracket_s,...
 'localizationThresholdNormalized',.005,'acceptanceThreshold','NOT_DEFINED_BY_ANOMALY_FLAG');
provenance=struct('sourceTag','24.2.1.5','sourceCommit','f98d21929a3a269dacd1ee38999cd9773760c6db','sourceSLXSHA256',P.pin,...
 'archivedReferenceRun','40449421507','archivedReferenceModelSHA',JTE2026sha256(P.originalFile),...
 'profiledModelSHA',sourceModelSHA,'loadSHA',JTE2026sha256(loadFile),'workspaceSHA',JTE2026sha256(fullfile(P.root,'source_workspace.mat')),...
 'runtime',version,'sourceSolver',s,'observerSettingNames',{obsNames},'observerBefore',{obsBefore},'observerAfter',{obsAfter},...
 'expectedInitialT312_K',expectedT0,'windows',windows,'controllerReferenceK',controllerRef,...
 'BufferSize',200000,'SaveStates','on','SaveZCSignals','on','SaveSimscapeStates','off','SaveJacobian','off',...
 'memoryPlan','GitHub hosted runner, avoid Simscape/Jacobian duplicate logs; save only selected TF state from native Dataset; no paid service',...
 'scope','New W103 authorized profiling0to340, not an old diagnostic replay; SECOND_EVENT NOT_COVERED',...
 'acceptedStepCertification','UNAVAILABLE_UNTIL_SUPPORTED_GUI_TRACE_REVIEW','G5_ACCEPTED',false);
save([P.prefix '_PROVENANCE.mat'],'provenance','before','afterObservation','-v7.3');writeJSON([P.prefix '_PROVENANCE.json'],provenance);
copyfile(P.modelFile,[P.prefix '_MODEL.slx']);
assert(~isfile(fullfile(P.root,'PROFILE_API_ENTERED.json')),'JTE103:Repeat','No repeated source profile.');
writeJSON(fullfile(P.root,'PROFILE_API_ENTERED.json'),struct('run',P.run,'phase','PUBLIC_PROFILE_CALL_NEXT'));
fprintf('JTE103_SOURCE_PROFILE_CALL_START originalSolver=1 unchangedControllerAndPhysics=1 horizon340=1 negativeControlPreregistered=1 no2400=1\n');
capturedLog=evalc('res=invokeSource(P);');
assert(isstruct(res)&&isfield(res,'summary')&&isfield(res,'file')&&isfile(res.file),'JTE103:Session','No supported profiler result/session.');
summary=res.summary;inventory=whos('-file',res.file);
complete=summary.tStart==0&&summary.tStop==340&&strcmp(summary.solver,'ode23t')&&summary.steps>0;
assert(summary.hMax==str2double(s.MaxStep)&&summary.relTol==str2double(s.RelTol),'JTE103:EffectiveSummary','Profiler summary changed source MaxStep/RelTol.');
save([P.prefix '_PUBLIC_RESULT.mat'],'res','capturedLog','inventory','complete','-v7.3');writeJSON([P.prefix '_PUBLIC_SUMMARY.json'],summary);
native=captureNative(P,tf,expectedT0,A.cases.ORIGINAL340.metadata.savedStateOutputGain,windows);
save([P.prefix '_NATIVE.mat'],'native','-v7.3');
after=JTE096_modelAudit(P.model);
save([P.prefix '_AFTER_AUDIT.mat'],'before','after','provenance','-v7.3');
assert(isequal(before.blocks,after.blocks)&&isequal(before.connectivity,after.connectivity)&&isequal(before.config,after.config),...
 'JTE103:AfterProfileDrift','Source physical/controller/solver declaration drifted during profiler.');
assert(strcmp(JTE2026sha256(P.vendorSource),P.pin),'JTE103:SourceChanged','Vendor mutated.');
flags=struct('PROFILER_API_R2024B','PASS_ACTUAL_CALL','PROFILE_SESSION_SAVED',true,'PROFILE_HORIZON_COMPLETE',complete,...
 'FIRST_EVENT_NATIVE',native.firstStatus,'FIRST_EVENT_CAUSALITY','NOT_PROVEN','NEGATIVE_CONTROL_NATIVE',native.negativeStatus,...
 'LOCAL_ZC_RESET_EXCEPTION_STEP_HISTORY','UNAVAILABLE_VIA_PUBLIC_HEADLESS_API_REQUIRES_SOLVER_PROFILER_GUI',...
 'EVENT_BLOCK_ACTOR','NOT_PROVEN','EXACT_RESET_OR_ZC_ACTOR_PROVEN',false,'SECOND_EVENT_SCOPE','NOT_COVERED_340',...
 'G5_PROVENANCE','PASS_PINNED_PRIVATE_ASSETS','G5_ACTUATION_EVENT','ACTOR_UNPROVEN','G5_THERMAL_CONVERGENCE','UNPROVEN',...
 'NUMERICAL_REFERENCE_DECISION','NOT_RUN_NO_SUPPORTED_LOCAL_EVENT_PROVENANCE','W103_3_2400','NOT_AUTHORIZED_PENDING_INDEPENDENT_REVIEW',...
 'GUI_AVAILABLE',usejava('awt')&&~isempty(getenv('DISPLAY')),'BUFFER_COMPLETENESS','NOT_CERTIFIED_BY_HIGH_LEVEL_SUMMARY',...
 'G5_ACCEPTED',false);
writeJSON([P.prefix '_FLAGS.json'],flags);
fprintf('JTE103_SOURCE_PROFILE_RESULT sessionSaved=1 horizonComplete=%d FIRST_EVENT_NATIVE=%s NEGATIVE_CONTROL_NATIVE=%s EVENT_BLOCK_ACTOR=NOT_PROVEN FIRST_EVENT_CAUSALITY=NOT_PROVEN SECOND_EVENT=NOT_COVERED_340 G5_ACTUATION_EVENT=ACTOR_UNPROVEN G5_THERMAL_CONVERGENCE=UNPROVEN\n',...
 complete,native.firstStatus,native.negativeStatus);
end
function res=invokeSource(P)
res=solverprofiler.profileModel(P.model,'StartTime',0,'StopTime',340,'OpenSP','off',...
 'DataFullFile',[P.prefix '_SESSION.mat'],'SaveStates','on','SaveSimscapeStates','off',...
 'SaveZCSignals','on','SaveJacobian','off','BufferSize',200000,'TimeOut',120);
end
function n=captureNative(P,tf,expectedT0,Ctf,w)
n=struct('available',false,'firstStatus','UNAVAILABLE_BASE_WORKSPACE_LOGS','negativeStatus','UNAVAILABLE_BASE_WORKSPACE_LOGS',...
 'acceptedStepCertification','UNAVAILABLE','TFStateScope','Private profiler SaveStates session, GUI required if native state export unavailable',...
 'minorStageInput','NOT_RECONSTRUCTED_FROM_NATIVE_SAMPLES','CtfFrozenFromAcceptedJTE101',Ctf);
if ~(evalin('base',"exist('jteTtrue','var')")&&evalin('base',"exist('jteUcore','var')")&&evalin('base',"exist('jteFlwR','var')")),return;end
try
 v=evalin('base','jteTtrue');[tt,T]=JTE056normalize(v.Time,v.Data,v.IsTimeFirst);
 v=evalin('base','jteUcore');[tu,u]=JTE056normalize(v.Time,v.Data,v.IsTimeFirst);
 v=evalin('base','jteFlwR');[ty,y]=JTE056normalize(v.Time,v.Data,v.IsTimeFirst);
 assert(size(T,2)==312&&tt(1)==0&&tt(end)==340&&isequal(tt,tu)&&isequal(tt,ty),'JTE103:Native','Incomplete or unequal native clocks.');
 n.available=true;n.time=tt;n.T312_K=T;n.core=u;n.postfilter=y;n.initialThermalMatches=isequal(T(1,:),expectedT0);
 n.coreHeldAtNativePoints=all(u==.25);n.repeatedAdjacentRows=sum(diff(tt)==0);
 hit=tt>=w.firstInspection_s(1)&tt<=w.firstInspection_s(2)&abs(y-.25)>.005;
 ctrl=tt>=w.negativeControl_s(1)&tt<=w.negativeControl_s(2);
 n.negativeFlaggedSamples=sum(abs(y(ctrl)-.25)>.005);
 if any(hit),n.firstStatus='EXCURSION_RECORDED';ix=find(hit,1);if ix>1,n.firstBracket_s=[tt(ix-1),tt(ix)];end
 else,n.firstStatus='NO_LOCALIZATION_FLAG_IN_NATIVE_WINDOW';end
 if n.negativeFlaggedSamples==0,n.negativeStatus='NO_NATIVE_LOCALIZATION_FLAGS';else,n.negativeStatus='NATIVE_LOCALIZATION_FLAGS_PRESENT';end
 if evalin('base',"exist('jte103InputLogs','var')")
  ds=evalin('base','jte103InputLogs');el=ds.getElement('JTE101ActualTFInput');
  [ti,input]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
  n.actualInputTime=ti;n.actualInput=input;n.actualInputEqualsCore=isequal(ti,tu)&&isequal(input,u);
 end
 if evalin('base',"exist('jte103XStates','var')")
  ds=evalin('base','jte103XStates');found=0;
  for k=1:ds.numElements
   el=ds.getElement(k);try,path=char(el.BlockPath.getBlock(1));catch,path='';end
   if strcmp(path,tf)
    found=found+1;[tx,x]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
   end
  end
  if found==1
   n.TFStateTime=tx;n.TFState=x;n.TFStateClockQualified=isequal(tx,ty);
   if n.TFStateClockQualified,n.TFStateOutputMaxResidual=max(abs(y-Ctf*x));end
  end
  clear ds;evalin('base','clear jte103XStates');
 end
catch err
 n.nativeCaptureFailure=struct('identifier',err.identifier,'message',err.message);n.firstStatus='UNAVAILABLE_OR_UNQUALIFIED_NATIVE_EXPORT';
end
end
function readback(P)
M=jsondecode(fileread(fullfile(P.root,'source_readback_manifest.json')));file=fullfile(P.root,M.local);
assert(strcmp(JTE2026sha256(file),M.sha256),'JTE103:Readback','Session readback changed.');
inventory=whos('-file',file);assert(~isempty(inventory),'JTE103:Inventory','Empty profiler session.');
flags=struct('PROFILE_SESSION_PRIVATE_SHA','PASS_FULL_CLOUD_DOWNLOAD_READBACK','SESSION_MAT_INVENTORY','PASS',...
 'GUI_EXPLORE_RESULT','UNAVAILABLE_HEADLESS','EVENT_BLOCK_ACTOR','NOT_PROVEN','FIRST_EVENT_CAUSALITY','NOT_PROVEN',...
 'SECOND_EVENT_SCOPE','NOT_COVERED_340','NUMERICAL_REFERENCE_DECISION','NOT_RUN_NO_SUPPORTED_LOCAL_EVENT_PROVENANCE',...
 'G5_PROVENANCE','PASS','G5_ACTUATION_EVENT','ACTOR_UNPROVEN','G5_THERMAL_CONVERGENCE','UNPROVEN','G5_ACCEPTED',false);
if usejava('awt')&&~isempty(getenv('DISPLAY'))
 try,solverprofiler.exploreResult(file);drawnow;flags.GUI_EXPLORE_RESULT='PUBLIC_EXPLORER_RETURNED_VISUAL_EVENT_REVIEW_NOT_PERFORMED';
 catch err,flags.GUI_EXPLORE_RESULT='UNAVAILABLE_PUBLIC_GUI_LOAD_ERROR';flags.guiFailureIdentifier=err.identifier;end
end
save(fullfile(P.root,['JTE103_' P.run '_SOURCE_READBACK_INVENTORY.mat']),'inventory','flags','-v7.3');
writeJSON(fullfile(P.root,['JTE103_' P.run '_SOURCE_READBACK_FLAGS.json']),flags);
fprintf('JTE103_SOURCE_RETENTION_RESULT PROFILE_SESSION_PRIVATE_SHA=PASS SESSION_INVENTORY=PASS GUI_EXPLORE_RESULT=%s EVENT_BLOCK_ACTOR=NOT_PROVEN G5_ACCEPTED=false\n',flags.GUI_EXPLORE_RESULT);
end
function P=paths()
P.root=fullfile(pwd,'jte103-private');P.run=getenv('GITHUB_RUN_ID');P.prefix=fullfile(P.root,['JTE103_' P.run '_SOURCE']);
P.vendor=fullfile(pwd,'vendor-pack');P.vendorSource=fullfile(P.vendor,'Models','Battery_Pack_Thermal_Management.slx');
P.pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
P.originalFile=fullfile(P.root,'JTE101Original.slx');P.generated=fullfile(pwd,'jte103-generated');
P.model='JTE103SourceProfiler';P.modelFile=fullfile(P.generated,[P.model '.slx']);
end
function writeJSON(file,v)
h=fopen(file,'w');assert(h~=-1,'JTE103:Write','Private write failed.');fprintf(h,'%s',jsonencode(v));fclose(h);
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
function quietProject(p)
try,close(p);catch,end
end
