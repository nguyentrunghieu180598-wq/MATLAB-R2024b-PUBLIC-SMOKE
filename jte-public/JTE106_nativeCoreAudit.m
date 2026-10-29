function JTE106_nativeCoreAudit()
% Existing archived records only. NO sim/profileModel/build/model edits.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE106:Runtime','R2024bU10 required.');
P.root=fullfile(pwd,'jte106-private');P.run=getenv('GITHUB_RUN_ID');P.prefix=fullfile(P.root,['JTE106_' P.run '_AUDIT']);
M=jsondecode(fileread(fullfile(P.root,'manifest.json')));
for kind={'references','cases','support'}
 list=M.(kind{1});for k=1:numel(list),assert(strcmp(JTE2026sha256(fullfile(P.root,list(k).local)),list(k).sha256),'JTE106:SHA','Verified archive changed.');end
end
law=JTE106_readLaw(P.root,P.prefix);
refs={};referenceResults={};B0Lcache={};
for k=1:numel(M.references)
 spec=M.references(k);
 try
  S=load(fullfile(P.root,spec.local),'record');r=S.record;d=data(r,false);
  assert(d.frame==spec.controllerReferenceK&&strcmp(r.profile,spec.profile),'JTE106:ReferenceFrame','Wrong reference frame/profile.');
  ref=compactRef(r,d,spec,law);rr=ref;rr=rmfield(rr,{'time','core','post','snapshot'});
  rr.B0L_C0_NATIVE_VECTOR_EQUIVALENCE='NOT_AVAILABLE_FOR_THIS_FRAME_PROFILE';
  if startsWith(spec.label,'B0L')
   B0Lcache{end+1}=struct('profile',spec.profile,'time',d.t,'T',d.T,'ref',ref); %#ok<AGROW>
  else
   matches=find(cellfun(@(v)strcmp(v.profile,spec.profile),B0Lcache));
   if d.frame==300&&numel(matches)==1
    b=B0Lcache{matches};same=isequal(b.time,d.t)&&isequal(b.T,d.T);
    [declared,detail]=sameFrame(b.ref,ref);
    rr.B0L_C0_NATIVE_VECTOR_EQUIVALENCE=pass(same&&declared);
    rr.B0L_C0_qualification=detail;rr.B0L_C0_fullClockAndT312Exact=same;
    B0Lcache(matches)=[]; % release full T reference; no row resampling
   end
  end
  referenceResults{end+1}=rr;refs{end+1}=ref; %#ok<AGROW>
  clear S r d
 catch err
  referenceResults{end+1}=struct('name',spec.label,'CASE_AVAILABLE',true,'DATA_QUALIFICATION',false,'failure',failure(err)); %#ok<AGROW>
 end
