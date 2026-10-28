function p=BTMS_M2_prepare340NoRun(sourceSLX, targetSLX, privateDir, sourceSHA)
% M2/340: make a NEW B0L10ms logging-only derivative; no MATLAB simulation.
% Requires Work verified source SHA and fresh output directory. Not G5 PASS.
assert(strcmp(version('-release'),'2024b') && contains(version,'24.2.0.3361896'),'M2Ops:Runtime','M2 validation failed: Runtime.');
assert(isfile(sourceSLX) && ~isfile(targetSLX) && isfolder(privateDir),'M2Ops:Fresh','M2 validation failed: Fresh.');
assert(exist('JTE2026sha256','file')==2,'M2Ops:SHAHelper','M2 validation failed: SHAHelper.');
sourceSLX=char(java.io.File(char(sourceSLX)).getCanonicalPath());
targetSLX=char(java.io.File(char(targetSLX)).getCanonicalPath());
privateDir=char(java.io.File(char(privateDir)).getCanonicalPath());
[~,~,ext]=fileparts(sourceSLX);[targetParent,m,ext2]=fileparts(targetSLX);
assert(strcmp(ext,'.slx') && strcmp(ext2,'.slx') && isfolder(targetParent) && ...
 isvarname(m) && ~bdIsLoaded(m) && ~strcmp(sourceSLX,targetSLX),'M2Ops:Paths','M2 validation failed: Paths.');
listing=dir(privateDir);listing=listing(~ismember({listing.name},{'.','..'}));
assert(isempty(listing),'M2Ops:PrivateDirNotFresh','M2 validation failed: PrivateDirNotFresh.');
originalSHA=JTE2026sha256(sourceSLX);
assert(strcmpi(originalSHA,char(sourceSHA)),'M2Ops:SourceReceiptMismatch','M2 validation failed: SourceReceiptMismatch.');
assert(copyfile(sourceSLX,targetSLX)==1,'M2Ops:CopyFailed','M2 validation failed: CopyFailed.');
load_system(targetSLX);
closeGuard=onCleanup(@()close_system(m,0)); %#ok<NASGU>
assert(str2double(get_param(m,'StartTime'))==0 && strcmp(get_param(m,'StopTime'),'2400') && ...
 strcmp(get_param(m,'Solver'),'ode23t') && str2double(get_param(m,'MaxStep'))==0.05,...
 'M2Ops:NotPinnedSource','M2 validation failed: NotPinnedSource.');
control=[m '/Battery Control'];
act=[control '/Amended sampled actuator'];hold=[control '/Amended command sample hold'];
assert(getSimulinkBlockHandle(act)>0 && getSimulinkBlockHandle(hold)>0 && ...
 strcmp(get_param(act,'BlockType'),'DiscreteStateSpace') && ...
 strcmp(get_param(hold,'BlockType'),'ZeroOrderHold') && ...
 str2double(get_param(act,'SampleTime'))==0.01 && ...
 str2double(get_param(hold,'SampleTime'))==0.01,'M2Ops:NotB0L10ms','M2 validation failed: NotB0L10ms.');
assert(getSimulinkBlockHandle([control '/JTE local bias'])==-1,'M2Ops:NotB0L','M2 validation failed: NotB0L.');
assert(isequal(str2double(get_param(act,'A')),exp(-10)) && ...
 isequal(str2double(get_param(act,'B')),1-exp(-10)) && ...
 str2double(get_param(act,'C'))==1 && str2double(get_param(act,'D'))==0,...
 'M2Ops:ActuatorChanged','M2 validation failed: ActuatorChanged.');
fileSinks=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','ToFile');
roles={'uCore','uSampled','actuatorY','Ttrue312'};
assert(numel(fileSinks)==4,'M2Ops:ToFileCount','M2 validation failed: ToFileCount.');
newFiles=cell(1,4);sinkPaths=cell(1,4);
for k=1:4
 ix=cellfun(@(s)strcmp(get_param(s,'Name'),['BTMS_M2_' roles{k}]),fileSinks);
 assert(nnz(ix)==1,'M2Ops:SinkIdentity','M2 validation failed: SinkIdentity.');s=fileSinks{find(ix,1)};
 assert(strcmp(get_param(s,'SaveFormat'),'Timeseries') && ...
 strcmp(get_param(s,'SampleTime'),'-1') && strcmp(get_param(s,'Decimation'),'1'),...
 'M2Ops:SinkPolicy','M2 validation failed: SinkPolicy.');
 f=fullfile(privateDir,[m '_' roles{k} '.mat']);
 assert(~isfile(f),'M2Ops:NeverOverwriteMAT','M2 validation failed: NeverOverwriteMAT.');
 sinkPaths{k}=s;newFiles{k}=f;
