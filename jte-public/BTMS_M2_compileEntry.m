function BTMS_M2_compileEntry()
% New ToFile instrumentation compile only. No sim, initialize, step or trajectory.
priv=fullfile(pwd,'actuator-review-private');
prefix=fullfile(priv,['BTMS_M2_' getenv('GITHUB_RUN_ID')]);
try
 console=evalc('runReview(priv,prefix);');
catch ME
 console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');
end
save([prefix '_CONSOLE.mat'],'console','-v7.3');
if isfile([prefix '_FLAGS.json'])
 f=jsondecode(fileread([prefix '_FLAGS.json']));
 fprintf('BTMS_M2_STATIC_RESULT staticCompileAll=%d decision=%s noPhysicalRun=1 G5_ACCEPTED=false\n',f.staticCompileAll,f.decision);
else
 fprintf('BTMS_M2_STATIC_RESULT staticCompileAll=0 decision=NO_GO_STATIC_LOGGER_GRAPH noPhysicalRun=1 G5_ACCEPTED=false\n');
end
end
function runReview(priv,prefix)
r=struct('decision','NO_GO_STATIC_LOGGER_GRAPH','staticCompileAll',false,'physicalRun',false,'G5Accepted',false,...
 'solvedPhysicalIC','UNQUALIFIED','acceptedMajorClock','UNQUALIFIED','physicalRuntimePeakRAM','UNMEASURED',...
 'legacyLoggingRemoval','PROPOSAL_ONLY_NO_CHANGES','caseProofs',{{}},'stage','START');