end
selection=jsondecode(fileread(fullfile(P.root,'selection_ledger.json')));
reports={};publicFlags={};anyNativeChange=false;allNoExcitation=true;
for k=1:numel(M.cases)
 spec=M.cases(k);report=struct('opaqueId',spec.opaqueId,'archive',spec,'CASE_AVAILABLE',true);
 flags=blankFlags(spec.opaqueId);flags.CASE_AVAILABLE=true;
 try
  S=load(fullfile(P.root,spec.local),'record');r=S.record;d=data(r,true);
  if isfield(r.injection,'channels_1based'),channels=r.injection.channels_1based(:)';else,channels=r.injection.channel_1based;end
  validateattributes(channels,{'double'},{'vector','integer','>=',1,'<=',312});
  assert(numel(unique(channels))==numel(channels)&&r.injection.biasK==-2,'JTE106:BiasScope','Not the locked distinct-channel minus2K intervention.');
  other=setdiff(1:312,channels);
  expected=d.T;expected(:,channels)=expected(:,channels)-2;
  scale=max([1,max(abs(d.T),[],'all'),max(abs(d.M),[],'all')]);tolK=8*eps(scale);tolU=8*eps(1);
  selectedResidual=max(abs(d.M(:,channels)-expected(:,channels)),[],'all');
  othersExact=isempty(other)||isequal(d.M(:,other),d.T(:,other));
  negativeOnly=othersExact&&selectedResidual<=tolK&&all(d.M(:,channels)<=d.T(:,channels),'all');
  mxTrue=max(d.T,[],2);mxMeas=max(d.M,[],2);
  if isempty(other),oracleLoss=2*ones(size(mxTrue));else,oracleLoss=max(0,min(2,max(d.T(:,channels),[],2)-max(d.T(:,other),[],2)));end
  observedLoss=mxTrue-mxMeas;oracleResidual=max(abs(observedLoss-oracleLoss));
  e1pass=negativeOnly&&oracleResidual<=tolK&&isequal(mxTrue,d.maxTrue)&&isequal(mxMeas,d.maxMeas);
  [uSameTrue,qTrue]=coreLaw(mxTrue,d.frame,law);
  [uSameFault,qFault]=coreLaw(mxMeas,d.frame,law);
  nativeLawResidual=max(abs(d.u-uSameFault));
  sampledLawMatch=law.verified&&nativeLawResidual<=tolU;
  sameStateDelta=uSameFault-uSameTrue;
  staticNonzero=any(abs(sameStateDelta)>tolU);
  sourceInfo=struct('sourceVendorSHA',r.sourceSHA256,'generatedModelSHA',r.generatedModelSHA256,'loadSHA',r.load.SHA256,...
   'controllerReferenceK',d.frame,'profile',r.profile,'caseName',r.caseName,'matlabVersion',r.matlabVersion,...
   'timeStep',stepInfo(d.t),'thermalObservations',312,'physicalSensorMapping','UNVERIFIED',...
   'sourceNativeFpBudget_K',tolK,'normalizedCommandRoundoffBudget',tolU,...
   'internalSimscapeICCoverage','UNVERIFIED; compare declared resolved IC parameters and T0 only');
  own=compactRef(r,d,spec,law);
  matches=find(cellfun(@(v)v.frame==d.frame&&strcmp(v.profile,r.profile)&&~startsWith(v.label,'B0L'),refs));
  baseline=[];frameMatch=false;frameDetail=struct('status','UNAVAILABLE_MATCHED_C0');
  if numel(matches)==1
   baseline=refs{matches};[frameMatch,frameDetail]=sameFrame(baseline,own);
  end
  transitions=nativeTransitions(d.t,d.u,law.step,tolU);
  cross=struct('status','UNAVAILABLE_MATCHED_FRAME','anyExactCommonCoreContrast',false,'anyDisjointTransitionBracket',false,'anyNewRawLevel',false,...
    'acceptedEventSemantics','NOT_CERTIFIED');
  if ~isempty(baseline)&&frameMatch,cross=compareCore(baseline,own,law.step,tolU);end
  recordedChange=frameMatch&&(cross.anyExactCommonCoreContrast||cross.anyDisjointTransitionBracket||cross.anyNewRawLevel||cross.sequenceDiffers);
  evidence=frameMatch&&e1pass&&negativeOnly&&sampledLawMatch&&(recordedChange||staticNonzero);
  noExcitation=frameMatch&&e1pass&&sampledLawMatch&&~evidence;
  if isfield(r,'elapsedWall_s'),sourceInfo.archivedElapsedWall_s=r.elapsedWall_s;end
  report.source=sourceInfo;report.injection=struct('channels_1based',channels,'biasK',r.injection.biasK,'nonselectedExact',othersExact,...
   'selectedResidualMax_K',selectedResidual,'recordedExpectedMeasuredBitwise',isequal(expected,d.M));
  report.selection=selectionMetadata(r,spec,selection);
  report.sameFrame=frameDetail;
  report.selector=struct('SELECTOR_ORACLE_PASS',e1pass,'residualMax_K',oracleResidual,'lossMax_K',max(observedLoss),...
   'lossMin_K',min(observedLoss),'nonzeroNativeRows',sum(abs(observedLoss)>tolK),'nativeRows',numel(d.t),...
   'semantics','Same physical Ttrue of THIS C1 only; finite-precision Max identity, not cross-trajectory thermal effect.');
  report.sameStateDecision=struct('sourceParametersVerified',law.verified,'recordedFaultCoreVsNativeMATLABMaxResidual',nativeLawResidual,...
   'recordedFaultCoreVsNativeMATLABBitwise',isequal(d.u,uSameFault),'sampledSourceLawMatch',sampledLawMatch,...
   'fullRecordedCoreUnique',unique(d.u)','unbiasedSameStateCoreUnique',unique(uSameTrue)',...
   'sameStateDeltaUnique',unique(sameStateDelta)','nonzeroDecisionAtNativeRows',sum(abs(sameStateDelta)>tolU),...
   'idealOneStepBoundDiagnostic',all(abs(sameStateDelta)<=law.step+tolU)&&all(sameStateDelta<=tolU),...
   'authority','Actual archived Simulink core at recorded states plus source MATLAB arithmetic. No new threshold canary; NumPy/Decimal is not substituted for Simulink.');
  report.recordedCore=transitions;report.crossTrajectoryCore=cross;
  report.postfilter=postfilterFlags(d,law.step);
  report.timeMasking=struct('E1_E2_TIME_METRICS','NOT_COMPUTED_NO_CERTIFIED_ACCEPTED_EVENT_SEMANTICS',...
   'nativeRowCountsAreTimeFractions',false,'maskedTimeFraction',[],'statisticalIndependenceClaim',false,...
   'pValuesComputed',false,'samplesVsTime','Repeated rows/transition brackets retained; no 1s interpolation or row-count duration.');
  flags.CASE_JTE042_RANK_APPLICABLE=strcmp(r.schema,'JTE067_C1_NATIVE_V1');
  flags.CASE_AVAILABLE=true;flags.DATA_QUALIFICATION=true;flags.SAME_FRAME_MATCH=frameMatch;flags.SELECTOR_ORACLE_PASS=e1pass;
  flags.NEGATIVE_BIAS_ONLY=negativeOnly;flags.C1_CORE_FLOOR_NATIVE=all(d.u==law.step);
  if ~isempty(baseline),flags.BASELINE_CORE_FLOOR_NATIVE=all(baseline.core==law.step);end
  if evidence
   flags.CONTROL_LEVEL_CHANGE_EVIDENCE='NATIVE_RECORDED_OR_SOURCE_SAME_STATE_CONTRAST';
   flags.CONTROL_EFFECT_RESOLVABLE='NATIVE_ONLY_ACCEPTED_EVENT_AND_ACTUATION_UNQUALIFIED';
  elseif noExcitation
   flags.CONTROL_LEVEL_CHANGE_EVIDENCE='NONE_IN_ARCHIVED_NATIVE_EVIDENCE';
   flags.CONTROL_EFFECT_RESOLVABLE='NO_RESOLVED_NATIVE_CORE_CHANGE';
  else
   flags.CONTROL_LEVEL_CHANGE_EVIDENCE='UNAVAILABLE_DATA_FRAME_OR_SOURCE_LAW';
   flags.CONTROL_EFFECT_RESOLVABLE='NOT_ESTABLISHED';
  end
  flags.SOURCE_MATLAB_ORACLE_MATCH_AT_ARCHIVED_SAMPLES=sampledLawMatch;
  if noExcitation,flags.DECISION='NO_CONTROL_EXCITATION_UNDER_ARCHIVED_CONDITIONS';
  elseif evidence,flags.DECISION='CONTROL_CONTRAST_OBSERVED_VALIDATION_PROPOSAL_ONLY';
  else,flags.DECISION='INCOMPLETE_NO_EFFECT_VERDICT_AUTHORIZED';end
  report.flags=flags;
  % Compact native scalar evidence only; original T312 matrices stay in their immutable archive.
  evidenceFile=fullfile(P.root,['JTE106_' P.run '_AUDIT_' spec.opaqueId '_EVIDENCE.mat']);
  time_s=d.t;recordedCore=d.u;recordedPostfilter=d.y; %#ok<NASGU>
  save(evidenceFile,'time_s','mxTrue','mxMeas','observedLoss','oracleLoss','uSameTrue','uSameFault','qTrue','qFault',...
   'recordedCore','recordedPostfilter','sameStateDelta','channels','-v7.3');
  report.evidenceFile=struct('name',evidenceFile,'SHA256',JTE2026sha256(evidenceFile));
  anyNativeChange=anyNativeChange||evidence;allNoExcitation=allNoExcitation&&noExcitation;
  clear S r d expected
 catch err
  flags.CASE_AVAILABLE=true;flags.DATA_QUALIFICATION=false;flags.DECISION='FAIL_DATA_QUALIFICATION_NO_EFFECT_COMPARISON';
  report.failure=failure(err);report.flags=flags;allNoExcitation=false;
 end
 reports{end+1}=report;publicFlags{end+1}=flags; %#ok<AGROW>
 fprintf('JTE106_CASE_FLAGS case=%s CASE_AVAILABLE=%d SAME_FRAME_MATCH=%d SELECTOR_ORACLE_PASS=%d NEGATIVE_BIAS_ONLY=%d BASELINE_CORE_FLOOR_NATIVE=%d C1_CORE_FLOOR_NATIVE=%d CONTROL_LEVEL_CHANGE_EVIDENCE=%s CONTROL_EFFECT_RESOLVABLE=%s G5_NUMERICAL_ACCEPTED=false G6_PROTOCOL_DEVIATION_PRESENT=1 G6_TEMPERATURE_CLAIM_AUTHORIZED=false\n',...
 flags.opaqueId,flags.CASE_AVAILABLE,flags.SAME_FRAME_MATCH,flags.SELECTOR_ORACLE_PASS,flags.NEGATIVE_BIAS_ONLY,...
 flags.BASELINE_CORE_FLOOR_NATIVE,flags.C1_CORE_FLOOR_NATIVE,flags.CONTROL_LEVEL_CHANGE_EVIDENCE,flags.CONTROL_EFFECT_RESOLVABLE);
