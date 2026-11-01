function BTMS_WK04_t0Fixture(privateRoot, preflightFile)
% WK04 SOURCE-ONLY candidate. Never load or simulate the battery model.
% A protected external prepare step must create a fresh privateRoot and an
% independently computed input-SHA receipt before MATLAB starts.
assert(strcmp(version('-release'),'2024b') && ...
 strcmp(version,'24.2.0.3361896 (R2024b) Update 10'), ...
 'WK04:Runtime','Pinned MATLAB R2024b Update 10 required.');
assert(isfolder(privateRoot) && isfile(preflightFile), ...
 'WK04:Preflight','Protected input receipt missing.');
assert(strcmp(char(preflightFile), ...
 fullfile(char(privateRoot),'WK04_PREPARE_GATE.json')), ...
 'WK04:PreflightPath','Receipt must be inside the private run folder.');
gate=jsondecode(fileread(preflightFile));
assert(strcmp(gate.sourceKind,'WK04_NONBATTERY') && ...
 strcmp(gate.commit,getenv('GITHUB_SHA')) && ...
 strcmp(gate.run,getenv('GITHUB_RUN_ID')) && ...
 isequal(gate.physicalRun,false) && ...
 isfield(gate,'sourceSHA256') && isfield(gate,'inputSHA256'), ...
 'WK04:Preflight','Input receipt is not bound to this source/job.');
% The receipt is a reference. The protected Python prepare process owns
% byte hashing; a caller-supplied Boolean is never used as attestation.
name='WK04T0Nonbattery';
assert(~bdIsLoaded(name),'WK04:Model','Fixture model already loaded.');
flags=struct('status','UNQUALIFIED','physicalRun',false, ...
 'G5Accepted',false,'stage','START');
