function JTE116_oneApprovedPlant()
% Exactly ONE owner-approved guarded025 initialization/trajectory. No retry.
root=pwd;priv=fullfile(root,'jte116-one-private');prefix=fullfile(priv,['JTE116ONE_' getenv('GITHUB_RUN_ID') '_PLANT']);
gm='JTE116Guarded';guard=fullfile(priv,[gm '.slx']);original=fullfile(priv,'JTE101Original.slx');
vendor=fullfile(root,'vendor-pack');pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
S=[];out=[];project=[];trace=struct([]);entered=false;begun=false;finished=false;stage='RESOURCE';
flags=struct('DECISION','UNQUALIFIED_LOGGING_OR_RESOURCE','SOURCE_PARITY',false,'T0_SAVED_STATE_PARITY',false,...
 'ACCEPTED_MAJOR_PROVENANCE','UNAVAILABLE','PHYSICAL_ATTEMPT_ENTERED',false,'TIME_ADVANCEMENT_ENTERED',false,...
 'HORIZON_340_COMPLETE',false,'FIRST_WINDOW_NATIVE_EXCURSION','UNAVAILABLE','FIRST_WINDOW_MAJOR_EXCURSION','UNAVAILABLE',...
 'SECOND_EVENT_NOT_COVERED_340',true,'G5_ACCEPTED',false);
r=struct('run',getenv('GITHUB_RUN_ID'),'commit',getenv('GITHUB_SHA'),'scope','One owner-approved exploratory event-topology diagnostic, not G5',...
 'scientificComment','PR61#issuecomment-6461303109','originalReferenceRun','40449421507','G5_ACCEPTED',false);
