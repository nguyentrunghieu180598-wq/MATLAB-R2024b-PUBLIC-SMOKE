function edges=JTE096_signalEdges(sys)
% Canonical directed signal endpoints for one local subsystem, not geometry.
blocks=find_system(sys,'SearchDepth',1,'Type','Block');
edges={};
for k=1:numel(blocks)
 if strcmp(blocks{k},sys),continue;end
 ph=get_param(blocks{k},'PortHandles');
 for j=1:numel(ph.Inport)
  h=get_param(ph.Inport(j),'Line');
  if h==-1,continue;end
  p=get_param(h,'SrcPortHandle');
  if p==-1,continue;end
  edges{end+1,1}=[endpoint(p,sys) '>' endpoint(ph.Inport(j),sys)]; %#ok<AGROW>
 end
end
edges=sort(edges);
end
function s=endpoint(p,sys)
b=get_param(p,'Parent');assert(startsWith(b,[sys '/']),'JTE096:Hierarchy','Cross-hierarchy endpoint.');
s=[b(numel(sys)+2:end) ':' num2str(get_param(p,'PortNumber'))];
end