end
% Disable ONLY redundant observer sinks. Retain unrecognized data sources.
ws=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','ToWorkspace');
redundant={'jteTtrue','jteUcore','jteFlwR'};roleForVariable={'Ttrue312','uCore','actuatorY'};
disabled={};sameSourceProof=cell(0,1);seen={};
for k=1:numel(ws)
 v=get_param(ws{k},'VariableName');
 if ~ismember(v,redundant),continue;end
 assert(~ismember(v,seen),'M2Ops:DuplicateObserverVariable','M2 validation failed: DuplicateObserverVariable.');seen{end+1}=v; %#ok<AGROW>
 ri=find(strcmp(redundant,v),1);fi=find(strcmp(roles,roleForVariable{ri}),1);
 wh=get_param(ws{k},'PortHandles');fh=get_param(sinkPaths{fi},'PortHandles');
 wsource=upstream(wh.Inport(1));fsource=upstream(fh.Inport(1));
 assert(wsource==fsource,'M2Ops:ObserverNotSameSource','M2 validation failed: ObserverNotSameSource.');
 assert(strcmp(get_param(ws{k},'SampleTime'),'-1') && ...
 strcmp(get_param(ws{k},'Decimation'),'1') && strcmp(get_param(ws{k},'MaxDataPoints'),'inf') && ...
 strcmp(get_param(ws{k},'SaveFormat'),'Timeseries'),'M2Ops:ObserverPolicyMismatch','M2 validation failed: ObserverPolicyMismatch.');
 assert(strcmp(get_param(ws{k},'Commented'),'off'),'M2Ops:SourceObserverAlreadyDisabled','M2 validation failed: SourceObserverAlreadyDisabled.');
 sameSourceProof{end+1}=struct('variable',v,'toFileRole',roles{fi},...
 'sourceBlock',get_param(wsource,'Parent'),'sourcePort',get_param(wsource,'PortNumber'),...
 'sameActualOutputPort',true,'bothInheritedAndUndecimated',true); %#ok<AGROW>
 disabled{end+1}=ws{k}; %#ok<AGROW>
end
assert(any(cellfun(@(s)strcmp(get_param(s,'VariableName'),'jteTtrue'),disabled)),...
 'M2Ops:NoCanonicalTrueVector','M2 validation failed: NoCanonicalTrueVector.');
assert(numel(unique(newFiles))==4,'M2Ops:FileTargetCollision','M2 validation failed: FileTargetCollision.');
for k=1:numel(disabled),set_param(disabled{k},'Commented','on');end
for k=1:4,set_param(sinkPaths{k},'FileName',newFiles{k});end
set_param(m,'StopTime','340');
assert(strcmp(get_param(m,'StopTime'),'340') && strcmp(get_param(m,'Solver'),'ode23t'),...
 'M2Ops:RuntimeCap','M2 validation failed: RuntimeCap.');
save_system(m,targetSLX);
assert(strcmp(JTE2026sha256(sourceSLX),originalSHA),'M2Ops:ImmutableSource','M2 validation failed: ImmutableSource.');
for k=1:4,assert(strcmp(get_param(sinkPaths{k},'FileName'),newFiles{k}),'M2Ops:SinkPath','M2 validation failed: SinkPath.');end
p=struct('status','STATIC_CLONE_ONLY_NOT_COMPILED_OR_RUN',...
 'sourceSHA256',originalSHA,'derivativeSHA256',JTE2026sha256(targetSLX),...
 'stopTime_s',340,'sampleTime_s',0.01,'disabledRedundantObservers',{disabled},...
 'retainedOtherObservers',numel(ws)-numel(disabled),'observerReplacementSourceProof',{sameSourceProof},...
 'fourLoggerPaths',{sinkPaths},'privateTargets',{newFiles},...
 'physicalGraphRevalidated',false,'solvedPhysicalICValidated',false,...
 'fileClocksValidated',false,'peakRAMMeasured',false,...
 'physicalRun',false,'G5Accepted',false);
fprintf('M2_340_LOGGING_CLONE_STATIC_ONLY source2400=1 clone340=1 run=0 G5_ACCEPTED=0\n');
end
function p=upstream(port)
l=get_param(port,'Line');assert(l~=-1,'M2Ops:ObserverDisconnected','M2 validation failed: ObserverDisconnected.');
p=get_param(l,'SrcPortHandle');assert(p~=-1,'M2Ops:ObserverSourceMissing','M2 validation failed: ObserverSourceMissing.');
end
