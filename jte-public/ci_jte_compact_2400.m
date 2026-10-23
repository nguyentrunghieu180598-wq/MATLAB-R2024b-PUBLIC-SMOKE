function ci_jte_compact_2400(caseName,solverProfile)
% FOUR INDEPENDENT REAL R2024b SIMULATIONS, ENCRYPT ALL DATA.
% Never use these as a completed G5 gate without reviewer comparison.
runnerRoot=pwd;
addpath(fullfile(runnerRoot,'jte-public'));
caseName=char(caseName); solverProfile=char(solverProfile);
assert(any(strcmp(caseName,{'B0L','C0'})),'Invalid case');
assert(any(strcmp(solverProfile,{'original','fine'})),'Invalid solver profile');
assert(strcmpi(version('-release'),'2024b'),'Wrong MATLAB version');
sourceRoot=fullfile(runnerRoot,'vendor-pack');
p=openProject(fullfile(sourceRoot,'batteryExamplesProjectSetup.prj'));
prjGuard=onCleanup(@()closeProjectQuietly(p)); %#ok<NASGU>
models=JTE2026build(sourceRoot,fullfile(runnerRoot,'generated-ephemeral'));
if strcmp(caseName,'B0L'), modelFile=models.baseline;
else, modelFile=models.study; end
[~,model]=fileparts(modelFile);
load_system(modelFile);
modelGuard=onCleanup(@()closeModelQuietly(model)); %#ok<NASGU>
s=Simulink.SimulationInput(model);
s=s.setModelParameter('StartTime','0','StopTime','2400', ...
   'SaveTime','on','TimeSaveName','tout');
if strcmp(caseName,'C0')
    s=s.setVariable('jteChannelIndex',1,'Workspace',model);
    s=s.setVariable('jteBiasK',0,'Workspace',model);
end
if strcmp(solverProfile,'fine')
    s=s.setModelParameter('RelTol','5e-4','AbsTol','5e-4');
end
profile=struct('Solver',get_param(model,'Solver'), ...
    'OriginalRelTol',get_param(model,'RelTol'), ...
    'OriginalAbsTol',get_param(model,'AbsTol'), ...
    'StudyRelTol',get_param(model,'RelTol'), ...
    'StudyAbsTol',get_param(model,'AbsTol'), ...
    'MaxStep',get_param(model,'MaxStep'));
if strcmp(solverProfile,'fine')
    profile.StudyRelTol='5e-4'; profile.StudyAbsTol='5e-4';
end
fprintf('JTE_2400_COMPACT_START %s %s\n',caseName,solverProfile);
timer=tic;
out=sim(s);
elapsed=toc(timer);
solverTime=out.get('tout');
assert(isnumeric(solverTime)&&numel(solverTime)>1&&...
    abs(double(solverTime(end))-2400)<1e-6,...
    'Solver did not complete full 2400s');
fprintf('JTE_2400_COMPACT_SIM_COMPLETE case=%s solver=%s elapsed=%.3f s points=%d\n',...
  caseName,solverProfile,elapsed,numel(solverTime));
horizon=2400;
grid=(0:1:horizon)';
names={'jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient'};
if strcmp(caseName,'C0')
    names=[names,{'jteTmaxMeas','jteTminMeas'}];
end
record=struct();
diagnostic=struct();
for k=1:numel(names)
  name=names{k};
  [t,x]=JTE2026timeseries(out,name);
  assert(all(isfinite(t))&&all(isfinite(x(:))),'Signal nonfinite');
  full=(numel(t)>1 && abs(t(1))<=1e-6 ...
         && abs(t(end)-horizon)<=1e-6);
  data=struct();
  data.name=name;data.timeCount=numel(t);
  data.signalChannels=size(x,2);
  data.start_s=t(1);data.end_s=t(end);data.fullHorizon=full;
  data.maxStep_s=NaN;
  if numel(t)>1,data.maxStep_s=max(diff(t));end
  if full
      val=interp1(t,x,grid,'linear');
      assert(all(isfinite(val(:))),'Interpolation failed');
      record.(name)=val;
  else
      record.(name)=struct('time_s',t,'originalValues',x, ...
          'warning','INCOMPLETE_LOGGED_HORIZON_NO_EXTRAPOLATION');
  end
  diagnostic.(name)=data;
end
result=struct('case',caseName,'solverProfile',solverProfile,...
    'matlabVersion',version,'horizon_s',horizon, ...
    'elapsedWall_s',elapsed,'solverPoints',numel(solverTime),...
    'sourceSHA256',models.sourceSHA256,...
    'modelSHA256',JTE2026sha256(modelFile),...
    'solver',profile,'grid_s',grid,'signals',record,...
    'loggingDiagnostics',diagnostic,'numericGateG5','PENDING_REVIEW');
directory=fullfile(runnerRoot,'private-compact-results');
if ~isfolder(directory),mkdir(directory);end
save(fullfile(directory,['real_' caseName '_' solverProfile '_2400.mat']), ...
   'result','-v7.3');
fid=fopen(fullfile(directory,'non_secret_provenance.json'),'w');
assert(fid>0);guard=onCleanup(@()fclose(fid)); %#ok<NASGU>
meta=rmfield(result,{'grid_s','signals','loggingDiagnostics'});
fprintf(fid,'%s',jsonencode(meta));
fprintf('JTE_2400_COMPACT_SAVED_ENCRYPT_NEXT G5_NOT_YET_ACCEPTED\n');
end
function closeProjectQuietly(p)
try,close(p);catch,end
end
function closeModelQuietly(name)
if bdIsLoaded(name),close_system(name,0);end
end
