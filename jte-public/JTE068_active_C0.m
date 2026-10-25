function JTE068_active_C0()
% Controlled second operating regime, separate from baseline original G5.
% Change ONLY source-defined ambient reference 300 -> 293.15 K
% (20 degC reference) in derivative model; pin official vendor .slx.
% Purpose: test whether source FlwR quantization is actually excited.
% NO bias, NO assumption of a certain outcome, NOT G5 ACCEPTANCE.
assert(strcmp(version('-release'),'2024b'),'JTE068:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
pc=onCleanup(@()quietProject(p)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte068-generated'));
[~,model]=fileparts(files.study);load_system(files.study);
mc=onCleanup(@()quietModel(model)); %#ok<NASGU>
ambient=[model '/Constant3'];
assert(strcmp(get_param(ambient,'BlockType'),'Constant')&&strcmp(get_param(ambient,'SID'),'199'),'JTE068:WrongAmbientSource');
old=slResolve(get_param(ambient,'Value'),ambient);
validateattributes(old,{'double'},{'scalar','real','finite'});
assert(abs(old-300)<1e-12,'JTE068:WrongOriginalAmbient');
set_param(ambient,'Value','293.15');
mw=get_param(model,'ModelWorkspace');
e=evalin(mw,'jte056AmbientProvenance');
e.expression='293.15';e.valueK=293.15;e.isConstant=true;
assignin(mw,'jte056AmbientProvenance',e);
save_system(model,files.study);
% Reopen/check derivative persisted, keep source SHA unchanged.
assert(strcmp(get_param(ambient,'Value'),'293.15'),'JTE068:EditedAmbientNotPersisted');
s=Simulink.SimulationInput(model);
s=s.setVariable('jteChannelIndex',1,'Workspace',model);
s=s.setVariable('jteBiasK',0,'Workspace',model);
s=s.setModelParameter('StartTime','0','StopTime','2400','SaveTime','on','TimeSaveName','tout');
fprintf('JTE068_ACTIVE_C0_START sourceSHA=%s ambientReferenceK=293.15 NOT_ORIGINAL_G5\n',files.sourceSHA256);
tm=tic;
out=sim(s);elapsed=toc(tm);
record=JTE056collect(out,model,files,'C0_original','original',s);
core=record.signalData.jteUcore.values;
record.dataUse='JTE068_ACTIVE_REFERENCE_C0_RAW_UNREVIEWED';
record.experimentalCondition='Controller/reference ambient parameter changed from source 300 K to 293.15 K (20 deg C) in isolated generated derivative; all other physics/load/IC/solver original; NOT an EV-specific ambient validation.';
record.activationHypothesis='Source FlwR_calc threshold near Tmax minus ambient = 5 K; originally max was lower, now check control response without forcing conclusions.';
record.hasNonfloorCommand=any(core>0.25+1e-12);
record.numRecordedCoreLevels=numel(unique(core));
record.elapsedWall_s=elapsed;
record.reviewStatus='SCIENTIFIC_REVIEW_REQUIRED';
dirp=fullfile(root,'jte068-private');
assert(~isfolder(dirp),'JTE068:ExistingPath');mkdir(dirp);
mat=fullfile(dirp,'JTE068_ACTIVE_C0_AMBIENT293p15_2400_NATIVE.mat');
save(mat,'record','-v7.3');
loadCheck=load(mat,'record');
assert(isequal(loadCheck.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE068:Readback');
info=dir(mat);
assert(info.bytes>0,'JTE068:MissingMAT');
fprintf('JTE068_ACTIVE_C0_RAW_SAVED SHA256=%s MATbytes=%d activationReviewed=false\n',...
 JTE2026sha256(mat),info.bytes);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),files.sourceSHA256),'JTE068:VendorSHAChanged');
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(name)
try
 if bdIsLoaded(name),set_param(name,'CloseFcn','');close_system(name,0);end
catch,end
end
