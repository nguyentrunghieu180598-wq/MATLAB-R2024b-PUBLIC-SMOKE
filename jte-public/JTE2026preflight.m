function info = JTE2026preflight(repoRoot)
% Read-only prerequisites. Does not open project, update diagrams or simulate.
repoRoot=char(repoRoot); assert(isfolder(repoRoot),'Repo folder missing.');
source=fullfile(repoRoot,'Models','Battery_Pack_Thermal_Management.slx');
assert(isfile(source),'Original MathWorks SLX missing: %s',source);
actual=JTE2026sha256(source);
expected='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmpi(actual,expected),'Unpinned model SHA256; STOP, do not build.');
info=struct(); info.date=datestr(now,31); info.matlab=version; info.release=version('-release');
info.originalSHA256=actual; info.repoRoot=repoRoot;
info.source=source; info.installed=ver;
if ~strcmpi(info.release,'2024b')
 warning('Not R2024b: compatibility exploration only, NOT reference equivalence.');
end
required={'Simulink','Simscape','Simscape Electrical'};
for k=1:numel(required)
    p=info.installed; names={p.Name};
    assert(any(strcmpi(names,required{k})),'Missing installed product: %s',required{k});
end
% Installation is NOT proof of checkout or runtime functionality.
projectFiles=dir(fullfile(repoRoot,'*.prj'));
info.projectCandidates={projectFiles.name};
fprintf('STATIC PREFLIGHT PASS: source SHA256 matches; required products installed.\n');
fprintf('MATLAB %s; release %s. License, project load and compile NOT YET PASS.\n', ...
    info.matlab,info.release);
end
