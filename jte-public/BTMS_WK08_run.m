function BTMS_WK08_run(manifestFile)
% ONE direct-start trajectory. Owner only; CI delivery stays disabled.
M=jsondecode(fileread(manifestFile));root=char(M.privateRoot);
assert(isfolder(root),'WK08:Private','Private root missing.');
flags=struct('status','UNQUALIFIED','physicalRun',false,'G5Accepted',false, ...
 'run',M.run,'commit',M.commit,'stopTime_s',M.stopTime_s, ...
 'stage','INPUT','hiddenSimscapeICCertified',false);
isCI5S=strcmp(M.mode,'CI_5S');
isD13=strcmp(M.mode,'D13_REF');
if isD13
 flags.mode='D13_REF';flags.scenarioSHA256=M.scenarioSHA256;
end
if isCI5S
 flags.mode='CI_5S';flags.prepareWall_s=NaN;flags.firstStepWall_s=NaN;
 flags.trajectoryWall_s=NaN;flags.majorSteps=0;
 flags.pausedNativeReadable=struct('file',{},'readable',{},'identifier',{});
 flags.allPausedNativeReadable=false;
end
s=[];project=[];m='';failure=[];wall=tic;
guard=onCleanup(@finish); %#ok<NASGU>
try
 assert(strcmp(char(version),'24.2.0.3361896 (R2024b) Update 10'), ...
  'WK08:Build','Pinned R2024b Update 10 build required.');
  if isD13
   assert(M.stopTime_s==340 && strcmp(getenv('WK08_OWNER_APPROVAL'), ...
    'APPROVE_WK10_D13_REF_K2_T340_A_ONCE_AFTER_CLAUDE_GO'), ...
    'WK10:Approval','D13 requires its separate owner approval after Claude GO.');
   assert(strcmp(M.run,getenv('GITHUB_RUN_ID')) && strcmp(M.commit,getenv('GITHUB_SHA')), ...
    'WK10:Context','Run/commit provenance mismatch.');
   specFile=fullfile(fileparts(mfilename('fullpath')),'WK10_scenario.json');
   assert(strcmp(JTE2026sha256(specFile),M.scenarioSHA256), ...
    'WK10:ScenarioSHA','Scenario bytes differ from manifest.');
   scenario=jsondecode(fileread(specFile));
   assert(isequaln(scenario,M.scenario),'WK10:Scenario','Scenario metadata mismatch.');
  elseif strcmp(M.mode,'R1')
  assert(M.stopTime_s==340 && strcmp(getenv('WK08_OWNER_APPROVAL'), ...
   'APPROVE_WK08_R1_ONCE_AFTER_CLAUDE_GO'), ...
   'WK08:Approval','R1 requires separate owner approval after Claude GO.');
  assert(strcmp(M.run,getenv('GITHUB_RUN_ID')) && ...
   strcmp(M.commit,getenv('GITHUB_SHA')), ...
   'WK08:Context','Run/commit provenance mismatch.');
 elseif isCI5S
  assert(M.stopTime_s==5 && strcmp(getenv('WK08_OWNER_APPROVAL'), ...
   'APPROVE_WK08_CI5S_E_ONCE_AFTER_CLAUDE_GO'), ...
   'WK08:Approval','CI_5S requires separate owner approval after Claude GO.');
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
 if isCI5S,prepareTimer=tic;end
  if isD13
   proof=BTMS_WK08_prepare(source,target,native,M.sourceSHA256,M.stopTime_s,scenario);
  else
   proof=BTMS_WK08_prepare(source,target,native,M.sourceSHA256,M.stopTime_s);
  end
 if isCI5S,flags.prepareWall_s=toc(prepareTimer);end
 m='WK08R1';load_system(target);
 assert(isequaln(proof.fingerprint,BTMS_WK08_structFingerprint(m)), ...
  'WK08:Fingerprint','Saved/reloaded structure differs.');
 loadFile=get_param([m '/Current demand'],'FileName');resolved=which(loadFile);
 pinned=dir(fullfile(M.vendorRoot,'**',loadFile));
 assert(numel(pinned)==1 && ~isempty(resolved) && ...
 strcmp(JTE2026sha256(resolved),JTE2026sha256(fullfile(pinned.folder,pinned.name))), ...
 'WK08:Load','Resolved source current file differs from pinned vendor.');
 proof.loadSHA256=JTE2026sha256(resolved);
  if isD13
   assert(strcmp(proof.loadSHA256,scenario.vendor_mat_sha256) && ...
    strcmp(pin,scenario.model_sha256),'WK10:Load','Scenario vendor provenance mismatch.');
   gain=[m '/WK10 scenario current scale'];gp=get_param(gain,'PortHandles');
   sp=get_param([m '/Current demand'],'PortHandles');dp=get_param([m '/Battery Control'],'PortHandles');
   assert(strcmp(get_param(gain,'BlockType'),'Gain') && ...
    str2double(get_param(gain,'Gain'))==scenario.k && ...
    get_param(get_param(gp.Inport(1),'Line'),'SrcPortHandle')==sp.Outport(1) && ...
    get_param(get_param(dp.Inport(2),'Line'),'SrcPortHandle')==gp.Outport(1), ...
    'WK10:Load','Declared scenario Gain/edge mismatch.');
   proof.scenarioSHA256=M.scenarioSHA256;
  end
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
 if isCI5S,firstStepTimer=tic;end
 final=step(s); % one completed initial major; paused To File readability is probed in CI_5S
 if isCI5S
  flags.firstStepWall_s=toc(firstStepTimer);flags.majorSteps=1;
 end
 assert(~final && strcmp(char(s.Status),'paused'), ...
  'WK08:FirstMajor','Initial completed-major witness unavailable.');
 if isCI5S
  % Probe every file while paused; never reinterpret missing/readability evidence as PASS.
  for k=1:numel(proof.privateTargets)
   [~,file,ext]=fileparts(proof.privateTargets{k});
   row=struct('file',[file ext],'readable',false,'identifier','');
   try
    probe=load(proof.privateTargets{k}); %#ok<NASGU>
    row.readable=true;
   catch pausedError
    row.identifier=pausedError.identifier;
   end
   flags.pausedNativeReadable(end+1)=row; %#ok<AGROW>
  end
  flags.allPausedNativeReadable=all([flags.pausedNativeReadable.readable]);
  writeJSON(fullfile(root,'WK08_FLAGS.json'),flags);
 end
 if isCI5S && ~all([flags.pausedNativeReadable([4 6 5]).readable])
  % The CI check must finish once to assess terminal files even if paused reads fail.
  flags.visibleT0Checked=false;
 else
  first=readNative(proof.privateTargets{4},312,0,false);
  measured=readNative(proof.privateTargets{6},1,0,false);
  trueMax=readNative(proof.privateTargets{5},1,0,false);
  assert(first.time(1)==0 && measured.time(1)==0 && trueMax.time(1)==0 && ...
  trueMax.data(1)==max(first.data(1,:)) && ...
  measured.data(1)==trueMax.data(1), ...
  'WK08:T0Values','Neutral true/measured t0 witness mismatch.');
  flags.visibleT0Checked=true;
 end
 flags.t0Protocol='DIRECT_START; HIDDEN_SIMSCAPE_IC_NOT_CERTIFIED';
 flags.stage='TRAJECTORY';
 if isCI5S,trajectoryTimer=tic;end
 while ~final
  assert(toc(wall)<1200,'WK08:Wall','One trajectory wall ceiling reached.');
  final=step(s);
  if isCI5S,flags.majorSteps=flags.majorSteps+1;end
 end
 if isCI5S,flags.trajectoryWall_s=toc(trajectoryTimer);end
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
 if isCI5S
  flags.status='CI_5S_GATES_PASS_NOT_R1';
  if ~flags.allPausedNativeReadable,flags.status='UNQUALIFIED';end
 end
 flags.stage='DONE';flags.terminalStatus=terminalStatus;
 flags.nativeFinite=true;flags.nativeEndpointsChecked=true;
 flags.runtimeWall_s=toc(wall);flags.derivativeSHA256=proof.derivativeSHA256;
 flags.structuralFingerprintChecked=true;
  if isD13
   % Diagnostic only: failures in this derived export never change native PASS gates.
   try
    summary=derivedSummary(proof.privateTargets);
    writeJSON(fullfile(root,'SUMMARY.json'),summary);
    flags.summaryStatus='DERIVED_NOT_EVIDENCE';
   catch summaryError
    flags.summaryStatus='NOT VERIFIED';
    try
     writeJSON(fullfile(root,'SUMMARY.json'),struct('label','DERIVED_NOT_EVIDENCE', ...
      'status','NOT VERIFIED','identifier',summaryError.identifier, ...
      'SOC_limit_intervention','NOT VERIFIED'));
    catch
     % No fallback computation outside MATLAB and no effect on run qualification.
    end
   end
  end
