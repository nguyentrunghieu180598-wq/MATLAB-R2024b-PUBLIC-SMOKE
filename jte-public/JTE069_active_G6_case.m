function JTE069_active_G6_case(position)
% JTE069: active-controller-reference 293.15 K sensitivity; independent from original JTE067 G6.
% Site hot/middle/cold is deterministically selected from the *C0 zero bias*
% time-weighted cell temperature mean (not G6 outcome); tie by cell index.
% Do not confuse a null controller effect with a numerical failure.
position=char(position);
assert(any(strcmp(position,{'hot','middle','cold'})),'JTE067:InvalidSite');
assert(strcmp(version('-release'),'2024b'),'JTE067:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
pg=onCleanup(@()quietProject(p)); %#ok<NASGU>
models=JTE056build(vendor,fullfile(root,['jte069-generated-' position]));
[~,model]=fileparts(models.study);
load_system(models.study);cg=onCleanup(@()quietModel(model)); %#ok<NASGU>
% CHANGE ONLY controller ambient REFERENCE Constant3 SID 199 in generated
% derivative. This is NOT a physical ambient boundary-condition experiment.
ambient=[model '/Constant3'];
assert(strcmp(get_param(ambient,'SID'),'199') && strcmp(get_param(ambient,'BlockType'),'Constant'),'JTE069:AmbientBlock');
old=slResolve(get_param(ambient,'Value'),ambient);
assert(isscalar(old)&&abs(old-300)<1e-12,'JTE069:OriginalReferenceChanged');
set_param(ambient,'Value','293.15');
mw=get_param(model,'ModelWorkspace');
a=evalin(mw,'jte056AmbientProvenance');
a.valueK=293.15;a.expression='293.15';
assignin(mw,'jte056AmbientProvenance',a);
save_system(model,models.study);
assert(strcmp(get_param(ambient,'Value'),'293.15'),'JTE069:ReferenceNotPersisted');
assert(isempty(get_param(model,'PreLoadFcn'))&&isempty(get_param(model,'CloseFcn')),'JTE067:Callback');
for event={'InitFcn','StartFcn','StopFcn','PostLoadFcn'}
 assert(isempty(get_param(model,event{1})),'JTE067:RuntimeCallback');
end
base=Simulink.SimulationInput(model);
base=base.setVariable('jteChannelIndex',1,'Workspace',model);
base=base.setVariable('jteBiasK',0,'Workspace',model);
base=base.setModelParameter('StartTime','0','StopTime','2400', ...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE069_ACTIVE_C0_REFERENCE_START sourceSHA256=%s referenceK=293.15 profile=original NOT_ORIGINAL_G6\n',models.sourceSHA256);
o0=sim(base);
[t,T]=JTE2026timeseries(o0,'jteTtrue');
assert(size(T,2)==312&&t(1)==0&&abs(t(end)-2400)<1e-8,'JTE067:Reference');
assert(all(diff(t)>=0)&&all(isfinite(T(:))),'JTE069:ReferenceNative');
[~,u0]=JTE2026timeseries(o0,'jteUcore');
assert(any(u0(:)>0.25+1e-12),'JTE069:InactiveControllerReference');
% T is N x 312, duplicate timestamps are preserved with zero integration width.
timeMean=trapz(t,T,1)/2400;
assert(numel(timeMean)==312&&all(isfinite(timeMean)),'JTE067:ReferenceMeans');
rank=sortrows([timeMean(:),(1:312)'],[1 2]);
switch position
 case 'hot',j=rank(end,2);
 case 'middle',j=rank(156,2);
 case 'cold',j=rank(1,2);
end
% First verify exact single-channel injection on a short real 20s model run.
probe=Simulink.SimulationInput(model);
probe=probe.setVariable('jteChannelIndex',j,'Workspace',model);
probe=probe.setVariable('jteBiasK',-2,'Workspace',model);
probe=probe.setModelParameter('StartTime','0','StopTime','20','SaveTime','on','TimeSaveName','tout');
short=sim(probe);
[tr,v]=JTE2026timeseries(short,'jteTtrue');
[tm,m]=JTE2026timeseries(short,'jteTmeas');
assert(isequal(tr,tm)&&size(v,2)==312,'JTE067:ProbeAlignment');
other=setdiff(1:312,j);
assert(all(m(:,other)==v(:,other),'all'),'JTE067:ProbeOtherChannels');
assert(all(abs(m(:,j)-v(:,j)+2)<1e-9),'JTE067:ProbeMinus2');
fprintf('JTE069_SINGLE_CHANNEL_20S_PROBE_PASS site=%s confidential_index_not_logged=true\\n',position);
clear short tr v tm m probe
% Retain metadata privately; no confidential cell index or thermal values in stdout.
clear o0 T
b=Simulink.SimulationInput(model);
b=b.setVariable('jteChannelIndex',j,'Workspace',model);
b=b.setVariable('jteBiasK',-2,'Workspace',model);
b=b.setModelParameter('StartTime','0','StopTime','2400', ...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE069_ACTIVE_C1_RUN_START site=%s biasK=-2 profile=original\n',position);
ticG6=tic;
out=sim(b);
elapsed=toc(ticG6);
record=JTE067collect(out,model,models,['C1_' position '_original'],'original',b);
assert(record.injection.channel_1based==j && record.injection.biasK==-2,'JTE067:SelectedChannelDrift');
record.selectionBasis='JTE069 active C0 293.15 K controller reference, original solver, entire 0-2400s time-weighted mean across 312 cells; tie smaller 1-based index first; selected before C1';
record.selectedRankLabel=position;
record.referenceC0SourceSHA256=models.sourceSHA256;
record.referenceC0LoadSHA256=record.load.SHA256;
record.elapsedWall_s=elapsed;
record.dataUse='JTE069_ACTIVE_CONTROLLER_REFERENCE_G6_RAW_UNREVIEWED_NOT_ORIGINAL_G6';
record.experimentalCondition='Only controller reference Constant3 SID199 300 -> 293.15 K in generated derivative; physical ambient/heat-transfer boundary not changed';
record.referenceAmbientK=293.15;
record.assessment='ACTIVE_REGIME_SENSITIVITY_UNREVIEWED_NO_PHYSICAL_PUMP_ENERGY';
private=fullfile(root,'jte069-private');
assert(~isfolder(private),'JTE067:UnexpectedPrivatePath');mkdir(private);
mat=fullfile(private,['JTE069_ACTIVE_C1_' position '_ref293p15_2400_NATIVE.mat']);
save(mat,'record','-v7.3');
stored=load(mat,'record');
assert(isequal(stored.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE067:Readback');
info=dir(mat);
assert(info.bytes>0&&info.bytes<3*1024^3,'JTE067:FileSize');
fprintf('JTE069_ACTIVE_G6_RAW_SAVED site=%s nativeRows=%d channels=312 MATbytes=%d SHA256=%s ACCEPTED=false\n', ...
 position,numel(record.signalData.jteTtrue.time_s),info.bytes,JTE2026sha256(mat));
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')), ...
 models.sourceSHA256),'JTE067:SourceChanged');
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(m)
try
 if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end
catch,end
end
