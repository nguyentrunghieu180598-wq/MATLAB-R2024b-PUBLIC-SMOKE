function JTE116_prepare()
% One new canary plus read-only archived diagnosis/static clone. NO sim call.
root=pwd;priv=fullfile(root,'jte116-private');run=getenv('GITHUB_RUN_ID');
prefix=fullfile(priv,['JTE116_' run]);vendor=fullfile(root,'vendor-pack');
original=fullfile(priv,'JTE101Original.slx');guardFile=fullfile(priv,'JTE116Guarded.slx');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
flags=struct('DECISION','UNQUALIFIED_RESOURCE','ARCHIVED_MISMATCH_CLASSIFICATION_COMPLETE',false,...
 'CANARY_BITWISE_PASS',false,'STATIC_MODEL_PARITY',false,'COMPILED_DOUBLE',false,...
 'OWNER_NEW_PLANT_AUTHORIZATION',false,'PHYSICAL_SIMULATION_STARTED',false,...
 'ACCEPTED_MAJOR_PROVENANCE','UNAVAILABLE_NO_TRAJECTORY','G5_ACCEPTED',false);
rec=struct('schema','JTE116_GUARD025_CANARY_STATIC_ONLY_NOT_G5','run',run,'commit',getenv('GITHUB_SHA'),...
 'canarySourceCommit','d07a4d23ea664544ef8dc9a352ec3023a87dd64e','G5_ACCEPTED',false,'physicalSimulation',false);