end
dictionary=dataDictionary();
decision='INCOMPLETE_ARCHIVE_OR_QUALIFICATION';
if allNoExcitation&&~isempty(reports)&&isempty(M.unqualifiedCandidates)
 decision='NO_CONTROL_EXCITATION_UNDER_ARCHIVED_CONDITIONS';
elseif anyNativeChange
 decision='NATIVE_CONTROL_CONTRAST_REQUIRES_INDEPENDENT_EVENT_AND_NUMERICAL_DESIGN';
end
audit=struct('schema','JTE106_NATIVE_CORE_DECISION_AUDIT','run',P.run,'commit',getenv('GITHUB_SHA'),'matlab',version,...
 'references',{referenceResults},'cases',{reports},'flags',{publicFlags},'manifest',M,'dictionary',dictionary,'decision',decision,...
 'CONTROL_EXCITATION_NATIVE_EVIDENCE_PRESENT',anyNativeChange,'G5_NUMERICAL_ACCEPTED',false,'G6_TEMPERATURE_CLAIM_AUTHORIZED',false,...
 'GUI_REQUIRED_FOR_THIS_AUDIT',false,'newSimulationRun',false,'pythonSyntheticTestsRepeated',false,...
 'scope','Archive-native E1 and core decisions, not accepted-step/actuation/thermal causality.');
