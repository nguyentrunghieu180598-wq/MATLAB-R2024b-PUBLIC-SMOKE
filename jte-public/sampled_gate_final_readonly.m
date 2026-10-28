function sampled_gate_final_readonly()
% No sim, simulation, stepping or source project/model initialization.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_FINAL_READONLY']);
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'Gate:Runtime','Pinned runtime unavailable.');
r=struct('run',getenv('GITHUB_RUN_ID'),'commit',getenv('GITHUB_SHA'),'runtime',version,'newToyRun',false,'baselineRepeated',false,'batteryRun',false,'G5Accepted',false);
f=fullfile(P,'SavedToy.slx');sha=JTE2026sha256(f);m='SavedToy';
r.existingToyCompile=struct('status','UNAVAILABLE','causes',[]);
try
 load_system(f);
 feval(m,[],[],[],'compile');
 feval(m,[],[],[],'term');
 r.existingToyCompile.status='COMPILE_ONLY_SUCCEEDED_DYNAMIC_TOY_STILL_UNQUALIFIED';
catch ME
 r.existingToyCompile.status='COMPILE_FAILURE_REPRODUCED';
 r.existingToyCompile.causes=causes(ME);
 r.existingToyCompile.fullReport=getReport(ME,'extended','hyperlinks','off');
 try,feval(m,[],[],[],'term');catch,end
end
try,close_system(m,0);catch,end
assert(strcmp(JTE2026sha256(f),sha),'Gate:Immutable','Saved toy artifact bytes changed.');
r.existingToyCompile.sourceArtifactSHA=sha;
try,r.oneLoadProposal=boundedInput(P);catch ME,r.oneLoadProposal=struct('status','UNAVAILABLE_SOURCE_GROUNDED_SECOND_REGIME','causes',causes(ME));end
save([pre '_RECORD.mat'],'r','-v7.3');writeJSON([pre '_RESULT.json'],r);
fprintf('BTMS_FINAL_READONLY_RESULT existingToyCompile=%s inputStatus=%s newToy=0 baselineRerun=0 batteryRun=0 G5_ACCEPTED=false\n',r.existingToyCompile.status,r.oneLoadProposal.status);
end
function q=boundedInput(P)
L=jsondecode(fileread(fullfile(P,'prior_baseline_ledger.json')));a=L.references(1);sha=a.loadSHA;
file=fullfile(pwd,'vendor-pack','Scripts_Data','Battery_Pack_Thermal_Management_Ivst.mat');
assert(strcmp(JTE2026sha256(file),sha),'Gate:Input','Pinned public load differs from archived source.');
info=whos('-file',file);S=load(file);keys=fieldnames(S);V={};names={};
for k=1:numel(keys)
 a=S.(keys{k});
 if isa(a,'timeseries')&&isvector(a.Data),v=[a.Time(:),a.Data(:)];enc='TIMESERIES';
 elseif isa(a,'double')&&ismatrix(a)&&size(a,2)==2&&size(a,1)>2,v=a;enc='N_BY_2';
 elseif isa(a,'double')&&ismatrix(a)&&size(a,1)==2&&size(a,2)>2,v=a';enc='2_BY_N';
 else,continue;end
 if v(1,1)==0&&all(isfinite(v),'all')&&all(diff(v(:,1))>=0)&&v(end,1)>=340
  V{end+1}=v;names{end+1}=[keys{k} ':' enc]; %#ok<AGROW>
 end
end
q=struct('status','UNAVAILABLE_SOURCE_GROUNDED_SECOND_REGIME','variables',info,'physicalRunAuthorized',false,'baselineReused',true);
assert(numel(V)==1,'Gate:Input','Unique explicit source time/current encoding absent.');
v=V{1};q.encoding=names{1};q.sourceRows=size(v,1);assert(size(v,1)<=1e7,'Gate:Resource','Public input exceeds fixed ten-million-row analysis cap.');
t=v(:,1);I=v(:,2);dt=diff(t);ix=find(dt>0);
assert(~isempty(ix),'Gate:Input','No positive-width input panels.');
t0=t(ix);t1=t(ix+1);i0=I(ix);i1=I(ix+1);h=t1-t0;
panelArea=h.*(i0.^2+i0.*i1+i1.^2)/3;
cum=[0;cumsum(panelArea)];edges=[t0;t1(end)];
starts=t0(t0+340<=t(end));assert(~isempty(starts),'Gate:Input','No complete340s source segment.');
score=(primitive(starts+340)-primitive(starts))/340;
assert(all(isfinite(score))&&all(score>=0),'Gate:Integral','Input energy integral invalid.');
[val,k]=max(score);first=starts(k);
q.sourceLoadSHA=sha;q.sourceStart_s=first;q.sourceStop_s=first+340;q.horizon_s=340;q.sourceRMS_A=sqrt(val);
q.computation='Positive-width original piecewise-linear panels; cumulative exact-panel I^2 integrals, vector binary-search queries; zero-width jumps retained in source, no quadratic rescan.';
q.rule='Highest computed RMS340s segment; exact score ties earliest native start. No thermal or biased-case selection.';
if first==0,q.status='NO_DISTINCT_SECOND_SOURCE_SEGMENT_UNDER_FROZEN_RULE';
else,q.status='ONE_SOURCE_CURRENT_SEGMENT_PROPOSAL_OWNER_REVIEW_REQUIRED';end
q.requestedInput='I_new(t)=I_source(t+sourceStart),0<=t<=340; same source current amplitude/polarity, changed demand phase only.';
q.limits={'Candidate only, no guaranteed controller activation or hardware operating-envelope validation',...
 'Confirm actual FromFile interpolation/polarity and check SOC/voltage/charge/lookup/rated-domain limits',...
 'Method/Ts/flow-unit/minimal logger/resource and independent numerical approvals still required; no physical dispatch',...
 'All original baseline and unsuccessful toy evidence remain immutable; source G5 not accepted'};
 function z=primitive(x)
  bins=discretize(x,edges);assert(all(~isnan(bins)),'Gate:Integral','Query outside input panels.');
  dx=x-t0(bins);slope=(i1(bins)-i0(bins))./h(bins);
  z=cum(bins)+i0(bins).^2.*dx+i0(bins).*slope.*dx.^2+slope.^2.*dx.^3/3;
 end
end
function c=causes(e)
c=struct('identifier',e.identifier,'message',e.message,'stack',{e.stack},'children',[]);
a=cell(size(e.cause));for k=1:numel(a),a{k}=causes(e.cause{k});end;c.children=a;
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'Gate:Write','Private file write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
