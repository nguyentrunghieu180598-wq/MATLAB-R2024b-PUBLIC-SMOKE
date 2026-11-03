function BTMS_WK09_run(manifestFile)
% Exactly one fresh direct-start trajectory. Warnings remain warnings.
M=jsondecode(fileread(manifestFile));root=char(M.privateRoot);D=M.definition;
flags=struct('run',M.run,'commit',M.commit,'case',D.id,'group',M.group, ...
 'status','UNQUALIFIED','physicalRun',false,'G5Accepted',false,'hiddenSimscapeICCertified',false);
s=[];project=[];m='';failure=[];wall=tic;guard=onCleanup(@finish); %#ok<NASGU>
try
 assert(strcmp(char(version),'24.2.0.3361896 (R2024b) Update 10'),'WK09:Build','Pinned build required.');
 code=fileparts(mfilename('fullpath'));R=jsondecode(fileread(fullfile(code,'WK09_runs.json')));
 G=R.groups.(M.group);
 assert(strcmp(getenv('WK09_OWNER_APPROVAL'),G.approval) && ...
  strcmp(getenv('WK09_GROUP'),M.group) && strcmp(getenv('WK09_CASE'),D.id) && ...
  any(strcmp(G.runs,D.id)) && strcmp(M.run,getenv('GITHUB_RUN_ID')) && ...
  strcmp(M.commit,getenv('GITHUB_SHA')),'WK09:Approval','Sealed group/run binding required.');
 assert(strcmp(JTE2026sha256(fullfile(code,'WK09_runs.json')),M.registrySHA256) && ...
  strcmp(JTE2026sha256(M.definitionFile),M.definitionSHA256),'WK09:Definition','Definition changed.');
 assert(strcmp(JTE2026sha256(M.vendorSLX),M.scenario.model_sha256), 'WK09:Vendor','Vendor changed.');
 for k=1:numel(M.inputs)
  a=M.inputs(k);assert(strcmp(JTE2026sha256(fullfile(root,a.local)),a.sha256),'WK09:Input','Input changed.');
 end
 project=openProject(fullfile(M.vendorRoot,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(root,'source_workspace.mat'),'workspaceSnapshot');names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),assignin('base',names{k},W.workspaceSnapshot.(names{k}));end
 assert(evalin('base','ambient')==300,'WK09:Ambient','Ambient changed.');
 source=fullfile(root,'M2340Source.slx');m=['WK09_' D.id];target=fullfile(root,[m '.slx']);
 native=fullfile(root,'native');assert(~isfolder(native),'WK09:Fresh','Fresh output directory required.');mkdir(native);
 proof=BTMS_WK09_prepare(source,target,native,M.sourceSHA256,M.definitionFile);load_system(target);
 assert(isequaln(proof.fingerprint,BTMS_WK08_structFingerprint(m)),'WK09:Fingerprint','Reload mismatch.');
 loadFile=get_param([m '/Current demand'],'FileName');resolved=which(loadFile);
 pinned=dir(fullfile(M.vendorRoot,'**',loadFile));
 assert(numel(pinned)==1 && ~isempty(resolved) && ...
  strcmp(JTE2026sha256(resolved),M.scenario.vendor_mat_sha256) && ...
  strcmp(JTE2026sha256(fullfile(pinned.folder,pinned.name)),M.scenario.vendor_mat_sha256), ...
  'WK09:Load','Frozen vendor MAT differs.');
 save(fullfile(root,'WK09_PREPARED_PROOF.mat'),'proof','M','-v7.3');
 for k=1:8,assert(~isfile(proof.privateTargets{k}),'WK09:Overwrite','Native target exists.');end
 flags.physicalRun=true;flags.stage='INITIALIZE_ONCE';writeJSON(fullfile(root,'WK09_FLAGS.json'),flags);
 s=simulation(m);initialize(s);
 assert(str2double(get_param(m,'StopTime'))==340 && strcmp(get_param(m,'Solver'),'ode23t') && ...
  str2double(get_param(m,'MaxStep'))==.05 && s.Time==0,'WK09:Config','Effective configuration mismatch.');
 final=step(s);assert(~final && strcmp(char(s.Status),'paused'),'WK09:FirstMajor','Initial major witness required.');
 t0=readNative(proof.privateTargets{4},312,0,false);
 q0=readNative(proof.privateTargets{6},1,0,false);x0=readNative(proof.privateTargets{5},1,0,false);
 expected=t0.data(1,:);expected(D.bias_channels)=expected(D.bias_channels)+D.bias_K;
 assert(t0.time(1)==0 && q0.time(1)==0 && x0.time(1)==0 && ...
  x0.data(1)==max(t0.data(1,:)) && q0.data(1)==max(expected(D.subset)), ...
  'WK09:T0','Declared true/measured initial witness mismatch.');
 flags.visibleT0Checked=true;flags.stage='TRAJECTORY';
 while ~final
  assert(toc(wall)<1200,'WK09:Wall','Internal process wall ceiling reached.');final=step(s);
 end
 terminalStatus=char(s.Status);
 assert(any(strcmp(terminalStatus,{'paused','inactive'})),'WK09:Terminal','Unexpected terminal status.');
 if strcmp(terminalStatus,'paused'),out=stop(s);else,out=s.SimulationOutput;end;s=[];
 meta=out.SimulationMetadata;info=meta.ExecutionInfo;
 assert(any(strcmp(char(info.StopEvent),{'ReachedStopTime','StopCommand'})) && ...
  isempty(out.ErrorMessage) && strcmp(char(meta.ModelInfo.SimulationMode),'normal'), ...
  'WK09:StopEvent','Unqualified stop event.');
 for k=1:8
  width=1;if any(k==[4 8]),width=312;end
  x=readNative(proof.privateTargets{k},width,340,true);
  if k==1 || k==2
   assert(all(ismember(x.data(:),[.25 .5 .75])),'WK09:Command','Command outside declared levels.');
  elseif k==8
   assert(isequal(x.time,(0:340)'),'WK09:Observer','One-second observer clock differs.');
  end
 end
 % Case-specific measurement invariant; no neutral equality gate is discarded.
 truth=readNative(proof.privateTargets{4},312,340,true);
 tx=readNative(proof.privateTargets{5},1,340,true);tm=readNative(proof.privateTargets{6},1,340,true);
 v=truth.data;v(:,D.bias_channels)=v(:,D.bias_channels)+D.bias_K;
 assert(isequaln(truth.time,tx.time) && isequaln(tx.time,tm.time) && ...
  isequaln(tx.data,max(truth.data,[],2)) && isequaln(tm.data,max(v(:,D.subset),[],2)), ...
  'WK09:Measurement','Native logged measurement differs from declared injection.');
 assert(isequaln(proof.fingerprint,BTMS_WK08_structFingerprint(m)) && ...
  strcmp(JTE2026sha256(target),proof.derivativeSHA256) && ...
  strcmp(JTE2026sha256(source),M.sourceSHA256) && ...
  strcmp(JTE2026sha256(M.vendorSLX),M.scenario.model_sha256), 'WK09:Immutable','Source/derivative changed.');
 flags.status='NATIVE_GATES_PASS_PENDING_PRIVATE_READBACK';flags.stage='DONE';
 flags.nativeFinite=true;flags.nativeEndpointsChecked=true;flags.structuralFingerprintChecked=true;
 flags.derivativeSHA256=proof.derivativeSHA256;flags.runtimeWall_s=toc(wall);
 try
  writeJSON(fullfile(root,'SUMMARY.json'),derivedSummary(proof.privateTargets));
 catch
  flags.summaryStatus='NOT VERIFIED'; % Never a native PASS criterion.
 end
catch err
 failure=err;flags.identifier=err.identifier;flags.reason=err.message;
end
writeJSON(fullfile(root,'WK09_FLAGS.json'),flags);
if ~isempty(failure),error('WK09:Unqualified','Private diagnostics saved; no retry.');end
 function finish()
  if ~isempty(s),try,if ~strcmp(char(s.Status),'inactive'),stop(s);end,catch,end,end
  if ~isempty(m),try,close_system(m,0);catch,end,end
  if ~isempty(project),try,close(project);catch,end,end
 end
end
function d=derivedSummary(files)
t=readNative(files{5},1,340,true);u=readNative(files{2},1,340,true);p=readNative(files{7},1,340,true);
[peak,ix]=max(t.data(:,1));a=NaN;b=NaN;
j=find(t.data(:,1)>=305,1);if ~isempty(j),a=t.time(j);end
j=find(t.data(:,1)>=307.5,1);if ~isempty(j),b=t.time(j);end
levels=[.25 .5 .75];counts=arrayfun(@(x)nnz(u.data(:,1)==x),levels);
d=struct('label','DERIVED_NOT_EVIDENCE','Tmax_peak_K',peak,'Tmax_peak_time_s',t.time(ix), ...
 'first_logged_Tmax_ge_305_K_s',a,'first_logged_Tmax_ge_307_5_K_s',b, ...
 'uSampled_levels',levels,'uSampled_counts',counts,'uSampled_level_switches',nnz(diff(u.data(:,1))~=0), ...
 'pump_energy_J',trapz(p.time,p.data(:,1)),'N_samples',numel(u.time),'SOC_limit_intervention','NOT VERIFIED');
end
function x=readNative(file,width,stopTime,complete)
assert(isfile(file),'WK09:NativeMissing','Native file missing.');a=load(file);keys=fieldnames(a);
assert(numel(keys)==1 && isa(a.(keys{1}),'timeseries'),'WK09:NativeSchema','Timeseries required.');
t=a.(keys{1});x.time=t.Time(:);d=t.Data;
if ~t.IsTimeFirst,d=permute(d,[ndims(d) 1:ndims(d)-1]);end
x.data=reshape(d,numel(x.time),[]);
assert(~isempty(x.time) && size(x.data,2)==width && all(isfinite(x.time)) && ...
 all(isfinite(x.data(:))) && x.time(1)==0 && all(diff(x.time)>=0),'WK09:NativeFinite','Native data invalid.');
if complete,assert(x.time(end)==stopTime && all(x.time<=stopTime),'WK09:Endpoint','Incomplete horizon.');end
end
function writeJSON(file,x)
f=fopen(file,'w');assert(f>=0,'WK09:Write','Private file unavailable.');c=onCleanup(@()fclose(f)); %#ok<NASGU>
fprintf(f,'%s',jsonencode(x));
end
