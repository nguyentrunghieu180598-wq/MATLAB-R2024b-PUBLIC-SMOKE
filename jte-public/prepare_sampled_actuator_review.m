function prepare_sampled_actuator_review()
% Static/compile-only method review. No simulation, stepping, toy or G5 acceptance.
root=pwd;priv=fullfile(root,'actuator-review-private');prefix=fullfile(priv,['ACTUATOR_REVIEW_' getenv('GITHUB_RUN_ID')]);
vendor=fullfile(root,'vendor-pack');sourceB=fullfile(priv,'JTE101Original.slx');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
flags=struct('DECISION','STATIC_REVIEW_UNQUALIFIED','SOURCE_G5_FINAL_THERMAL_REJECTED',true,...
 'PHYSICAL_GRAPH_PARITY',false,'CONTROLLER_BIAS_PRESERVED',false,'IC_PARAMETERS_PRESERVED',false,...
 'ARCHIVED_Y0_USED',false,'COMPILE_ALL',false,'UNIT_METADATA_PARITY',false,'UNIT_METADATA_EXPLICIT',false,...
 'OWNER_METHOD_APPROVAL',false,'TOY_RUN',false,'PHYSICAL_RUN',false,'G5_ACCEPTED',false);
r=struct('schema','BTMS_ACTUATOR_METHOD_AMENDMENT_STATIC_ONLY','run',getenv('GITHUB_RUN_ID'),'commit',getenv('GITHUB_SHA'),...
 'scientificDecision','PR61 comment6462936805','TsReviewPair_s',[.01 .005],'tau_s',.001,...
 'methodAlreadyApproved',false,'sourceBitwiseEquivalenceClaimed',false,'physicalSimulation',false);
