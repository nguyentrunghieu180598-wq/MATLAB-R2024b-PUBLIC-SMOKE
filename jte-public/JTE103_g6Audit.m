function JTE103_g6Audit()
% Read-only protocol deviation audit using actual R2024b arithmetic.
root=fullfile(pwd,'jte103-private');run=getenv('GITHUB_RUN_ID');prefix=fullfile(root,['JTE103_' run '_CAPABILITY_G6']);
M=jsondecode(fileread(fullfile(root,'cap_manifest.json')));
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
references={};ledger={};failures={};active=struct();rankFiles={};
for k=1:numel(M.files)
 item=M.files(k);if ~strcmp(item.kind,'C0'),continue;end
 try
  S=load(fullfile(root,item.local),'record');r=S.record;
  assert(strcmp(r.sourceSHA256,pin)&&strcmp(r.units.temperature,'K')&&strcmp(r.units.time,'s'),'JTE103:G6Provenance','C0 source/units mismatch.');
  assert(abs(r.ambient.valueK-item.controllerReferenceK)<1e-10,'JTE103:ReferenceFrame','Controller reference frame mismatch.');
  t=r.signalData.jteTtrue.time_s(:);T=r.signalData.jteTtrue.values;
  assert(t(1)==0&&t(end)==2400&&all(diff(t)>=0)&&size(T,2)==312&&size(T,1)==numel(t)&&all(isfinite(T(:))),'JTE103:Native','Invalid C0 native data.');
  assert(isequal(T,r.signalData.jteTmeas.values)&&isequal(t,r.signalData.jteTmeas.time_s(:)),'JTE103:ZeroBias','C0 measured/true mismatch.');
  full=trapz(t,T,1)/2400;[tt,tailT,boundary]=last600(t,T);tail=trapz(tt,tailT,1)/600;
  indices=(1:312)';legacy=sortrows([full(:),indices],[1 2]);descFull=sortrows([-full(:),indices],[1 2]);descTail=sortrows([-tail(:),indices],[1 2]);
  legacySites=struct('hot',legacy(end,2),'middle',legacy(156,2),'cold',legacy(1,2));
  fullDescSites=struct('hot',descFull(1,2),'middle',descFull(156,2),'cold',descFull(end,2));
  intended=struct('hot',descTail(1,2),'middle',descTail(156,2),'cold',descTail(end,2));
  ref=struct('name',item.local,'inputSHA256',item.sha256,'sourceSHA256',r.sourceSHA256,'generatedModelSHA256',r.generatedModelSHA256,...
   'loadSHA256',r.load.SHA256,'profile',r.profile,'controllerReferenceK',item.controllerReferenceK,...
   'fullMean_K',full,'last600Mean_K',tail,'legacyAscending',legacy,'fullDescending',descFull,'intendedLast600Descending',descTail,...
   'legacySites',legacySites,'sameWindowDescendingSites',fullDescSites,'intendedSites',intended,...
   'meanWindowBoundary',boundary,'duplicateNativeRows',sum(diff(t)==0),'legacyHotExactTies',find(full==max(full)),...
   'intendedHotExactTies',find(tail==max(tail)),...
   'physicalSensorMapping','312 model thermal observations; NOT established as 312 physical sensors',...
   'coldTieSemantics','Literal final row of descending-mean/ascending-index order. If smallest index is intended for cold ties too, independent clarification is required before any future selection.',...
   'referenceEquivalenceLimit','G6 internal C0 trajectories were not saved by the case writers. This archived C0 reproduces declared source/load/reference/profile, not every hidden state or schedule of that unsaved internal run.');
  names={'hot','middle','cold'};changes=struct();
  for j=1:3
   site=names{j};changes.(site)=struct('windowOnlyChangesIndex',fullDescSites.(site)~=intended.(site),...
    'directionTieOrMiddleOnlyChangesIndex',legacySites.(site)~=fullDescSites.(site),...
    'combinedChangesIndex',legacySites.(site)~=intended.(site));
  end
  ref.deviationDecomposition=changes;references{end+1}=ref; %#ok<AGROW>
  lr=zeros(312,1);dr=lr;tr=lr;
  lr(legacy(:,2))=(1:312)';dr(descFull(:,2))=(1:312)';tr(descTail(:,2))=(1:312)';
  tab=table(indices,full(:),tail(:),lr,dr,tr,'VariableNames',{'channel_1based','fullMean_K','last600Mean_K','legacyAscendingRank','fullDescendingRank','last600DescendingRank'});
  out=[prefix '_RANK_' erase(item.local,'.mat') '.csv'];writetable(tab,out);rankFiles{end+1}=out; %#ok<AGROW>
  if item.controllerReferenceK==293.15&&strcmp(r.profile,'original')
   active=struct('time',t,'T',T,'loadSHA',r.load.SHA256,'referenceName',item.local);
  end
  clear S r T tailT
 catch err
  failures{end+1}=struct('file',item.local,'phase','C0_RANK_READONLY','identifier',err.identifier,'message',err.message); %#ok<AGROW>
 end
