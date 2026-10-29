function JTE115_run(mode)
% New guard hypothesis only. Canary once in prepare; exactly one normal sim in run.
root=pwd;priv=fullfile(root,'jte115-private');run=getenv('GITHUB_RUN_ID');
prefix=fullfile(priv,['JTE115_' run]);vendor=fullfile(root,'vendor-pack');
original=fullfile(priv,'JTE101Original.slx');guardFile=fullfile(priv,'JTE115Guarded.slx');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
flags=struct('DECISION','UNQUALIFIED_RESOURCE','CANARY_BITWISE_PASS',false,'READY_FOR_ONE_SIM',false,...
 'STATIC_MODEL_PARITY',false,'SOURCE_PARITY',false,'simulationStarted',false,'horizonComplete',false,...
 'ACCEPTED_MAJOR_PROVENANCE','UNAVAILABLE_NATIVE_LOGS_ONLY','THERMAL_COMPARISON_NOT_AUTHORIZED',true,'G5_ACCEPTED',false);
rec=struct('schema','JTE115_SOURCE_EQUIVALENT_GUARD_NOT_G5','run',run,'commit',getenv('GITHUB_SHA'),...
 'sourceProtocolCommit','0e91f54e8445ebcc6a97f6f270c449ab7c164329','sourceSHA256',pin,'mode',mode,'G5_ACCEPTED',false);
