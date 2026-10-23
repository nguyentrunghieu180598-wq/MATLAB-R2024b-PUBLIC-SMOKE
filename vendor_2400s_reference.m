function vendor_2400s_reference()
% Original public MathWorks model only. NOT JTE B0/C0 or bias results.
repo = fullfile(pwd,'vendor-pack');
prj = fullfile(repo,'batteryExamplesProjectSetup.prj');
slx = fullfile(repo,'Models','Battery_Pack_Thermal_Management.slx');
assert(isfile(prj)&&isfile(slx),'Pinned public MathWorks source missing.');
reportDir = fullfile(pwd,'reports');
if ~isfolder(reportDir), mkdir(reportDir); end
diary(fullfile(reportDir,'vendor-2400s-reference.log'));diary on;
cleanupD = onCleanup(@()diary('off')); %#ok<NASGU>
assert(strcmp(version('-release'),'2024b'),'Wrong MATLAB release.');
p = openProject(prj);
cleanupP = onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
mdl='Battery_Pack_Thermal_Management';
if ~bdIsLoaded(mdl),load_system(slx);end
cleanupM = onCleanup(@()safeCloseModel(mdl)); %#ok<NASGU>
solver = get_param(mdl,'Solver');
relTol = get_param(mdl,'RelTol');
absTol = get_param(mdl,'AbsTol');
fprintf('Original solver %s; RelTol %s; AbsTol %s\n',solver,relTol,absTol);
in=Simulink.SimulationInput(mdl);
in=in.setModelParameter('StartTime','0','StopTime','2400', ...
 'SaveTime','on','TimeSaveName','tout');
tStart=tic;
out=sim(in);
elapsed_s=toc(tStart);
tout=out.get('tout');
assert(isnumeric(tout)&&~isempty(tout),'No solver grid');
assert(abs(double(tout(end))-2400)<1e-6,'Simulation did not reach 2400s');
report=struct('type','OFFICIAL_UNMODIFIED_SOURCE_ONLY', ...
 'horizon_s',2400,'elapsed_wall_s',elapsed_s, ...
 'solver',solver,'RelTol',relTol,'AbsTol',absTol, ...
 'sample_count',numel(tout),'matlab',version, ...
 'scope','Runtime feasibility only; not JTE bias experiment');
save(fullfile(reportDir,'vendor_2400s_reference_receipt.mat'),'report');
fprintf('OFFICIAL VENDOR 2400s REFERENCE PASS, elapsed %g s. NOT JTE RESULTS.\n',elapsed_s);
end

function safeCloseModel(name)
if bdIsLoaded(name),close_system(name,0);end
end
function safeCloseProject(p)
try,close(p);catch,end
end