end
for k=1:numel(M.files)
 item=M.files(k);if strcmp(item.kind,'C0'),continue;end
 try
  S=load(fullfile(root,item.local),'record');r=S.record;
  assert(strcmp(r.sourceSHA256,pin)&&abs(r.ambient.valueK-item.controllerReferenceK)<1e-10&&r.injection.biasK==-2,'JTE103:C1Identity','Stored C1 source/reference/injection differs.');
  entry=struct('file',item.local,'inputSHA256',item.sha256,'kind',item.kind,'caseName',r.caseName,...
   'controllerReferenceK',item.controllerReferenceK,'sourceSHA256',r.sourceSHA256,'loadSHA256',r.load.SHA256,...
   'G5PhysicalAcceptance','NOT_ACCEPTED','newSimulationRun',false,'oldOutcomeEdited',false);
  if strcmp(item.kind,'C1_SINGLE')
   index=r.injection.channel_1based;site=r.selectedRankLabel;
   validateattributes(index,{'double'},{'scalar','integer','>=',1,'<=',312});
   matches=find(cellfun(@(v)v.controllerReferenceK==item.controllerReferenceK&&strcmp(v.profile,'original'),references));
   entry.actualStoredIndex=index;entry.actualStoredLabel=site;entry.storedSelectionBasis=r.selectionBasis;
   if numel(matches)==1
    ref=references{matches};assert(strcmp(ref.loadSHA256,r.load.SHA256),'JTE103:Load','C0/C1 declared load differs.');
    entry.availableReference=ref.name;entry.legacyReproducedIndex=ref.legacySites.(site);entry.intendedProtocolIndex=ref.intendedSites.(site);
    entry.storedMatchesAvailableLegacyReproduction=index==ref.legacySites.(site);
    entry.storedDiffersFromIntendedProtocol=index~=ref.intendedSites.(site);
    entry.deviation='FULL_HORIZON_ASCENDING_IMPLEMENTATION_VS_LAST600_DESCENDING_PROTOCOL';
    entry.referenceEquivalenceLimit=ref.referenceEquivalenceLimit;
   else
    entry.deviation='UNAVAILABLE_MATCHED_C0_REFERENCE_DO_NOT_MIX_FRAMES';
   end
  else
   group=r.injection.channels_1based(:)';entry.actualStoredGroup=group;entry.selectionTime_s=r.groupSelectionTime_s;
   if contains(item.local,'early'),expected=[34 35 36];when=200;
   elseif contains(item.local,'mid'),expected=[199 200 201];when=600;
   else,expected=[202 203 204];when=2200;end
   entry.matchesFixedSourceCode=isequal(group,expected)&&r.groupSelectionTime_s==when;
   entry.deviation='SEPARATE_FIXED_GROUP_COMAX_DESIGN_NOT_JTE042_SINGLE_SITE_RANK';
   if isfield(active,'time')
    ix=find(active.time>=when,1,'first');residual=max(abs(active.T(ix,group)-max(active.T(ix,:))));
    entry.availableActiveC0Reference=active.referenceName;entry.actualNativeCheckTime_s=active.time(ix);
    entry.comaxResidual_K=residual;entry.comaxUnderOriginalCodeTolerance=residual<1e-11;
    entry.referenceEquivalenceLimit='Available JTE068 active C0, not a saved copy of each internal JTE072 C0; no C1 outcome used for selection.';
   else
    entry.comaxStatus='UNAVAILABLE_ACTIVE_C0';
   end
  end
  ledger{end+1}=entry;clear S r
 catch err
  failures{end+1}=struct('file',item.local,'phase','SAVED_SELECTION_METADATA','identifier',err.identifier,'message',err.message); %#ok<AGROW>
 end
