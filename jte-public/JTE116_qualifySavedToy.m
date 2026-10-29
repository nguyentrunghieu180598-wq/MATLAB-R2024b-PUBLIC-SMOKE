function JTE116_qualifySavedToy()
% Read-only assessment of the ONE already-executed non-plant toy. NO simulation.
root=pwd;priv=fullfile(root,'jte116-one-private');prefix=fullfile(priv,['JTE116ONE_' getenv('GITHUB_RUN_ID') '_TOY']);
flags=struct('LOGGER_QUALIFIED',false,'SAVED_TOY_READ_ONLY',true,'PHYSICAL_SIMULATION_STARTED',false,'G5_ACCEPTED',false);
a=struct('sourceRun','40644248712','sourceCommit','ce4079477393f3cacbdb744b861d7b42a94af9f2',...
 'scope','Saved actual toy interval logger assessment; the original overall toy failure is preserved. No toy rerun.','G5_ACCEPTED',false);
try
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE116:Resource','Pinned runtime unavailable.');
 M=jsondecode(fileread(fullfile(priv,'manifest.json')));
 for name={'archived_toy_raw.mat','archived_toy_summary.json','archived_toy_receipt.json'}
  ix=find(strcmp({M.files.local},name{1}));
  assert(numel(ix)==1&&strcmp(JTE2026sha256(fullfile(priv,name{1})),M.files(ix).sha256),'JTE116:Logging','Archived toy SHA missing.');
 end
 old=jsondecode(fileread(fullfile(priv,'archived_toy_summary.json')));
 assert(strcmp(old.failure.identifier,'JTE116:Logging')&&strcmp(old.failure.message,'Next top-of-step reverses.')&&...
  any(strcmp({old.failure.stack.name},'JTE116_majorStepToy')&[old.failure.stack.line]==38),...
  'JTE116:Logging','Source toy did not stop at the isolated terminal-next-time assumption.');
 R=load(fullfile(priv,'archived_toy_raw.mat'),'r');r=R.r;
 assert(~r.physicalSimulation&&~r.flags.PHYSICAL_SIMULATION_STARTED&&contains(r.runtime,'24.2.0.3361896'),...
  'JTE116:Logging','Wrong archived toy scope/runtime.');
 trace=r.checkpoints;assert(numel(trace)>3&&trace(1).time==0,'JTE116:Logging','Archived initial/window checkpoints unavailable.');
 for k=1:numel(trace)
  q=trace(k);
  assert(q.time==q.processedPriorTime&&all(q.lastSignalTimes==q.time)&&q.lastStateTime==q.time&&...
   isfinite(q.nextTopOfStepTime)&&q.nextTopOfStepTime>=q.time&&numel(q.T312)==312,...
   'JTE116:Logging','Archived completed-major window clock/vector criterion failed.');
 end
 w=[trace.time]>=.005&[trace.time]<=.008;
 assert(any(w)&&all(strcmp({trace(w).phase},'COMPLETED_WINDOW_MAJOR')),'JTE116:Logging','Requested archived interval unavailable.');
 out=r.simulationOutput;ds=out.get('jte116States');tf='';
 for k=1:ds.numElements,e=ds.getElement(k);
  if e.BlockPath.getLength()==1
   path=char(e.BlockPath.getBlock(1));if endsWith(path,'/Filter'),assert(isempty(tf),'JTE116:Logging','Ambiguous toy TF.');tf=path;end
  end
 end
 assert(~isempty(tf),'JTE116:Logging','Archived toy filter state path unavailable.');
 model=tf(1:end-numel('/Filter'));d=JTE116_nativeData(out,tf,model);
 assert(d.clocksExact&&d.time(1)==0&&d.time(end)==.02&&size(d.T312,2)==312&&...
  isequal(d.core,d.actualInput)&&isequal(d.output,d.loggedOutput)&&isequal(d.T312,d.loggedT312),...
  'JTE116:Logging','Archived completed horizon/native independent signal clocks unqualified.');
 a.native=d;a.completedMajorCheckpoints=trace;a.originalToyFailure=old.failure;
 a.preTimeAdvanceOutputAvailable=old.preAdvanceOutputAvailable;
 a.terminalScope='No future major step exists after the terminal hit. The original extra next-Time assertion failed there; it is not used to qualify terminal completion. Required window clock equality and full native final horizon are independently retained.';
 flags.LOGGER_QUALIFIED=true;
catch ME
 a.failure=struct('identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
end
a.flags=flags;save([prefix '_RAW.mat'],'a','-v7.3');
writeJSON([prefix '_FLAGS.json'],flags);
summary=struct('flags',flags,'sourceRun',a.sourceRun,'sourceCommit',a.sourceCommit,'scope',a.scope);
if isfield(a,'failure'),summary.failure=a.failure;end
if isfield(a,'terminalScope'),summary.terminalScope=a.terminalScope;end
writeJSON([prefix '_SUMMARY.json'],summary);
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'JTE116:Resource','Private saved-toy assessment write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
