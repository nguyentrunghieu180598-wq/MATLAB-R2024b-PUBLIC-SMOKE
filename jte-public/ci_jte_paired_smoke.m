function ci_jte_paired_smoke()
% Public-reference-only CI: run G4 20s B0L/C0; NEVER upload study data.
% Numerical series and residuals remain in disposable runner filesystem.
runnerRoot=pwd;
addpath(fullfile(runnerRoot,'jte-public'));
assert(strcmpi(version('-release'),'2024b'),'Wrong MATLAB release');
sourceRoot=fullfile(runnerRoot,'vendor-pack');
projectFile=fullfile(sourceRoot,'batteryExamplesProjectSetup.prj');
assert(isfile(projectFile),'MathWorks source project not found');
p=openProject(projectFile);
prjCleanup=onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
files=JTE2026build(sourceRoot,fullfile(runnerRoot,'ephemeral-models'));
JTE2026compile(files.baseline);
JTE2026compile(files.study);
results=fullfile(runnerRoot,'ephemeral-raw-20s');
% Capture any numeric printout; never send experimental traces to public logs.
capturedText=evalc('receipt=JTE2026paired(fileparts(files.baseline),20,results);'); %#ok<NASGU>
assert(receipt.modelRunSuccess,'B0L/C0 simulation did not return normally');
assert(~receipt.G5_PASS,'Numerical G5 cannot auto-PASS without solver review');
assert(numel(receipt.maxAbsResidual)==4 && ...
    all(isfinite(receipt.maxAbsResidual)), 'Residuals invalid');
assert(isfinite(receipt.zeroBiasExtremaResidual_K),'Zero-bias error invalid');
assert(strcmpi(JTE2026sha256(fullfile(sourceRoot,'Models', ...
    'Battery_Pack_Thermal_Management.slx')), ...
    '0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0'), ...
    'Original source changed unexpectedly');
fprintf('G4 PUBLIC-REFERENCE B0L/C0 20s executed on MATLAB R2024b.\n');
fprintf('G5 numeric residual/solver acceptance: PENDING, no experimental data published.\n');
end

function safeCloseProject(p)
try,close(p);catch,end
end
