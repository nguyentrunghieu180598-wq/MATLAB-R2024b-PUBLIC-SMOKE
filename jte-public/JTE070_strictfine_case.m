function JTE070_strictfine_case(caseName)
% JTE065 G5 scientific DATA ACQUISITION ONLY. Not acceptance or publication.
% Four independent R2024b 2400s cases, preserving full native channels.
% MAT stays on private GitHub-hosted scratch until owner-private Drive upload.
caseName=char(caseName); solverProfile='fine';
assert(ismember(caseName,{'B0L','C0'}),'JTE065:BadCase');
assert(ismember(solverProfile,{'original','fine'}),'JTE065:BadProfile');
assert(strcmp(version('-release'),'2024b'),'JTE065:WrongMATLAB');
root=pwd;
% Independent frozen strict profile from reviewed JTE058 staging: 1e-4/1e-4/0.025.
vendor=fullfile(root,'vendor-pack');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cleanupProject=onCleanup(@()safeCloseProject(project)); %#ok<NASGU>
generated=fullfile(root,['jte070-generated-' caseName '-strictfine']);
files=JTE056build(vendor,generated);
if strcmp(caseName,'B0L'), target=files.baseline;
else, target=files.study;end
[~,mdl]=fileparts(target);
load_system(target);
cleanupModel=onCleanup(@()safeCloseModel(mdl)); %#ok<NASGU>
assert(isempty(get_param(mdl,'PreLoadFcn'))&&isempty(get_param(mdl,'CloseFcn')),'JTE065:UnsafeModelCallbacks');
for event={'InitFcn','StartFcn','StopFcn','PostLoadFcn'}
 assert(isempty(get_param(mdl,event{1})),'JTE065:UnsafeRuntimeCallback');
end
stop='2400';
simIn=Simulink.SimulationInput(mdl);
if strcmp(caseName,'C0')
 simIn=simIn.setVariable('jteChannelIndex',1,'Workspace',mdl);
 simIn=simIn.setVariable('jteBiasK',0,'Workspace',mdl);
end
simIn=simIn.setModelParameter('StartTime','0','StopTime',stop, ...
    'SaveTime','on','TimeSaveName','tout');
sourceRelTol=str2double(get_param(mdl,'RelTol'));
assert(abs(sourceRelTol-1e-3)<1e-12,'JTE070:OriginalToleranceChanged');
assert(strcmp(get_param(mdl,'Solver'),'ode23t'),'JTE070:SolverAlgorithmChanged');
simIn=simIn.setModelParameter('RelTol','1e-4','AbsTol','1e-4','MaxStep','0.025');
assert(strcmp(get_param(mdl,'SolverType'),'Variable-step'),'JTE065:UnexpectedSolverType');
fprintf('JTE070_STRICT_FINE_START case=%s profile=%s sourceRelTol=%g sourceSHA256=%s\n', ...
    caseName,solverProfile,sourceRelTol,files.sourceSHA256);
clock=tic;
simOut=sim(simIn);
wall_s=toc(clock);
label=[caseName '_' solverProfile];
record=JTE056collect(simOut,mdl,files,label,solverProfile,simIn);
assert(strcmp(record.sourceSHA256,files.sourceSHA256),'JTE065:SourceDrift');
record.elapsedWall_s=wall_s;
record.dataUse='JTE070_STRICT_FINE_G5_RAW_UNREVIEWED_NOT_ACCEPTED';
record.assessment='STRICT_NUMERICAL_CANDIDATE_PENDING_REVIEW';
record.solverProfileDefinition='strict fine predefined: ode23t RelTol 1e-4 AbsTol 1e-4 MaxStep 0.025, vendor physics/IC/load unchanged';
record.profileReferenceRelTol=sourceRelTol;
record.strictFine=true;
assert(strcmp(record.solver.RelTol,'1e-4')&&strcmp(record.solver.AbsTol,'1e-4')&&strcmp(record.solver.MaxStep,'0.025'),'JTE070:OverrideDrift');
assert(record.signalData.jteTtrue.time_s(1)==0,'JTE065:BadStart');
assert(abs(record.signalData.jteTtrue.time_s(end)-2400)<1e-8,'JTE065:BadStop');
assert(all(diff(record.signalData.jteTtrue.time_s)>=0),'JTE065:NonNativeClock');
if strcmp(caseName,'C0')
 assert(isequal(record.signalData.jteTtrue.values,record.signalData.jteTmeas.values),'JTE065:ZeroBiasVector');
end
directory=fullfile(root,'jte070-private');
assert(~isfolder(directory),'JTE065:PrivateDirExists');
mkdir(directory);
mat=fullfile(directory,['JTE070_' caseName '_strictfine_2400_NATIVE.mat']);
save(mat,'record','-v7.3');
s=load(mat,'record');
assert(isequal(s.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE065:LocalReadbackMismatch');
info=dir(mat);
assert(info.bytes>0&&info.bytes<=3*1024^3,'JTE065:MATQuotaGuard');
fprintf('JTE070_STRICT_FINE_RAW_SAVED case=%s profile=%s seconds=%.6f nativeRows=%d channels=%d MATbytes=%d SHA256=%s ACCEPTED=false\n', ...
    caseName,solverProfile,wall_s,numel(record.signalData.jteTtrue.time_s), ...
    size(record.signalData.jteTtrue.values,2),info.bytes,JTE2026sha256(mat));
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')), ...
    files.sourceSHA256),'JTE065:VendorChanged');
end
function safeCloseProject(p)
try,close(p);catch,end
end
function safeCloseModel(m)
try
if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end
catch,end
end
