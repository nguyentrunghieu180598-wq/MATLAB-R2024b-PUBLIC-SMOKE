function p=BTMS_WK09_prepare(source,target,privateDir,sourceSHA,definitionFile)
% Static source builder; no compile, initialization or simulation here.
D=jsondecode(fileread(definitionFile));code=fileparts(mfilename('fullpath'));
isProbe=any(strcmp(D.id,{'P150','P175'}));
registry='WK09_runs.json';if isProbe,registry='WK10_D14_probe.json';end
R=jsondecode(fileread(fullfile(code,registry)));
row=R.runs(strcmp({R.runs.id},D.id));assert(isscalar(row),'WK09:Run','Unknown case.');
spec='WK10_scenario.json';digest=R.scenario_sha256;
if isProbe,spec=row.scenario_file;digest=row.scenario_sha256;end
S=jsondecode(fileread(fullfile(code,spec)));
A=jsondecode(fileread(fullfile(code,R.selector_file)));
assert(strcmp(JTE2026sha256(fullfile(code,R.selector_file)),R.selector_sha256) && ...
 strcmp(JTE2026sha256(fullfile(code,spec)),digest), ...
 'WK09:Digest','Selector/scenario bytes changed.');
assert(D.start_s==0 && D.stop_s==340 && D.k==S.k && S.T==340 && ...
 (isProbe || (D.k==2 && S.k==2)),'WK09:Scenario','Only the declared scenario is allowed.');
fields=fieldnames(row);
for k=1:numel(fields)
 assert(isequaln(D.(fields{k}),row.(fields{k})),'WK09:Definition','Case differs from registry.');
end
assert(strcmp(D.selector_sha256,R.selector_sha256) && ...
 strcmp(D.scenario_sha256,digest) && ...
 strcmp(D.predictions_sha256,R.predictions_sha256) && ...
 strcmp(D.baseline_receipt_sha256,R.baseline.receipt_sha256) && ...
 strcmp(D.subset_sha256,JTE2026sha256(fullfile(code,'WK08_sparse_sets.csv'))), ...
 'WK09:Provenance','Definition digest mismatch.');
subset=BTMS_WK08_sparseSets(D.sensors);order=A.ranking_descending(:)';
switch D.channel_rule
 case 'top_three',J=sort(order(1:3));
 case 'rank_156',J=order(156);
 case {'rank_1','hottest_in_subset'},J=order(find(ismember(order,subset),1));
 case 'first_sensed',J=subset(1);
 otherwise,error('WK09:Selection','Unknown channel rule.');
end
assert(isequal(D.subset(:)',subset) && isequal(D.bias_channels(:)',J), ...
 'WK09:Selection','Channels must come from the frozen selector/subset.');
% Exactly the same reviewed Gain construction as R2, then only declared deltas.
p=BTMS_WK08_prepare(source,target,privateDir,sourceSHA,340,S);
[~,m]=fileparts(target);load_system(target);c=onCleanup(@()close_system(m,0)); %#ok<NASGU>
bc=[m '/Battery Control'];act=[bc '/Amended sampled actuator'];hold=[bc '/Amended command sample hold'];
archivedActuator=actuatorParameters(act,hold);archivedTolerances=toleranceParameters(m);
assert(str2double(archivedActuator.SampleTime)==.01 && ...
 str2double(archivedActuator.holdSampleTime)==.01 && ...
 str2double(archivedTolerances.RelTol)==1e-3 && str2double(archivedTolerances.AbsTol)==1e-3, ...
 'WK09:Archive','Expected unchanged archived parameters.');
p.injection=BTMS_WK08_inject(m,D.bias_K,J,subset,strcmp(D.measurement_pipeline,'active'));
assert(p.injection.identityBypass==strcmp(D.measurement_pipeline,'identity_bypass'), ...
 'WK09:Pipeline','C0/sparse cases must use the active chart.');
if strcmp(D.id,'R3')
 assert(D.Ts_s==.005,'WK09:Ts','Only R3 uses 5ms.');a=exp(-D.Ts_s/.001);
 set_param(act,'A',mat2str(a,17),'B',mat2str(1-a,17),'SampleTime',mat2str(D.Ts_s,17));
 set_param(hold,'SampleTime',mat2str(D.Ts_s,17));
else
 assert(D.Ts_s==.01 && isequaln(archivedActuator,actuatorParameters(act,hold)), ...
  'WK09:Actuator','Non-R3 A/B/sample-time strings must not change.');
end
if strcmp(D.id,'R4')
 assert(strcmp(D.RelTol,'1e-4') && strcmp(D.AbsTol,'1e-4'),'WK09:Tol','Only declared R4 tolerances.');
 set_param(m,'RelTol',D.RelTol,'AbsTol',D.AbsTol);
else
 assert(strcmp(D.RelTol,'1e-3') && strcmp(D.AbsTol,'1e-3') && ...
  isequaln(archivedTolerances,toleranceParameters(m)),'WK09:Tol','Non-R4 tolerance strings changed.');
end
assert(strcmp(get_param(m,'Solver'),'ode23t') && str2double(get_param(m,'MaxStep'))==.05 && ...
 str2double(get_param(m,'StopTime'))==340,'WK09:Solver','Frozen solver/horizon changed.');
for k=1:numel(p.roles)
 file=fullfile(privateDir,['WK09_' D.id '_' p.roles{k} '.mat']);
 assert(~isfile(file),'WK09:Overwrite','Fresh native targets required.');
 set_param(p.fourLoggerPaths{k},'FileName',file);p.privateTargets{k}=file;
end
finalActuator=actuatorParameters(act,hold);finalTolerances=toleranceParameters(m);
if ~strcmp(D.id,'R3'),assert(isequaln(finalActuator,archivedActuator),'WK09:Actuator','Actuator changed.');end
if ~strcmp(D.id,'R4'),assert(isequaln(finalTolerances,archivedTolerances),'WK09:Tol','Tolerances changed.');end
p.parameterAudit=struct('actuatorBefore',archivedActuator,'actuatorAfter',finalActuator, ...
 'tolerancesBefore',archivedTolerances,'tolerancesAfter',finalTolerances);
p.definition=D;p.stopTime_s=340;p.fingerprint=BTMS_WK08_structFingerprint(m);
save_system(m,target);p.derivativeSHA256=JTE2026sha256(target);
close_system(m,0);load_system(target);
assert(isequaln(p.fingerprint,BTMS_WK08_structFingerprint(m)) && ...
 strcmp(JTE2026sha256(source),sourceSHA),'WK09:Fingerprint','Source/reload changed.');
end
function a=actuatorParameters(act,hold)
a=struct('A',get_param(act,'A'),'B',get_param(act,'B'), ...
 'SampleTime',get_param(act,'SampleTime'),'holdSampleTime',get_param(hold,'SampleTime'));
end
function t=toleranceParameters(m)
t=struct('RelTol',get_param(m,'RelTol'),'AbsTol',get_param(m,'AbsTol'));
end