project=[];models={};
try
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'M2:Runtime','Pinned R2024bU10 required.');
 r.runtime=version;r.processAtStart=processState();r.clock=tic;
 M=jsondecode(fileread(fullfile(priv,'m2_manifest.json')));
 for k=1:numel(M.inputs)
  a=M.inputs(k);assert(strcmp(JTE2026sha256(fullfile(priv,a.local)),a.sha256),'M2:InputSHA','Input bytes changed.');
 end
 r.stage='PIN_AND_LIBRARY';
 vendor=fullfile(pwd,'vendor-pack');original=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
 assert(strcmp(JTE2026sha256(original),M.vendorSLXSHA),'M2:VendorPin','Vendor SLX differs.');
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),assignin('base',names{k},W.workspaceSnapshot.(names{k}));end
 for ci=1:numel(M.cases)
  c=M.cases(ci);r.stage=['PREPARE_' c.key];src=fullfile(priv,c.source);
  assert(strcmp(JTE2026sha256(src),c.sourceSHA),'M2:ApprovedSource','Source does not match approved archive receipt.');
  h=load_system(src);sm=get_param(h,'Name');models{end+1}=sm; %#ok<AGROW>
  prior=jsondecode(fileread(fullfile(priv,c.priorProof)));
  assert(prior.proof.physicalParameterParity&&prior.modelWorkspaceICParametersExact,'M2:PriorProof','Prior source proof not qualified.');
  a=JTE096_modelAudit(sm);ws=workspace(sm);chartsBefore=chartScripts(sm);wireBefore=wireNames(sm);
  inv=loggingInventory(sm);srcModelSHA=JTE2026sha256(src);
  dn=['M2_' c.key];dest=fullfile(priv,[dn '.slx']);models{end+1}=dn; %#ok<AGROW>
  proof=BTMS_M2_prepareShortToFile(src,dest,c.privateDir);
  load_system(dest);paths=proof.loggerBlockPaths;loggers=find_system(dn,'LookUnderMasks','all','FollowLinks','off','BlockType','ToFile');
  assert(numel(loggers)==4&&isequal(sort(loggers(:)),sort(paths(:))),'M2:ExactlyFour','Only four ToFile additions allowed.');
  b=JTE096_modelAudit(dn,paths);
  assert(isequaln(a.blocks,b.blocks)&&isequaln(a.config,b.config),'M2:RetainedParameters','Source physical/control/IC/config parameters differ.');
  [bc,removed]=pruneLoggerEdges(b.connectivity,paths,dn);
  assert(removed==4&&isequaln(a.connectivity,bc),'M2:FullGraph','Original signal/physical connectivity differs beyond four logger branches.');
  assert(isequaln(ws,workspace(dn))&&isequal(chartsBefore,chartScripts(dn))&&isequal(wireBefore,wireNames(dn,paths)),...
   'M2:ICLawWireNames','Workspace/controller law/source wire names changed.');
  assert(strcmp(JTE2026sha256(src),srcModelSHA),'M2:ImmutableSource','Original amended source bytes changed.');
  inventoryAfter=loggingInventory(dn);
  assert(isequaln(inv.toWorkspace,inventoryAfter.toWorkspace)&&isequaln(inv.config,inventoryAfter.config)&&...
   isequaln(inv.scopes,inventoryAfter.scopes),'M2:LegacyLogging','No existing history may be silently disabled.');
  copyfile(dest,[prefix '_' c.key '_LOGGER.slx']);
  r.stage=['COMPILE_' c.key];ct=tic;
  feval(dn,[],[],[],'compile');finish=onCleanup(@()quietTerm(dn));
  ca=cell(1,4);
  for j=1:4
   sink=paths{j};ph=get_param(sink,'PortHandles');line=get_param(ph.Inport(1),'Line');
   sp=get_param(line,'SrcPortHandle');sb=get_param(sp,'Parent');
   st=attr(sink);up=attr(sb);
   assert(strcmp(st.types.Inport{1},'double'),'M2:Double','Each ToFile input must be double.');
   expected=1;if j==4,expected=312;end
   assert(st.widths.Inport(1)==expected,'M2:Width','Scalar/T312 logger width differs.');
   assert(strcmp(get_param(sink,'SampleTime'),'-1')&&strcmp(get_param(sink,'Decimation'),'1')&&...
    strcmp(get_param(sink,'SaveFormat'),'Timeseries'),'M2:TapPolicy','File logger sampling policy differs.');
   if j==2||j==3
    assert(isequal(normalRate(st.sampleTime),[proof.period_s 0]),'M2:DiscreteRate','Declared sampled rate differs.');
   end
   ss=normalRate(st.sampleTime);us=normalRate(up.sampleTime);
   assert(all(ismember(ss,us,'rows')),'M2:RateExpansion','Logger introduced rate not supported by its actual source block.');
   ca{j}=struct('role',proof.names{j},'logger',rel(sink,dn),'source',rel(sb,dn),...
    'input',st,'sourceBlock',up,'sourceRateContainsLoggerRate',true,...
    'nativeFileClockObserved',false,'acceptedSolverStepProven',false);
  end
  feval(dn,[],[],[],'term');clear finish
  elapsed=toc(ct);
  assert(strcmp(JTE2026sha256(src),c.sourceSHA),'M2:SourceMutated','Source bytes changed after compile.');
  proof.trueT312CompiledWidthVerified=true;proof.staticCompileOnly=true;
  proof.fullRetainedParametersConfigGraphParity=true;proof.fullWorkspaceAndControllerCodeParity=true;
  proof.sourceTwoPathProofReused=true;proof.tapCompiled=ca;proof.existingLogging=inv;
  proof.compileWall_s=elapsed;proof.processAfterCompile=processState();
  proof.sourceSHA256=srcModelSHA;
  proof.runtimeFileClockSemantics='NOT_OBSERVED_COMPILE_ONLY';proof.acceptedMajorStateVerified=false;
  proof.stopTimePreserved=get_param(dn,'StopTime');proof.shortHorizonRunCapApplied=false;
  save([prefix '_' c.key '_PROOF.mat'],'proof','a','b','ws','inv','ca','-v7.3');
  writeJSON([prefix '_' c.key '_PROOF.json'],proof);
  r.caseProofs{end+1}=struct('case',c.key,'compilePass',true,'graphPass',true,'legacyLoggingChanged',false); %#ok<AGROW>
  close_system(dn,0);close_system(sm,0);
 end
 assert(strcmp(JTE2026sha256(original),M.vendorSLXSHA),'M2:VendorMutated','Vendor pin changed.');
 r.staticCompileAll=true;r.decision='NO_GO_IC_CLOCK_OR_RESOURCE';
 r.loggerCandidate='M2_STATIC_LOGGER_CANDIDATE_READY';
 r.reasons={'Four added taps compile; duplicate legacy histories retained, so memory reduction unproved',...
 'Workspace/parameter identity is not complete solved Simscape t0 operating-point equality',...
 'ToFile actual file clocks/duplicates/phase and accepted physical checkpoints not observed',...
 'Actual 340s process peak/runtime/private-sink stop and free headroom not qualified by compile',...
 'StopTime is preserved from source; a future separately approved run requires an explicit340s cap'};
 r.loggingOnlyProposal=proposal();r.noPlantToFileTest='NOT_RUN; actual runtime semantics remain explicit and a toy would not resolve solved physical IC or physical process peak.';
