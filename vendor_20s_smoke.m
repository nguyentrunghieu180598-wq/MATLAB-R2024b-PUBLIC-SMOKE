function vendor_20s_smoke()
% Disposable cloud ONLY. Official public MathWorks R2024b model, 20s smoke.
% NO researcher input profiles, NO study bias, NO paper results.
root = fullfile(pwd,'vendor-pack');
prj = fullfile(root,'batteryExamplesProjectSetup.prj');
slx = fullfile(root,'Models','Battery_Pack_Thermal_Management.slx');
assert(isfile(prj) && isfile(slx),'Missing pinned official source');
reportDir = fullfile(pwd,'reports');
if ~isfolder(reportDir), mkdir(reportDir); end
diary(fullfile(reportDir,'vendor-20s-smoke.log')); diary on;
cleanDiary = onCleanup(@()diary('off')); %#ok<NASGU>
assert(strcmp(version('-release'),'2024b'),'MATLAB release changed');
p = openProject(prj);
cleanProject = onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
model = 'Battery_Pack_Thermal_Management';
if ~bdIsLoaded(model), load_system(slx); end
cleanModel = onCleanup(@()safeCloseModel(model)); %#ok<NASGU>
s = Simulink.SimulationInput(model);
s = s.setModelParameter('StartTime','0', 'StopTime','20', ...
  'SaveTime','on', 'TimeSaveName','tout');
% Smoke only; must never be called validated thermal response.
out = sim(s);
try, tout = out.get('tout'); catch, tout=[]; end
assert(isnumeric(tout) && ~isempty(tout), 'Missing solver time grid');
assert(abs(double(tout(end))-20)<1e-6,'Simulation ended before 20 s');
report = struct('type','VENDOR_UPSTREAM_SMOKE_ONLY', ...
 'simulationStart_s',double(tout(1)), ...
 'simulationEnd_s',double(tout(end)), ...
 'samples',numel(tout),'version',version,'release',version('-release'));
save(fullfile(reportDir,'vendor_20s_smoke_receipt.mat'),'report');
fprintf('VENDOR 20s SMOKE PASS. No JTE experiment or paper results.\n');
end

function safeCloseModel(model)
if bdIsLoaded(model), close_system(model,0); end
end
function safeCloseProject(p)
try,close(p);catch,end
end
