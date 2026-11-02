function BTMS_WK08_dryRun5s(manifestFile)
% OWNER MATLAB ONLY. This function executes ONE 5s pack run; never called by CI.
% Owner supplies a fresh private manifest with the same pinned assets as R1.
m=jsondecode(fileread(manifestFile));
assert(m.stopTime_s==5 && strcmp(m.mode,'OWNER_LOCAL_5S'), ...
 'WK08:DryScope','Explicit owner-local 5s manifest required.');
assert(isfield(m,'ownerApproval') && ...
 strcmp(m.ownerApproval,'APPROVE_WK08_LOCAL_5S_ONCE'), ...
 'WK08:DryApproval','Owner must authorize this separate local run.');
BTMS_WK08_run(manifestFile);
end
