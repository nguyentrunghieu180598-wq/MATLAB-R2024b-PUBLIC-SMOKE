function sampled_gate_baseline()
% One read-only baseline feasibility map, actual MATLAB source arithmetic.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_BASELINE']);
M=jsondecode(fileread(fullfile(P,'gate_manifest.json')));law=jsondecode(fileread(fullfile(P,'source_law.json')));
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'Gate:Runtime','Pinned runtime absent.');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
reports={};pairCache=struct();pairProof={};failed={};loadSHA='';loadFilename='';primaryEligible=false;primaryUnresolved=false;
for fi=1:numel(M.references)
 spec=M.references(fi);
 try
  assert(strcmp(JTE2026sha256(fullfile(P,spec.local)),spec.sha256),'Gate:SHA','Immutable MAT changed.');
  s=load(fullfile(P,spec.local),'record');r=s.record;
  assert(strcmp(r.schema,'JTE056_NATIVE_V1')&&strcmp(r.sourceSHA256,pin)&&contains(r.matlabVersion,'24.2.0.3361896')&&...
   strcmp(r.units.temperature,'K')&&strcmp(r.units.time,'s')&&r.ambient.valueK==spec.frameK&&strcmp(r.profile,spec.profile),'Gate:Frame','Source frame differs.');
  if isempty(loadSHA),loadSHA=r.load.SHA256;loadFilename=r.load.filename;else,assert(strcmp(loadSHA,r.load.SHA256),'Gate:Load','Reference-only change must not be called a new load.');end
  t=r.signalData.jteTtrue.time_s(:);T=r.signalData.jteTtrue.values;
  assert(isa(T,'double')&&size(T,2)==312&&size(T,1)==numel(t)&&all(isfinite(T),'all')&&t(1)==0&&t(end)==2400&&all(diff(t)>=0),'Gate:Native','Invalid full native T312.');
  assert(isequal(t,r.signalData.jteUcore.time_s(:)),'Gate:Clock','Core/native clock differs.');
  if ~strcmp(spec.caseLabel,'B0L'),assert(isequal(T,r.signalData.jteTmeas.values)&&isequal(t,r.signalData.jteTmeas.time_s(:)),'Gate:C0','Not zero-bias vector.');end
  mx=max(T,[],2);u0=sourceLaw(mx,spec.frameK,law);actual=r.signalData.jteUcore.values(:);
  coreBudget=8*eps(1);nativeCoreMatch=all(abs(u0-actual)<=coreBudget);
  assert(nativeCoreMatch,'Gate:NativeLaw','Stored core/native MATLAB law mismatch.');
  n=numel(t);theta=spec.frameK+[5 7.5];delta=[2 3];budgetK=8*eps(max([1;abs(T(:))]));
  kmin=inf(n,2);chosen=zeros(n,2,'uint8');near=false(n,2);subset=false(n,312,2);faultMax=nan(n,2);uf=nan(n,2);
  valid=false(n,2);mismatch=false(n,2);best3=zeros(n,2);best3Step=false(n,2);
  top=maxk(T,4,2); % Only native vectors, no physical trajectory or re-selection of old cases.
  for di=1:2
   for ti=1:2
    th=theta(ti);eligible=mx>=th&delta(di)>mx-th;counts=sum(T>=th,2);
    pick=eligible&counts<kmin(:,di);kmin(pick,di)=counts(pick);chosen(pick,di)=ti;
    near(:,di)=near(:,di)|any(abs(T-th)<=budgetK,2)|abs(mx-delta(di)-th)<=budgetK;
   end
   for ti=1:2
    ix=chosen(:,di)==ti;subset(ix,:,di)=T(ix,:)>=theta(ti);
   end
   finite=isfinite(kmin(:,di));
   assert(all(sum(subset(:,:,di),2)==replaceInf(kmin(:,di))),'Gate:Subset','Deterministic minimal-set cardinality differs.');
   faultMax(:,di)=max(T-delta(di)*double(subset(:,:,di)),[],2);
   uf(:,di)=sourceLaw(faultMax(:,di),spec.frameK,law);
   near(:,di)=near(:,di)|any(abs(faultMax(:,di)-theta)<=budgetK,2);
   nativeStep=uf(:,di)<u0-coreBudget;
   mismatch(:,di)=finite~=nativeStep;
   % Best attainable Max after any <=3 negative faults: fault the top3.
   best3(:,di)=max(max(top(:,1:3)-delta(di),[],2),top(:,4));
   ub=sourceLaw(best3(:,di),spec.frameK,law);best3Step(:,di)=ub<u0-coreBudget;
   small=finite&kmin(:,di)<=3;
   mismatch(:,di)=mismatch(:,di)|(small~=best3Step(:,di));
   near(:,di)=near(:,di)|any(abs(best3(:,di)-theta)<=budgetK,2);
   valid(:,di)=small&~near(:,di)&~mismatch(:,di);
  end
  duplicates=find(diff(t)==0)+1;duplicateTExact=isempty(duplicates)||isequal(T(duplicates,:),T(duplicates-1,:));
  rank=struct('source','B0L only, no C0 substitute or active B0L invented','status','NOT_APPLICABLE_C0','qualifiedConfirmatory',false);
  if strcmp(spec.caseLabel,'B0L')
   rank=tailRank(t,T,duplicateTExact,spec.sha256);
   cache=struct('time',t,'T',T,'kmin',kmin,'rank',rank);pairCache.(spec.profile)=cache;
  elseif spec.frameK==300
   assert(isfield(pairCache,spec.profile),'Gate:Pair','Missing matching B0L.');
   b=pairCache.(spec.profile);
   same=isequal(b.time,t)&&isequal(b.T,T);
   assert(same&&isequal(b.kmin,kmin),'Gate:Pair','Prior full native B0L/C0 equivalence not reproduced for this map.');
   pairProof{end+1}=struct('profile',spec.profile,'fullNativeClockT312Exact',same,'kminExact',true); %#ok<AGROW>
   pairCache=rmfield(pairCache,spec.profile);
  end
  rows=table((1:n)',t,mx,actual,u0,kmin(:,1),kmin(:,2),chosen(:,1),chosen(:,2),near(:,1),near(:,2),...
   mismatch(:,1),mismatch(:,2),valid(:,1),valid(:,2),best3Step(:,1),best3Step(:,2),...
   'VariableNames',{'row1','nativeTime_s','MaxT_K','recordedCore','nativeMATLABCore','kmin2','kmin3','thresholdIndex2','thresholdIndex3',...
   'nearBoundary2','nearBoundary3','nativeMismatch2','nativeMismatch3','qualifiedSmallSet2','qualifiedSmallSet3','best3NativeStep2','best3NativeStep3'});
  stem=[pre '_' spec.caseLabel '_' spec.profile];
  writetable(rows,[stem '_ROWS.csv']);
  save([stem '_SETS.mat'],'t','theta','delta','kmin','chosen','subset','near','mismatch','valid','faultMax','uf','best3','best3Step','-v7.3');
  flags=struct('FRAME_K',spec.frameK,'PROFILE',spec.profile,'CASE_DESIGN','SOURCE_BASELINE_EXPLORATORY',...
   'NATIVE_DATA_QUALIFIED',true,'NATIVE_CORE_MATCH',nativeCoreMatch,'ELIGIBLE_SUBSET_LE1',any(valid&kmin<=1,'all'),...
   'ELIGIBLE_SUBSET_LE3',any(valid,'all'),'NEAR_THRESHOLD_PRESENT',any(near,'all'),...
   'NEAR_THRESHOLD_UNRESOLVED',any(near&(isfinite(kmin)|best3Step),'all')||any(mismatch,'all'),...
   'ALL_KMIN_GT3_OR_INF',all(kmin>3,'all'),'SOURCE_G5_THERMAL_ACCEPTED',false);
  rep=struct('archive',spec,'caseName',r.caseName,'sourceSHA',r.sourceSHA256,'generatedModelSHA',r.generatedModelSHA256,...
   'loadSHA',r.load.SHA256,'controllerReferenceK',spec.frameK,'solver',r.solver,'units',r.units,'flags',flags,...
   'nativeRows',n,'duplicateRows',numel(duplicates),'duplicateT312Exact',duplicateTExact,'nativeCoreBitwise',isequal(u0,actual),...
   'roundoffProximityBudget_K',budgetK,'budgetRole','Localize FP boundaries only; never sensor/physical/solver tolerance',...
   'rank',rank,'rowsFile',[stem '_ROWS.csv'],'setsFile',[stem '_SETS.mat'],...
   'setEncoding','subset(row,channel,deltaIndex) logical gives every deterministic minimal set; chosen0/kminInf means none.',...
   'timeSemantics','Stored native row presence only. No duration, time fraction, accepted solver state or thermal truth claim.');
  reports{end+1}=rep; %#ok<AGROW>
  if spec.frameK==300,primaryEligible=primaryEligible||flags.ELIGIBLE_SUBSET_LE3;primaryUnresolved=primaryUnresolved||flags.NEAR_THRESHOLD_UNRESOLVED;end
  fprintf('BASELINE_FEASIBILITY_FLAGS frame=%g profile=%s eligibleLE3=%d unresolved=%d batteryRun=0 G5_ACCEPTED=false\n',spec.frameK,spec.profile,flags.ELIGIBLE_SUBSET_LE3,flags.NEAR_THRESHOLD_UNRESOLVED);
  clear s r T rows subset cache b
 catch ME
  failed{end+1}=struct('case',spec.caseLabel,'profile',spec.profile,'identifier',ME.identifier,'message',ME.message); %#ok<AGROW>
 end
