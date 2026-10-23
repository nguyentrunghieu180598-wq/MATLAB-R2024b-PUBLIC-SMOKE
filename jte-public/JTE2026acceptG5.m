function receipt=JTE2026acceptG5(folder,tolTempK,tolCmd,solverEvidenceFile,reviewer,justification)
% Explicit acceptance AFTER numeric B0/C0 check AND independent solver evidence.
% NOT an automatic PASS and NOT a default arbitrary tolerance.
validateattributes(tolTempK,{'double'},{'scalar','real','finite','positive'});
validateattributes(tolCmd,{'double'},{'scalar','real','finite','positive'});
assert(isfile(solverEvidenceFile),'Missing solver sensitivity evidence file.');
[~,~,ext]=fileparts(char(solverEvidenceFile));
assert(strcmpi(ext,'.mat'),'Evidence must be a MATLAB .mat from JTE2026solverEvidence.');
content=load(solverEvidenceFile,'evidence');
assert(isfield(content,'evidence'),'Missing structured solver evidence.');
ev=content.evidence;
need={'B0L_sha','C0_sha','horizon_s','configCoarse','configFine', ...
 'comparisons','maxTempSolverDeltaK','maxCommandSolverDelta', ...
 'maxAmbientSolverDeltaK','status'};
for k=1:numel(need)
 assert(isfield(ev,need{k}),'Missing solver evidence field: %s',need{k});
end
assert(strcmp(ev.status,'REAL_RUNS_COMPARED_REVIEW_REQUIRED'), ...
 'Evidence is not derived from paired MATLAB runs.');
assert(strlength(string(reviewer))>=3,'Reviewer name is required');
assert(strlength(string(justification))>=40,'Document a meaningful tolerance/solver rationale.');
p=fullfile(folder,'JTE2026B0C0receipt.mat');assert(isfile(p),'Paired receipt missing');
s=load(p,'receipt');receipt=s.receipt;
assert(isfield(receipt,'modelRunSuccess') && receipt.modelRunSuccess, ...
    'Paired model runs have no valid success evidence.');
assert(isfield(receipt,'maxAbsResidual') && numel(receipt.maxAbsResidual)==4, ...
    'Missing residual array');
assert(max(receipt.maxAbsResidual(1:2))<=tolTempK, ...
    'Temperature residual beyond approved threshold');
assert(receipt.zeroBiasExtremaResidual_K<=tolTempK, ...
    'Zero-bias extremum residual beyond threshold');
assert(receipt.maxAbsResidual(3)<=tolCmd, ...
    'Control residual beyond approved threshold');
assert(receipt.maxAbsResidual(4)<=tolTempK, ...
    'Ambient residual beyond approved threshold');
assert(strcmp(ev.B0L_sha,receipt.B0L_sha) && ...
    strcmp(ev.C0_sha,receipt.C0_sha) && ev.horizon_s==receipt.horizon_s, ...
    'Solver evidence not tied to this baseline/study/horizon.');
assert(ev.maxTempSolverDeltaK<=tolTempK && ...
       ev.maxCommandSolverDelta<=tolCmd && ...
       ev.maxAmbientSolverDeltaK<=tolTempK, ...
    'Solver variations exceed reviewed thresholds.');
assert(isfield(receipt,'alignment') && numel(receipt.alignment)==4, ...
    'Missing explicit B0/C0 time alignment diagnostics.');
receipt.G5_PASS=true;
receipt.reviewer=char(reviewer);receipt.reviewedAt=datestr(now,31);
receipt.tolerance_T_K=tolTempK;receipt.tolerance_u=tolCmd;
receipt.evidenceSolverPath=char(solverEvidenceFile);
receipt.evidenceSolverSHA256=JTE2026sha256(solverEvidenceFile);
receipt.reason=char(justification);
save(p,'receipt');
fprintf('Recorded G5 PASS with review and external solver evidence.\n');
end