if anyNativeChange
 audit.oneProposedVerification=proposal(reports);
else
 audit.oneProposedVerification=struct('status','NO_NEW_CASE_OR_PROFILER_REQUEST','reason','No qualified native core-excitation evidence or incomplete data; do not manufacture reference/severity/outcomes.');
end
writeJSON([P.prefix '_RESULTS.json'],audit);save([P.prefix '_RESULTS.mat'],'audit','-v7.3');
writeJSON([P.prefix '_FLAGS.json'],struct('cases',{publicFlags},'decision',decision,'G5_NUMERICAL_ACCEPTED',false,'G6_TEMPERATURE_CLAIM_AUTHORIZED',false));
writeJSON([P.prefix '_DATA_DICTIONARY.json'],dictionary);
fprintf('JTE106_FINAL_DECISION decision=%s nativeEvidence=%d simulationRun=0 GUIrequired=0 pythonTestsRepeated=0 G5_NUMERICAL_ACCEPTED=false G6_TEMPERATURE_CLAIM_AUTHORIZED=false\n',decision,anyNativeChange);
end
function d=data(r,isC1)
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
if isC1
 assert(ismember(r.schema,{'JTE067_C1_NATIVE_V1','JTE072_GROUP3_C1_NATIVE_V1'})&&startsWith(r.caseName,'C1_'),'JTE106:Schema','Not a qualified archived C1 schema.');
else
 assert(strcmp(r.schema,'JTE056_NATIVE_V1')&&(startsWith(r.caseName,'C0_')||startsWith(r.caseName,'B0L_')),'JTE106:Schema','Not a baseline/reference native schema.');
end
assert(strcmp(r.sourceSHA256,pin)&&contains(r.matlabVersion,'24.2.0.3361896')&&strcmp(r.units.temperature,'K')&&strcmp(r.units.time,'s'),'JTE106:Provenance','Wrong source/runtime/units.');
d.frame=r.ambient.valueK;assert(d.frame==300||d.frame==293.15,'JTE106:Frame','Unregistered controller reference.');
d.t=r.signalData.jteTtrue.time_s(:);d.T=r.signalData.jteTtrue.values;
assert(isa(d.T,'double')&&size(d.T,2)==312&&size(d.T,1)==numel(d.t)&&all(isfinite(d.T(:)))&&...
 d.t(1)==0&&d.t(end)==2400&&all(diff(d.t)>=0),'JTE106:NativeT','Invalid native T312/clock.');
