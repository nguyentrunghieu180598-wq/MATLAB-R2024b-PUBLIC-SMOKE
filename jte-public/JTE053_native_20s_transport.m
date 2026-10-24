function JTE053_native_20s_transport()
% Real R2024b diagnostic, NOT the G5 2400 s study.
% Save all diagnostic numbers privately; public CI logs print provenance/counts only.
repoRoot=pwd;
addpath(fullfile(repoRoot,'jte-public'));
assert(strcmp(version('-release'),'2024b'),'JTE053:WrongMatlabVersion');
vendor=fullfile(repoRoot,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
projectCleanup=onCleanup(@()quietCloseProject(p)); %#ok<NASGU>
models=JTE2026build(vendor,fullfile(repoRoot,'jte053-generated'));
[~,model]=fileparts(models.study);
load_system(models.study);
modelCleanup=onCleanup(@()quietCloseModel(model)); %#ok<NASGU>
s=Simulink.SimulationInput(model);
s=s.setVariable('jteChannelIndex',1,'Workspace',model);
s=s.setVariable('jteBiasK',0,'Workspace',model);
s=s.setModelParameter('StartTime','0','StopTime','20', ...
                      'SaveTime','on','TimeSaveName','tout');
fprintf('JTE053_REAL_20S_START source_SHA256=%s\n',models.sourceSHA256);
out=sim(s);
time=double(out.get('tout'));
assert(numel(time)>1 && abs(time(1))<1e-8 && abs(time(end)-20)<1e-6, ...
    'JTE053:SimulationHorizonNotComplete');
names={'jteTtrue','jteTmeas','jteTmaxTrue','jteTmaxMeas', ...
       'jteTminTrue','jteTminMeas','jteUcore','jteAmbient'};
pilot=struct();
pilot.studyType='REAL_MATLAB_20S_DIAGNOSTIC_NOT_G5';
pilot.caseName='C0_zero_bias';
pilot.horizon_s=20;
pilot.modelVersion=version;
pilot.sourceSHA256=models.sourceSHA256;
pilot.generatedModelSHA256=JTE2026sha256(models.study);
pilot.signalData=struct();
for k=1:numel(names)
   name=names{k};
   [t,x]=JTE2026timeseries(out,name);
   assert(all(isfinite(t)) && all(isfinite(x(:))), ...
       'JTE053:NonFiniteSignal');
   pilot.signalData.(name)=struct('time_s',t,'values',x);
   fprintf('JTE053_SIGNAL name=%s samples=%d channels=%d\n', ...
       name,numel(t),size(x,2));
   if strcmp(name,'jteTtrue') || strcmp(name,'jteTmeas')
       assert(size(x,2)==312, 'JTE053:Not312Channels');
       assert(abs(t(1))<1e-8 && abs(t(end)-20)<1e-6, ...
           'JTE053:NotFullSensorHorizon');
   end
end
tt=pilot.signalData.jteTtrue;tm=pilot.signalData.jteTmeas;
assert(isequal(tt.time_s,tm.time_s), ...
    'JTE053:TrueMeasuredTimeMismatch');
assert(isequal(tt.values,tm.values), ...
    'JTE053:ZeroBiasVectorMismatch');
maxtrue=pilot.signalData.jteTmaxTrue;
maxmeas=pilot.signalData.jteTmaxMeas;
assert(isequal(maxtrue.time_s,maxmeas.time_s), ...
    'JTE053:MaxTimeMismatch');
assert(isequal(maxtrue.values,maxmeas.values), ...
    'JTE053:ZeroBiasMaxMismatch');
folder=fullfile(repoRoot,'jte053-private');
if ~isfolder(folder), mkdir(folder); end
save(fullfile(folder,'JTE053_AUTHENTICATED_20S_DATA.mat'),'pilot','-v7.3');
fprintf('JTE053_REAL_20S_DATA_SAVED_ENCRYPT_BEFORE_UPLOAD\n');
end
function quietCloseProject(p)
try,close(p);catch,end
end
function quietCloseModel(name)
try,if bdIsLoaded(name),close_system(name,0);end;catch,end
end