end
decision='HOLD_INCOMPLETE_OR_BOUNDARY_UNRESOLVED';
if isempty(failed)&&~primaryUnresolved
 if primaryEligible,decision='BASELINE_ONLY_POTENTIAL_WITH_PROSPECTIVE_AMENDMENT';
 else,decision='NO_ELIGIBLE_SMALL_GROUP_IN_CURRENT_BASELINE';end
end
proposal=struct('status','NOT_PROPOSED_PENDING_PRIMARY_MAP');
if strcmp(decision,'NO_ELIGIBLE_SMALL_GROUP_IN_CURRENT_BASELINE'),proposal=oneSourceLoadProposal(loadFilename,loadSHA);end
out=struct('schema','BTMS_TOY_AND_BASELINE_FEASIBILITY_NOT_G5','run',getenv('GITHUB_RUN_ID'),'commit',getenv('GITHUB_SHA'),...
 'runtime',version,'references',{reports},'pairProof',{pairProof},'failures',{failed},'decision',decision,...
 'sourceLawCertificateReused',law,'primaryFrameK',300,'supplementaryFrameK',293.15,...
 'activeReferenceIsSecondPhysicalLoad',false,'activeB0L','UNAVAILABLE_NOT_FABRICATED','sourceG5ThermalAccepted',false,...
 'oneLoadProposal',proposal,'oldC1CasesRead',false,'newPhysicalSimulation',false,'allSelectionsExploratory',true,...
 'nextStep','No current-load fault run if no small group. Any sampled baseline or load amendment needs independent/owner approval; no plan dispatch.');
