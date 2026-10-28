function proof=JTE115_buildGuardedDiagnostic(sourceFile,destFile)
% Diagnostic model clone only; never modify vendor or claim G5 from graph work.
% Precondition: SHA-pin original source/model and PASS JTE115_guardedLawCanary.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE115:Release');
assert(isfile(sourceFile)&&~isfile(destFile),'JTE115:FreshCopyRequired');
sourceSHA=JTE2026sha256(sourceFile);
copyfile(sourceFile,destFile);
load_system(destFile);[~,mdl]=fileparts(destFile);
onExit=onCleanup(@()close_system(mdl,0)); %#ok<NASGU>
step=[mdl '/Battery Control/FlwR_calc/Step Change']; mb=[step '/Mod'];
hp=get_param(mb,'PortHandles');
assert(strcmp(get_param(mb,'Operator'),'mod'),'JTE115:SourceMod');
q=up(hp.Inport(1));stepValue=up(hp.Inport(2));
out=find_system(step,'SearchDepth',1,'BlockType','Outport');
assert(numel(out)==1,'JTE115:OutputCount');
oh=get_param(out{1},'PortHandles');
fin=get_param(up(oh.Inport(1)),'Parent');
assert(strcmp(get_param(fin,'BlockType'),'MinMax')&&strcmp(get_param(fin,'Function'),'max'),'JTE115:OriginalFloor');
fh=get_param(fin,'PortHandles');
assert(up(fh.Inport(2))==stepValue,'JTE115:OriginalFloorValue');
sub=get_param(up(fh.Inport(1)),'Parent');
sh=get_param(sub,'PortHandles');
assert(strcmp(get_param(sub,'BlockType'),'Sum')&&strcmp(erase(get_param(sub,'Inputs'),'|'),'+-'),'JTE115:SourceSubtract');
assert(up(sh.Inport(1))==q&&up(sh.Inport(2))==hp.Outport(1),'JTE115:SourceGraphChanged');
assert(JTE096_orphanLines(step)==0,'JTE115:ExistingOrphans');
old=string(JTE096_signalEdges(step));
a=label(q,step)+">"+label(hp.Inport(1),step);
b=label(q,step)+">"+label(sh.Inport(1),step);
assert(sum(old==a)==1&&sum(old==b)==1,'JTE115:SourceEdgeMultiplicity');
const=[step '/JTE115 guard constant']; guard=[step '/JTE115 q guard'];
add_block('simulink/Sources/Constant',const,'Value','0.375','SampleTime','0');
add_block('simulink/Math Operations/MinMax',guard,'Function','max','Inputs','2');
ch=get_param(const,'PortHandles');gh=get_param(guard,'PortHandles');
delete_line(step,q,hp.Inport(1));
delete_line(step,q,sh.Inport(1));
assert(get_param(hp.Inport(1),'Line')==-1&&get_param(sh.Inport(1),'Line')==-1,'JTE115:DetachFailed');
add_line(step,q,gh.Inport(1),'autorouting','on');
add_line(step,ch.Outport(1),gh.Inport(2),'autorouting','on');
add_line(step,gh.Outport(1),hp.Inport(1),'autorouting','on');
add_line(step,gh.Outport(1),sh.Inport(1),'autorouting','on');
assert(up(oh.Inport(1))==fh.Outport(1)&&up(fh.Inport(2))==stepValue,'JTE115:FloorLost');
assert(JTE096_orphanLines(step)==0,'JTE115:CreatedOrphans');
new=[label(q,step)+">"+label(gh.Inport(1),step); ...
 label(ch.Outport(1),step)+">"+label(gh.Inport(2),step); ...
 label(gh.Outport(1),step)+">"+label(hp.Inport(1),step); ...
 label(gh.Outport(1),step)+">"+label(sh.Inport(1),step)];
expected=sort([setdiff(old,[a;b]);new]);
assert(isequal(sort(string(JTE096_signalEdges(step))),expected),'JTE115:UnexpectedWireChange');
save_system(mdl,destFile);
assert(strcmp(JTE2026sha256(sourceFile),sourceSHA),'JTE115:SourceFileChanged');
proof=struct('sourceModelSHA256',sourceSHA,'guardedModelSHA256',JTE2026sha256(destFile),'sourceModelUnchanged',true,'cloneOnly',true,'deletedWires',2,'addedWires',4,...
 'newBlocks',2,'physicalEquivalenceEstablished',false,'eventTopologyChanged',true,'simulationRun',false,'G5Accepted',false);
fprintf('JTE115_GUARDED_DERIVATIVE_PREPARE_PASS scope=cloneOnly simulation=0 G5_ACCEPTED=0\n');
end
function p=up(port)
ln=get_param(port,'Line');assert(ln~=-1,'JTE115:NoLine');
p=get_param(ln,'SrcPortHandle');assert(p~=-1,'JTE115:NoSource');
end
function s=label(port,sys)
b=get_param(port,'Parent');
s=string(b(numel(sys)+2:end))+":"+string(get_param(port,'PortNumber'));
end