d.u=r.signalData.jteUcore.values(:);d.y=r.signalData.jteFlwR.values(:);
assert(isequal(d.t,r.signalData.jteUcore.time_s(:))&&isequal(d.t,r.signalData.jteFlwR.time_s(:))&&all(isfinite(d.u))&&all(isfinite(d.y)),'JTE106:NativeControl','Invalid native control clocks.');
d.maxTrue=r.signalData.jteTmaxTrue.values(:);assert(isequal(d.t,r.signalData.jteTmaxTrue.time_s(:))&&isequal(max(d.T,[],2),d.maxTrue),'JTE106:TrueReducer','True Max logger differs.');
if isC1||startsWith(r.caseName,'C0')
 d.M=r.signalData.jteTmeas.values;d.maxMeas=r.signalData.jteTmaxMeas.values(:);
 assert(isequal(size(d.M),size(d.T))&&all(isfinite(d.M(:)))&&isequal(d.t,r.signalData.jteTmeas.time_s(:))&&...
  isequal(d.t,r.signalData.jteTmaxMeas.time_s(:))&&isequal(max(d.M,[],2),d.maxMeas),'JTE106:Measured','Measured vector/reducer/clock differs.');
 if ~isC1,assert(isequal(d.M,d.T),'JTE106:ZeroBias','C0 measured true differs.');end
else,d.M=[];d.maxMeas=[];end
end
function ref=compactRef(r,d,spec,law)
ref=struct('label',spec.local,'frame',d.frame,'profile',r.profile,'sourceSHA',r.sourceSHA256,'loadSHA',r.load.SHA256,...
 'modelSHA',r.generatedModelSHA256,'solver',r.solver,'initialT0',d.T(1,:),'snapshot',snapshot(r),...
 'time',d.t,'core',d.u,'post',d.y,'coreUnique',unique(d.u)','coreFloorNative',all(d.u==law.step),...
 'timeCoverage_s',[d.t(1) d.t(end)],'nativeAcceptedStepCertification','UNAVAILABLE',...
 'referenceRole','Declared source/load/solver/IC parameters + initial T312, not hidden algebraic IC/accepted event proof.');
[u,~]=coreLaw(d.maxTrue,d.frame,law);ref.sourceMATLABCoreResidual=max(abs(u-d.u));
ref.sourceMATLABCoreMatch=law.verified&&ref.sourceMATLABCoreResidual<=8*eps(1);
end
function [match,detail]=sameFrame(a,b)
keys={'Solver','SolverType','StartTime','StopTime','MaxStep','MinStep','InitialStep','RelTol','AbsTol','FixedStep','ZeroCrossControl','LoadInitialState','InitialState','SimulationMode'};
diff={};for k=1:numel(keys),key=keys{k};if ~isfield(a.solver,key)||~isfield(b.solver,key)||~isequaln(a.solver.(key),b.solver.(key)),diff{end+1}=key;end;end %#ok<AGROW>
snapdiff={};sameSnap=a.snapshot.complete&&b.snapshot.complete&&isequal(a.snapshot.keys,b.snapshot.keys);
if sameSnap
 for k=1:numel(a.snapshot.keys),if ~isequaln(a.snapshot.values{k},b.snapshot.values{k}),snapdiff{end+1}=a.snapshot.keys{k};end;end %#ok<AGROW>
 sameSnap=isempty(snapdiff);
end
detail=struct('sourceEqual',strcmp(a.sourceSHA,b.sourceSHA),'controllerReferenceEqual',a.frame==b.frame,...
 'loadEqual',strcmp(a.loadSHA,b.loadSHA),'solverDifferences',{diff},'declaredICSnapshotMatch',sameSnap,'snapshotDifferenceKeys',{snapdiff},...
 'snapshotCoverageA',a.snapshot.coverage,'snapshotCoverageB',b.snapshot.coverage,'initialT312Exact',isequal(a.initialT0,b.initialT0),...
 'hiddenSimscapeIC','NOT_CERTIFIED','matchingScope','Declared source/load/solver/resolved-IC parameters/initialT312 only; excludes only declared injection variables.');
match=detail.sourceEqual&&detail.controllerReferenceEqual&&detail.loadEqual&&isempty(diff)&&sameSnap&&detail.initialT312Exact;
detail.match=match;
end
function s=snapshot(r)
root=strtok(r.load.block,'/');keys={};vals={};complete=true;unsupported={};
assert(isfield(r,'resolvedVariables'),'JTE106:ICMetadata','Missing resolved parameter snapshot.');
for k=1:numel(r.resolvedVariables)
 v=r.resolvedVariables(k);if ismember(v.name,{'jteBiasK','jteChannelIndex'}),continue;end
 if strcmp(v.sourceType,'base workspace'),source='$BASE';
 elseif strcmp(v.sourceType,'model workspace'),source='$MODEL';
 else,source=strrep(v.source,root,'$ROOT');end
 value=normal(v.value,root);
 if ~(isnumeric(value)||islogical(value)||ischar(value)||isstring(value)||iscell(value)||isstruct(value))
  complete=false;unsupported{end+1}=[v.name ':' class(value)]; %#ok<AGROW>
 end
 keys{end+1}=[v.sourceType '|' source '|' v.name];vals{end+1}=value; %#ok<AGROW>
