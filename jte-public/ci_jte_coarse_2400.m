function ci_jte_coarse_2400()
% Reproducible G5 phase A: full horizon, original solver settings.
% Private raw numeric results are handled ONLY by encrypted artifact step.
runnerRoot=pwd;
addpath(fullfile(runnerRoot,'jte-public'));
assert(strcmpi(version('-release'),'2024b'),'MATLAB R2024b is required');
sourceRoot=fullfile(runnerRoot,'vendor-pack');
p=openProject(fullfile(sourceRoot,'batteryExamplesProjectSetup.prj'));
closeGuard=onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
models=JTE2026build(sourceRoot,fullfile(runnerRoot,'ephemeral-models'));
JTE2026compile(models.baseline);
JTE2026compile(models.study);
dataDir=fullfile(runnerRoot,'private-g5-coarse');
fprintf('JTE G5 COARSE PHASE BEGIN: B0L/C0 2400 s, reference ode23t tolerances.\n');
% IMPORTANT: capture numeric study output in memory; public stdout stays clean.
capture=evalc('receipt=JTE2026paired(fileparts(models.baseline),2400,dataDir);'); %#ok<NASGU>
assert(receipt.modelRunSuccess && ~receipt.G5_PASS, ...
  'Coarse paired run incomplete or inappropriately accepted');
assert(all(isfinite(receipt.maxAbsResidual)) && ...
  isfinite(receipt.zeroBiasExtremaResidual_K), 'Invalid numeric metrics');
json=fullfile(dataDir,'JTE2026B0C0receipt.json');
fid=fopen(json,'w');assert(fid>=0);
fprintf(fid,'%s',jsonencode(receipt));fclose(fid);
fprintf('JTE G5 COARSE PHASE EXECUTED, raw data will be encrypted.\n');
fprintf('G5 remains PENDING scientific tolerances, full-horizon fine solver check.\n');
end
function safeCloseProject(p)
try,close(p);catch,end
end
