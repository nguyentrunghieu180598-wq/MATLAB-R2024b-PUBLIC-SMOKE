function sampled_gate_load_only()
% Only inspect the pinned PUBLIC input MAT; never re-read study MAT or simulate.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_SOURCE_LOAD']);
L=jsondecode(fileread(fullfile(P,'prior_baseline_ledger.json')));first=L.references(1);sha=first.loadSHA;
p=fullfile(pwd,'vendor-pack','Scripts_Data','Battery_Pack_Thermal_Management_Ivst.mat');
q=struct('status','UNAVAILABLE_SOURCE_GROUNDED_SECOND_REGIME','physicalRunAuthorized',false,'priorBaselineReused',true);
try
 assert(isfile(p)&&strcmp(JTE2026sha256(p),sha),'Gate:Input','Pinned public input does not match archived load.');
 info=whos('-file',p);q.variables=info;s=load(p);keys=fieldnames(s);candidates={};labels={};
 for j=1:numel(keys)
  a=s.(keys{j});enc='';
  if isa(a,'timeseries')&&isvector(a.Data),v=[a.Time(:),a.Data(:)];enc='TIMESERIES';
  elseif isa(a,'double')&&ismatrix(a)&&size(a,2)==2&&size(a,1)>2,v=a;enc='N_BY_2';
  elseif isa(a,'double')&&ismatrix(a)&&size(a,1)==2&&size(a,2)>2,v=a';enc='2_BY_N';
  else,continue;end
  if all(isfinite(v),'all')&&v(1,1)==0&&all(diff(v(:,1))>=0)&&v(end,1)>=340
   candidates{end+1}=v;labels{end+1}=[keys{j} ':' enc]; %#ok<AGROW>
  end
 end
 assert(numel(candidates)==1,'Gate:Input','Unique explicit time/current encoding not established.');
 v=candidates{1};t=v(:,1);I=v(:,2);H=340;starts=unique(t(t+H<=t(end)),'stable');rms=zeros(size(starts));
 for k=1:numel(starts)
  lo=starts(k);hi=lo+H;ix=t>=lo&t<=hi;tt=t(ix);ii=I(ix);
  if tt(end)<hi
   a=find(t<hi,1,'last');b=a+1;w=(hi-t(a))/(t(b)-t(a));tt(end+1)=hi;ii(end+1)=I(a)+w*(I(b)-I(a));
  end
  dt=diff(tt);rms(k)=sqrt(sum(dt.*(ii(1:end-1).^2+ii(1:end-1).*ii(2:end)+ii(2:end).^2)/3)/H);
 end
 [best,k]=max(rms);sourceStart=starts(k);
 q.status='ONE_SOURCE_CURRENT_SEGMENT_PROPOSAL_OWNER_REVIEW_REQUIRED';q.encoding=labels{1};q.sourceLoadSHA=sha;
 q.sourceStart_s=sourceStart;q.sourceStop_s=sourceStart+H;q.horizon_s=H;q.sourceRMS_A=best;
 q.rule='Highest RMS340s contiguous segment of the pinned input, exact ties earliest native start; source piecewise-linear panels and zero-width jumps retained. No bias/thermal outcome selection.';
 q.requestedInput='I_new(t)=I_source(t+sourceStart),0<=t<=340; unchanged source current values/polarity, no amplitude sweep.';
 q.scope='One source-grounded demand-phase candidate, NOT validated hardware/operating envelope or guaranteed command activation.';
 q.beforeAnyRun={'Confirm source FromFile interpolation and physical polarity','Screen SOC/voltage/charge and lookup/rated-domain limits; do not invent hardware ratings',...
  'Owner/scientific approval of this one load proposal, sampled method, units, fixed-Ts numerics and minimal logger/resources'};
 q.oldUnavailabilityPreserved=true;q.noAlternativeSearch=true;
catch ME,q.reason=struct('identifier',ME.identifier,'message',ME.message);
end
save([pre '_INSPECTION.mat'],'q','-v7.3');h=fopen([pre '_PROPOSAL.json'],'w');fprintf(h,'%s',jsonencode(q));fclose(h);
fprintf('PINNED_PUBLIC_INPUT_REVIEW status=%s baselineRerun=0 batteryRun=0 G5_ACCEPTED=false\n',q.status);
end