project=[];out=[];started=false;stage='RESOURCE';
try
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for k=1:numel(M.files),z=M.files(k);
  assert(strcmp(JTE2026sha256(fullfile(priv,z.local)),z.sha256),'JTE115:Source','Verified input changed.');
 end
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE115:Resource','Pinned runtime unavailable.');
 [ok,~]=license('checkout','Simulink');assert(ok,'JTE115:Resource','Included license unavailable.');
 assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE115:Source','Vendor pin.');
 rec.runtime=version;rec.resourceEntitlement=M.resource;
 if strcmp(mode,'prepare')
  stage='CANARY';
  JTE115_guardedLawCanary(); % THE ONLY canary invocation; no Python tests repeated.
  flags.CANARY_BITWISE_PASS=true;
 end
 stage='SOURCE';
 O=load(fullfile(priv,'original_raw.mat'),'record');o=O.record;
 assert(strcmp(o.role,'ORIGINAL340')&&strcmp(o.sourceSHA256,pin)&&strcmp(JTE2026sha256(original),o.modelSHA256),...
  'JTE115:Source','Wrong archived comparator/model.');
 ref=struct('modelSHA',o.modelSHA256,'loadSHA',o.prepared.loadSHA256,'workspaceSHA',o.prepared.workspaceSHA256,...
  'initialMap',o.observed.initialStateMap,'initialMapAvailable',o.observed.initialStateMapAvailable,...
  'T0',o.observed.trueTemperature(1,:),'x0',o.observed.state(1),'y0',o.observed.output(1),...
  'C',o.calibration.C,'nativeRows',numel(o.observed.outputTime));
 clear O o
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 assert(strcmp(JTE2026sha256(fullfile(priv,'source_workspace.mat')),ref.workspaceSHA),'JTE115:Source','Frozen workspace hash.');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),v=W.workspaceSnapshot.(names{k});assignin('base',names{k},v);
  assert(isequaln(evalin('base',names{k}),v),'JTE115:Source','Original initialization variable differs.');
 end
 if strcmp(mode,'prepare')
  stage='SOURCE_STATIC';
  load_system(original);om='JTE101Original';verifySource(om,ref);
  sourceAudit=JTE096_modelAudit(om);
  converter=JTE115_converterAudit(om);
  converter.classification=classifyConverters(converter);
  converter.scope='Read-only native source settings/upstream trace; no derivative/filter changes. Source output holding at saved points is not proof that derivatives are zero.';
  writeJSON([prefix '_CONVERTER_AUDIT.json'],converter);
  save([prefix '_CONVERTER_AUDIT.mat'],'converter','-v7.3');
  sourceFileBefore=JTE2026sha256(original);
  stage='BUILD';
  proof=JTE115_buildGuardedDiagnostic(original,guardFile);
  gm='JTE115Guarded';load_system(guardFile);
  step=[gm '/Battery Control/FlwR_calc/Step Change'];
  newBlocks={[step '/JTE115 guard constant'],[step '/JTE115 q guard']};
  after=JTE096_modelAudit(gm,newBlocks);
  assert(isequal(sourceAudit.blocks,after.blocks)&&isequal(sourceAudit.config,after.config),...
   'JTE115:ModelParity','Retained block parameters/source solver/IC changed.');
  key='$ROOT/Battery Control/FlwR_calc/Step Change';
  sa=sourceAudit.connectivity;ga=after.connectivity;
  sa=sa(~startsWith(sa(:,1),key),:);ga=ga(~startsWith(ga(:,1),key),:);
  assert(isequal(sa,ga),'JTE115:ModelParity','Signal/physical graph outside local guard changed.');
  assert(strcmp(JTE2026sha256(original),sourceFileBefore),'JTE115:ModelParity','Archived original file mutated.');
  verifySource(gm,ref);
  guardConverter=JTE115_converterAudit(gm);
  assert(isequal(normal(converter.entries,om),normal(guardConverter.entries,gm)),...
   'JTE115:ModelParity','A retained converter setting/upstream changed.');
  stage='COMPILE';
  feval(gm,[],[],[],'compile'); % Documented compile/term, no simulation time advancement.
  compileCleanup=onCleanup(@()quietTerm(gm));
  gh=get_param([step '/JTE115 q guard'],'PortHandles');qh=source(gh.Inport(1));
  assert(strcmp(get_param(qh,'CompiledPortDataType'),'double')&&strcmp(get_param(gh.Outport(1),'CompiledPortDataType'),'double'),...
   'JTE115:ModelParity','Guard/source arithmetic is not compiled double.');
  feval(gm,[],[],[],'term');clear compileCleanup
  save([prefix '_STATIC_AUDIT.mat'],'sourceAudit','after','proof','-v7.3');
  gh=get_param([step '/JTE115 q guard'],'PortHandles');qh=source(gh.Inport(1));
  % Logging metadata on existing ports only, no new physical/control edges.
  th=get_param([gm '/Battery Control/sensor dynamics 1'],'PortHandles');
  mark(source(th.Inport(1)),'JTE115ActualTFInput');
  mark(qh,'JTE115OriginalQ');mark(gh.Outport(1),'JTE115GuardQStar');
  save_system(gm,guardFile);
  stage='RESOURCE';
  [available,total]=ram();stateWidth=0;
  for k=1:numel(ref.initialMap),stateWidth=stateWidth+numel(ref.initialMap(k).value);end
  reserve=3*50000*8*(double(stateWidth)+312+12);
  disk=java.io.File(priv);free=double(disk.getUsableSpace());
  assert(available>reserve+2*1024^3&&free>max(4*1024^3,2*reserve)&&M.resource.drive.availableBytes>max(2*1024^3,reserve),...
   'JTE115:Resource','Source-state logging/private sink RAM/disk reserve insufficient.');
  prepared=struct('run',run,'commit',getenv('GITHUB_SHA'),'canaryBitwisePass',true,...
   'canaryCodeSHA',JTE2026sha256(which('JTE115_guardedLawCanary')),'reference',ref,'graphProof',proof,...
   'guardModelSHA',JTE2026sha256(guardFile),'sourceModelSHA',sourceFileBefore,...
   'staticRetainedBlocksConfigExact',true,'outsideGuardConnectivityExact',true,'converterConfigUnchanged',true,...
   'compiledDouble',true,'initializationScope','Same source physical graph, original full workspace/IC/default initialization policy at0; full saved initial states checked after run, hidden algebraic parity not a G5 certificate.',...
   'resource',struct('availableRAM_bytes',available,'totalRAM_bytes',total,'diskFree_bytes',free,...
   'loggingReserve_bytes',reserve,'sourceStateWidth',stateWidth,'rowPlanningCap',50000,'planningOnly',true));
  save([prefix '_PREPARED.mat'],'prepared','-v7.3');writeJSON([prefix '_STATIC_PROOF.json'],prepared);
  copyfile(guardFile,[prefix '_GUARDED_MODEL.slx']);
  flags.STATIC_MODEL_PARITY=true;flags.READY_FOR_ONE_SIM=true;flags.DECISION='GUARDED_PREPARED_NOT_SIMULATED';
  rec.prepared=prepared;
  fprintf('JTE115_PREPARED CANARY_BITWISE_PASS=1 STATIC_MODEL_PARITY=1 simulationStarted=0 G5_ACCEPTED=false\n');
 else
  assert(strcmp(mode,'simulate'),'JTE115:Mode','Unknown mode.');
  P=load([prefix '_PREPARED.mat'],'prepared');p=P.prepared;
  assert(strcmp(p.run,run)&&strcmp(p.commit,getenv('GITHUB_SHA'))&&p.canaryBitwisePass&&...
   strcmp(p.canaryCodeSHA,JTE2026sha256(which('JTE115_guardedLawCanary'))),'JTE115:Source','Same-run canary/proof not available.');
  flags.CANARY_BITWISE_PASS=true;flags.STATIC_MODEL_PARITY=true;rec.prepared=p;
  assert(strcmp(JTE2026sha256(guardFile),p.guardModelSHA)&&strcmp(JTE2026sha256(original),p.sourceModelSHA),...
   'JTE115:ModelParity','Guard or original bytes changed after qualification.');
  gm='JTE115Guarded';load_system(guardFile);verifySource(gm,ref);
  stage='ONE_SIMULATION';
  marker=fullfile(priv,'GUARD_SIMULATION_ENTERED.json');
  assert(~isfile(marker),'JTE115:RepeatDenied','No second physical attempt.');
  writeJSON(marker,struct('run',run,'phase','ONE_GUARD_SIM_CALL_ENTERED'));
  input=Simulink.SimulationInput(gm);
  input=input.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
   'SaveState','on','StateSaveName','jte115States','SaveFormat','Dataset',...
   'SaveTime','on','TimeSaveName','tout','SignalLogging','on','SignalLoggingName','jte115Inputs');
  rec.requestedOverrides={input.ModelParameters};rec.sourceConfig=JTE096_modelAudit(gm);
  rec.reference=ref;started=true;flags.simulationStarted=true;ticStudy=tic;
  fprintf('JTE115_ONE_GUARDED_SIM_START sourceSolver=ode23t noOriginalRerun=1 noSecondAttempt=1\n');
  out=sim(input); % EXACTLY ONE normal source-matched driver call.
  rec.elapsedWall_s=toc(ticStudy);rec.simulationOutput=out;rec.flags=flags;
  % Persist every captured original MATLAB field before qualification assertions.
  save([prefix '_CANDIDATE_RAW.mat'],'rec','-v7.3');
  stage='QUALIFICATION';
  d=extract(out,gm);rec.observed=d;
  assert(d.time(1)==0&&d.time(end)==340&&d.clocksExact&&size(d.T312,2)==312,...
   'JTE115:ModelParity','Native horizon/vector/clock qualification failed.');
  flags.horizonComplete=true;
  sameIC=ref.initialMapAvailable&&mapsEqual(ref.initialMap,d.initialMap)&&...
   isequal(ref.T0,d.T312(1,:))&&ref.x0==d.state(1)&&ref.y0==d.output(1);
  assert(sameIC,'JTE115:ModelParity','Saved complete initial-state map/T312/filter state differs.');
  assert(isequal(d.core,d.actualInput),'JTE115:ModelParity','Actual filter input differs from authentic final core.');
  assert(all(abs(d.output-ref.C*d.state)<=1e-9),'JTE115:ModelParity','Original filter-state/output calibration mismatch.');
  sourceLaw=max(.25,d.q-mod(d.q,.25));guardLaw=max(.25,d.qstar-mod(d.qstar,.25));
  assert(bitsEqual(sourceLaw,guardLaw)&&bitsEqual(d.core,sourceLaw)&&bitsEqual(d.qstar,max(d.q,.375)),...
   'JTE115:RuntimeBitwise','Original-vs-guard native MATLAB arithmetic or actual source output mismatches.');
  assert(strcmp(JTE2026sha256(original),ref.modelSHA)&&strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
   'JTE115:ModelParity','Original/vendor source bytes changed.');
  flags.SOURCE_PARITY=true;
  e=envelope(d.time,d.output);first=d.time>=330&d.time<=338;control=d.time>=330&d.time<=334;
  excursion=any(abs(d.output(first)-d.core(first))>.005);
  rec.conditionalEnvelope=e;
  rec.windowSummary=struct('firstLocalizationExcursion',excursion,'firstEnvelopeOutside',any(e.flag(first)),...
   'negativeControlEnvelopeOutside',any(e.flag(control)),'negativeControlLocalizationExcursion',any(abs(d.output(control)-d.core(control))>.005),...
   'globalEnvelopeOutside',any(e.flag),'startupEnvelopeOutside',any(e.flag(d.time<330)),...
   'firstConditionalExcessMax',max(e.excess(first)),...
   'firstNativeClockSemantics','Native only; accepted solution/event commits not independently certified',...
   'acceptedMajorProvenance','UNAVAILABLE_NORMAL_BATCH_DRIVER_MATCHES_ARCHIVED_COMPARATOR',...
   'thresholdRole','.005 is historical localization only;32ULP is output-interval roundoff localization, neither is a thermal/solver acceptance tolerance.',...
   'causalScope','A source-output-equivalent event-graph counterfactual, not proof that q=.25 alone is the causal actor and not G5.');
  if excursion||any(e.flag(first))||rec.windowSummary.negativeControlLocalizationExcursion||any(e.flag(control))
   flags.DECISION='GUARDED_EVENT_PERSISTS_STOP';
  else
   flags.DECISION='GUARDED_EVENT_REMOVED_CONDITIONAL';
  end
  flags.EXCURSION_PERSISTS=excursion;flags.ENVELOPE_FIRST_WINDOW_CONDITIONAL=any(e.flag(first));
  rec.initialSavedStateMapExact=sameIC;rec.nativeSourceOutputBitwiseExact=true;
  rec.acceptedMajorScope='No certified checkpoints exposed by this normal source-matched batch driver; no callback relabeled accepted. No alternate stepping/profiler run performed.';
  fprintf('JTE115_ONE_GUARDED_SIM_RETURNED qualificationComplete=1 G5_ACCEPTED=false\n');
 end
