function BTMS_M2_340_compileEntry()
priv=fullfile(pwd,'actuator-review-private');pre=fullfile(priv,['BTMS_M2340_' getenv('GITHUB_RUN_ID')]);
try,console=evalc('review(priv,pre);');catch ME,console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');end
save([pre '_CONSOLE.mat'],'console','-v7.3');
if isfile([pre '_FLAGS.json'])
 f=jsondecode(fileread([pre '_FLAGS.json']));
 fprintf('BTMS_M2_340_STATIC_RESULT status=%s compile=%d physicalRun=0 G5_ACCEPTED=false\n',f.status,f.staticCompilePass);
else,fprintf('BTMS_M2_340_STATIC_RESULT status=M2_340_STATIC_GRAPH_REJECTED compile=0 physicalRun=0 G5_ACCEPTED=false\n');end
end
function review(priv,pre)
r=struct('status','M2_340_STATIC_GRAPH_REJECTED','staticCompilePass',false,'physicalRun',false,'G5Accepted',false,...
 'stage','INPUT','compileCalls',0,'runtimePeakKnown',false,'ownerPhysicalApproval',false);project=[];models={};timer=tic;
try
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'M2340:Runtime','Pinned runtime required.');
 M=jsondecode(fileread(fullfile(priv,'m2340_manifest.json')));r.runtime=version;
 assert(M.staticCompileResourceScreen,'M2340:Resource','Static host/cgroup reserve unavailable.');
 for k=1:numel(M.inputs),a=M.inputs(k);assert(strcmp(JTE2026sha256(fullfile(priv,a.local)),a.sha256),'M2340:SHA','Verified input drift.');end
 src=fullfile(priv,'M2340Source.slx');target=fullfile(priv,'M2340Prepared.slx');
 old=load(fullfile(priv,'old_proof.mat'),'proof');prior=old.proof;
 assert(strcmp(prior.instrumentedModelSHA256,M.sourceModel.sha256)&&prior.period_s==.01&&prior.trueT312CompiledWidthVerified,...
  'M2340:Prior','Wrong archived B0L10ms proof.');
 vendor=fullfile(pwd,'vendor-pack');original=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
 pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
 assert(strcmp(JTE2026sha256(original),pin),'M2340:Vendor','Vendor SLX pin differs.');
 r.stage='PROJECT_AND_INPUTS';project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),assignin('base',names{k},W.workspaceSnapshot.(names{k}));end
 h=load_system(src);sm=get_param(h,'Name');models{end+1}=sm;
 sa=JTE096_modelAudit(sm);sw=workspace(sm);sc=chartScripts(sm);sn=wireNames(sm);
 commentsBefore=comments(sm);sourceInventory=loggingInventory(sm);
 loadFile=get_param([sm '/Current demand'],'FileName');resolved=which(loadFile);
 pinned=dir(fullfile(vendor,'**',loadFile));assert(numel(pinned)==1&&~isempty(resolved),'M2340:Load','Pinned current input missing/ambiguous.');
 loadSHA=JTE2026sha256(fullfile(pinned.folder,pinned.name));assert(strcmp(JTE2026sha256(resolved),loadSHA),'M2340:Load','Resolved current load differs from vendor pin.');
 r.stage='PREPARE_ONE_LOGGING_ONLY_CLONE';
 proof=BTMS_M2_prepare340NoRun(src,target,M.privateDir,M.sourceModel.sha256);copyfile(target,[pre '_MODEL.slx']);r.stage='ALLOWED_DIFF_AUDIT';tm='M2340Prepared';models{end+1}=tm;load_system(target);
 assert(numel(proof.disabledRedundantObservers)==3&&proof.retainedOtherObservers==3,'M2340:ObserverCount','Expected exact archived B0L observer inventory.');
 ta=JTE096_modelAudit(tm);expected=sa;
 for k=1:4
  path=rel(proof.fourLoggerPaths{k},tm);si=find(strcmp(expected.blocks(:,1),path));ti=find(strcmp(ta.blocks(:,1),path));
  assert(numel(si)==1&&numel(ti)==1&&strcmp(expected.blocks{si,2},'ToFile'),'M2340:Sink','Unknown file sink.');
  params=expected.blocks{si,3};other=ta.blocks{ti,3};fi=find(strcmp(params{1},'FileName'));
  assert(numel(fi)==1&&isequal(params{1},other{1}),'M2340:SinkParameters','File sink parameter set changed.');
  assert(strcmp(other{2}{fi},proof.privateTargets{k})&&~strcmp(params{2}{fi},other{2}{fi}),'M2340:PrivatePath','Fresh private file path not bound.');
  params{2}{fi}=other{2}{fi};expected.blocks{si,3}=params;
 end
 ci=find(strcmp(expected.config{1},'StopTime'));assert(numel(ci)==1&&strcmp(expected.config{2}{ci},'2400'),'M2340:StopSource','Source not2400.');
 expected.config{2}{ci}='340';
 assert(isequaln(expected.blocks,ta.blocks)&&isequaln(expected.config,ta.config)&&isequaln(sa.connectivity,ta.connectivity),...
  'M2340:FullGraph','Unapproved block/config/signal/physical graph change.');
 afterComments=comments(tm);expectedComments=commentsBefore;
 for k=1:numel(proof.disabledRedundantObservers)
  b=rel(proof.disabledRedundantObservers{k},tm);ix=find(strcmp(expectedComments(:,1),b));assert(numel(ix)==1&&strcmp(expectedComments{ix,2},'off'),'M2340:CommentSource','Observer was not active.');
  expectedComments{ix,2}='on';
 end
 assert(isequal(expectedComments,afterComments),'M2340:OnlyComments','Unexpected Commented change.');
 assert(isequaln(sw,workspace(tm))&&isequal(sc,chartScripts(tm))&&isequal(sn,wireNames(tm)),...
  'M2340:ICLawNames','Workspace/controller source/old wire names differ.');
 assert(strcmp(JTE2026sha256(which(get_param([tm '/Current demand'],'FileName'))),loadSHA),'M2340:Load','Target load changed.');
 assert(getSimulinkBlockHandle([tm '/Battery Control/JTE local bias'])==-1,'M2340:Bias','Unexpected fault chart.');
 for k=1:4,assert(~isfile(proof.privateTargets{k}),'M2340:Overwrite','Target MAT exists.');end
 copyfile(target,[pre '_MODEL.slx']);
 r.stage='COMPILE_TARGET_ONCE';r.compileCalls=1;ct=tic;feval(tm,[],[],[],'compile');finish=onCleanup(@()quietTerm(tm));
 taps=cell(1,4);
 for k=1:4
  sink=proof.fourLoggerPaths{k};ph=get_param(sink,'PortHandles');l=get_param(ph.Inport(1),'Line');
  source=get_param(l,'SrcPortHandle');sb=get_param(source,'Parent');a=attr(sink);b=attr(sb);
  assert(isequaln(a,prior.tapCompiled{k}.input)&&isequaln(b,prior.tapCompiled{k}.sourceBlock),...
   'M2340:CompiledSourceRate','Removing observer changed actual source/sink type,width,units or compiled rates.');
  assert(strcmp(a.types.Inport{1},'double'),'M2340:Double','File input notdouble.');
  width=1;if k==4,width=312;end;assert(a.widths.Inport(1)==width,'M2340:Width','Wrong scalar/T312 width.');
  taps{k}=struct('role',prior.names{k},'input',a,'sourceBlock',b,'sourcePath',rel(sb,tm),...
   'sameAsPriorCompiledSource',true,'actualNativeClockObserved',false);
 end
 inactive=cell(1,numel(proof.disabledRedundantObservers));
 for k=1:numel(inactive)
  b=proof.disabledRedundantObservers{k};active=get_param(b,'CompiledIsActive');
  assert(strcmp(active,'off'),'M2340:Inactive','Commented observer still compiled active.');
  inactive{k}=struct('path',rel(b,tm),'CompiledIsActive',active);
 end
 feval(tm,[],[],[],'term');clear finish
 assert(strcmp(JTE2026sha256(src),M.sourceModel.sha256)&&strcmp(JTE2026sha256(original),pin),'M2340:Immutable','Source/vendor bytes changed.');
 assert(strcmp(get_param(tm,'StopTime'),'340')&&str2double(get_param(tm,'StartTime'))==0,'M2340:EffectiveCap','Saved horizon differs.');
 proof.status='M2_340_PREPARED_STATIC_PASS_OWNER_PHYSICAL_APPROVAL_NEEDED';
 proof.staticCompilePass=true;proof.fullGraphOnlyAllowedChanges=true;proof.physicalGraphRevalidated=true;
 proof.compiledTaps=taps;proof.inactiveObservers=inactive;proof.sourceInventory=sourceInventory;
 proof.derivativeInventory=loggingInventory(tm);proof.compileOnlyWall_s=toc(ct);proof.processStaticMemory=processState();
 proof.solvedPhysicalICValidated=false;proof.fileClocksValidated=false;proof.peakRAMMeasured=false;
 proof.sourceLoadSHA=loadSHA;proof.sourceModelWorkspaceExact=true;proof.controllerCodeExact=true;
 proof.savedRuntimeCapVerified=true;proof.fullDynamicEventBehavior='NOT_OBSERVED; controller graph/code/source compiled rates unchanged';
 save([pre '_PROOF.mat'],'proof','sa','ta','sw','sc','commentsBefore','afterComments','prior','-v7.3');
 writeJSON([pre '_PROOF.json'],proof);
 r.status=proof.status;r.staticCompilePass=true;r.actualTapTypeRateParity=true;r.sourceSHA=M.sourceModel.sha256;
 r.disabledObservers=3;r.retainedObservers=3;r.knownDynamicUnknowns={'solved physical t0/hidden operating point',...
  'actual file/accepted-major clocks','actual340s peak and runtime'};
 r.onlyRemainingAuthorizationBlocker='OWNER_EXPLICIT_PHYSICAL_APPROVAL_REQUIRED';
 r.interpretation='Static source/logger/host policy supports bounded observation only. Unmeasured future peak/solved IC are runtime gates, not pre-run proof requirements.';