project=[];stage='RESOURCE';models={};
try
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for k=1:numel(M.files),z=M.files(k);assert(strcmp(JTE2026sha256(fullfile(priv,z.local)),z.sha256),'ActReview:InputSHA','Verified input changed.');end
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'ActReview:Runtime','Pinned runtime unavailable.');
 [ok,~]=license('checkout','Simulink');assert(ok,'ActReview:Resource','Included license unavailable.');r.runtime=version;
 assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'ActReview:Vendor','Vendor bytes changed.');
 stage='ARCHIVED_INITIALIZATION';
 O=load(fullfile(priv,'original_raw.mat'),'record');o=O.record;
 assert(strcmp(o.role,'ORIGINAL340')&&strcmp(o.sourceSHA256,pin)&&strcmp(JTE2026sha256(sourceB),o.modelSHA256),...
  'ActReview:Archive','Wrong archived original source.');
 B=struct('y0',o.observed.output(1),'T0',o.observed.trueTemperature(1,:),'workspaceSHA',o.prepared.workspaceSHA256,...
  'loadSHA',o.prepared.loadSHA256,'sourceModelSHA',o.modelSHA256,'sourceInitialMap',o.observed.initialStateMap);
 clear O o
 Z=load(fullfile(priv,'c0_original.mat'),'record');z=Z.record;
 assert(strcmp(z.caseName,'C0_original')&&strcmp(z.profile,'original')&&strcmp(z.sourceSHA256,pin)&&...
  z.signalData.jteFlwR.time_s(1)==0&&z.signalData.jteTtrue.time_s(1)==0,'ActReview:Archive','Wrong C0 archive.');
 C=struct('y0',z.signalData.jteFlwR.values(1),'T0',z.signalData.jteTtrue.values(1,:),...
  'baseSnapshot',struct(),'loadSHA',z.load.SHA256,'unitsDeclaredByPriorCollector',z.units);
 for k=1:numel(z.resolvedVariables)
  e=z.resolvedVariables(k);if strcmp(e.sourceType,'base workspace')
   if isfield(C.baseSnapshot,e.name),assert(isequaln(C.baseSnapshot.(e.name),e.value),'ActReview:Archive','Duplicate base variable differs.');end
   C.baseSnapshot.(e.name)=e.value;
  end
 end
 assert(strcmp(B.loadSHA,C.loadSHA)&&isequal(B.T0,C.T0),'ActReview:Archive','Source input frame/initial temperatures differ.');
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 cn=fieldnames(C.baseSnapshot);
 for k=1:numel(cn),assert(isfield(W.workspaceSnapshot,cn{k})&&isequaln(C.baseSnapshot.(cn{k}),W.workspaceSnapshot.(cn{k})),...
  'ActReview:InputFrame','Archived C0/B0L base input/IC values differ.');end
 clear W Z z e
 N=load(fullfile(priv,'negative_raw.mat'),'r');n=N.r;
 assert(strcmp(n.flags.DECISION,'GUARD025_EVENT_PERSISTS')&&n.flags.HORIZON_340_COMPLETE,'ActReview:Archive','Final negative provenance absent.');
 benchmark=struct('run','40645118578','wallMeasured_s',n.elapsedWall_s,'nativeRows',numel(n.observed.time),...
  'savedStateWidth',n.resourcePreflight.savedStateWidth,'scope','Rejected source numerical configuration used for resource screening only, never thermal truth.');
 clear N n
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 restoreB(priv,B.workspaceSHA);
 sourceC=fullfile(priv,'JTE2026LocalBias.slx');copyfile(sourceC,[prefix '_SOURCE_C0_TEMPLATE.slx']);models={'JTE101Original','JTE2026LocalBias'};
 load_system(sourceB);load_system(sourceC);
 verifySource('JTE101Original',B.loadSHA);verifySource('JTE2026LocalBias',C.loadSHA);
 bAudit=JTE096_modelAudit('JTE101Original');cAudit=JTE096_modelAudit('JTE2026LocalBias');
 % Independent physical/outside-controller comparison across the two source architectures.
 a=bAudit.blocks;b=cAudit.blocks;
 a=a(~strcmp(a(:,1),'$ROOT')&~startsWith(a(:,1),'$ROOT/Battery Control'),:);
 b=b(~strcmp(b(:,1),'$ROOT')&~startsWith(b(:,1),'$ROOT/Battery Control'),:);
 assert(isequal(a,b),'ActReview:Physical','Legacy C0 rebuild differs physically from archived B0L.');
 bb=biasContract('JTE101Original');assert(~bb.present,'ActReview:Bias','Unexpected B0L fault block.');
 bc=biasContract('JTE2026LocalBias');assert(bc.present&&bc.biasK==0&&bc.channel==1,'ActReview:Bias','Legacy zero-bias contract differs.');
 r.sourceProvenance=struct('B0L','Archived JTE101 original340 source SLX/actual y0/workspace',...
  'C0','Legacy source template rebuilt from frozen JTE056/JTE2026 builder; actual archived C0 y0/base values reused. No archival byte-equivalence claim.',...
  'B0L_initial_output',B.y0,'C0_initial_output',C.y0,'C0_original_units',C.unitsDeclaredByPriorCollector,...
  'initializationScope','All retained IC parameters/workspace preserved. New discrete state is actual source OUTPUT y0; original TF internal state scaling is not reused. Solved IC unproven without future authorized dynamics.');
 caseFiles={sourceB,sourceC};caseNames={'B0L','C0'};initial={B,C};results=cell(2,2);allUnits=true;allExplicit=true;
 for ci=1:2
  srcFile=caseFiles{ci};[~,sm]=fileparts(srcFile);load_system(srcFile);
  baseAudit=JTE096_modelAudit(sm,{[sm '/Battery Control/sensor dynamics 1']});
  sourceWorkspace=workspaceSnapshot(sm);sourceCharts=charts(sm);sourceBias=biasContract(sm);
  if ci==1,restoreB(priv,B.workspaceSHA);else,restoreSnapshot(C.baseSnapshot);end
  stage=['COMPILE_SOURCE_' caseNames{ci}];
  baseCompile=compileAttributes(sm,[sm '/Battery Control/sensor dynamics 1'],'');
  for ri=1:2
   Ts=r.TsReviewPair_s(ri);role={'Ref','Fine'};
   name=['BTMS_Amended_' caseNames{ci} '_' role{ri}];dest=fullfile(priv,[name '.slx']);models{end+1}=name; %#ok<AGROW>
   stage=['BUILD_' caseNames{ci} '_' role{ri}];
   proof=build_sampled_actuator_review(srcFile,dest,Ts,initial{ci}.y0);
   load_system(dest);
   act=[name '/Battery Control/Amended sampled actuator'];hold=[name '/Battery Control/Amended command sample hold'];
   targetAudit=JTE096_modelAudit(name,{act,hold});
   assert(isequal(baseAudit.blocks,targetAudit.blocks)&&isequal(baseAudit.config,targetAudit.config),...
    'ActReview:Retained','Original model/IC/solver/controller/physics parameters changed.');
   x=baseAudit.connectivity;y=targetAudit.connectivity;allowed=proof.changedConnectivityRows;
   x=x(~ismember(x(:,1),allowed),:);y=y(~ismember(y(:,1),allowed),:);
   assert(isequal(x,y),'ActReview:Graph','Outside exact replacement endpoint graph differs.');
   assert(isequaln(sourceWorkspace,workspaceSnapshot(name))&&isequal(sourceCharts,charts(name))&&isequal(sourceBias,biasContract(name)),...
    'ActReview:BiasIC','Source model workspace/chart/bias mechanism changed.');
   verifySource(name,initial{ci}.loadSHA,false);
   assert(slResolve(get_param(act,'InitialCondition'),act)==initial{ci}.y0,'ActReview:InitialOutput','Archived output y0 not used as new x0.');
   if ci==1,restoreB(priv,B.workspaceSHA);else,restoreSnapshot(C.baseSnapshot);end
   stage=['COMPILE_' caseNames{ci} '_' role{ri}];
   compiled=compileAttributes(name,act,hold);
   assert(isequal(compiled.actuator.sampleTime,[Ts 0])&&isequal(compiled.hold.sampleTime,[Ts 0]),...
    'ActReview:SampleTime','Actual compiled sample period/offset differs.');
   assert(strcmp(compiled.actuator.types.Inport{1},'double')&&strcmp(compiled.actuator.types.Outport{1},'double')&&...
    compiled.trueVectorWidth==312,'ActReview:CompiledType','Actuator double/T312 width differs.');
   [unitsSame,explicit,comparable]=unitsParity(baseCompile,compiled);
   if comparable,assert(unitsSame,'ActReview:Units','Known actuator boundary/T312 unit metadata changed.');end
   allUnits=allUnits&&unitsSame;allExplicit=allExplicit&&explicit;
   q=struct('caseSource',caseNames{ci},'role',role{ri},'modelMethod','UNAPPROVED_REVIEW_ONLY',...
    'proof',proof,'sourceCompile',baseCompile,'amendedCompile',compiled,'unitsMetadataParity',unitsSame,...
    'unitsExplicit',explicit,'unitAuditComparable',comparable,'controllerCompiledRateSame',isequal(baseCompile.controller.sampleTime,compiled.controller.sampleTime),'biasMechanismPreserved',true,'modelWorkspaceICParametersExact',true,...
    'stateScaling','x_new=y_source_output; C=1 D=0; no old internal TF scaling inserted.',...
    'alteredEvents',{{'Input command sampled/held at k*Ts, offset0','Discrete state update at k*Ts, output uses x[k] before update',...
    'Actuator output held between sample hits; sub-Ts raw decision pulses can be missed','Continuous1ms integration state removed','Original controller event logic retained; global major-time grid gains scheduled sample hits',...
    'Inherited actuator observer rates can become discrete; raw controller and physical T312 clocks stay separate'}},...
    'solvedPhysicalIC','UNPROVEN_STATIC_ONLY','G5Accepted',false);
   results{ci,ri}=q;r.partialResults=results;
   copyfile(dest,[prefix '_' caseNames{ci} '_' role{ri} '_MODEL.slx']);
   save([prefix '_' caseNames{ci} '_' role{ri} '_PROOF.mat'],'q','baseAudit','targetAudit','sourceCharts','sourceWorkspace','-v7.3');
   writeJSON([prefix '_' caseNames{ci} '_' role{ri} '_PROOF.json'],q);
   close_system(name,0);
  end
 end
 stage='RESOURCE_SCREEN';
 % Lower bounds at mandated periodic sample hits only; extra solver/event rows add cost.
 H=[340 2400];screen=struct([]);
 for hi=1:2,for ri=1:2
  Ts=r.TsReviewPair_s(ri);rows=ceil(H(hi)/Ts)+1;
  numeric=rows*8*(benchmark.savedStateWidth+2*312+32);
  screen(end+1)=struct('horizon_s',H(hi),'Ts_s',Ts,'minimumScheduledRows',rows,... %#ok<AGROW>
   'T312_singleCopy_bytes',rows*312*8,'legacyThreeCopyLogging_bytes',3*numeric,...
   'oldRuntimeLinearScreen_s',benchmark.wallMeasured_s*rows/benchmark.nativeRows,...
   'runtimeScope','Not a benchmark/guarantee for amended dynamics. Old rejected-source timing includes stepping/logger costs.');
 end;end
 r.results=results;r.resourceScreen=struct('benchmark',benchmark,'scenarios',screen,'currentResource',M.resource,...
  'currentFullStateLoggerFullThermalStatus','NO_GO_UNQUALIFIED_FOR_FULL_THERMAL_CLAIMS',...
  'essentialSignalBoundedStatePlan','PROPOSED_NOT_IMPLEMENTED_NOT_QUALIFIED',...
  'scope','No full2400 approval or affordability guarantee. Need measured amended-case peak and valid storage/runtime plan; otherwise full thermal claim unavailable under current infrastructure. No automatic trial or paper narrowing.');
 save([prefix '_REVIEW.mat'],'r','-v7.3');writeJSON([prefix '_RESOURCE_SCREEN.json'],r.resourceScreen);
 assert(strcmp(JTE2026sha256(sourceB),B.sourceModelSHA)&&strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
  'ActReview:OriginalBytes','Immutable original bytes changed.');
 flags.PHYSICAL_GRAPH_PARITY=true;flags.CONTROLLER_BIAS_PRESERVED=true;flags.IC_PARAMETERS_PRESERVED=true;
 flags.ARCHIVED_Y0_USED=true;flags.COMPILE_ALL=true;flags.UNIT_METADATA_PARITY=allUnits;flags.UNIT_METADATA_EXPLICIT=allExplicit;
 if allUnits,flags.DECISION='STATIC_COMPILE_REVIEW_READY_OWNER_METHOD_APPROVAL_REQUIRED';
 else,flags.DECISION='STATIC_COMPILE_REVIEW_WITH_UNIT_LIMITATIONS';end
