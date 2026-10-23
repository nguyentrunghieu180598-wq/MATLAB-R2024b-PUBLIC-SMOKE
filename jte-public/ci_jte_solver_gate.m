function ci_jte_solver_gate()
% Full-horizon B0L/C0 R2024b CI: user-cleared source; NO DATA PUBLICATION.
% Executes solver sensitivity. Numeric evidence stays on ephemeral runner.
runnerRoot=pwd;
addpath(fullfile(runnerRoot,'jte-public'));
assert(strcmpi(version('-release'),'2024b'),'MATLAB release mismatch');
sourceRoot=fullfile(runnerRoot,'vendor-pack');
p=openProject(fullfile(sourceRoot,'batteryExamplesProjectSetup.prj'));
projectCleanup=onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
models=JTE2026build(sourceRoot,fullfile(runnerRoot,'ephemeral-models'));
JTE2026compile(models.baseline);
JTE2026compile(models.study);
folder=fileparts(models.baseline);
coarse=fullfile(runnerRoot,'ephemeral-g5-coarse');
fine=fullfile(runnerRoot,'ephemeral-g5-fine');
% Suppress all study metrics in public logs; data is not uploaded.
unused1=evalc('r1=JTE2026paired(folder,2400,coarse);'); %#ok<NASGU>
assert(r1.modelRunSuccess && ~r1.G5_PASS,'Coarse model run incomplete');
unused2=evalc('r2=JTE2026paired(folder,2400,fine,struct(''RelTol'',''5e-4'',''AbsTol'',''5e-4''));'); %#ok<NASGU>
assert(r2.modelRunSuccess && ~r2.G5_PASS,'Fine model run incomplete');
unused3=evalc('e=JTE2026solverEvidence(coarse,fine,fullfile(runnerRoot,''ephemeral-solver-evidence.mat''));'); %#ok<NASGU>
assert(isfinite(e.maxTempSolverDeltaK) && ...
       isfinite(e.maxCommandSolverDelta) && ...
       isfinite(e.maxAmbientSolverDeltaK), ...
       'Numerical sensitivity evidence invalid');
assert(strcmp(e.status,'REAL_RUNS_COMPARED_REVIEW_REQUIRED'), ...
       'Solver evidence status mismatch');
original=fullfile(sourceRoot,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmpi(JTE2026sha256(original), ...
 '0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0'), ...
 'Original MathWorks SLX changed');
fprintf('FULL 2400s paired B0L/C0 coarse/fine SIMULATIONS EXECUTED.\n');
fprintf('Numerical solver comparison COMPUTED. G5 REVIEW REQUIRED, NOT PASS.\n');
fprintf('No JTE data, MAT, CSV, bias results or scientific metrics published.\n');
end

function safeCloseProject(p)
try,close(p);catch,end
end
