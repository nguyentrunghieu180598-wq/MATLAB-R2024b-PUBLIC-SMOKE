function matlab_r2024b_smoke()
% PUBLIC, NON-RESEARCH MATLAB/Simulink smoke test for R2024b.
% No battery model, confidential data, external accounts, or credentials.
% Purpose: GitHub public runner availability and installed product checks.
reportDir = fullfile(pwd, 'reports');
if ~isfolder(reportDir), mkdir(reportDir); end
logFile = fullfile(reportDir, 'matlab_smoke.log');
diary(logFile);
diary on;
logGuard = onCleanup(@() diary('off')); %#ok<NASGU>

fprintf('JTE CI public smoke start: %s\n', char(datetime('now')));
fprintf('MATLAB full version: %s\n', version);
fprintf('MATLAB release: %s\n', version('-release'));
assert(strcmpi(version('-release'), '2024b'), 'Wrong MATLAB release');

installed = ver;
required = {'MATLAB', 'Simulink', 'Simscape', ...
    'Simscape Electrical', 'Simscape Battery', 'Stateflow'};
installedNames = {installed.Name};
fprintf('\nInstalled products:\n');
for k = 1:numel(installed)
    fprintf('  %s | %s\n', installed(k).Name, installed(k).Version);
end
for k = 1:numel(required)
    assert(any(strcmpi(installedNames, required{k})), ...
        'Missing product: %s', required{k});
end

% Loading the Simscape libraries verifies their Simulink integration is present.
% It is NOT a compile or thermal simulation of the JTE pack.
load_system('simulink');
load_system('fl_lib');
load_system('ee_lib');
fprintf('Simulink, Simscape Foundation and Electrical library load: PASS\n');

model = 'jte_public_ci_smoke';
if bdIsLoaded(model), close_system(model, 0); end
new_system(model);
modelGuard = onCleanup(@() closeLoadedModel(model)); %#ok<NASGU>
add_block('simulink/Sources/Constant', [model '/Input'], ...
    'Value', '3', 'Position', [50 75 100 105]);
add_block('simulink/Math Operations/Gain', [model '/Gain'], ...
    'Gain', '2', 'Position', [165 75 225 105]);
add_block('simulink/Sinks/To Workspace', [model '/Log'], ...
    'VariableName', 'smoke_y', 'SaveFormat', 'Timeseries', ...
    'Position', [290 75 385 105]);
add_line(model, 'Input/1', 'Gain/1');
add_line(model, 'Gain/1', 'Log/1');
set_param(model, 'Solver', 'ode45', 'StopTime', '2');
set_param(model, 'SaveTime', 'on', 'TimeSaveName', 'tout');
set_param(model, 'SimulationCommand', 'update');
fprintf('Minimal Simulink diagram update/compile: PASS\n');

out = sim(model, 'StopTime', '2', 'ReturnWorkspaceOutputs', 'on');
y = out.get('smoke_y');
assert(isa(y, 'timeseries'), 'Expected timeseries output');
assert(~isempty(y.Data) && all(isfinite(y.Data(:))), 'Bad output');
assert(abs(double(y.Data(end)) - 6) < 1e-9, 'Wrong gain test result');
tSim = out.get('tout');
assert(isnumeric(tSim) && ~isempty(tSim) && ...
    abs(double(tSim(end)) - 2) < 1e-6, ...
    'Simulator end time not 2 s');
fprintf('Logged Constant signal last timestamp: %g s (event-based sample, not run end)\n', double(y.Time(end)));
fprintf('Minimal Simulink simulation: PASS (value 6 at 2 s)\n');

save_system(model, fullfile(reportDir, [model '.slx']));
fprintf('\nPUBLIC SMOKE PASS. JTE original pack and full Simscape thermal dynamics NOT TESTED.\n');
end

function closeLoadedModel(name)
if bdIsLoaded(name)
    close_system(name, 0);
end
end
