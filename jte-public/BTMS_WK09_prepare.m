function p=BTMS_WK09_prepare(source,target,privateDir,sourceSHA,definitionFile)
% Static derivative builder only: no compile, initialize, step or simulation.
% definitionFile is the resolved offline WK09 contract, not run authorization.
D=jsondecode(fileread(definitionFile));
assert(D.enabled==false && D.stop_s==2400 && D.start_s==0, ...
 'WK09:Definition','Source-only 0..2400 contract required.');
assert(strcmp(D.resolution,'SOURCE_CONTRACT_ONLY_NOT_RUN_AUTHORIZATION'), ...
 'WK09:Unresolved','No fallback for missing frozen R2 selector.');
assert(any(strcmp(D.id,{'R2','R3','R4','R5','R6','R7','R8','R9','R10','R11','R12','R13'})), ...
 'WK09:RunID','Only registered R2..R13 definitions.');
assert(any(D.Ts_s==[.01 .005]) && D.tau_s==.001 && ...
 strcmp(D.solver,'ode23t') && D.MaxStep_s==.05,'WK09:Method','Unexpected method.');
% Reuse all reviewed M2 archive/actuator/IC protections and eight logging roles.
p=BTMS_WK08_prepare(source,target,privateDir,sourceSHA,340);
[~,m]=fileparts(target);load_system(target);
c=onCleanup(@()close_system(m,0)); %#ok<NASGU>
bc=[m '/Battery Control'];act=[bc '/Amended sampled actuator'];
hold=[bc '/Amended command sample hold'];
% WK08's receipt-pinned copy still has the archived actuator and tolerance strings.
archivedActuator=actuatorParameters(act,hold);
archivedTolerances=toleranceParameters(m);
assert(str2double(archivedActuator.SampleTime)==.01 && ...
 str2double(archivedActuator.holdSampleTime)==.01, ...
 'WK09:ArchivedSampleTime','Expected archived 10ms source.');
assert(str2double(archivedTolerances.RelTol)==1e-3 && ...
 str2double(archivedTolerances.AbsTol)==1e-3, ...
 'WK09:ArchivedTolerance','Expected archived 1e-3 source tolerances.');
assert(isequal(D.subset(:)',BTMS_WK08_sparseSets(D.sensors)), ...
 'WK09:Subset','Fixed CSV map required.');
active=strcmp(D.measurement_pipeline,'active');
p.injection=BTMS_WK08_inject(m,D.bias_K,D.channel,D.subset(:)',active);
if strcmp(D.id,'R3')
 assert(D.Ts_s==.005,'WK09:SampleTime','Only R3 uses 5ms.');
 a=exp(-D.Ts_s/.001);
 set_param(act,'A',mat2str(a,17),'B',mat2str(1-a,17),'SampleTime',mat2str(D.Ts_s,17));
 set_param(hold,'SampleTime',mat2str(D.Ts_s,17));
else
 assert(D.Ts_s==.01,'WK09:SampleTime','Only R3 may change sample time.');
 currentActuator=actuatorParameters(act,hold);
 assert(isequaln(currentActuator,archivedActuator), ...
  'WK09:ActuatorUnchanged','Retain exact archived A/B/sample-time strings.');
end
% C,D and InitialCondition remain the archived amended source values.
if strcmp(D.id,'R4')
 assert(strcmp(D.RelTol,'1e-4') && strcmp(D.AbsTol,'1e-4'), ...
  'WK09:Tolerance','R4 requires its predeclared tolerances.');
 set_param(m,'RelTol',D.RelTol,'AbsTol',D.AbsTol);
else
 assert(strcmp(D.RelTol,'1e-3') && strcmp(D.AbsTol,'1e-3'), ...
  'WK09:Tolerance','Only R4 may change tolerances.');
 currentTolerances=toleranceParameters(m);
 assert(isequaln(currentTolerances,archivedTolerances), ...
  'WK09:TolerancesUnchanged','Retain exact archived tolerance strings.');
end
set_param(m,'StopTime','2400');
for k=1:numel(p.roles)
 file=fullfile(privateDir,['WK09_' D.id '_' p.roles{k} '.mat']);
 assert(~isfile(file),'WK09:Overwrite','Never overwrite a prior run.');
 set_param(p.fourLoggerPaths{k},'Filename',file);
 p.privateTargets{k}=file;
end
finalActuator=actuatorParameters(act,hold);
finalTolerances=toleranceParameters(m);
if ~strcmp(D.id,'R3')
 assert(isequaln(finalActuator,archivedActuator), ...
  'WK09:ActuatorUnchanged','Non-R3 actuator strings changed.');
end
if ~strcmp(D.id,'R4')
 assert(isequaln(finalTolerances,archivedTolerances), ...
  'WK09:TolerancesUnchanged','Non-R4 tolerance strings changed.');
end
p.parameterAudit=struct('actuatorBefore',archivedActuator, ...
 'actuatorAfter',finalActuator,'tolerancesBefore',archivedTolerances, ...
 'tolerancesAfter',finalTolerances,'actuatorChangeAllowed',strcmp(D.id,'R3'), ...
 'toleranceChangeAllowed',strcmp(D.id,'R4'));
p.definition=D;p.stopTime_s=2400;p.fingerprint=BTMS_WK08_structFingerprint(m);
save_system(m,target);p.derivativeSHA256=JTE2026sha256(target);
close_system(m,0);load_system(target);
assert(isequaln(p.fingerprint,BTMS_WK08_structFingerprint(m)), ...
 'WK09:Fingerprint','Saved structure changed.');
assert(strcmp(JTE2026sha256(source),sourceSHA),'WK09:Source','Source changed.');
end
function a=actuatorParameters(act,hold)
a=struct('A',get_param(act,'A'),'B',get_param(act,'B'), ...
 'SampleTime',get_param(act,'SampleTime'),'holdSampleTime',get_param(hold,'SampleTime'));
end
function t=toleranceParameters(m)
t=struct('RelTol',get_param(m,'RelTol'),'AbsTol',get_param(m,'AbsTol'));
end