catch ME
 r.failure=struct('stage',r.stage,'identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
end
r.staticReviewWall_s=toc(timer);r.processStaticMemory=processState();
save([pre '_RECORD.mat'],'r','-v7.3');writeJSON([pre '_FLAGS.json'],r);
for k=1:numel(models),try,quietTerm(models{k});close_system(models{k},0);catch,end;end
try,if ~isempty(project),close(project);end;catch,end
end
function a=attr(b)
a=struct();a.types=get_param(b,'CompiledPortDataTypes');a.widths=get_param(b,'CompiledPortWidths');
a.sampleTime=get_param(b,'CompiledSampleTime');a.units='UNAVAILABLE';
try,a.units=get_param(b,'CompiledPortUnits');catch,end
end
function c=comments(m)
bs=sort(find_system(m,'LookUnderMasks','all','FollowLinks','off','Type','Block'));c=cell(numel(bs),2);
for k=1:numel(bs),c(k,:)={rel(bs{k},m),get_param(bs{k},'Commented')};end
end
function v=workspace(m)
mw=get_param(m,'ModelWorkspace');z=whos(mw);v=struct();
for k=1:numel(z),v.(z(k).name)=getVariable(mw,z(k).name);end
end
function c=chartScripts(m)
sf=sfroot;all=sf.find('-isa','Stateflow.EMChart');c=cell(0,2);
for k=1:numel(all),p=char(all(k).Path);if startsWith(p,[m '/']),c(end+1,:)={rel(p,m),char(all(k).Script)};end;end %#ok<AGROW>
if ~isempty(c),c=sortrows(c,1);end
end
function c=wireNames(m)
bs=find_system(m,'LookUnderMasks','all','FollowLinks','off','Type','Block');c=cell(0,3);
for k=1:numel(bs)
 ph=get_param(bs{k},'PortHandles');
 for j=1:numel(ph.Outport)
  l=get_param(ph.Outport(j),'Line');name='';if l~=-1,name=get_param(l,'Name');end
  c(end+1,:)={rel(bs{k},m),j,name}; %#ok<AGROW>
 end
end
if ~isempty(c),c=sortrows(c,[1 2]);end
end
function i=loggingInventory(m)
bs=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','ToWorkspace');i.toWorkspace=cell(numel(bs),2);
for k=1:numel(bs),i.toWorkspace(k,:)={rel(bs{k},m),struct('variable',get_param(bs{k},'VariableName'),'Commented',get_param(bs{k},'Commented'))};end
keys={'SaveState','SaveFinalState','SaveOperatingPoint','SignalLogging','DSMLogging','SaveOutput','LoggingIntervals','Decimation','Refine'};
i.config=cell(numel(keys),2);for k=1:numel(keys),i.config(k,:)={keys{k},get_param(m,keys{k})};end
i.globalSDI='UNAVAILABLE_UNCHANGED';
end
function p=processState()
p=struct('scope','STATIC_COMPILE_ONLY_NOT_PHYSICAL_PEAK','procStatus',{{}});
if isfile('/proc/self/status')
 s=fileread('/proc/self/status');p.procStatus=regexp(s,'(?m)^(VmHWM|VmRSS|VmPeak|VmSize):[^\r\n]*','match');
end
end
function n=rel(b,m)
if strcmp(b,m),n='$ROOT';else,n=['$ROOT' b(numel(m)+1:end)];end
end
function quietTerm(m)
try,feval(m,[],[],[],'term');catch,end
end
function writeJSON(p,x)
f=fopen(p,'w');assert(f~=-1,'M2340:PrivateWrite','Private write failed.');c=onCleanup(@()fclose(f));fprintf(f,'%s',jsonencode(x));
end