end
[keys,ix]=sort(keys);vals=vals(ix);assert(numel(unique(keys))==numel(keys),'JTE106:SnapshotKeys','Ambiguous parameter snapshot.');
s=struct('keys',{keys},'values',{vals},'complete',complete,'coverage',struct('unsupported',{unsupported},'excluded',{{'jteBiasK','jteChannelIndex'}},...
 'scope','Resolved declared parameters only; no hidden Simscape algebraic-state claim.'));
end
function v=normal(v,root)
if ischar(v),v=strrep(v,root,'$ROOT');
elseif isstring(v),v=replace(v,root,'$ROOT');
elseif iscell(v),v=cellfun(@(x)normal(x,root),v,'UniformOutput',false);
elseif isstruct(v),names=fieldnames(v);for k=1:numel(v),for j=1:numel(names),v(k).(names{j})=normal(v(k).(names{j}),root);end;end
end
end
function [u,q]=coreLaw(maxT,ref,law)
% Native MATLAB operators in declared source order; not Decimal/Python.
q=law.gain*(maxT-ref);q=min(law.upper,max(law.lower,q));u=max(law.step,q-mod(q,law.step));
end
function info=nativeTransitions(t,u,step,tol)
ix=find(diff(u)~=0)+1;labels=round(u/step)*step;valid=abs(u-labels)<=tol;
jx=find(diff(labels)~=0)+1;
info=struct('rawUniqueLevels',unique(u)','rawAdjacentChanges',numel(ix),'rawChangeRows',ix',...
 'rawAdjacentChangeBrackets_s',[t(ix-1),t(ix)],'rawFromTo',[u(ix-1),u(ix)],...
 'sameTimestampRawChanges',sum(t(ix)==t(ix-1)),'allRowsNearDeclaredQuarterGrid',all(valid),...
 'gridLabelsDiagnosticOnly',unique(labels)','levelChangeRows',jx','levelChangeBrackets_s',[t(jx-1),t(jx)],...
 'levelFromTo',[labels(jx-1),labels(jx)],'observedLevelSequence',[labels(1);labels(jx)]',...
 'acceptedStepCertificate','UNAVAILABLE','semantics','Changes between adjacent RECORDED rows, brackets not certified accepted physical events. Grid labels never replace raw data.');
end
function c=compareCore(a,b,step,tol)
c=struct('status','NATIVE_COMPARISON_ONLY','anyExactCommonCoreContrast',false,'anyDisjointTransitionBracket',false,'anyNewRawLevel',false,...
 'sequenceDiffers',false,'acceptedEventSemantics','NOT_CERTIFIED','sampleContrastsAreDurations',false);
if isequal(a.time,b.time)
 ia=(1:numel(a.time))';ib=ia;exact=true;amb=0;
else
 [ta,sa,ga]=unique(a.time,'stable');[tb,sb,gb]=unique(b.time,'stable');
 ca=accumarray(ga,1);cb=accumarray(gb,1);
 [~,xa,xb]=intersect(ta,tb);
 valid=ca(xa)==cb(xb);amb=sum(~valid);xa=xa(valid);xb=xb(valid);
 counts=ca(xa);total=sum(counts);left=zeros(total,1);right=zeros(total,1);offset=0;
 for k=1:numel(xa)
  n=counts(k);left(offset+(1:n))=sa(xa(k))+(0:n-1);right(offset+(1:n))=sb(xb(k))+(0:n-1);offset=offset+n;
 end
 ia=left;ib=right;exact=false;
end
c.fullClockExact=exact;c.commonRecordedRows=numel(ia);c.ambiguousDuplicateGroupsExcluded=amb;
if ~isempty(ia)
 delta=b.core(ib)-a.core(ia);c.commonPointMaxAbs=max(abs(delta));c.commonPointContrasts=[a.time(ia),a.core(ia),b.core(ib)];
 c.anyExactCommonCoreContrast=any(abs(delta)>tol);