catch ME
 rec.failure=struct('stage',stage,'identifier',ME.identifier,'message',ME.message,'simulationStarted',started,'stack',{ME.stack});
 if strcmp(stage,'RESOURCE')||startsWith(ME.identifier,'JTE115:Resource')||contains(lower(ME.message),'license')
  flags.DECISION='UNQUALIFIED_RESOURCE';
 else
  flags.DECISION='GUARDED_REJECTED_BITWISE_OR_MODEL_PARITY';
 end
end
rec.flags=flags;rec.simulationStarted=started;
if ~isempty(out),rec.simulationOutput=out;save([prefix '_CANDIDATE_RAW.mat'],'rec','-v7.3');end
if strcmp(mode,'prepare'),suffix='_PREPARE';else,suffix='_STUDY';end
save([prefix suffix '_RECORD.mat'],'rec','-v7.3');
writeJSON([prefix suffix '_FLAGS.json'],flags);
summary=struct('flags',flags,'G5_ACCEPTED',false);
if isfield(rec,'failure'),summary.failure=rec.failure;end
if isfield(rec,'windowSummary'),summary.windowSummary=rec.windowSummary;end
writeJSON([prefix suffix '_SUMMARY.json'],summary);
try,close_system('JTE115Guarded',0);catch,end
try,close_system('JTE101Original',0);catch,end
try,if ~isempty(project),close(project);end;catch,end
end
function verifySource(m,ref)
assert(strcmp(get_param(m,'Solver'),'ode23t')&&strcmp(get_param(m,'RelTol'),'1e-3')&&strcmp(get_param(m,'AbsTol'),'1e-3')&&...
 str2double(get_param(m,'MaxStep'))==.05&&strcmp(get_param(m,'SolverResetMethod'),'Fast')&&...
 strcmp(get_param(m,'ZeroCrossControl'),'UseLocalSettings')&&strcmp(get_param(m,'LoadInitialState'),'off'),...
 'JTE115:Source','Original solver/config/initialization policy changed.');
