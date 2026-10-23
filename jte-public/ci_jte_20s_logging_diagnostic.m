function ci_jte_20s_logging_diagnostic()
% Diagnostic only: 20s zero-bias study; print timestamps/samples, NO NUMERIC VALUES.
rootDir=pwd;addpath(fullfile(rootDir,'jte-public'));
p=openProject(fullfile(rootDir,'vendor-pack','batteryExamplesProjectSetup.prj'));
pg=onCleanup(@()quietClose(p)); %#ok<NASGU>
models=JTE2026build(fullfile(rootDir,'vendor-pack'), ...
 fullfile(rootDir,'logging-test-generated'));
mdl='JTE2026LocalBias';
load_system(models.study);
mg=onCleanup(@()quietCloseModel(mdl)); %#ok<NASGU>
s=Simulink.SimulationInput(mdl);
s=s.setVariable('jteChannelIndex',1,'Workspace',mdl);
s=s.setVariable('jteBiasK',0,'Workspace',mdl);
s=s.setModelParameter('StartTime','0','StopTime','20','SaveTime','on','TimeSaveName','tout');
out=sim(s);
names={'jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient','jteTmaxMeas','jteTminMeas'};
for k=1:numel(names)
 [t,x]=JTE2026timeseries(out,names{k});
 full=(numel(t)>1 && abs(t(1))<=1e-6 && abs(t(end)-20)<=1e-6);
 fprintf('LOG_SCOPE %s samples=%d first_s=%g last_s=%g channels=%d full=%d\n', ...
  names{k},numel(t),t(1),t(end),size(x,2),full);
end
fprintf('LOGGING_DIAGNOSTIC_COMPLETE_20S; NO_STUDY_DATA_PRINTED\n');
end
function quietClose(p)
try,close(p);catch,end
end
function quietCloseModel(m)
if bdIsLoaded(m),close_system(m,0);end
end
