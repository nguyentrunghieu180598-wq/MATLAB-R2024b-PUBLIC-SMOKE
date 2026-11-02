function WK08_run(root,vendor,horizon)
% Exactly one direct-start simulation. No retry and no operating-point restore.
assert(any(horizon==[5 340]),'WK08:Horizon','Invalid horizon.');
assert(strcmp(version,'24.2.0.3361896 (R2024b) Update 10'), ...
 'WK08:Build','Exact R2024b U10 build required.');
M=jsondecode(fileread(fullfile(root,'m2340_manifest.json')));
for k=1:numel(M.inputs)
 a=M.inputs(k);assert(strcmp(JTE2026sha256(fullfile(root,a.local)),a.sha256), ...
  'WK08:InputSHA','Private source changed.');
end
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
original=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmp(JTE2026sha256(original),pin),'WK08:VendorSHA','Vendor mismatch.');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cleanup=onCleanup(@()close(project)); %#ok<NASGU>
W=load(fullfile(root,'source_workspace.mat'),'workspaceSnapshot');names=fieldnames(W.workspaceSnapshot);
for k=1:numel(names),assignin('base',names{k},W.workspaceSnapshot.(names{k}));end
source=fullfile(root,'M2340Source.slx');target=fullfile(root,'WK08R1.slx');
p=WK08_prepare(source,target,M.privateDir,M.sourceModel.sha256,horizon);
load_system(target);
ambientBlock='WK08R1/Constant3';
assert(slResolve(get_param(ambientBlock,'Value'),ambientBlock)==300,'WK08:Ambient','Ambient changed.');
loadFile=get_param('WK08R1/Current demand','FileName');resolved=which(loadFile);
pinned=dir(fullfile(vendor,'**',loadFile));
assert(numel(pinned)==1 && ~isempty(resolved) && ...
 strcmp(JTE2026sha256(resolved),JTE2026sha256(fullfile(pinned.folder,pinned.name))), ...
 'WK08:Load','Current demand differs from pinned vendor.');
finish=onCleanup(@()close_system('WK08R1',0)); %#ok<NASGU>
assert(strcmp(JTE2026sha256(target),p.derivativeSHA256) && ...
 isequaln(p.fingerprint,WK08_structFingerprint('WK08R1')), ...
 'WK08:PreRunFingerprint','Derivative drift before simulation.');
% Save proof before execution so a failed attempt still has provenance.
save(fullfile(root,'WK08_PREPARE_PROOF.mat'),'p','-v7.3');
t=tic;sim('WK08R1');elapsed=toc(t); % sole plant execution, no catch/retry
assert(isequaln(p.fingerprint,WK08_structFingerprint('WK08R1')), ...
 'WK08:PostRunFingerprint','Derivative structure changed.');
r=struct('status','UNQUALIFIED','horizon_s',horizon,'elapsedWall_s',elapsed, ...
 'sourceSHA256',p.sourceSHA256,'derivativeSHA256',p.derivativeSHA256, ...
 'version',version,'G5Accepted',false,'run',getenv('GITHUB_RUN_ID'),'commit',getenv('GITHUB_SHA'));
for k=1:numel(p.roles)
 role=p.roles{k};z=load(fullfile(M.privateDir,['WK08_R1_' role '.mat']));
 ts=z.(['wk08_' role]);assert(isa(ts,'timeseries'),'WK08:Format','Expected timeseries.');
 x=ts.Data;time=ts.Time;
 assert(~isempty(time)&&all(isfinite(time))&&all(isfinite(x(:)))&&time(1)==0&& ...
 time(end)==horizon&&all(diff(time)>=0),'WK08:Output','Nonfinite/incomplete output.');
 if any(strcmp(role,{'uCore','uSampled'}))
  assert(all(ismember(x(:),[.25 .5 .75])),'WK08:Levels','Invalid command level.');
 end
 if strcmp(role,'Ttrue312')
  assert(numel(x)==numel(time)*312 && isequal(time(:),(0:horizon)'), ...
   'WK08:TemperatureClock','Expected 312 channels on exact 1s clock.');
 end
end
assert(strcmp(JTE2026sha256(original),pin)&&strcmp(JTE2026sha256(source),M.sourceModel.sha256), ...
 'WK08:Immutable','Input bytes changed.');
r.status='R1_GATES_PASS_PENDING_PRIVATE_READBACK_AND_CLAUDE_REVIEW';
if horizon==5,r.status='LOCAL_5S_DIAGNOSTIC_ONLY';end
f=fopen(fullfile(root,'WK08_FLAGS.json'),'w');assert(f>=0);fprintf(f,'%s',jsonencode(r));fclose(f);
end