tf=[m '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),...
 'JTE115:Source','Source TransferFcn changed.');
h=get_param(tf,'PortHandles');c=get_param([m '/Battery Control/FlwR_calc'],'PortHandles');
assert(source(h.Inport(1))==c.Outport(1),'JTE115:Source','Original final controller-to-filter edge changed.');
amb=[m '/Constant3'];assert(slResolve(get_param(amb,'Value'),amb)==300,'JTE115:Source','Controller reference changed.');
lp=which(get_param([m '/Current demand'],'FileName'));assert(~isempty(lp)&&strcmp(JTE2026sha256(lp),ref.loadSHA),'JTE115:Source','Load changed.');
s=[m '/Battery Control/FlwR_calc/step'];sat=[m '/Battery Control/FlwR_calc/FlwR calc/Saturation'];g=[m '/Battery Control/FlwR_calc/FlwR calc/Gain1'];
assert(slResolve(get_param(s,'Value'),s)==.25&&slResolve(get_param(g,'Gain'),g)==.1&&...
 slResolve(get_param(sat,'LowerLimit'),sat)==.001&&slResolve(get_param(sat,'UpperLimit'),sat)==.95,...
 'JTE115:Source','Source law parameters changed.');
for k={'InitFcn','StartFcn','StopFcn','PreLoadFcn','CloseFcn'}
 assert(isempty(get_param(m,k{1})),'JTE115:Source','Unexpected source callback.');
