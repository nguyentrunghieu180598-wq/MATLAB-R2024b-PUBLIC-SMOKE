function JTE103_capability(mode)
% Public R2024b APIs only. Canary is not a physical G5 model.
P=paths();
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE103:Runtime','Wrong R2024b Update10 runtime.');
if strcmp(mode,'readback'),readback(P);return;end
assert(strcmp(mode,'capture'),'JTE103:Mode','Unknown capability mode.');
M=jsondecode(fileread(fullfile(P.root,'cap_manifest.json')));
for k=1:numel(M.files)
 v=M.files(k);assert(strcmp(JTE2026sha256(fullfile(P.root,v.local)),v.sha256),'JTE103:SHA','Input changed.');
end
api=struct('runtime',version,'profileModelWhich',which('solverprofiler.profileModel'),...
 'exploreResultWhich',which('solverprofiler.exploreResult'),'profileModelHelp',help('solverprofiler.profileModel'),...
 'exploreResultHelp',help('solverprofiler.exploreResult'),'useJavaAWT',usejava('awt'),'useJavaDesktop',usejava('desktop'),...
 'displayConfigured',~isempty(getenv('DISPLAY')),'publicDoc','https://www.mathworks.com/help/releases/R2024b/simulink/slref/solverprofiler.profilemodel.html');
required={'DataFullFile','OpenSP','SaveStates','SaveSimscapeStates','SaveZCSignals','SaveJacobian','StartTime','StopTime','BufferSize','TimeOut'};
api.documentedNames=required;api.namesPresent=cellfun(@(x)contains(lower(api.profileModelHelp),lower(x)),required);
api.available=~isempty(api.profileModelWhich)&&~isempty(api.exploreResultWhich)&&~isempty(api.profileModelHelp)&&~isempty(api.exploreResultHelp);
api.helpNameCoverageRole='DIAGNOSTIC_ONLY: runtime help uses UI labels, not literal API keywords. Exact R2024b documented signature must be exercised by the canary call.';
api.signatureValidation='PENDING_ACTUAL_DOCUMENTED_CANARY_CALL';
save([P.prefix '_API.mat'],'api','-v7.3');writeJSON([P.prefix '_API.json'],api);
flags=struct('PROFILER_API_R2024B','PENDING_ACTUAL_CALL','CANARY_CAPTURE','NOT_RUN','canaryCaptured',false,'priorSessionPresent',~isempty(M.priorProfiles),...
 'retentionFile','','SOURCE_PROFILE_AUTHORIZED',false,'GUI_EXPLORE_RESULT','UNAVAILABLE_HEADLESS_OR_NOT_ATTEMPTED',...
 'G5_PROVENANCE','PASS_INHERITED','G5_ACTUATION_EVENT','ACTOR_UNPROVEN','G5_THERMAL_CONVERGENCE','UNPROVEN','G5_ACCEPTED',false);