failure=[];s=[];created=false;
try
 new_system(name);created=true;
 set_param(name,'StartTime','0','StopTime','.03','Solver','ode23t', ...
  'MaxStep','.005','BlockReduction','off','SimulationMode','normal');
 add_block('simulink/Sources/Constant',[name '/u'],'Value','.5');
 add_block('simulink/Discrete/Zero-Order Hold',[name '/hold'],'SampleTime','.01');
 add_block('simulink/Discrete/Discrete State-Space',[name '/state'], ...
  'A','.5','B','.5','C','1','D','0','InitialCondition','.25', ...
  'SampleTime','.01');
 add_block('simulink/Sources/Clock',[name '/clock']);
 add_block('simulink/Math Operations/Gain',[name '/T312'], ...
  'Gain','ones(312,1)');
 add_line(name,'u/1','hold/1');
 add_line(name,'hold/1','state/1');
 add_line(name,'clock/1','T312/1');
 paths={'clock','hold','state','T312'};
 ports=zeros(1,4);
 for k=1:4
  h=get_param([name '/' paths{k}],'PortHandles');
  ports(k)=h.Outport(1);
  add_block('simulink/Sinks/To File',[name '/file' num2str(k)], ...
   'FileName',fullfile(privateRoot,['UNUSED_' num2str(k) '.mat']), ...
   'MatrixName',['native' num2str(k)],'SaveFormat','Timeseries', ...
   'SampleTime','-1','Decimation','1');
  add_line(name,[paths{k} '/1'],['file' num2str(k) '/1'], ...
   'autorouting','on');
 end
 BTMS_M3_instrument(name,ports,[name '/state'],privateRoot);
 assert(strcmp(get_param(name,'BlockReduction'),'off') && ...
  strcmp(get_param(name,'SimulationMode'),'normal'), ...
  'WK04:Config','Fixture config changed before capture.');

 flags.stage='ZERO_STOP_CAPTURE';
 zeroFiles=targets(name,privateRoot,'ZERO');
 BTMS_M3_events('close');
 BTMS_M3_events('init',[name '/state'], ...
  fullfile(privateRoot,'ZERO_PHASE.csv'));
 in0=Simulink.SimulationInput(name);
 in0=setModelParameter(in0,'StartTime','0','StopTime','0', ...
  'SaveFinalState','on','SaveOperatingPoint','on');
 out0=sim(in0);
 BTMS_M3_events('close');
 op0=out0.get('m3FinalOP');
 assert(isa(op0,'Simulink.op.ModelOperatingPoint') && ...
  isequal(op0.startTime,0) && isequal(op0.snapshotTime,0), ...
  'WK04:T0','Zero-stop complete operating point absent or mistimed.');
 meta0=metadata(out0,'ZERO');
 assert(strcmp(meta0.simulationMode,'normal') && ...
  ~isempty(meta0.structuralChecksum) && ...
  strcmp(meta0.stopEvent,'ReachedStopTime'), ...
  'WK04:ZeroStopEvent','Zero-stop reason unqualified.');
 nativeZero=readFour(zeroFiles,0);
 phaseZero=phaseCSV(fullfile(privateRoot,'ZERO_PHASE.csv'));

 flags.stage='DIRECT_START';
 directFiles=targets(name,privateRoot,'DIRECT');
 BTMS_M3_events('init',[name '/state'], ...
  fullfile(privateRoot,'DIRECT_PHASE.csv'));
 s=simulation(name);initialize(s);
 witness={};lastPhaseSequence=0;majorCount=0;
 while true
  assert(majorCount<100,'WK04:StepBound','Toy major-step bound exceeded.');
  priorTop=s.Time;
  finalstep=step(s);majorCount=majorCount+1;
  if finalstep
   terminal=terminalReceipt(s,priorTop,finalstep);
   break
  end
  w=nonterminalWitness(s,priorTop,lastPhaseSequence);
  witness{end+1}=w; %#ok<AGROW>
  lastPhaseSequence=w.lastObservedPhaseSequence;
 end
 assert(strcmp(terminal.status,'paused'), ...
  'WK04:TerminalMode','Normal-mode terminal did not pause.');
 outD=stop(s);s=[];
 BTMS_M3_events('close');
 metaD=metadata(outD,'DIRECT');
 nativeDirect=readFour(directFiles,.03);
 phaseDirect=phaseCSV(fullfile(privateRoot,'DIRECT_PHASE.csv'));
 assert(~isempty(witness),'WK04:Nonterminal','No completed nonterminal major witness.');

 flags.stage='SAME_MODEL_RESTORE';
 restoreFiles=targets(name,privateRoot,'RESTORE');
 BTMS_M3_events('init',[name '/state'], ...
  fullfile(privateRoot,'RESTORE_PHASE.csv'));
 inR=Simulink.SimulationInput(name);
 inR=setInitialState(inR,op0);
 inR=setModelParameter(inR,'StartTime','0','StopTime','.03');
 outR=sim(inR);
 BTMS_M3_events('close');
 metaR=metadata(outR,'RESTORE');
 nativeRestore=readFour(restoreFiles,.03);
 phaseRestore=phaseCSV(fullfile(privateRoot,'RESTORE_PHASE.csv'));

 flags.stage='PARITY';
 assert(strcmp(metaD.simulationMode,'normal') && ...
  ~isempty(metaD.structuralChecksum) && ...
  ~strcmp(metaD.stopEvent,'UNAVAILABLE') && ...
  strcmp(terminal.metadata.stopEvent,'ReachedStopTime'), ...
  'WK04:DirectMetadata','Direct mode, checksum or terminal event unavailable.');
 assert(isequal(meta0.structuralChecksum,metaD.structuralChecksum) && ...
  isequal(metaD.structuralChecksum,metaR.structuralChecksum), ...
  'WK04:StructuralChecksum','Model structural checksum mismatch.');
 for k=1:4
  assert(isequaln(nativeDirect{k}.Time,nativeRestore{k}.Time) && ...
   isequaln(nativeDirect{k}.Data,nativeRestore{k}.Data), ...
   'WK04:ReplayParity','Direct and restored native series differ.');
 end
 assert(strcmp(metaD.simulationMode,'normal') && ...
  strcmp(metaR.simulationMode,'normal'), ...
  'WK04:Mode','Effective simulation mode unqualified.');
 assert(strcmp(metaR.stopEvent,'ReachedStopTime'), ...
  'WK04:RestoreStop','Restore terminal event unqualified.');
 save(fullfile(privateRoot,'WK04_PRIVATE_EVIDENCE.mat'), ...
  'op0','meta0','metaD','metaR','terminal','witness', ...
  'nativeZero','nativeDirect','nativeRestore', ...
  'phaseZero','phaseDirect','phaseRestore','gate','-v7.3');
 flags.status='WK04_NONBATTERY_API_CANDIDATE_ONLY';
 flags.stage='DONE';
catch err
 failure=err;
 flags.identifier=err.identifier;
 flags.reason=err.message; % Owner-private only; public runner prints ID.
 try
  partial=struct('stage',flags.stage);
  if exist('op0','var'),partial.op0=op0;end
  if exist('meta0','var'),partial.meta0=meta0;end
  if exist('metaD','var'),partial.metaD=metaD;end
  if exist('metaR','var'),partial.metaR=metaR;end
  if exist('terminal','var'),partial.terminal=terminal;end
  if exist('witness','var'),partial.witness=witness;end
  if exist('nativeZero','var'),partial.nativeZero=nativeZero;end
  if exist('nativeDirect','var'),partial.nativeDirect=nativeDirect;end
  if exist('nativeRestore','var'),partial.nativeRestore=nativeRestore;end
  if ~isempty(s)
   try
    partial.liveStatus=char(s.Status);
    partial.liveTime=s.Time;
   catch
   end
  end
  save(fullfile(privateRoot,'WK04_PARTIAL_EVIDENCE.mat'), ...
   'flags','gate','partial','-v7.3');
 catch
 end
