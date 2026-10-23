function result=JTE2026compile(modelFile)
% G2/G3 compile/update selected generated model; no simulation.
assert(isfile(modelFile),'Model file missing.');
[~,model]=fileparts(modelFile);
assert(~bdIsLoaded(model),'Close the model before compile to avoid stale workspace.');
load_system(modelFile);
c=onCleanup(@()close_system(model,0));
set_param(model,'SimulationCommand','update');
result=struct('model',model,'solver',get_param(model,'Solver'), ...
    'stopTime',get_param(model,'StopTime'),'updated',true, ...
    'time',datestr(now,31),'fileSHA256',JTE2026sha256(modelFile));
fprintf('SIMULINK UPDATE PASS: %s, solver=%s (NOT a thermal run).\n', ...
  model,result.solver);
end
