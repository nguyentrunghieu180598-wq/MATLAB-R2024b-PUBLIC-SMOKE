function JTE072_group_C1(site)
% Controlled follow-up: correlated -2 K on 3 co-maximum observations.
% Three pre-registered groups are selected from independent JTE068 active
% C0 2400s (times ~200,600,2200s), NOT from this C1 outcome.
% Ambient REFERENCE only changes 300K->293.15K, NOT heat-transfer ambient.
site=char(site);
assert(ismember(site,{'early','mid','late'}),'JTE072:BadGroup');
assert(strcmp(version('-release'),'2024b'),'JTE072:MATLABRelease');
switch site
 case 'early', group=[34 35 36];selectionTime=200;
 case 'mid',   group=[199 200 201];selectionTime=600;
 case 'late',  group=[202 203 204];selectionTime=2200;
end
root=pwd;vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));cg=onCleanup(@()closeProjectQuiet(p)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,['jte072-generated-' site]));
[~,model]=fileparts(files.study);load_system(files.study);
mg=onCleanup(@()closeModelQuiet(model)); %#ok<NASGU>
assert(isempty(get_param(model,'PreLoadFcn'))&&isempty(get_param(model,'CloseFcn')),'JTE072:SourceCallbacks');
for event={'InitFcn','StartFcn','StopFcn','PostLoadFcn'}
 assert(isempty(get_param(model,event{1})),'JTE072:RuntimeCallback');
end
block=[model '/Constant3'];
assert(strcmp(get_param(block,'SID'),'199')&&strcmp(get_param(block,'BlockType'),'Constant'),'JTE072:ReferenceBlock');
old=slResolve(get_param(block,'Value'),block);
assert(isscalar(old)&&abs(old-300)<1e-12,'JTE072:ChangedSourceReference');
set_param(block,'Value','293.15');
mw=get_param(model,'ModelWorkspace');
prov=evalin(mw,'jte056AmbientProvenance');
prov.valueK=293.15;prov.expression='293.15';
assignin(mw,'jte056AmbientProvenance',prov);
save_system(model,files.study);
% Use C0 active baseline to VERIFY fixed group was co-maximum before C1.
base=Simulink.SimulationInput(model);
base=base.setVariable('jteChannelIndex',1,'Workspace',model);
base=base.setVariable('jteBiasK',0,'Workspace',model);
base=base.setModelParameter('StartTime','0','StopTime','2400','SaveTime','on','TimeSaveName','tout');
b0=sim(base);
[tc,ref]=JTE2026timeseries(b0,'jteTtrue');
assert(size(ref,2)==312&&tc(1)==0&&abs(tc(end)-2400)<1e-8,'JTE072:Baseline');
ix=find(tc>=selectionTime,1,'first');
assert(~isempty(ix),'JTE072:NoPredefinedTime');
assert(all(abs(ref(ix,group)-max(ref(ix,:)))<1e-11),'JTE072:PredeclaredGroupNotMax');
[~,ucore]=JTE2026timeseries(b0,'jteUcore');
assert(any(ucore(:)>0.25+1e-12),'JTE072:ControllerNotActive');
clear b0 ref tc ucore
% Runtime actuator logger/model physics remain the same.
% A vector j is accepted only if the pinned MATLAB Function supports fixed
% array indexed assignment Tm(j)=T(j)+b; fail-closed otherwise.
probe=Simulink.SimulationInput(model);
probe=probe.setVariable('jteChannelIndex',group,'Workspace',model);
probe=probe.setVariable('jteBiasK',-2,'Workspace',model);
probe=probe.setModelParameter('StartTime','0','StopTime','20','SaveTime','on','TimeSaveName','tout');
short=sim(probe);
[tTrue,T]=JTE2026timeseries(short,'jteTtrue');
[tMeas,M]=JTE2026timeseries(short,'jteTmeas');
assert(isequal(tTrue,tMeas)&&size(T,2)==312,'JTE072:ProbeClock');
other=setdiff(1:312,group);
assert(all(M(:,other)==T(:,other),'all'),'JTE072:ProbeUnselectedChannels');
assert(all(abs(M(:,group)-T(:,group)+2)<1e-9,'all'),'JTE072:ProbeGroupBias');
fprintf('JTE072_GROUP_PROBE_PASS site=%s channels=%d referenceK=293.15\n',site,numel(group));
clear short tTrue tMeas T M probe
input=Simulink.SimulationInput(model);
input=input.setVariable('jteChannelIndex',group,'Workspace',model);
input=input.setVariable('jteBiasK',-2,'Workspace',model);
input=input.setModelParameter('StartTime','0','StopTime','2400','SaveTime','on','TimeSaveName','tout');
ticv=tic;out=sim(input);duration=toc(ticv);
record=JTE072collect(out,model,files,['C1_group_' site '_original'],'original',input);
assert(isequal(record.injection.channels_1based,group),'JTE072:GroupDrift');
record.dataUse='JTE072_THREE_CORRELATED_SENSORS_MINUS2K_ACTIVE_REFERENCE_UNREVIEWED';
record.experimentalCondition='Control reference only 293.15K; source thermal physics unchanged. Pre-registered max groups from independent JTE068 active C0, no claim of Porsche-specific cell physical ambient.';
record.groupSelectionTime_s=selectionTime;
record.referenceC0SourceSHA256=files.sourceSHA256;
record.elapsedWall_s=duration;
record.assessment='STUDY_RAW_NOT_ACCEPTED_NO_PUMP_ENERGY';
dest=fullfile(root,'jte072-private');
assert(~isfolder(dest),'JTE072:PrivatePath');mkdir(dest);
f=fullfile(dest,['JTE072_GROUP_C1_' site '_ref293p15_2400_NATIVE.mat']);
save(f,'record','-v7.3');
q=load(f,'record');
assert(isequal(q.record.signalData.jteTtrue.values,record.signalData.jteTtrue.values),'JTE072:LocalReadback');
info=dir(f);
assert(info.bytes>0 && info.bytes<3*1024^3,'JTE072:FileSize');
fprintf('JTE072_GROUP_RAW_SAVED site=%s nativeRows=%d channels=312 MATbytes=%d SHA256=%s accepted=false\n',site,numel(record.signalData.jteTtrue.time_s),info.bytes,JTE2026sha256(f));
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),files.sourceSHA256),'JTE072:VendorChanged');
end
function closeProjectQuiet(p)
try,close(p);catch,end
end
function closeModelQuiet(model)
try
 if bdIsLoaded(model),set_param(model,'CloseFcn','');close_system(model,0);end
catch,end
end