end
try,BTMS_M3_events('close');catch,end
if ~isempty(s)
 try,if ~strcmp(char(s.Status),'inactive'),stop(s);end,catch,end
end
if created
 try,close_system(name,0);catch,end
end
writeFlags(fullfile(privateRoot,'WK04_FLAGS.json'),flags);
if ~isempty(failure)
 safeID=regexprep(failure.identifier,'[^A-Za-z0-9_:]','_');
 if isempty(safeID),safeID='UNSPECIFIED';end
 error('WK04:Unqualified','Private diagnostic saved; identifier=%s',safeID);
end
fprintf('WK04_NONBATTERY_API_CANDIDATE_ONLY physicalRun=0 G5_ACCEPTED=false\n');
end

function files=targets(m,root,tag)
files=cell(1,4);
for k=1:4
 files{k}=fullfile(root,[tag '_NATIVE_' num2str(k) '.mat']);
 assert(~isfile(files{k}),'WK04:OutputExists','Native target already exists.');
 set_param([m '/file' num2str(k)],'FileName',files{k});
end
end

function q=nonterminalWitness(s,prior,lastSeq)
assert(strcmp(char(s.Status),'paused') && isfinite(s.Time) && ...
 s.Time>=prior,'WK04:NextTop','Nonterminal next top unavailable.');
v=BTMS_M3_completed(s,prior,false,NaN);
e=v.phases;seq=[e{1}.sequence,e{2}.sequence,e{3}.sequence];
assert(all(seq>lastSeq)||all(seq<=lastSeq), ...
 'WK04:PhaseMix','Mixed new and stale phase triplet.');
q=struct('processedPriorTop',prior,'nextTop',s.Time, ...
 'fourSignalTailClocks',v.signalTimes, ...
 'lastObservedPhaseSequence',seq(3), ...
 'newEventsSincePriorStep',all(seq>lastSeq), ...
 'phaseSequence',seq,'preState',e{1}.state, ...
 'postState',e{3}.state,'actuatorOutput',v.y, ...
 'T312',v.T312, ...
 'scope','Completed nonterminal major; phase callbacks may be stale.');
end

function t=terminalReceipt(s,prior,finalstep)
o=s.SimulationOutput;
t=struct('processedPriorTop',prior,'finalstep',finalstep, ...
 'status',char(s.Status),'returnedTime',s.Time, ...
 'metadata',metadata(o,'TERMINAL_PRE_STOP'), ...
 'scope','Terminal receipt only; not an accepted next-major row.');
end

function m=metadata(out,role)
m=struct('role',role,'simulationMode','UNAVAILABLE', ...
 'stopEvent','UNAVAILABLE','stopEventTime',NaN, ...
 'structuralChecksum',[],'errorMessage',out.ErrorMessage);
assert(isempty(out.ErrorMessage),'WK04:OutputError','SimulationOutput error.');
try
 mi=out.SimulationMetadata.ModelInfo;
 ex=out.SimulationMetadata.ExecutionInfo;
 if isfield(mi,'SimulationMode'),m.simulationMode=char(mi.SimulationMode);end
 if isfield(mi,'ModelStructuralChecksum')
  m.structuralChecksum=mi.ModelStructuralChecksum;
 end
 if isfield(ex,'StopEvent'),m.stopEvent=char(ex.StopEvent);end
 if isfield(ex,'StopEventTime'),m.stopEventTime=ex.StopEventTime;end
catch
end
end

function out=readFour(files,horizon)
out=cell(1,4);widths=[1,1,1,312];
for k=1:4
 assert(isfile(files{k}),'WK04:NativeMissing','To File output missing.');
v=load(files{k});ts=v.(['native' num2str(k)]);
 assert(isa(ts,'timeseries') && ~isempty(ts.Time) && ...
  ts.Time(1)==0 && all(isfinite(ts.Time)) && ...
  all(diff(ts.Time)>=0) && ...
  abs(ts.Time(end)-horizon)<=32*eps(1) && ...
  numel(ts.Data)==numel(ts.Time)*widths(k), ...
  'WK04:NativeClock','Native role clock, horizon or width invalid.');
out{k}=ts;
end
end

function p=phaseCSV(file)
assert(isfile(file),'WK04:PhaseMissing','Full phase CSV missing.');
p=readmatrix(file);
assert(size(p,2)==7 && size(p,1)>=3 && ...
 mod(size(p,1),3)==0 && ...
 all(p(:,3)==repmat([1;2;3],size(p,1)/3,1)) && ...
 all(diff(p(:,1))==1) && all(diff(p(:,2))>=0) && ...
 all(p(:,7)==1), ...
 'WK04:PhaseCSV','Full phase order/readability invalid.');
end

function writeFlags(path,flags)
f=fopen(path,'w');
assert(f>=0,'WK04:FlagsWrite','Cannot preserve private flags.');
fprintf(f,'%s',jsonencode(flags));fclose(f);
end