stage='RESOURCE';project=[];
try
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for k=1:numel(M.files),z=M.files(k);
  assert(strcmp(JTE2026sha256(fullfile(priv,z.local)),z.sha256),'JTE116:InputSHA','Verified private input changed.');
 end
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE116:Runtime','Pinned R2024bU10 required.');
 rec.runtime=version;
 stage='ARCHIVED_DIAGNOSTIC';
 D=load(fullfile(priv,'j115_canary.mat'),'diagnostic');d=D.diagnostic;
 assert(isfield(d,'syntheticOnly')&&d.syntheticOnly&&contains(d.runtime,'24.2.0.3361896'),...
  'JTE116:Archive','Wrong archived canary diagnostic.');
 q=d.q;bits=typecast(d.original(:),'uint64')~=typecast(d.guarded(:),'uint64');
 assert(isequal(bits,d.bitMismatch)&&any(bits),'JTE116:Archive','Archived bit mismatch mask inconsistent.');
 ranges=struct('below025',nnz(bits&q<.25),'from025Below0375',nnz(bits&q>=.25&q<.375),'atOrAbove0375',nnz(bits&q>=.375));
 first=find(bits,1);
 ledger=struct('archivedOnly',true,'priorRun','40631662726','inputSHA',M.files(1).sha256,...
  'mismatchCount',nnz(bits),'ranges',ranges,'allMismatchInSourceDomain',all(q(bits)>=.001&q(bits)<=.95),...
  'firstMismatchQHex',num2hex(q(first)),'firstOriginalHex',num2hex(d.original(first)),...
  'firstGuardedHex',num2hex(d.guarded(first)),...
  'scope','Only exact saved JTE115 diagnostic read; no q counterexamples inferred or old canary re-executed.');
 writeJSON([prefix '_JTE115_RANGE_LEDGER.json'],ledger);
 save([prefix '_JTE115_RANGE_LEDGER.mat'],'ledger','-v7.3');
 flags.ARCHIVED_MISMATCH_CLASSIFICATION_COMPLETE=true;clear D d bits q
 stage='CANARY';
 JTE116_guard025Canary([prefix '_CANARY_PROOF.mat']); % ONLY invocation of this new MATLAB canary.
 flags.CANARY_BITWISE_PASS=true;
 C=load([prefix '_CANARY_PROOF.mat'],'diagnostic');
 rec.canary=struct('codeSHA',JTE2026sha256(which('JTE116_guard025Canary')),'underfloorOK',C.diagnostic.underfloorOK,...
  'untouchedOK',C.diagnostic.untouchedOK,'strictBitwisePass',~any(C.diagnostic.bitMismatch),'syntheticOnly',true);clear C
 stage='RESOURCE';[ok,~]=license('checkout','Simulink');
 assert(ok,'JTE116:Resource','Included Simulink license unavailable for static preparation.');
 assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE116:Source','Vendor pin.');
 stage='SOURCE';
 O=load(fullfile(priv,'original_raw.mat'),'record');o=O.record;
 assert(strcmp(o.role,'ORIGINAL340')&&strcmp(o.sourceSHA256,pin)&&strcmp(JTE2026sha256(original),o.modelSHA256),...
  'JTE116:Source','Wrong source archived original.');
 assert(o.observed.initialStateMapAvailable,'JTE116:Source','Saved full source initialization map unavailable.');
 ref=struct('modelSHA',o.modelSHA256,'loadSHA',o.prepared.loadSHA256,'workspaceSHA',o.prepared.workspaceSHA256,...
  'initialMap',o.observed.initialStateMap,'T0',o.observed.trueTemperature(1,:),'x0',o.observed.state(1),...
  'y0',o.observed.output(1),'C',o.calibration.C);
 clear O o
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 assert(strcmp(JTE2026sha256(fullfile(priv,'source_workspace.mat')),ref.workspaceSHA),'JTE116:Source','Original workspace SHA.');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),value=W.workspaceSnapshot.(names{k});assignin('base',names{k},value);
  assert(isequaln(evalin('base',names{k}),value),'JTE116:Source','Source workspace variable differs.');
 end
 load_system(original);om='JTE101Original';verifySource(om,ref);
 before=JTE096_modelAudit(om);converter=JTE115_converterAudit(om);
 writeJSON([prefix '_CONVERTER_AUDIT.json'],converter);
 stage='BUILD';
 proof=JTE116_buildGuardedDiagnostic(original,guardFile);
 gm='JTE116Guarded';load_system(guardFile);step=[gm '/Battery Control/FlwR_calc/Step Change'];
 after=JTE096_modelAudit(gm,{[step '/JTE115 guard constant'],[step '/JTE115 q guard']});
 assert(isequal(before.blocks,after.blocks)&&isequal(before.config,after.config),...
  'JTE116:ModelParity','Retained source blocks/config/IC/solver differ.');
 key='$ROOT/Battery Control/FlwR_calc/Step Change';
 a=before.connectivity;b=after.connectivity;
 a=a(~startsWith(a(:,1),key),:);b=b(~startsWith(b(:,1),key),:);
 assert(isequal(a,b),'JTE116:ModelParity','Outside-local-guard graph differs.');
 verifySource(gm,ref);
 guardConverter=JTE115_converterAudit(gm);
 assert(isequal(normal(converter.entries,om),normal(guardConverter.entries,gm)),...
  'JTE116:ModelParity','Converter configuration/upstream changed.');
 constant=[step '/JTE115 guard constant'];
 assert(slResolve(get_param(constant,'Value'),constant)==.25,'JTE116:ModelParity','Wrong guard constant.');
 stage='COMPILE';
 feval(gm,[],[],[],'compile');cleanup=onCleanup(@()quietTerm(gm));
 h=get_param([step '/JTE115 q guard'],'PortHandles');p=source(h.Inport(1));
 assert(strcmp(get_param(p,'CompiledPortDataType'),'double')&&strcmp(get_param(h.Outport(1),'CompiledPortDataType'),'double'),...
  'JTE116:ModelParity','Source/guard operands are not compiled double.');
 feval(gm,[],[],[],'term');clear cleanup
 assert(strcmp(JTE2026sha256(original),ref.modelSHA)&&strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
  'JTE116:Source','Original or vendor file changed.');
 flags.STATIC_MODEL_PARITY=true;flags.COMPILED_DOUBLE=true;
 flags.DECISION='GUARD025_CANARY_STATIC_PASS_AWAIT_OWNER_SIM_AUTHORIZATION';
 rec.prepared=struct('guardModelSHA',JTE2026sha256(guardFile),'originalModelSHA',ref.modelSHA,...
  'loadSHA',ref.loadSHA,'workspaceSHA',ref.workspaceSHA,'source',ref,'graphProof',proof,...
  'retainedBlocksConfigExact',true,'outsideLocalGuardConnectivityExact',true,'converterConfigUnchanged',true,...
  'compiledDouble',true,'guardValue',.25,'simulationRun',false,...
  'ICScope','Static model initialization policy/workspace/saved-source-map only; guarded solved Simscape IC parity not established without a separately authorized trajectory.',...
  'sourceModEvidence','Existing R2024b JTE094 runs40301939641 and40303063260 reused; finite fixture support, not all-input/event-topology certification.',...
  'acceptedMajorScope','UNAVAILABLE_NO_TRAJECTORY; native/callback rows cannot be certified accepted checkpoints.',...
  'nextRunAuthorization','Not granted by JTE116 handoff; no intent or simulation enabled.');
 save([prefix '_PREPARED.mat'],'rec','before','after','proof','-v7.3');
 writeJSON([prefix '_STATIC_PROOF.json'],rec.prepared);
 copyfile(guardFile,[prefix '_GUARDED_MODEL.slx']);
catch ME
 rec.failure=struct('stage',stage,'identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
 if strcmp(stage,'CANARY'),flags.DECISION='GUARD025_REJECTED_BITWISE';
 elseif strcmp(stage,'RESOURCE'),flags.DECISION='UNQUALIFIED_RESOURCE';
 else,flags.DECISION='GUARD025_STATIC_OR_ARCHIVE_REJECTED_NO_PLANT';end
end
rec.flags=flags;save([prefix '_RECORD.mat'],'rec','-v7.3');
summary=struct('flags',flags,'G5_ACCEPTED',false);
if isfield(rec,'failure'),summary.failure=rec.failure;end
if exist('ledger','var'),summary.privateArchivedRanges=ledger;end
if isfield(rec,'canary'),summary.canary=rec.canary;end
writeJSON([prefix '_SUMMARY.json'],summary);writeJSON([prefix '_FLAGS.json'],flags);
try,close_system('JTE116Guarded',0);catch,end
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
function v=normal(v,m)
if ischar(v),v=strrep(v,m,'$ROOT');
elseif isstring(v),v=replace(v,m,'$ROOT');
elseif iscell(v),v=cellfun(@(x)normal(x,m),v,'UniformOutput',false);
elseif isstruct(v),f=fieldnames(v);for k=1:numel(v),for j=1:numel(f),v(k).(f{j})=normal(v(k).(f{j}),m);end;end
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