else,c.commonPointMaxAbs=[];c.commonPointContrasts=[];end
c.fullRecordedCoreBitwiseIdentity=exact&&isequal(a.core,b.core);
c.anyNewRawLevel=any(arrayfun(@(x)all(abs(a.core-x)>tol),unique(b.core)));
x=nativeTransitions(a.time,a.core,step,tol);y=nativeTransitions(b.time,b.core,step,tol);
c.baselineTransitions=x;c.caseTransitions=y;
if x.allRowsNearDeclaredQuarterGrid&&y.allRowsNearDeclaredQuarterGrid
 c.sequenceDiffers=~isequal(x.observedLevelSequence,y.observedLevelSequence);
 if ~c.sequenceDiffers&&size(x.levelChangeBrackets_s,1)==size(y.levelChangeBrackets_s,1)
  A=x.levelChangeBrackets_s;B=y.levelChangeBrackets_s;
  c.correspondingBracketOverlap=max(A(:,1),B(:,1))<=min(A(:,2),B(:,2));
  c.minimumRecordedBracketSeparation_s=max(0,max(A(:,1),B(:,1))-min(A(:,2),B(:,2)));
  c.anyDisjointTransitionBracket=any(~c.correspondingBracketOverlap);
 end
end
end
function p=postfilterFlags(d,step)
windows={[0 2400],[330 338],[2000 2400]};labels={'FULL','FIRST_SOURCE_WINDOW','SECOND_SOURCE_WINDOW'};p=struct();
for k=1:3
 w=windows{k};ix=d.t>=w(1)&d.t<=w(2);u=d.u(ix);y=d.y(ix);t=d.t(ix);
 hit=abs(y-u)>.005;changes=find(diff(u)~=0)+1;
 p.(labels{k})=struct('nativeRows',numel(t),'recordedFlaggedRows',sum(hit),'postMinusCorePeakAbs',max(abs(y-u)),...
  'recordedCoreChanges',numel(changes),'coreHeldAtNativePoints',all(u==u(1)),...
  'flaggedNativeTimes_s',t(hit),'thresholdNormalized',.005,'thresholdRole','LOCALIZATION_NOT_ACCEPTANCE',...
  'interpretation','Postfilter-core gap can include legitimate startup/command transient, numerical excursion, or unobserved event; not physical flow/power or causal thermal effect.');
end
p.normalizedFloor=step;p.acceptedEventSemantics='UNAVAILABLE';
end
function s=selectionMetadata(r,spec,ledger)
s=struct('legacyOutcomeImmutable',true,'G6_PROTOCOL_DEVIATION_PRESENT',true,...
 'JTE042Reference','B0L_LAST600_DESCENDING; C0 is a proxy only with same-frame full clock/T312 equivalence',...
 'fixedGroupsSeparateDesign',contains(spec.name,'JTE072'),'sourceSelectionMetadata','SEE_RAW_RECORD_AND_COMPLETED_JTE103_LEDGER');
if isfield(r,'selectionBasis'),s.savedBasis=r.selectionBasis;end
if isfield(r,'selectedRankLabel'),s.savedLabel=r.selectedRankLabel;end
if isfield(r,'groupSelectionTime_s'),s.savedGroupTime_s=r.groupSelectionTime_s;end
s.inheritedAuditRun=ledger.run;s.coldTieRequiresIndependentInterpretation=true;
end
function f=blankFlags(id)
f=struct('opaqueId',id,'CASE_AVAILABLE',false,'DATA_QUALIFICATION',false,'SAME_FRAME_MATCH',false,'SELECTOR_ORACLE_PASS',false,'NEGATIVE_BIAS_ONLY',false,...
 'BASELINE_CORE_FLOOR_NATIVE',false,'C1_CORE_FLOOR_NATIVE',false,'SOURCE_MATLAB_ORACLE_MATCH_AT_ARCHIVED_SAMPLES',false,...
 'CONTROL_LEVEL_CHANGE_EVIDENCE','UNAVAILABLE','CONTROL_EFFECT_RESOLVABLE','NOT_ESTABLISHED','G5_NUMERICAL_ACCEPTED',false,...
 'G6_PROTOCOL_DEVIATION_PRESENT',true,'CASE_JTE042_RANK_APPLICABLE',false,'G6_TEMPERATURE_CLAIM_AUTHORIZED',false,'DECISION','NOT_ASSESSED');