catch ME
 r.failure=struct('stage',r.stage,'identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
end
if isfield(r,'clock'),r.totalWall_s=toc(r.clock);r=rmfield(r,'clock');end
r.processAtEnd=processState();
save([prefix '_RECORD.mat'],'r','-v7.3');writeJSON([prefix '_FLAGS.json'],r);
for k=1:numel(models),try,quietTerm(models{k});close_system(models{k},0);catch,end;end
try,if ~isempty(project),close(project);end;catch,end
end
function a=attr(b)
% Assign fields separately: multirate cell sample times must not expand a struct array.
a=struct();a.types=get_param(b,'CompiledPortDataTypes');a.widths=get_param(b,'CompiledPortWidths');
a.sampleTime=get_param(b,'CompiledSampleTime');a.units='UNAVAILABLE';
try,a.units=get_param(b,'CompiledPortUnits');catch,end
end
function x=normalRate(x)
if iscell(x),x=vertcat(x{:});end
assert(isnumeric(x)&&size(x,2)==2,'M2:RateShape','Compiled block sample rates unavailable.');
end
function [x,n]=pruneLoggerEdges(x,paths,m)
prefixes=cellfun(@(p)[rel(p,m) ':'],paths,'UniformOutput',false);n=0;
for k=1:size(x,1)
 c=x{k,2};
 for j=1:numel(c)
  dst=c{j}{4};bad=false(size(dst));
  for z=1:numel(prefixes),bad=bad|startsWith(dst,prefixes{z});end
  n=n+nnz(bad);c{j}{4}=dst(~bad);
 end
 x{k,2}=c;
end
end
function v=workspace(m)
mw=get_param(m,'ModelWorkspace');w=whos(mw);v=struct();
for k=1:numel(w),v.(w(k).name)=getVariable(mw,w(k).name);end
end
function c=chartScripts(m)
sf=sfroot;all=sf.find('-isa','Stateflow.EMChart');c=cell(0,2);
for k=1:numel(all),p=char(all(k).Path);if startsWith(p,[m '/']),c(end+1,:)={rel(p,m),char(all(k).Script)};end;end %#ok<AGROW>
if ~isempty(c),c=sortrows(c,1);end
end
function c=wireNames(m,exclude)
if nargin<2,exclude={};end
b=find_system(m,'LookUnderMasks','all','FollowLinks','off','Type','Block');c=cell(0,3);
for k=1:numel(b)
 if ismember(b{k},exclude),continue;end
 ph=get_param(b{k},'PortHandles');
 for j=1:numel(ph.Outport)
  l=get_param(ph.Outport(j),'Line');name='';if l~=-1,name=get_param(l,'Name');end
  c(end+1,:)={rel(b{k},m),j,name}; %#ok<AGROW>
 end
end
if ~isempty(c),c=sortrows(c,[1 2]);end
end
function i=loggingInventory(m)
keys={'SaveState','SaveFinalState','SaveOperatingPoint','LoadInitialState','InitialState',...
 'SaveOutput','SaveTime','SaveFormat','SignalLogging','DSMLogging','LoggingToFile','LoggingIntervals','Decimation','LimitDataPoints'};
i.config=cell(numel(keys),2);
for k=1:numel(keys),i.config(k,:)={keys{k},get_param(m,keys{k})};end
tw=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','ToWorkspace');i.toWorkspace=cell(numel(tw),2);
for k=1:numel(tw)
 p=struct();for key={'VariableName','SaveFormat','MaxDataPoints','Decimation','SampleTime'},p.(key{1})=get_param(tw{k},key{1});end
 i.toWorkspace(k,:)={rel(tw{k},m),p};
end
sc=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','Scope');i.scopes=cell(numel(sc),2);
for k=1:numel(sc)
 v=struct();
 try
  cfg=get_param(sc{k},'ScopeConfiguration');pp=properties(cfg);
  for j=1:numel(pp),if contains(pp{j},'DataLogging'),try,v.(pp{j})=cfg.(pp{j});catch,v.(pp{j})='UNAVAILABLE';end;end;end
 catch,v.status='UNAVAILABLE';end
 i.scopes(k,:)={rel(sc{k},m),v};
end
i.globalSDIPreferences='UNAVAILABLE_NOT_CHANGED';i.simulationInputOverrides='NO_PHYSICAL_RUN_OR_OVERRIDES';
end
function p=proposal()
p=struct('status','SEPARATE_REVIEW_REQUIRED_NOT_APPLIED',...
 'ToWorkspace','Replace duplicate core/y/Ttrue workspace histories with reviewed ToFile evidence; do not remove before native-file semantics/sink/readback qualification',...
 'derivedMetrics','Derive Tmax/Tmin from full T312 only with verified port ordering/units/native clocks; retain provenance of constant Ambient',...
 'global','Disable only proven redundant SignalLogging/DSMLogging/SaveOutput/Scope/SDI buffers on separate clone, after checking the actual inventory. SaveState may already be off; do not invent active full-state history',...
 'retained','No physical/controller/sensor/workspace/source law/IC parameter change; retain native330-338 with330-334 control; duplicates/own clocks unchanged',...
 'checkpoints','Retain documented complete initial operating-point and bounded event-state witness plan; no all2400 state history is demanded for340 feasibility',...
 'stop','One future explicitly approved340 run only with measured peak/RAM/disk/time guards, file byte budget and verified private readback; no automatic repeat');
end
function r=processState()
r=struct('scope','MATLAB_PROCESS_STATIC_ONLY_NOT_PLANT_PEAK','procStatus','UNAVAILABLE');
if isfile('/proc/self/status'),s=fileread('/proc/self/status');r.procStatus=regexp(s,'(?m)^(VmHWM|VmRSS|VmPeak|VmSize):.*$','match');end
end
function n=rel(p,m)
if strcmp(p,m),n='$ROOT';else,n=['$ROOT' p(numel(m)+1:end)];end
end
function quietTerm(m)
try,feval(m,[],[],[],'term');catch,end
end
function writeJSON(p,x)
f=fopen(p,'w');assert(f~=-1,'M2:PrivateWrite','Private write failed.');c=onCleanup(@()fclose(f));fprintf(f,'%s',jsonencode(x));
end
