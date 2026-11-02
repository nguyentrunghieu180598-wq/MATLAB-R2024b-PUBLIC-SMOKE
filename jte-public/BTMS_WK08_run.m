function BTMS_WK08_run(manifestFile)
% ONE direct-start trajectory. Owner only; CI delivery stays disabled.
M=jsondecode(fileread(manifestFile));root=char(M.privateRoot);
assert(isfolder(root),'WK08:Private','Private root missing.');
flags=struct('status','UNQUALIFIED','physicalRun',false,'G5Accepted',false, ...
 'run',M.run,'commit',M.commit,'stopTime_s',M.stopTime_s, ...
 'stage','INPUT','hiddenSimscapeICCertified',false);
s=[];project=[];m='';failure=[];wall=tic;
guard=onCleanup(@finish); %#ok<NASGU>
try
 assert(strcmp(char(version),'24.2.0.3361896 (R2024b) Update 10'), ...
  'WK08:Build','Pinned R2024b Update 10 build required.');
 if strcmp(M.mode,'R1')
  assert(M.stopTime_s==340 && strcmp(getenv('WK08_OWNER_APPROVAL'), ...
   'APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO'), ...
   'WK08:Approval','R1 requires separate owner approval after Claude GO.');
  assert(strcmp(M.run,getenv('GITHUB_RUN_ID')) && ...
   strcmp(M.commit,getenv('GITHUB_SHA')), ...
   'WK08:Context','Run/commit provenance mismatch.');
 else
  assert(strcmp(M.mode,'OWNER_LOCAL_5S') && M.stopTime_s==5 && ...
   strcmp(M.ownerApproval,'APPROVE_WK08_LOCAL_5S_ONCE'), ...
   'WK08:Approval','Separate owner-local 5s approval required.');
 end
 pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
 assert(strcmp(JTE2026sha256(M.vendorSLX),pin),'WK08:VendorSHA','Vendor SHA mismatch.');
 for k=1:numel(M.inputs)
  a=M.inputs(k);
  assert(strcmp(JTE2026sha256(fullfile(root,a.local)),a.sha256), ...
   'WK08:InputSHA','Protected input SHA mismatch.');
 end
 project=openProject(fullfile(M.vendorRoot,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(root,'source_workspace.mat'),'workspaceSnapshot');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),assignin('base',names{k},W.workspaceSnapshot.(names{k}));end
 assert(evalin('base','ambient')==300,'WK08:Ambient','Reference must remain 300K.');
 source=fullfile(root,'M2340Source.slx');target=fullfile(root,'WK08R1.slx');
 native=fullfile(root,'native');assert(~isfolder(native),'WK08:Fresh','Fresh output folder required.');
 mkdir(native);
 flags.stage='PREPARE';
 proof=BTMS_WK08_prepare(source,target,native,M.sourceSHA256,M.stopTime_s);
 m='WK08R1';load_system(target);
 assert(isequaln(proof.fingerprint,BTMS_WK08_structFingerprint(m)), ...
  'WK08:Fingerprint','Saved/reloaded structure differs.');
 loadFile=get_param([m '/Current demand'],'FileName');resolved=which(loadFile);
 pinned=dir(fullfile(M.vendorRoot,'**',loadFile));
 assert(numel(pinned)==1 && ~isempty(resolved) && ...
 strcmp(JTE2026sha256(resolved),JTE2026sha256(fullfile(pinned.folder,pinned.name))), ...
 'WK08:Load','Resolved source current file differs from pinned vendor.');
 proof.loadSHA256=JTE2026sha256(resolved);
 proof.runtimeBuild=char(version);
 save(fullfile(root,'WK08_PREPARED_PROOF.mat'),'proof','M','-v7.3');
 for k=1:numel(proof.privateTargets)
  assert(~isfile(proof.privateTargets{k}),'WK08:Overwrite','Native target exists.');
 end
 % Receipt is written before the only initialize. No restore/fallback/retry.
 flags.stage='INITIALIZE_ONCE';flags.physicalRun=true;
 writeJSON(fullfile(root,'WK08_FLAGS.json'),flags);
 s=simulation(m);initialize(s);
 assert(str2double(get_param(m,'StopTime'))==M.stopTime_s && ...
 strcmp(get_param(m,'Solver'),'ode23t') && ...
 str2double(get_param(m,'MaxStep'))==.05, ...
 'WK08:EffectiveConfig','Effective run cap/solver changed.');
 assert(s.Time==0,'WK08:T0','Direct-start time is not zero.');
 flags.stage='FIRST_MAJOR';
 final=step(s); % one completed initial major; paused To File files are closed
 assert(~final && strcmp(char(s.Status),'paused'), ...
  'WK08:FirstMajor','Initial completed-major witness unavailable.');
 first=readNative(proof.privateTargets{4},312,0,false);
 measured=readNative(proof.privateTargets{6},1,0,false);
 trueMax=readNative(proof.privateTargets{5},1,0,false);
 assert(first.time(1)==0 && measured.time(1)==0 && trueMax.time(1)==0 && ...
 trueMax.data(1)==max(first.data(1,:)) && ...
 measured.data(1)==trueMax.data(1), ...
 'WK08:T0Values','Neutral true/measured t0 witness mismatch.');
 flags.visibleT0Checked=true;
 flags.t0Protocol='DIRECT_START; HIDDEN_SIMSCAPE_IC_NOT_CERTIFIED';
 flags.stage='TRAJECTORY';
 while ~final
  assert(toc(wall)<1200,'WK08:Wall','One trajectory wall ceiling reached.');
  final=step(s);
 end
 % R2024b final step may already be inactive (WK07 verified).
 terminalStatus=char(s.Status);
 assert(any(strcmp(terminalStatus,{'paused','inactive'})), ...
  'WK08:Terminal','Unexpected final Simulation status.');
 if strcmp(terminalStatus,'paused'),out=stop(s);else,out=s.SimulationOutput;end
 s=[];
 meta=out.SimulationMetadata;info=meta.ExecutionInfo;
 assert(any(strcmp(char(info.StopEvent),{'ReachedStopTime','StopCommand'})) && ...
 isempty(out.ErrorMessage) && strcmp(char(meta.ModelInfo.SimulationMode),'normal'), ...
 'WK08:StopEvent','Terminal event or runtime diagnostic unqualified.');
 % ExecutionInfo.StopEventTime does not exist in pinned R2024b.
 % Require every native To File endpoint at the saved stop time instead.
 flags.stage='NATIVE_GATES';
 for k=1:8
  width=1;if any(k==[4 8]),width=312;end
  x=readNative(proof.privateTargets{k},width,M.stopTime_s,true);
  if k==1 || k==2
   assert(all(ismember(x.data(:),[.25 .5 .75])), ...
    'WK08:CommandLevels','Native core/held command outside source levels.');
  elseif k==8
   assert(isequal(x.time,(0:M.stopTime_s)'), ...
    'WK08:OneSecond','Per-channel observation is not exactly 0:1:stop.');
  end
  if k==5,tx=x;end
  if k==6
   assert(isequaln(tx.time,x.time) && isequaln(tx.data,x.data), ...
    'WK08:NeutralMax','True/measured native maxima differ in neutral R1.');
  end
 end
 assert(isequaln(proof.fingerprint,BTMS_WK08_structFingerprint(m)) && ...
 strcmp(JTE2026sha256(target),proof.derivativeSHA256) && ...
 strcmp(JTE2026sha256(source),M.sourceSHA256) && ...
 strcmp(JTE2026sha256(M.vendorSLX),pin), ...
 'WK08:Immutable','Source/derivative/fingerprint changed.');
 flags.status='R1_NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK';
 if M.stopTime_s==5,flags.status='LOCAL_5S_GATES_PASS_NOT_R1';end
 flags.stage='DONE';flags.terminalStatus=terminalStatus;
 flags.nativeFinite=true;flags.nativeEndpointsChecked=true;
 flags.runtimeWall_s=toc(wall);flags.derivativeSHA256=proof.derivativeSHA256;
 flags.structuralFingerprintChecked=true;
catch err
 failure=err;flags.identifier=err.identifier;flags.reason=err.message;
end
writeJSON(fullfile(root,'WK08_FLAGS.json'),flags);
if ~isempty(failure)
 error('WK08:Unqualified','Private diagnostics saved; no automatic retry.');
end
 function finish()
  if ~isempty(s),try,if ~strcmp(char(s.Status),'inactive'),stop(s);end,catch,end,end
  if ~isempty(m),try,close_system(m,0);catch,end,end
  if ~isempty(project),try,close(project);catch,end,end
 end
end
function x=readNative(file,width,stopTime,complete)
assert(isfile(file),'WK08:NativeMissing','Native To File missing.');
a=load(file);keys=fieldnames(a);
assert(numel(keys)==1 && isa(a.(keys{1}),'timeseries'), ...
 'WK08:NativeSchema','Expected one Timeseries variable.');
t=a.(keys{1});x.time=t.Time(:);d=t.Data;
if ~t.IsTimeFirst,d=permute(d,[ndims(d) 1:ndims(d)-1]);end
x.data=reshape(d,numel(x.time),[]);
assert(~isempty(x.time) && size(x.data,2)==width && ...
 all(isfinite(x.time)) && all(isfinite(x.data(:))) && ...
 x.time(1)==0 && all(diff(x.time)>=0), ...
 'WK08:NativeFinite','Invalid native width/time/finite values.');
if complete
 assert(x.time(end)==stopTime && all(x.time<=stopTime), ...
  'WK08:StopTime','Native horizon incomplete or beyond approved stop.');
end
end
function writeJSON(file,x)
f=fopen(file,'w');assert(f>=0,'WK08:PrivateWrite','Private flags unavailable.');
c=onCleanup(@()fclose(f));fprintf(f,'%s',jsonencode(x));
end
