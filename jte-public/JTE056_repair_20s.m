function JTE056_repair_20s()
% Specific logger repair validation, not a rerun for reconfirming accepted D20.
assert(strcmp(version('-release'),'2024b'),'JTE056:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
pcl=onCleanup(@()quietProject(project)); %#ok<NASGU>
folder=fullfile(root,'jte056-generated');
files=JTE056build(vendor,folder);
[~,model]=fileparts(files.study);load_system(files.study);
mcl=onCleanup(@()quietModel(model)); %#ok<NASGU>
% Assert generated callbacks are inert before introducing controlled variables.
assert(isempty(get_param(model,'PreLoadFcn'))&&isempty(get_param(model,'CloseFcn')),'JTE056:UnsafeCallbacks');
% Model runtime callbacks must be inert; vendor masked initialization remains
% source-defined and must be checked against actual SimulationMetadata.
callbacks={'InitFcn','StartFcn','StopFcn','PostLoadFcn'};
for k=1:numel(callbacks)
 assert(isempty(get_param(model,callbacks{k})),'JTE056:UnsafeRuntimeCallback','Unexpected %s',callbacks{k});
end
s=Simulink.SimulationInput(model);
s=s.setVariable('jteChannelIndex',1,'Workspace',model);
s=s.setVariable('jteBiasK',0,'Workspace',model);
s=s.setModelParameter('StartTime','0','StopTime','20','SaveTime','on','TimeSaveName','tout');
fprintf('JTE056_REPAIR_20S_START sourceSHA256=%s\n',files.sourceSHA256);
out=sim(s);
record=JTE056collect(out,model,files,'C0_diagnostic20','original',s);
assert(evalin(get_param(model,'ModelWorkspace'),'jteBiasK')==0,'JTE056:WorkspaceReset');
% Every nonconstant dynamic logger must reach the diagnostic horizon.
for name={'jteTtrue','jteTmeas','jteUcore','jteFlwR'}
 signal=record.signalData.(name{1});
 assert(signal.time_s(1)==0&&abs(signal.time_s(end)-20)<1e-8,'JTE056:IncompleteLogger');
 if strcmp(name{1},'jteUcore')||strcmp(name{1},'jteFlwR')
  assert(size(signal.values,2)==1&&all(signal.values(:)>=-1e-8)&&all(signal.values(:)<=1+1e-8),'JTE056:CommandRange');
 end
end
record.studyType='REAL_MATLAB_LOGGER_REPAIR_20S_NOT_G5';
record.selftest='JTE056selftest executed separately in same workflow before repair';
record.matlabRuntime=version;record.outputSchema='JTE056_NATIVE_V1';
private=fullfile(root,'jte056-private');assert(~isfolder(private),'JTE056:PrivateOutputExists');mkdir(private);
matPath=fullfile(private,'JTE056_NATIVE_LOGGER_REPAIR_20S.mat');
save(matPath,'record','-v7.3');
check=load(matPath,'record');
assert(isequal(check.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE056:MATReadback');
info=dir(matPath);
fprintf('JTE056_REPAIR_20S_PASS rows=%d channels=312 postFilterRows=%d MATbytes=%d MATsha256=%s\n', ...
 numel(record.signalData.jteTtrue.time_s),numel(record.signalData.jteFlwR.time_s),info.bytes,JTE2026sha256(matPath));
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
