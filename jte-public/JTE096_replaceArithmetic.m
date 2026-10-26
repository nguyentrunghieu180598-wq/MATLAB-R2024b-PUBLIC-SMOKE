function proof=JTE096_replaceArithmetic(step)
% Same arithmetic as the already-tested negative diagnostic. WIRE HOTFIX ONLY.
ip=find_system(step,'SearchDepth',1,'BlockType','Inport');
op=find_system(step,'SearchDepth',1,'BlockType','Outport');
assert(numel(ip)==2&&numel(op)==1,'JTE096:Ports','Unexpected interface.');
modblock=[step '/Mod'];mp=get_param(modblock,'PortHandles');
assert(strcmp(get_param(modblock,'Operator'),'mod'),'JTE096:Mod','Wrong operator.');
q=source(mp.Inport(1));s=source(mp.Inport(2));
assert(any(strcmp(get_param(q,'Parent'),ip))&&any(strcmp(get_param(s,'Parent'),ip))&&q~=s,'JTE096:Inputs','Unexpected source ports.');
oh=get_param(op{1},'PortHandles');maxblock=get_param(source(oh.Inport(1)),'Parent');
assert(strcmp(get_param(maxblock,'BlockType'),'MinMax')&&strcmp(get_param(maxblock,'Function'),'max'),'JTE096:Max','Retain final source max.');
mh=get_param(maxblock,'PortHandles');
assert(numel(mh.Inport)==2&&source(mh.Inport(2))==s,'JTE096:StepMax','Step-to-Max changed.');
sub=get_param(source(mh.Inport(1)),'Parent');sh=get_param(sub,'PortHandles');
assert(strcmp(get_param(sub,'BlockType'),'Sum')&&strcmp(erase(get_param(sub,'Inputs'),'|'),'+-')&&...
 source(sh.Inport(1))==q&&source(sh.Inport(2))==mp.Outport(1),'JTE096:Subtract','Wrong source arithmetic.');
assert(JTE096_orphanLines(step)==0,'JTE096:SourceOrphan','Review source orphans before mutation.');
before=JTE096_signalEdges(step);
retained=JTE096_modelAudit(step,{modblock,sub});
% Exact five removed endpoint pairs; documented delete_line preserves branches.
pairs=[q mp.Inport(1);s mp.Inport(2);q sh.Inport(1);mp.Outport(1) sh.Inport(2);sh.Outport(1) mh.Inport(1)];
removed=cell(5,1);
for k=1:5
 assert(source(pairs(k,2))==pairs(k,1),'JTE096:WireProof','Endpoint changed before deletion.');
 removed{k}=[ep(pairs(k,1),step) '>' ep(pairs(k,2),step)];
 delete_line(step,pairs(k,1),pairs(k,2));
 assert(get_param(pairs(k,2),'Line')==-1,'JTE096:Detach','Exact destination not detached.');
 assert(source(mh.Inport(2))==s&&source(oh.Inport(1))==mh.Outport(1),'JTE096:BranchLost','Legitimate final-Max branch was cut.');
end
delete_block(modblock);delete_block(sub);
block=[step '/JTE094 Atomic Quantization'];
add_block('simulink/User-Defined Functions/MATLAB Function',block);
sf=sfroot;chart=sf.find('-isa','Stateflow.EMChart','Path',block);
assert(numel(chart)==1,'JTE096:Chart','Missing atomic chart.');
chart.Script=sprintf('function y=atomicQuantization(q,step)\n%%#codegen\ny=q-mod(q,step);\nend\n');
ah=get_param(block,'PortHandles');assert(numel(ah.Inport)==2,'JTE096:AtomicPorts','Missing ports.');
add_line(step,q,ah.Inport(1),'autorouting','on');
add_line(step,s,ah.Inport(2),'autorouting','on');
add_line(step,ah.Outport(1),mh.Inport(1),'autorouting','on');
added={[ep(q,step) '>' ep(ah.Inport(1),step)];[ep(s,step) '>' ep(ah.Inport(2),step)];[ep(ah.Outport(1),step) '>' ep(mh.Inport(1),step)]};
expected=sort([setdiff(before,removed);added]);
assert(isequal(expected,JTE096_signalEdges(step)),'JTE096:GraphDelta','Unexpected retained/deleted signal edge.');
after=JTE096_modelAudit(step,{block});
assert(isequal(retained.blocks,after.blocks),'JTE096:RetainedParams','A retained block/declared target changed.');
assert(JTE096_orphanLines(step)==0,'JTE096:NewOrphan','New dangling branch or orphan line.');
proof=struct('removedEndpoints',5,'addedEndpoints',3,'orphans',0,...
 'retainedPortConnectivityChecked',true,'declaredBlockTargetsUnchanged',true,...
 'solvedSimscapeIC','UNAVAILABLE','causalRepairAccepted',false);
end
function p=source(dst)
h=get_param(dst,'Line');assert(h~=-1,'JTE096:MissingLine','Missing source line.');
p=get_param(h,'SrcPortHandle');assert(p~=-1,'JTE096:MissingSource','Missing source endpoint.');
end
function s=ep(p,sys)
b=get_param(p,'Parent');s=[b(numel(sys)+2:end) ':' num2str(get_param(p,'PortNumber'))];
end
