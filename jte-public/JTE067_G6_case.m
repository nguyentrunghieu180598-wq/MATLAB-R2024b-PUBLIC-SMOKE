function JTE067_G6_case(position)
% G6: three negative controls on unchanged pinned 2400s physical source.
% Site hot/middle/cold is deterministically selected from the *C0 zero bias*
% time-weighted cell temperature mean (not G6 outcome); tie by cell index.
% Do not confuse a null controller effect with a numerical failure.
position=char(position);
assert(any(strcmp(position,{'hot','middle','cold'})),'JTE067:InvalidSite');
assert(strcmp(version('-release'),'2024b'),'JTE067:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
pg=onCleanup(@()quietProject(p)); %#ok<NASGU>
models=JTE056build(vendor,fullfile(root,['jte067-generated-' position]));
[~,model]=fileparts(models.study);
load_system(models.study);cg=onCleanup(@()quietModel(model)); %#ok<NASGU>
assert(isempty(get_param(model,'PreLoadFcn'))&&isempty(get_param(model,'CloseFcn')),'JTE067:Callback');
for event={'InitFcn','StartFcn','StopFcn','PostLoadFcn'}
 assert(isempty(get_param(model,event{1})),'JTE067:RuntimeCallback');
end
base=Simulink.SimulationInput(model);
base=base.setVariable('jteChannelIndex',1,'Workspace',model);
base=base.setVariable('jteBiasK',0,'Workspace',model);
base=base.setModelParameter('StartTime','0','StopTime','2400', ...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE067_C0_REFERENCE_START sourceSHA256=%s profile=original\n',models.sourceSHA256);
o0=sim(base);
[t,T]=JTE2026timeseries(o0,'jteTtrue');
assert(size(T,2)==312&&t(1)==0&&abs(t(end)-2400)<1e-8,'JTE067:Reference');
assert(all(diff(t)>=0)&&all(isfinite(T(:))),'JTE067:ReferenceNative');
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
fprintf('JTE067_SINGLE_CHANNEL_20S_PROBE_PASS site=%s confidential_index_not_logged=true\\n',position);
clear short tr v tm m probe
% Retain metadata privately; no confidential cell index or thermal values in stdout.
clear o0 T
b=Simulink.SimulationInput(model);
b=b.setVariable('jteChannelIndex',j,'Workspace',model);
b=b.setVariable('jteBiasK',-2,'Workspace',model);
b=b.setModelParameter('StartTime','0','StopTime','2400', ...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE067_C1_RUN_START site=%s biasK=-2 profile=original\n',position);
ticG6=tic;
out=sim(b);
elapsed=toc(ticG6);
record=JTE067collect(out,model,models,['C1_' position '_original'],'original',b);
assert(record.injection.channel_1based==j && record.injection.biasK==-2,'JTE067:SelectedChannelDrift');
record.selectionBasis='C0 original solver, entire 0-2400s time-weighted mean across 312 cells; tie smaller 1-based index first; not selected from G6 outcome';
record.selectedRankLabel=position;
record.referenceC0SourceSHA256=models.sourceSHA256;
record.referenceC0LoadSHA256=record.load.SHA256;
record.elapsedWall_s=elapsed;
record.dataUse='REAL_R2024B_G6_MINUS2K_SINGLE_CHANNEL_RAW_UNREVIEWED';
record.assessment='G6_RAW_STUDY_NOT_ACCEPTED_NO_PHYSICAL_PUMP_ENERGY';
private=fullfile(root,'jte067-private');
assert(~isfolder(private),'JTE067:UnexpectedPrivatePath');mkdir(private);
mat=fullfile(private,['JTE067_C1_' position '_original_2400_NATIVE.mat']);
save(mat,'record','-v7.3');
stored=load(mat,'record');
assert(isequal(stored.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE067:Readback');
info=dir(mat);
assert(info.bytes>0&&info.bytes<3*1024^3,'JTE067:FileSize');
fprintf('JTE067_G6_RAW_SAVED site=%s nativeRows=%d channels=312 MATbytes=%d SHA256=%s ACCEPTED=false\n', ...
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