save([pre '_LEDGER.mat'],'out','-v7.3');writeJSON([pre '_LEDGER.json'],out);
writeJSON([pre '_FLAGS.json'],struct('decision',decision,'SOURCE_G5_THERMAL_ACCEPTED',false,'PHYSICAL_RUN',false,'G5_ACCEPTED',false));
end
function y=replaceInf(x)
y=x;y(~isfinite(y))=0;
end
function u=sourceLaw(mx,ref,law)
q=law.gain*(mx-ref);q=min(law.upper,max(law.lower,q));u=max(law.step,q-mod(q,law.step));
end
function q=tailRank(t,T,dupExact,sha)
q=struct('status','BLOCKED_NATIVE_DUPLICATE_T312_CONFLICT','qualifiedConfirmatory',false,'baselineFileSHA',sha,...
 'window_s',[1800 2400],'N',312,'tiePolicy','Descending mean then ascending channel index; hot1,middle156,cold312',...
 'selectionCodeSHA',JTE2026sha256(which('sampled_gate_baseline')),'sourceG5ThermalAccepted',false);
if ~dupExact,return;end
ix=t>=1800;tt=t(ix);Y=T(ix,:);q.boundaryNativeExact=tt(1)==1800;
if tt(1)>1800
 l=find(t<1800,1,'last');h=l+1;w=(1800-t(l))/(t(h)-t(l));v=T(l,:)+w*(T(h,:)-T(l,:));
 tt=[1800;tt];Y=[v;Y];q.boundaryRule='ONE explicitly provisional piecewise-linear temperature boundary, no command interpolation';