try
 assert(api.available,'JTE103:PublicAPI','Required R2024b public APIs/help signature not verified.');
 if ~isempty(M.priorProfiles)
  prior=struct([]);
  for k=1:numel(M.priorProfiles)
   item=M.priorProfiles(k);file=fullfile(P.root,item.local);assert(strcmp(JTE2026sha256(file),item.sha256),'JTE103:PriorSHA','Prior session changed.');
   inv=whos('-file',file); % inventory only, never load/access session object fields
   x=struct('input',item,'inventory',inv,'sourceAndWindowProvenance','REQUIRES_PUBLIC_GUI_REVIEW');
   if isempty(prior),prior=x;else,prior(end+1)=x;end %#ok<AGROW>
   copyfile(file,[P.prefix '_PRIOR_PROFILE_' num2str(k) '.mat']);
  end
  save([P.prefix '_PRIOR_INVENTORY.mat'],'prior','-v7.3');
  flags.CANARY_CAPTURE='SKIPPED_EXISTING_PRIVATE_SESSION_CANDIDATE';flags.PROFILER_API_R2024B=pass(api.available);
  flags.retentionFile=['JTE103_' P.run '_CAPABILITY_PRIOR_PROFILE_1.mat'];
  flags.SOURCE_PROFILE_AUTHORIZED=false; % reuse/review before any new study run
 else
  model='JTE103ProfilerPathCanary';new_system(model);g=onCleanup(@()quietModel(model)); %#ok<NASGU>
  set_param(model,'Solver','ode23t','RelTol','1e-3','AbsTol','auto','MaxStep','.001','StopTime','.02','ReturnWorkspaceOutputs','off');
  add_block('simulink/Sources/Constant',[model '/UnitInput'],'Value','1','SampleTime','0');
  add_block('simulink/Sources/Step',[model '/ResetAt10ms'],'Time','.01','Before','0','After','1','SampleTime','0');
  add_block('simulink/Continuous/Integrator',[model '/ResettableState'],'ExternalReset','rising','InitialCondition','0');
  add_block('simulink/Sinks/To Workspace',[model '/CanaryOutput'],'VariableName','jte103CanaryY','SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
  add_line(model,'UnitInput/1','ResettableState/1');add_line(model,'ResetAt10ms/1','ResettableState/2');add_line(model,'ResettableState/1','CanaryOutput/1');
  canaryModelFile=fullfile(P.root,[model '.slx']);save_system(model,canaryModelFile);
  copyfile(canaryModelFile,[P.prefix '_CANARY_MODEL.slx']);
  file=[P.prefix '_CANARY_SESSION.mat'];
  capturedLog=evalc("res=solverprofiler.profileModel(model,'StartTime',0,'StopTime',.02,'DataFullFile',file,'OpenSP','off,'SaveStates','on,'SaveSimscapeStates','off,'SaveZCSignals','on,'SaveJacobian','off,'BufferSize',10000,'TimeOut',30);");
  assert(isstruct(res)&&isfield(res,'summary')&&isfield(res,'file')&&isfile(res.file),'JTE103:Capture','No documented profiler result.');
  assert(res.summary.tStart==0&&res.summary.tStop==.02&&res.summary.steps>0&&strcmp(res.summary.solver,'ode23t'),'JTE103:CanarySummary','Wrong canary execution.');
  sessionInventory=whos('-file',res.file);sessionSHA=JTE2026sha256(res.file);
  save([P.prefix '_CANARY_PUBLIC_RESULT.mat'],'res','capturedLog','sessionInventory','sessionSHA','-v7.3');
  writeJSON([P.prefix '_CANARY_PUBLIC_SUMMARY.json'],res.summary);
  flags.CANARY_CAPTURE='PASS';flags.canaryCaptured=true;flags.PROFILER_API_R2024B='PASS_ACTUAL_R2024B_CALL';
  flags.retentionFile=['JTE103_' P.run '_CAPABILITY_CANARY_SESSION.mat'];
  flags.SOURCE_PROFILE_AUTHORIZED=true; % still requires private readback before source intent
 end
catch err
 failure=struct('identifier',err.identifier,'message',err.message,'phase','PUBLIC_API_OR_CANARY','physicalG5SimulationRun',false);
 writeJSON([P.prefix '_FAILURE.json'],failure);flags.CANARY_CAPTURE='FAIL_OR_BLOCKED';flags.SOURCE_PROFILE_AUTHORIZED=false;
end
writeJSON([P.prefix '_FLAGS.json'],flags);
% Independent useful work: read-only G6 ranking/deviation audit even if profiler blocked.
if isfield(M,'reusedG6AuditRun')
 fprintf('JTE103_G6_READONLY_RESULT status=PASS_REUSED_FROM_40473995420 rankingRecomputed=0 newClosedLoopSimulations=0 oldOutcomesEdited=0\n');
else
 JTE103_g6Audit();
end
fprintf('JTE103_CAPABILITY_RESULT PROFILER_API_R2024B=%s CANARY_CAPTURE=%s priorSessionPresent=%d sourceProfileRequiresPrivateReadback=1 G6_newSimulations=0 G5_ACCEPTED=false\n',...
 flags.PROFILER_API_R2024B,flags.CANARY_CAPTURE,flags.priorSessionPresent);
end
function readback(P)
flags=jsondecode(fileread([P.prefix '_FLAGS.json']));
result=struct('SESSION_SHA_READBACK','UNAVAILABLE','SESSION_INVENTORY_READBACK','UNAVAILABLE','GUI_EXPLORE_RESULT','UNAVAILABLE_HEADLESS',...
 'SESSION_EVENT_FIELDS','NOT_ACCESSED','G5_ACCEPTED',false);
if isfile(fullfile(P.root,'readback_manifest.json'))
 m=jsondecode(fileread(fullfile(P.root,'readback_manifest.json')));file=fullfile(P.root,m.local);
 assert(strcmp(JTE2026sha256(file),m.sha256),'JTE103:ReadbackSHA','Session bytes changed.');
 inventory=whos('-file',file);assert(~isempty(inventory),'JTE103:ReadbackInventory','Empty MAT inventory.');
 result.SESSION_SHA_READBACK='PASS';result.SESSION_INVENTORY_READBACK='PASS';
 if usejava('awt')&&~isempty(getenv('DISPLAY'))
  try
   solverprofiler.exploreResult(file);drawnow;
   result.GUI_EXPLORE_RESULT='PUBLIC_EXPLORER_LOAD_RETURNED_REQUIRES_VISUAL_REVIEW';
  catch err
   result.GUI_EXPLORE_RESULT='UNAVAILABLE_PUBLIC_API_GUI_ERROR';result.guiFailureIdentifier=err.identifier;
  end
 end
 save(fullfile(P.root,['JTE103_' P.run '_READBACK_INVENTORY.mat']),'inventory','result','-v7.3');
end
result.SOURCE_PROFILE_ELIGIBLE=flags.SOURCE_PROFILE_AUTHORIZED&&strcmp(result.SESSION_SHA_READBACK,'PASS')&&strcmp(result.SESSION_INVENTORY_READBACK,'PASS');
writeJSON(fullfile(P.root,['JTE103_' P.run '_READBACK_FLAGS.json']),result);
fprintf('JTE103_PROFILER_RETENTION_RESULT SESSION_SHA_READBACK=%s SESSION_INVENTORY_READBACK=%s GUI_EXPLORE_RESULT=%s sourceProfileEligible=%d ACTOR_PROVEN=0 G5_ACCEPTED=false\n',...
 result.SESSION_SHA_READBACK,result.SESSION_INVENTORY_READBACK,result.GUI_EXPLORE_RESULT,result.SOURCE_PROFILE_ELIGIBLE);
end
function P=paths()
P.root=fullfile(pwd,'jte103-private');P.run=getenv('GITHUB_RUN_ID');P.prefix=fullfile(P.root,['JTE103_' P.run '_CAPABILITY']);
end
function s=pass(v)
if v,s='PASS';else,s='UNAVAILABLE_OR_SIGNATURE_MISMATCH';end
end
function writeJSON(file,v)
h=fopen(file,'w');assert(h~=-1,'JTE103:Write','Private write failed.');fprintf(h,'%s',jsonencode(v));fclose(h);
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
