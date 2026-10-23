function vendor_r2024b_preflight()
% Public upstream MathWorks package validation only; no JTE study data.
root = fullfile(pwd, 'vendor-pack');
logFolder = fullfile(pwd, 'reports');
if ~isfolder(logFolder), mkdir(logFolder); end
diary(fullfile(logFolder, 'vendor-preflight.log')); diary on;
cleanupDiary = onCleanup(@()diary('off')); %#ok<NASGU>
fprintf('Official upstream preflight started: %s\n', datestr(now,31));
fprintf('MATLAB: %s release %s\n', version, version('-release'));
assert(strcmpi(version('-release'), '2024b'), 'Incorrect release');
prj = fullfile(root, 'batteryExamplesProjectSetup.prj');
slx = fullfile(root, 'Models', 'Battery_Pack_Thermal_Management.slx');
assert(isfile(prj) && isfile(slx), 'MathWorks original project/model not found');
originalInfo = dir(slx);
assert(originalInfo.bytes > 0, 'Empty source model');
% Open the official source project in disposable CI workspace.
p = openProject(prj);
cleanupProject = onCleanup(@()closeProjectIfOpen(p)); %#ok<NASGU>
model = 'Battery_Pack_Thermal_Management';
if ~bdIsLoaded(model), load_system(slx); end
cleanupModel = onCleanup(@()closeSystemIfLoaded(model)); %#ok<NASGU>
ctrl = [model '/Battery Control'];
reducer = [ctrl '/min-max T']; controller = [ctrl '/FlwR_calc'];
assert(getSimulinkBlockHandle(reducer)>0 && ...
    getSimulinkBlockHandle(controller)>0, 'Pinned blocks missing');
r = get_param(reducer, 'PortHandles'); f = get_param(controller, 'PortHandles');
assert(numel(r.Outport)==2 && numel(f.Inport)==2, 'Unexpected ports');
lineOne = get_param(f.Inport(1), 'Line');
lineTwo = get_param(f.Inport(2), 'Line');
assert(lineOne~=-1 && lineTwo~=-1, 'Controller input disconnected');
assert(get_param(lineOne, 'SrcPortHandle')==r.Outport(2), ...
 'Expected Tmax in FlwR_calc Inport 1');
assert(get_param(lineTwo,'SrcPortHandle')~=-1, ...
 'Expected Ambient source on Inport 2');
fprintf('Pinned original controller wiring: structural PASS\n');
set_param(model, 'SimulationCommand','update');
fprintf('Original Simulink update/compile: PASS\n');
infoAfter = dir(slx);
assert(isfile(slx) && infoAfter.bytes==originalInfo.bytes, ...
 'Original file length changed unexpectedly');
report = struct('release',version('-release'), ...
 'model',model,'compiled',true, 'tag','24.2.1.5', ...
 'note','Vendor source only, no thermal simulation, no JTE study');
save(fullfile(logFolder,'vendor-preflight-receipt.mat'),'report');
fprintf('UPSTREAM PREFLIGHT PASS. Thermal simulation and JTE B0/C0 NOT RUN.\n');
end

function closeSystemIfLoaded(model)
if bdIsLoaded(model), close_system(model,0); end
end

function closeProjectIfOpen(p)
try, close(p); catch, end
end