else,q.boundaryRule='Native boundary, all duplicate rows retained';end
means=trapz(tt,Y,1)/600;ordered=sortrows([-means(:),(1:312)'],[1 2]);
q.status='EXPLORATORY_PIECEWISE_LINEAR_RANK_NOT_CONFIRMATORY_G5';q.mean_K=means;
q.descendingChannelIds=ordered(:,2);q.hot=ordered(1,2);q.middle=ordered(156,2);q.cold=ordered(end,2);
q.limit='Identical duplicate T rows have zero-width panels and remain intact. Linear-between-record reconstruction is explicit; source G5/continuous-time physical validity unqualified, so not exact confirmatory protocol reproduction.';
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'Gate:Write','Private file write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end

function q=oneSourceLoadProposal(name,sha)
% ONE proposal from the existing current trace; no new file/model/run generated.
q=struct('status','UNAVAILABLE_SOURCE_GROUNDED_SECOND_REGIME','physicalRunAuthorized',false);
try
 p=fullfile(pwd,'vendor-pack','Scripts_Data',name);assert(isfile(p)&&strcmp(JTE2026sha256(p),sha),'Gate:Input','Load source pin differs.');
 s=load(p);keys=fieldnames(s);candidates={};
 for k=1:numel(keys)
  a=s.(keys{k});
  if isa(a,'double')&&ismatrix(a)&&size(a,1)==2&&size(a,2)>2&&all(isfinite(a),'all')&&all(diff(a(1,:))>0)
   candidates{end+1}=a; %#ok<AGROW>
  end
 end
 assert(numel(candidates)==1,'Gate:Input','Unique source FromFile time/current matrix not established.');
 a=candidates{1};t=a(1,:)';I=a(2,:)';H=340;starts=t(t+H<=t(end));assert(~isempty(starts),'Gate:Input','No source340s segment.');
 rms=zeros(size(starts));
 for k=1:numel(starts)
  tt=[starts(k);t(t>starts(k)&t<starts(k)+H);starts(k)+H];v=interp1(t,I,tt,'linear');
  d=diff(tt);rms(k)=sqrt(sum(d.*(v(1:end-1).^2+v(1:end-1).*v(2:end)+v(2:end).^2)/3)/H);
 end
 [best,k]=max(rms);first=starts(k);
 q=struct('status','ONE_SOURCE_CURRENT_SEGMENT_PROPOSAL_OWNER_REVIEW_REQUIRED','rule',...
  'Highest RMS340s contiguous segment of unchanged pinned current trace under explicit piecewise-linear input convention; exact ties earliest native start. No thermal/bias result used.',...
  'sourceLoadSHA',sha,'sourceStart_s',first,'sourceStop_s',first+H,'horizon_s',H,'sourceRMS_A',best,...
  'requestedInput','I_new(t)=I_source(t+sourceStart),0<=t<=340. Source values/polarity retained; only operating-load phase differs.',...
  'scope','One source-grounded demand candidate, NOT a validated operating/safe regime or guaranteed controller activation.',...
  'unchanged','Physical pack, original thermal/electrical parameters, controller reference, SOC/T initialization; sampled actuator method awaits separate approval.',...
  'beforeAnyRun',{{'Confirm actual FromFile interpolation and current polarity','Screen voltage/SOC/charge and source lookup domains; no rated-current certification invented',...
   'Independently preregister this one regime and numerical/logging plan, then owner approval','No current-load C0/C1 expenditure when map shows no eligible subset'}},...
  'noAlternativeSearch',true,'physicalRunAuthorized',false);
catch ME,q.reason=struct('identifier',ME.identifier,'message',ME.message);end
end