end
function d=dataDictionary()
d=struct('Ttrue','N x312 double, K, native recorded physical-model temperatures; not312 certified physical sensors',...
 'Tmeas','Same C1-state recorded measured vector, K, validated minus2K only on archived indices',...
 'E1','MATLAB native same-C1-state Max loss identity; residual inK, 8ULP data-operation budget, no novelty/closed-loop claim',...
 'E5_same_state','Actual MATLAB source arithmetic at C1 Ttrue vs C1 Tmeas; actual saved Simulink core remains threshold authority',...
 'E5_cross_trajectory','Recorded C1 vs corresponding same-frame C0 core, exact common clocks and native transition brackets; no interpolated control jumps',...
 'SAME_FRAME_MATCH','Source/load/solver/declared resolved IC parameters and initial T312 match; excludes two intervention vars only; hidden algebraic IC not certified',...
 'core','Normalized command; raw levels preserved; quarter-grid labels only8ULP diagnostics, never corrected data',...
 'postfilter','Normalized output of original1ms filter; source-window gaps not automatically physical anomalies/flow/power',...
 'transition','Change between adjacent native samples; duplicate timestamps retained; accepted-step classification absent',...
 'time_masking','E1/E2 durations/fractions NOT COMPUTED without accepted-event semantics; sample counts are not time weights or independent replicates',...
 'CONTROL_EFFECT_RESOLVABLE','Categorical native evidence only, not accepted physical event/actuation/thermal resolution',...
 'temperature_claim','E3/E4/E8 causal thermal effect NOT computed or authorized; G5 numerical acceptance remains false',...
 'G6_PROTOCOL_DEVIATION_PRESENT','Study-level inherited single-site deviation flag; CASE_JTE042_RANK_APPLICABLE=false marks separate fixed-group design, not an allegation that group ranking violated JTE042.',...
 'preregistration','JTE042 B0L last600 descending; archived C0 choice/full ascending and fixed-group design retained as deviations; no re-selection',...
 'clock_rule','No1s interpolation, no clipping/dedup, no pseudop-values or profiler dependency for archived core decision audit.');
end
function p=proposal(reports)
% Exactly one technical proposal, not a dispatch. No arbitrary new solver or severity.
p=struct('status','ONE_CONDITIONAL_VERIFICATION_NOT_RUN','hypothesis','At the first bias-associated archived core contrast, source-law same-state loss can shift a genuine controller level; causal actuation/thermal effect remains unqualified.',...
 'equations','Tm=Ttrue-2*1_S; L=max(0,min(2,max(T_S)-max(T_notS))); q=sat(0.1*(max(Tm)-ref)); u=max(.25,q-mod(q,.25)); dy/dt=1000*(u-y).',...
 'selectionRule','Use the chronologically first archived qualified contrast window, with immutable original case/group/reference and explicit JTE042 deviation; never choose the largest/favorable effect.',...
 'solver','Retain actual source ode23t/RelTol/AbsTol/IC/load as archived; an independent numerical reference must be specified and reviewed by Chat before any run.',...
 'MaxStep','Source0.05s is retained for source reproduction, not asserted sufficient for tau0.001s. No new MaxStep/reference is silently authorized. Filter-resolving MaxStep and convergence budget must be pre-registered by independent review.',...
 'IC','Same complete source initialization and physical model; initial T312/declared parameters alone do not license restart from a short window without a qualified full operating point.',...
 'acceptance','Exact injection/same-frame/source-law checks; accepted-event order/time uncertainty and stable postfilter must be qualified first. Physical temperature tolerance inK and normalized-command tolerance must be locked prospectively; existing .005 flag/8ULP budget are not physical acceptance.',...
 'cost','Zero additional simulation authorized. Forecast runtime/memory from archived wall-time/step metadata before approval; fine1ms-filter full2400 may exceed runner/storage budgets. No paid service.',...
 'stop','If accepted core contrast disappears or reference/actuation uncertainty not qualified, stop without changing severity/reference/law or inventing thermal effects.',...
 'dispatchAuthorized',false,'caseCountAudited',numel(reports));
end
function s=stepInfo(t)
dt=diff(t);p=dt(dt>0);s=struct('rows',numel(t),'duplicates',sum(dt==0),'start_s',t(1),'end_s',t(end),'maxGap_s',max(p),...
 'minPositiveGap_s',min(p),'acceptedStepCertificate','UNAVAILABLE');
end
function f=failure(e)
f=struct('identifier',e.identifier,'message',e.message);
end
function s=pass(x)
if x,s='PASS';else,s='FAIL_OR_UNQUALIFIED';end
end
function writeJSON(file,v)
h=fopen(file,'w');assert(h~=-1,'JTE106:Write','Private write failed.');fprintf(h,'%s',jsonencode(v));fclose(h);
end
