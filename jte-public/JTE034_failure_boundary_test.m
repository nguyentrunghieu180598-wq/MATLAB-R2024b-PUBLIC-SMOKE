function JTE034_failure_boundary_test()
% Controlled missing-project fixture; no pack simulation, no study data.
old=pwd; work=tempname; mkdir(work); cd(work);
guard=onCleanup(@()restore(old,work));
failed=false;
try
 ci_jte030_logging();
catch ME
 failed=strcmp(ME.identifier,'JTE030:PrivateDiagnosticFailure');
end
assert(failed,'JTE034:FalseGreen','Diagnostic must throw sanitized failure.');
assert(isfile(fullfile(work,'private-jte030','diagnostic_failure.mat')));
fprintf('JTE034 FAILURE BOUNDARY PASS: missing-project fixture only.\n');
end
function restore(old,work)
cd(old);rmdir(work,'s');
end