try
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for k=1:numel(M.files),z=M.files(k);assert(strcmp(JTE2026sha256(fullfile(priv,z.local)),z.sha256),'JTE116:ModelIC','Input SHA changed.');end
 assert(M.ownerAuthorization.exactlyOne&&~M.resource.paidServices&&M.resource.repositoryPublicVerifiedFromGithubEvent,...
  'JTE116:Resource','Owner/free resource qualification absent.');
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE116:Resource','Pinned runtime unavailable.');
 [ok,~]=license('checkout','Simulink');assert(ok,'JTE116:Resource','Included Simulink license unavailable.');
 toy=jsondecode(fileread(fullfile(priv,['JTE116ONE_' getenv('GITHUB_RUN_ID') '_TOY_FLAGS.json'])));
 assert(toy.LOGGER_QUALIFIED,'JTE116:Logging','Same-run documented logger toy not qualified.');
 r.runtime=version;r.resourceEntitlement=M.resource;
 stage='SOURCE';
 P=load(fullfile(priv,'prepared.mat'),'rec','before','after','proof');p=P.rec.prepared;
 f=jsondecode(fileread(fullfile(priv,'static_flags.json')));
 assert(f.CANARY_BITWISE_PASS&&f.STATIC_MODEL_PARITY&&f.COMPILED_DOUBLE&&f.CONVERTER_TOPOLOGY_AUDIT_COMPLETE,...
  'JTE116:ModelIC','Prior source/canary/static gates absent.');
 assert(strcmp(JTE2026sha256(guard),p.guardModelSHA)&&strcmp(JTE2026sha256(original),p.originalModelSHA)&&...
  strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
  'JTE116:ModelIC','Source or prepared guard pin changed.');
 O=load(fullfile(priv,'original_raw.mat'),'record');o=O.record;
 assert(strcmp(o.schema,'JTE101_TF_340_RAW_NOT_G5')&&strcmp(o.role,'ORIGINAL340')&&o.qualification.qualified&&o.observed.initialStateMapAvailable&&strcmp(o.sourceSHA256,pin)&&...
  strcmp(o.modelSHA256,p.originalModelSHA),'JTE116:ModelIC','Original saved comparator unqualified.');
 ref=struct('initialMap',o.observed.initialStateMap,'T0',o.observed.trueTemperature(1,:),'x0',o.observed.state(1),...
  'y0',o.observed.output(1),'C',o.calibration.C,'loadSHA',o.prepared.loadSHA256,...
  'workspaceSHA',o.prepared.workspaceSHA256,'modelSHA',o.modelSHA256,'nativeRows',numel(o.observed.outputTime));
 baseline=struct('time',o.observed.outputTime,'output',o.observed.output,'core',o.observed.core,...
  'T312',o.observed.trueTemperature,'trueTime',o.observed.trueTime,'acceptedStepCertification',o.observed.acceptedStepCertification);
 clear O o
 project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
 W=load(fullfile(priv,'source_workspace.mat'),'workspaceSnapshot');
 assert(strcmp(JTE2026sha256(fullfile(priv,'source_workspace.mat')),ref.workspaceSHA),'JTE116:ModelIC','Frozen workspace hash mismatch.');
 names=fieldnames(W.workspaceSnapshot);
 for k=1:numel(names),value=W.workspaceSnapshot.(names{k});assignin('base',names{k},value);
  assert(isequaln(evalin('base',names{k}),value),'JTE116:ModelIC','Source workspace differs.');end
 clear W value
 load_system(guard);verifySource(gm,ref);
 stepPath=[gm '/Battery Control/FlwR_calc/Step Change'];
 audit=JTE096_modelAudit(gm,{[stepPath '/JTE115 guard constant'],[stepPath '/JTE115 q guard']});
 assert(isequal(audit,P.after),'JTE116:ModelIC','Full prepared graph/config proof changed before observers.');
 c=JTE116_converterAudit(gm);assert(c.discoveryComplete,'JTE116:ModelIC','Converter topology unavailable.');
 assert(slResolve(get_param([stepPath '/JTE115 guard constant'],'Value'),[stepPath '/JTE115 guard constant'])==.25,...
  'JTE116:ModelIC','Guard constant changed.');
 tf=[gm '/Battery Control/sensor dynamics 1'];ph=get_param(tf,'PortHandles');
 mark(source(ph.Inport(1)),'JTE116ActualInput');mark(ph.Outport(1),'JTE116Postfilter');
 gh=get_param([stepPath '/JTE115 q guard'],'PortHandles');mark(source(gh.Inport(1)),'JTE116Q');mark(gh.Outport(1),'JTE116QStar');
 blocks=find_system(gm,'BlockType','ToWorkspace');ix=[];
 for k=1:numel(blocks),if strcmp(get_param(blocks{k},'VariableName'),'jteTtrue'),ix(end+1)=k;end;end %#ok<AGROW>
 assert(numel(ix)==1,'JTE116:Logging','Unique true T312 source unavailable.');
 th=get_param(blocks{ix},'PortHandles');mark(source(th.Inport(1)),'JTE116T312');
 afterObserve=JTE096_modelAudit(gm,{[stepPath '/JTE115 guard constant'],[stepPath '/JTE115 q guard']});
 assert(isequal(audit,afterObserve),'JTE116:ModelIC','Observer changed a block/config/edge.');
 save_system(gm,guard);r.loggedModelSHA=JTE2026sha256(guard);copyfile(guard,[prefix '_LOGGED_MODEL.slx']);
 r.frozenGuardModelSHA=p.guardModelSHA;r.observerScope='Only logging metadata on existing source ports. Actual input/core share one validated physical source port; final native ToWorkspace core compared independently.';
 stage='RESOURCE';width=0;for k=1:numel(ref.initialMap),width=width+numel(ref.initialMap(k).value);end
 maxRows=max(20000,ceil(3*ref.nativeRows));numericBytes=double(maxRows)*8*(double(width)+2*312+32);
 reserve=3*numericBytes;rawBound=2*numericBytes;
 [avail,total]=ram();disk=java.io.File(priv);free=double(disk.getUsableSpace());
 assert(rawBound<3*1024^3&&avail>reserve+2*1024^3&&free>max(4*1024^3,2*rawBound)&&M.resource.drive.availableBytes>rawBound+1024^3,...
  'JTE116:Resource','Conservative log/RAM/disk/private-file reserve insufficient.');
 elapsedSetup=posixtime(datetime('now','TimeZone','UTC'))-M.resource.preflightUnixEpoch;
 assert(M.resource.jobLimit_s-elapsedSetup>1200+300,'JTE116:Resource','Remaining job time cannot cover the one trajectory and private delivery.');
 r.resourcePreflight=struct('availableRAM_bytes',avail,'totalRAM_bytes',total,'diskFree_bytes',free,...
  'savedStateWidth',width,'maxNativeRows',maxRows,'numericLoggingReserve_bytes',reserve,'plannedRawBound_bytes',rawBound,...
  'wallStop_s',1200,'scope','Conservative three-copy numeric plan, not a measured candidate peak. Stop rather than tune or pay.');
 r.reference=ref;r.baselineNative=baseline;r.beforeObserverAudit=audit;r.converterAudit=c;
 marker=fullfile(priv,'APPROVED_GUARD025_ATTEMPT_ENTERED.json');
 assert(~isfile(marker),'JTE116:Resource','One attempt already entered.');
 writeJSON(marker,struct('run',getenv('GITHUB_RUN_ID'),'phase','ONE_OWNER_APPROVED_INITIALIZATION','retryAuthorized',false));
 entered=true;flags.PHYSICAL_ATTEMPT_ENTERED=true;stage='INITIALIZE';
 S=simulation(gm);S=setModelParameter(S,'StartTime','0','StopTime','340','SimulationMode','normal',...
  'SaveState','on','StateSaveName','jte116States','SaveFormat','Dataset','SaveTime','on','TimeSaveName','tout',...
  'SignalLogging','on','SignalLoggingName','jte116Signals','ReturnWorkspaceOutputs','on');
 initialize(S);
 verifySource(gm,ref);assert(strcmp(get_param(gm,'Refine'),'1'),'JTE116:Logging','Source refinement is not1.');
 current=JTE096_modelAudit(gm,{[stepPath '/JTE115 guard constant'],[stepPath '/JTE115 q guard']});
 assert(isequal(current.blocks,audit.blocks)&&isequal(current.connectivity,audit.connectivity),...
  'JTE116:ModelIC','Runtime changed retained blocks or graph.');
 c2=JTE116_converterAudit(gm);assert(isequal(c,c2),'JTE116:ModelIC','Runtime converter config changed.');
 r.effectiveRuntimeConfig=current.config;
 [avail,~]=ram();assert(avail>reserve+2*1024^3,'JTE116:Resource','Initialized RAM reserve insufficient.');
 r.preTimeAdvanceSavedICAvailable=false;
 try
  pre=JTE116_completedMajor(S,0,tf);preMap=JTE116_savedStateMap(S.SimulationOutput.get('jte116States'),gm);
  r.preTimeAdvanceSavedICAvailable=true;
 catch
  r.preTimeAdvanceICScope='Initialized output inaccessible/uncomputed. Qualify first completed major0 before processing later major hits; not claimed pre-step.';
 end
 if r.preTimeAdvanceSavedICAvailable
  assert(JTE116_sameStateMap(ref.initialMap,preMap)&&isequal(pre.T312,ref.T0)&&pre.x==ref.x0&&pre.y==ref.y0,...
   'JTE116:ModelIC','Initialized t0 state differs; no time advancement.');
 end
 stage='INITIAL_MAJOR0';expected=S.Time;assert(expected==0,'JTE116:Logging','Initial major is not0.');
 begun=true;flags.TIME_ADVANCEMENT_ENTERED=true;timer=tic;finished=step(S);
 q=JTE116_completedMajor(S,expected,tf);q.phase='COMPLETED_INITIAL_MAJOR0';trace=q;
 initialMap=JTE116_savedStateMap(S.SimulationOutput.get('jte116States'),gm);
 assert(JTE116_sameStateMap(ref.initialMap,initialMap)&&isequal(q.T312,ref.T0)&&q.x==ref.x0&&q.y==ref.y0,...
  'JTE116:ModelIC','Entire saved t0 state map/T312/filter state differs; stop before further major steps.');
 checkLaw(q);flags.T0_SAVED_STATE_PARITY=true;flags.SOURCE_PARITY=true;
 r.initialParityScope='Exact full SAVED Dataset t0 map/T312/TF x0/y0 at first completed major0; unrepresented algebraic variables not independently certified.';
 save([prefix '_T0_CHECKPOINT.mat'],'initialMap','q','-v7.3');
 stage='TRAJECTORY';assert(~finished,'JTE116:Logging','Unexpected final initial step.');
 finished=step(S,PauseTime=330); % Same trajectory, no restart/comparator rerun.
 assert(S.Time>=330,'JTE116:Logging','Bulk pause failed to reach window.');
 while ~finished&&S.Time<=338
  assert(toc(timer)<1200,'JTE116:Resource','One-shot wall budget exhausted.');
  [avail,~]=ram();assert(avail>1024^3,'JTE116:Resource','RAM headroom exhausted.');
  expected=S.Time;finished=step(S);q=JTE116_completedMajor(S,expected,tf);q.phase='COMPLETED_FIRST_WINDOW_MAJOR';checkLaw(q);
  trace(end+1)=q; %#ok<AGROW>
  tmp=S.SimulationOutput;assert(numel(tmp.get('tout'))<=maxRows,'JTE116:Resource','Native-row reserve cap reached.');clear tmp
  if mod(numel(trace),200)==0,save([prefix '_CHECKPOINTS.mat'],'trace','-v7.3');end
 end
 assert(any([trace.time]>=330&[trace.time]<=334)&&any([trace.time]>334&[trace.time]<=338),...
  'JTE116:Logging','Completed major checkpoints do not cover both first-window/control intervals.');
 if ~finished,finished=step(S,PauseTime=340);end
 if ~finished,expected=S.Time;finished=step(S);q=JTE116_completedMajor(S,expected,tf);q.phase='COMPLETED_FINAL_MAJOR';checkLaw(q);trace(end+1)=q;end
 assert(finished,'JTE116:Logging','No completed final step.');
 out=stop(S);r.elapsedWall_s=toc(timer);r.simulationOutput=out;r.checkpoints=trace;save([prefix '_RAW.mat'],'r','-v7.3');
 stage='QUALIFICATION';d=JTE116_nativeData(out,tf,gm);
 assert(d.time(1)==0&&d.time(end)==340&&size(d.T312,2)==312&&d.clocksExact,'JTE116:Logging','Native horizon/vector/clocks unqualified.');
 flags.HORIZON_340_COMPLETE=true;
 assert(isequal(d.actualInput,d.core)&&isequal(d.loggedOutput,d.output)&&isequal(d.loggedT312,d.T312),...
  'JTE116:ModelIC','Independent native signal representations differ.');
 assert(JTE116_sameStateMap(ref.initialMap,d.initialMap)&&isequal(d.T312(1,:),ref.T0)&&d.state(1)==ref.x0&&d.output(1)==ref.y0,...
  'JTE116:ModelIC','Final saved initial-state proof differs.');
 checkNativeLaw(d);
 assert(all(abs(d.output-ref.C*d.state)<=1e-9)&&all(abs([trace.y]'-ref.C*[trace.x]')<=1e-9),...
  'JTE116:Logging','Source-calibrated TF state/output residual exceeds the inherited local identity criterion.');
 assert(strcmp(JTE2026sha256(original),ref.modelSHA)&&strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),...
  'JTE116:ModelIC','Original/vendor bytes changed.');
 flags.ACCEPTED_MAJOR_PROVENANCE='DOCUMENTED_COMPLETED_MAJOR_CHECKPOINTS_FIRST_WINDOW';
 e=JTE116_conditionalEnvelope(d.time,d.output,ref.y0);te=[trace.time]';ce=JTE116_conditionalEnvelope(te,[trace.y]',ref.y0);
 first=d.time>=330&d.time<=338;control=d.time>=330&d.time<=334;
 cm=te>=330&te<=338;cc=te>=330&te<=334;gap=abs(d.output-d.core);cg=abs([trace.y]'-[trace.core]');
 nExc=any(gap(first)>.005);aExc=any(cg(cm)>.005);
 flags.FIRST_WINDOW_NATIVE_EXCURSION=nExc;flags.FIRST_WINDOW_MAJOR_EXCURSION=aExc;
 r.windowSummary=struct('nativeFirstLocalizationExcursion',nExc,'majorFirstLocalizationExcursion',aExc,...
  'nativeFirstEnvelopeFlag',any(e.flag(first)),'majorFirstEnvelopeFlag',any(ce.flag(cm)),...
  'nativeControlLocalizationExcursion',any(gap(control)>.005),'majorControlLocalizationExcursion',any(cg(cc)>.005),...
  'nativeControlEnvelopeFlag',any(e.flag(control)),'majorControlEnvelopeFlag',any(ce.flag(cc)),...
  'startupNativeEnvelopeFlag',any(e.flag(d.time<330)),'globalNativeEnvelopeFlag',any(e.flag),...
  'conditionalAssumptions','Static ideal source bound/reset-free graph supported; all-time input/minor-stage/numerical reset not certified.',...
  'localizationCriteria','.005 dimensionless gap historical localization ONLY;32ULP analytic envelope ONLY;1e-9 inherited source state-output arithmetic identity ONLY. None is a thermal/solver-convergence tolerance.',...
  'secondEvent','SECOND_EVENT_NOT_COVERED_340','G5_ACCEPTED',false);
 if aExc||any(ce.flag(cm))||any(cg(cc)>.005)||any(ce.flag(cc))
  flags.DECISION='GUARD025_EVENT_PERSISTS';
 elseif nExc||any(e.flag(first))||any(gap(control)>.005)||any(e.flag(control))
  flags.DECISION='UNQUALIFIED_LOGGING_OR_RESOURCE';r.nativeOnlyAmbiguity='Native flagged but all completed-major checkpoints clear; do not claim repair or physical failure.';
 else,flags.DECISION='GUARD025_FIRST_WINDOW_CLEAN_CONDITIONAL';end
 bw=baseline.time>=330&baseline.time<=338;
 r.comparison=struct('baselineNativeFirstExcursion',any(abs(baseline.output(bw)-baseline.core(bw))>.005),...
  'baselineAcceptedMajor','UNAVAILABLE_NATIVE_RECORDS_ONLY','crossTrajectoryNativeClockExact',isequal(baseline.time,d.time),...
  'endpointT312MaxAbs_K',max(abs(d.T312(end,:)-baseline.T312(end,:))),...
  'steppingDriverDiffersFromArchivedNormalDriver',true,...
  'scope','Endpoint/same-time native diagnostic only. Execution stepping also differs from archived normal-driver reference; no unique guard causality or thermal convergence claim.');
 r.observed=d;r.nativeEnvelope=e;r.completedMajorEnvelope=ce;