end
end
function p=source(port)
ln=get_param(port,'Line');assert(ln~=-1,'JTE115:Source','Missing source edge.');p=get_param(ln,'SrcPortHandle');assert(p~=-1,'JTE115:Source','Missing source port.');
end
function mark(port,name)
set_param(port,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName',name,...
 'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
end
function v=normal(v,m)
if ischar(v),v=strrep(v,m,'$ROOT');
elseif isstring(v),v=replace(v,m,'$ROOT');
elseif iscell(v),v=cellfun(@(x)normal(x,m),v,'UniformOutput',false);
elseif isstruct(v),f=fieldnames(v);for k=1:numel(v),for j=1:numel(f),v(k).(f{j})=normal(v(k).(f{j}),m);end;end
end
end
function d=extract(out,m)
[t,u]=JTE2026timeseries(out,'jteUcore');[ty,y]=JTE2026timeseries(out,'jteFlwR');[tt,T]=JTE2026timeseries(out,'jteTtrue');
logs=out.get('jte115Inputs');names={'JTE115ActualTFInput','JTE115OriginalQ','JTE115GuardQStar'};vals=cell(1,3);times=cell(1,3);
for k=1:3,el=logs.getElement(names{k});ts=el.Values;[times{k},vals{k}]=JTE056normalize(ts.Time,ts.Data,ts.IsTimeFirst);end
ds=out.get('jte115States');x=[];tx=[];found=0;initial=struct('key',{},'time',{},'value',{});
for k=1:ds.numElements
 el=ds.getElement(k);paths={};for z=1:el.BlockPath.getLength(),paths{z}=char(el.BlockPath.getBlock(z));end %#ok<AGROW>
 [st,sv]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
 path=strjoin(paths,'::');key=strrep([path '|' char(el.Name)],m,'$ROOT');
 initial(end+1)=struct('key',key,'time',st(1),'value',sv(1,:)); %#ok<AGROW>
 if strcmp(path,[m '/Battery Control/sensor dynamics 1']),found=found+1;tx=st;x=sv;end
end
assert(found==1,'JTE115:ModelParity','TF state unavailable/ambiguous.');
same=isequal(t,ty)&&isequal(t,tt)&&isequal(t,tx);
for k=1:3,same=same&&isequal(t,times{k});end
d=struct('time',t,'core',u,'output',y,'state',x,'T312',T,'actualInput',vals{1},'q',vals{2},'qstar',vals{3},...
 'initialMap',initial,'clocksExact',same,'timeSemantics','Native rows, duplicates retained, no interpolation; not certified accepted steps.');
end
function ok=mapsEqual(a,b)
ok=false;[ka,ia]=sort({a.key});[kb,ib]=sort({b.key});
if ~isequal(ka,kb),return;end
for k=1:numel(ia),if a(ia(k)).time~=0||b(ib(k)).time~=0||~isequaln(a(ia(k)).value,b(ib(k)).value),return;end;end
ok=true;
end
function b=bitsEqual(a,c)
b=isequal(size(a),size(c))&&isequal(a,c)&&isequal(typecast(a(:),'uint64'),typecast(c(:),'uint64'));
end
function e=envelope(t,y)
a=-expm1(-t/.001);y0=y(1);lo=y0+(.25-y0)*a;hi=y0+(.75-y0)*a;
margin=32*eps(max([ones(size(t)),abs(y),abs(lo),abs(hi),abs(y0)*ones(size(t))],[],2));
e=struct('time',t,'y0',y0,'lower',lo,'upper',hi,'margin32ULP',margin,...
 'excess',max([lo-y,y-hi,zeros(size(t))],[],2),'flag',y<lo-margin|y>hi+margin);
end
function c=classifyConverters(r)
c=struct('converter',{},'trace',{},'classification',{},'zeroDerivativeAuthorized',{});
for k=1:numel(r.entries)
 path=r.entries(k).block;trace=struct('block',{},'type',{});try,ph=get_param(path,'PortHandles');port=source(ph.Inport(1));trace=struct('block',{},'type',{});cls='UNRESOLVED_NOT_PROVEN_PIECEWISE_CONSTANT';seen={};
 for j=1:16
  b=get_param(port,'Parent');if ismember(b,seen),break;end;seen{end+1}=b;type=get_param(b,'BlockType');
  trace(end+1)=struct('block',b,'type',type); %#ok<AGROW>
  if strcmp(type,'TransferFcn'),cls='CONTINUOUS_STATEFUL_FILTER_OUTPUT_NOT_ZERO_DERIVATIVE';break;end
  if ismember(type,{'FromFile','FromWorkspace','Sine','Ramp','Clock'}),cls='DYNAMIC_SOURCE_NOT_CERTIFIED_PIECEWISE_CONSTANT';break;end
  if ismember(type,{'Constant','Step','PulseGenerator'}),cls='DIRECT_PIECEWISE_CONSTANT_BLOCK_SEMANTICS_ONLY_NO_HANDLING_CHANGE_AUTHORIZED';break;end
  h=get_param(b,'PortHandles');
  if strcmp(type,'Inport')
   parent=get_param(b,'Parent');hp=get_param(parent,'PortHandles');i=str2double(get_param(b,'Port'));
   if i>numel(hp.Inport),break;end;port=source(hp.Inport(i));
  elseif strcmp(type,'SubSystem')
   i=get_param(port,'PortNumber');outs=find_system(b,'SearchDepth',1,'BlockType','Outport');which=[];
   for z=1:numel(outs),if str2double(get_param(outs{z},'Port'))==i,which(end+1)=z;end;end %#ok<AGROW>
   if numel(which)~=1,break;end;oh=get_param(outs{which},'PortHandles');port=source(oh.Inport(1));
  elseif numel(h.Inport)==1
   port=source(h.Inport(1));
  else,break;end
 end
 catch
  cls='UNRESOLVED_TRACE_NOT_CERTIFIED_PIECEWISE_CONSTANT';
  if ~exist('trace','var'),trace=struct('block',{},'type',{});end
 end
 c(end+1)=struct('converter',path,'trace',trace,'classification',cls,'zeroDerivativeAuthorized',false); %#ok<AGROW>
end
end
function [a,b]=ram()
s=fileread('/proc/meminfo');a=str2double(regexp(s,'MemAvailable:\s+(\d+)','tokens','once'))*1024;b=str2double(regexp(s,'MemTotal:\s+(\d+)','tokens','once'))*1024;
end
function writeJSON(path,v)
f=fopen(path,'w');assert(f~=-1,'JTE115:Resource','Private write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end

function quietTerm(m)
try,feval(m,[],[],[],'term');catch,end
end