catch ME
 r.failure=struct('stage',stage,'identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
end
r.flags=flags;save([prefix '_RECORD.mat'],'r','-v7.3');writeJSON([prefix '_FLAGS.json'],flags);
summary=struct('flags',flags,'reviewTsPair_s',r.TsReviewPair_s,'physicalSimulation',false,'toySimulation',false,'G5Accepted',false);
if isfield(r,'failure'),summary.failure=r.failure;end
writeJSON([prefix '_SUMMARY.json'],summary);
for k=1:numel(models),try,close_system(models{k},0);catch,end;end
try,if ~isempty(project),close(project);end;catch,end
end
function verifySource(m,loadSHA,checkTF)
if nargin<3,checkTF=true;end
assert(strcmp(get_param(m,'Solver'),'ode23t')&&strcmp(get_param(m,'RelTol'),'1e-3')&&strcmp(get_param(m,'AbsTol'),'1e-3')&&...
 str2double(get_param(m,'MaxStep'))==.05&&strcmp(get_param(m,'LoadInitialState'),'off'),'ActReview:Source','Source solver/IC policy differs.');
for key={'PreLoadFcn','InitFcn','StartFcn','StopFcn','PostLoadFcn','CloseFcn'}
 assert(isempty(get_param(m,key{1})),'ActReview:Callback','Unexpected callback.');
end
p=[m '/Constant3'];assert(slResolve(get_param(p,'Value'),p)==300,'ActReview:Reference','Source reference differs.');
lp=which(get_param([m '/Current demand'],'FileName'));assert(~isempty(lp)&&strcmp(JTE2026sha256(lp),loadSHA),'ActReview:Load','Load differs.');
if checkTF
 p=[m '/Battery Control/sensor dynamics 1'];assert(strcmp(get_param(p,'SID'),'197')&&strcmp(get_param(p,'BlockType'),'TransferFcn'),...
  'ActReview:SourceFilter','Source TF differs.');
end
end
function v=workspaceSnapshot(m)
mw=get_param(m,'ModelWorkspace');list=whos(mw);v=struct();
for k=1:numel(list),v.(list(k).name)=getVariable(mw,list(k).name);end
end
function c=charts(m)
sf=sfroot;all=sf.find('-isa','Stateflow.EMChart');c=cell(0,2);
for k=1:numel(all),p=char(all(k).Path);
 if startsWith(p,[m '/']),c(end+1,:)={['$ROOT' p(numel(m)+1:end)],char(all(k).Script)};end %#ok<AGROW>
end
if ~isempty(c),c=sortrows(c,1);end
end
function c=biasContract(m)
p=[m '/Battery Control/JTE local bias'];present=getSimulinkBlockHandle(p)>0;
c=struct('present',present,'biasK',[],'channel',[],'script','');
if present
 sf=sfroot;ch=sf.find('-isa','Stateflow.EMChart','Path',p);assert(numel(ch)==1,'ActReview:Bias','Bias chart ambiguous.');
 script=char(ch.Script);expected=sprintf('function Tm=localBias(T,j,b)\n%%#codegen\nTm=T;\nTm(j)=T(j)+b;\nend\n');
 assert(strcmp(strtrim(strrep(script,sprintf('\r\n'),sprintf('\n'))),strtrim(expected)),...
  'ActReview:Bias','Legacy local-bias formula differs.');
 mw=get_param(m,'ModelWorkspace');c.biasK=getVariable(mw,'jteBiasK');c.channel=getVariable(mw,'jteChannelIndex');c.script=script;
end
end
function restoreB(priv,sha)
p=fullfile(priv,'source_workspace.mat');assert(strcmp(JTE2026sha256(p),sha),'ActReview:Workspace','Archive workspace changed.');
S=load(p,'workspaceSnapshot');restoreSnapshot(S.workspaceSnapshot);
end
function restoreSnapshot(v)
names=fieldnames(v);for k=1:numel(names),assignin('base',names{k},v.(names{k}));assert(isequaln(evalin('base',names{k}),v.(names{k})),'ActReview:Workspace','Exact source value restore failed.');end
end
function a=compileAttributes(m,act,hold)
feval(m,[],[],[],'compile');finish=onCleanup(@()quietTerm(m)); %#ok<NASGU>
a=struct('actuator',attributes(act),'hold',[],'controller',attributes([m '/Battery Control/FlwR_calc']),...
 'trueVectorWidth',NaN,'trueVectorUnits',[],'converter',JTE116_converterAudit(m));
if ~isempty(hold),a.hold=attributes(hold);end
sinks=find_system(m,'BlockType','ToWorkspace');ix=[];
for k=1:numel(sinks),if strcmp(get_param(sinks{k},'VariableName'),'jteTtrue'),ix(end+1)=k;end;end %#ok<AGROW>
assert(numel(ix)==1,'ActReview:TrueVector','True-vector source ambiguous.');
w=get_param(sinks{ix},'CompiledPortWidths');a.trueVectorWidth=w.Inport(1);
try,u=get_param(sinks{ix},'CompiledPortUnits');a.trueVectorUnits=u.Inport;catch,a.trueVectorUnits='UNAVAILABLE';end
a.converterUnitParameters=cell(0,3);
for k=1:numel(a.converter.entries)
 b=a.converter.entries(k).block;dp=get_param(b,'DialogParameters');keys=fieldnames(dp);
 for j=1:numel(keys),if contains(lower(keys{j}),'unit')
  a.converterUnitParameters(end+1,:)={strrep(b,m,'$ROOT'),keys{j},get_param(b,keys{j})}; %#ok<AGROW>
 end;end
end
a.converter=normalize(a.converter,m);
feval(m,[],[],[],'term');clear finish
end
function a=attributes(p)
a=struct();a.types=get_param(p,'CompiledPortDataTypes');a.widths=get_param(p,'CompiledPortWidths');
a.sampleTime=get_param(p,'CompiledSampleTime');a.units=[];a.unitsAvailable=false;
try,a.units=get_param(p,'CompiledPortUnits');a.unitsAvailable=true;catch,a.units='UNAVAILABLE';end
if iscell(a.sampleTime)&&numel(a.sampleTime)==1,a.sampleTime=a.sampleTime{1};end
end
function [same,explicit,comparable]=unitsParity(source,target)
same=false;explicit=false;comparable=false;
if ~source.actuator.unitsAvailable||~target.actuator.unitsAvailable||~target.hold.unitsAvailable||~iscell(source.trueVectorUnits)||~iscell(target.trueVectorUnits),return;end
comparable=true;
same=isequal(source.actuator.units.Inport,target.hold.units.Inport)&&isequal(source.actuator.units.Outport,target.actuator.units.Outport)&&...
 isequal(source.trueVectorUnits,target.trueVectorUnits)&&isequal(source.converterUnitParameters,target.converterUnitParameters)&&...
 isequal(converterConfiguration(source.converter),converterConfiguration(target.converter));
values=[source.actuator.units.Inport source.actuator.units.Outport source.trueVectorUnits];
if iscell(values),explicit=all(cellfun(@(x)ischar(x)&&~isempty(x)&&~strcmp(x,'inherit'),values));end
end
function c=converterConfiguration(c)
% Expected filter/hold upstream edge/type changes are captured by exact graph proof.
if ~isempty(c.entries),c.entries=rmfield(c.entries,{'upstream','upstreamType'});end
end
function v=normalize(v,m)
if ischar(v),v=strrep(v,m,'$ROOT');
elseif isstring(v),v=replace(v,m,'$ROOT');
elseif iscell(v),v=cellfun(@(x)normalize(x,m),v,'UniformOutput',false);
elseif isstruct(v),f=fieldnames(v);for k=1:numel(v),for j=1:numel(f),v(k).(f{j})=normalize(v(k).(f{j}),m);end;end
end
end
function quietTerm(m)
try,feval(m,[],[],[],'term');catch,end
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'ActReview:PrivateWrite','Private write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