catch ME
 r.failure=struct('stage',stage,'identifier',ME.identifier,'message',ME.message,'stack',{ME.stack},'physicalAttemptEntered',entered,'timeAdvancementEntered',begun);
 if strcmp(stage,'SOURCE')||startsWith(ME.identifier,'JTE116:ModelIC')||startsWith(ME.identifier,'JTE115:Source')
  flags.DECISION='GUARD025_REJECTED_MODEL_OR_IC';
 else,flags.DECISION='UNQUALIFIED_LOGGING_OR_RESOURCE';end
end
try,if ~isempty(S)&&isempty(out),if strcmp(S.Status,'inactive'),out=S.SimulationOutput;else,out=stop(S);end;end;catch,try,out=S.SimulationOutput;catch,end;end
r.simulationOutput=out;r.checkpoints=trace;r.flags=flags;r.physicalAttemptEntered=entered;r.timeAdvancementEntered=begun;
save([prefix '_RAW.mat'],'r','-v7.3');save([prefix '_CHECKPOINTS.mat'],'trace','-v7.3');
writeJSON([prefix '_FLAGS.json'],flags);
summary=struct('flags',flags,'G5_ACCEPTED',false);
for key={'failure','windowSummary','comparison','resourcePreflight','preTimeAdvanceSavedICAvailable','initialParityScope','nativeOnlyAmbiguity'}
 if isfield(r,key{1}),summary.(key{1})=r.(key{1});end