end
files={'jte-public/JTE067_G6_case.m','jte-public/JTE069_active_G6_case.m','jte-public/JTE072_group_C1.m'};
expected={'264bc4f1ad5e81959841622e3bcc45e84d344b31','9094a280223829f24d5c0c630a631b5b4363d105','73359ac4c22cf5b2ecb9b5d10ad6a42f5aa9be13'};
sourceCode={};
for k=1:3
 [status,blob]=system(['git hash-object ' files{k}]);sourceCode{end+1}=struct('path',files{k},'actualGitBlob',strtrim(blob),...
  'observedDefaultBranchBlob',expected{k},'matchesObservedDefaultBranch',status==0&&strcmp(strtrim(blob),expected{k})); %#ok<AGROW>
end
status='PASS_READONLY_LEDGER_COMPLETE';
if ~isempty(failures)||~isempty(M.missing)||numel(ledger)<9,status='PARTIAL_MISSING_OR_UNQUALIFIED_INPUTS';end
audit=struct('schema','JTE103_G6_READONLY_PROTOCOL_DEVIATION','run',run,'commit',getenv('GITHUB_SHA'),...
 'references',{references},'savedSelections',{ledger},'failures',{failures},'missing',{M.missing},'sourceCode',{sourceCode},...
 'status',status,'physicalSensorMapping','UNVERIFIED','newClosedLoopSimulations',0,'newChannelSelectionAuthorized',false,...
 'scientificConclusion','Protocol deviation audit only; no causal thermal effect and no G6 scientific acceptance. Existing outcomes remain immutable.');
save([prefix '_LEDGER.mat'],'audit','-v7.3');writeJSON([prefix '_LEDGER.json'],audit);
fprintf('JTE103_G6_READONLY_RESULT status=%s nativeMATandStoredSelectionRead=1 framesKeptSeparate=1 newClosedLoopSimulations=0 oldOutcomesEdited=0 physicalSensorMapping=UNVERIFIED\n',status);
end
function [tt,Y,b]=last600(t,T)
inside=t>=1800;tt=t(inside);Y=T(inside,:);b=struct('boundary_s',1800,'nativeBoundaryExact',tt(1)==1800,...
 'method','Original trapz piecewise-linear convention; at most one temperature boundary interpolation, no command or 1s resampling.');
if tt(1)>1800
 left=find(t<1800,1,'last');right=left+1;w=(1800-t(left))/(t(right)-t(left));
 boundary=T(left,:)+w*(T(right,:)-T(left,:));tt=[1800;tt];Y=[boundary;Y];
 b.supportNativeTimes_s=[t(left),t(right)];b.linearWeight=w;
else,b.supportNativeTimes_s=[1800,1800];b.linearWeight=0;end
assert(tt(1)==1800&&tt(end)==2400&&all(diff(tt)>=0),'JTE103:Tail','Tail integration domain invalid.');
end
function writeJSON(file,v)
h=fopen(file,'w');assert(h~=-1,'JTE103:Write','Private ledger write failed.');fprintf(h,'%s',jsonencode(v));fclose(h);
end