catch err
 if isCI5S
  if exist('prepareTimer','var') && isnan(flags.prepareWall_s)
   flags.prepareWall_s=toc(prepareTimer);
  end
  if exist('firstStepTimer','var') && isnan(flags.firstStepWall_s)
   flags.firstStepWall_s=toc(firstStepTimer);
  end
  if exist('trajectoryTimer','var') && isnan(flags.trajectoryWall_s)
   flags.trajectoryWall_s=toc(trajectoryTimer);
  end
 end
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
function d=derivedSummary(files)
% Logged sample statistics only; no interpolated crossing, suitability or PASS test.
t=readNative(files{5},1,340,true);u=readNative(files{2},1,340,true);
p=readNative(files{7},1,340,true);
[peak,ix]=max(t.data(:,1));levels=[.25 .5 .75];counts=zeros(1,3);
for k=1:3,counts(k)=nnz(u.data(:,1)==levels(k));end
first305=NaN;ix305=find(t.data(:,1)>=305,1);
if ~isempty(ix305),first305=t.time(ix305);end
first3075=NaN;ix3075=find(t.data(:,1)>=307.5,1);
if ~isempty(ix3075),first3075=t.time(ix3075);end
% jsonencode converts NaN to JSON null: never-crossed thresholds are not failures.
d=struct('label','DERIVED_NOT_EVIDENCE','diagnosticOnly',true, ...
 'Tmax_peak_K',peak,'Tmax_peak_time_s',t.time(ix), ...
 'first_logged_Tmax_ge_305_K_s',first305,'first_logged_Tmax_ge_307_5_K_s',first3075, ...
 'uSampled_levels',levels,'uSampled_counts',counts, ...
 'uSampled_level_switches',nnz(diff(u.data(:,1))~=0), ...
 'pump_energy_J',trapz(p.time,p.data(:,1)),'N_samples',numel(u.time), ...
 'sampleCounts',struct('TmaxTrue',numel(t.time),'uSampled',numel(u.time),'pumpPower',numel(p.time)), ...
 'SOC_limit_intervention','NOT VERIFIED', ...
 'SOC_limit_observability','Existing eight logs contain no demanded/applied current or SOC witness.');
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