end
writeJSON([prefix '_SUMMARY.json'],summary);
try,if ~isempty(S)&&~strcmp(S.Status,'inactive'),terminate(S);end;catch,end
try,close_system(gm,0);catch,end
try,if ~isempty(project),close(project);end;catch,end
end
function checkLaw(q)
old=max(.25,q.q-mod(q.q,.25));candidate=max(.25,q.qstar-mod(q.qstar,.25));
assert(bits(old,candidate)&&bits(q.core,old)&&bits(q.qstar,max(q.q,.25)),...
 'JTE116:ModelIC','Completed-major source-law/output bitwise mismatch.');
end
function checkNativeLaw(d)
old=max(.25,d.q-mod(d.q,.25));candidate=max(.25,d.qstar-mod(d.qstar,.25));
assert(bits(old,candidate)&&bits(d.core,old)&&bits(d.qstar,max(d.q,.25)),...
 'JTE116:ModelIC','Native source-law/output bitwise mismatch.');
end
function ok=bits(a,b)
ok=isequal(size(a),size(b))&&isequal(a,b)&&isequal(typecast(a(:),'uint64'),typecast(b(:),'uint64'));
end
function mark(p,n)
set_param(p,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName',n,'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
end
function verifySource(m,ref)
assert(strcmp(get_param(m,'Solver'),'ode23t')&&strcmp(get_param(m,'RelTol'),'1e-3')&&strcmp(get_param(m,'AbsTol'),'1e-3')&&...
 str2double(get_param(m,'MaxStep'))==.05&&strcmp(get_param(m,'SolverResetMethod'),'Fast')&&...
 strcmp(get_param(m,'ZeroCrossControl'),'UseLocalSettings')&&strcmp(get_param(m,'LoadInitialState'),'off'),...
 'JTE115:Source','Original solver/config/initialization policy changed.');
tf=[m '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),...
 'JTE115:Source','Source TransferFcn changed.');
h=get_param(tf,'PortHandles');c=get_param([m '/Battery Control/FlwR_calc'],'PortHandles');
assert(source(h.Inport(1))==c.Outport(1),'JTE115:Source','Original final controller-to-filter edge changed.');
amb=[m '/Constant3'];assert(slResolve(get_param(amb,'Value'),amb)==300,'JTE115:Source','Controller reference changed.');
lp=which(get_param([m '/Current demand'],'FileName'));assert(~isempty(lp)&&strcmp(JTE2026sha256(lp),ref.loadSHA),'JTE115:Source','Load changed.');
s=[m '/Battery Control/FlwR_calc/step'];sat=[m '/Battery Control/FlwR_calc/FlwR calc/Saturation'];g=[m '/Battery Control/FlwR_calc/FlwR calc/Gain1'];
assert(slResolve(get_param(s,'Value'),s)==.25&&slResolve(get_param(g,'Gain'),g)==.1&&...
 slResolve(get_param(sat,'LowerLimit'),sat)==.001&&slResolve(get_param(sat,'UpperLimit'),sat)==.95,...
 'JTE115:Source','Source law parameters changed.');
for k={'InitFcn','StartFcn','StopFcn','PreLoadFcn','CloseFcn'}
 assert(isempty(get_param(m,k{1})),'JTE115:Source','Unexpected source callback.');
end
end
function p=source(port)
ln=get_param(port,'Line');assert(ln~=-1,'JTE115:Source','Missing source edge.');p=get_param(ln,'SrcPortHandle');assert(p~=-1,'JTE115:Source','Missing source port.');
end

function [a,b]=ram()
s=fileread('/proc/meminfo');a=str2double(regexp(s,'MemAvailable:\s+(\d+)','tokens','once'))*1024;b=str2double(regexp(s,'MemTotal:\s+(\d+)','tokens','once'))*1024;
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'JTE116:Resource','Private write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
