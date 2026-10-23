function ci_jte_case_diagnostic(caseName,horizon)
% Independent simulation to isolate runtime/resource problems.
% Only public MathWorks input; numerical results protected by encryption.
runnerRoot=pwd;
addpath(fullfile(runnerRoot,'jte-public'));
validateattributes(horizon,{'double'},{'scalar','positive','finite'});
caseName=char(caseName);
assert(any(strcmp(caseName,{'B0L','C0'})),'Unknown scenario');
assert(strcmpi(version('-release'),'2024b'),'Wrong MATLAB release');
sourceRoot=fullfile(runnerRoot,'vendor-pack');
p=openProject(fullfile(sourceRoot,'batteryExamplesProjectSetup.prj'));
pGuard=onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
models=JTE2026build(sourceRoot,fullfile(runnerRoot,'ephemeral-models'));
if strcmp(caseName,'B0L')
    mdl='JTE2026B0L';
    file=models.baseline;
else
    mdl='JTE2026LocalBias';
    file=models.study;
end
load_system(file);
mGuard=onCleanup(@()safeCloseModel(mdl)); %#ok<NASGU>
s=Simulink.SimulationInput(mdl);
if strcmp(caseName,'C0')
    s=s.setVariable('jteChannelIndex',1,'Workspace',mdl);
    s=s.setVariable('jteBiasK',0,'Workspace',mdl);
end
s=s.setModelParameter('StartTime','0','StopTime',num2str(horizon,17), ...
    'SaveTime','on','TimeSaveName','tout');
fprintf('CASE_DIAGNOSTIC_SIM_START %s %.0fs release=R2024b solver=%s\n',caseName,horizon,get_param(mdl,'Solver'));
start=tic;
out=sim(s);
wallSec=toc(start);
t=out.get('tout');
assert(isnumeric(t)&&~isempty(t) && abs(double(t(end))-horizon)<1e-6, ...
    'Simulation did not reach requested time');
fprintf('CASE_DIAGNOSTIC_SIM_FINISH %s horizon=%.0fs wall=%.3fs samples=%d\n', ...
    caseName,horizon,wallSec,numel(t));
folder=fullfile(runnerRoot,['private-diagnostics-' caseName]);
if ~isfolder(folder),mkdir(folder);end
receipt=struct('caseName',caseName,'horizon_s',horizon,'wall_s',wallSec, ...
    'samples',numel(t),'sourceSHA256',models.sourceSHA256, ...
    'modelSHA256',JTE2026sha256(file),'solver',get_param(mdl,'Solver'), ...
    'status','SINGLE_MODEL_RUNTIME_ONLY_NOT_B0C0_EQUIVALENCE');
save(fullfile(folder,'single_case_raw.mat'),'out','receipt','-v7.3');
fid=fopen(fullfile(folder,'runtime_receipt.json'),'w');assert(fid>0);
fprintf(fid,'%s',jsonencode(receipt));fclose(fid);
fprintf('CASE_DIAGNOSTIC_SAVE_COMPLETE %s\n',caseName);
end

function safeCloseModel(mdl)
if bdIsLoaded(mdl),close_system(mdl,0);end
end
function safeCloseProject(p)
try,close(p);catch,end
end
