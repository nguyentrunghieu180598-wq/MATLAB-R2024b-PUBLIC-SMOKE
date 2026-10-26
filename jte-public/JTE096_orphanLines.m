function bad=JTE096_orphanLines(sys)
% Read every line/branch; NEVER delete by scanning. Resolve parent sources.
lines=find_system(sys,'FindAll','on','LookUnderMasks','all','FollowLinks','off','Type','line');
bad=0;
for k=1:numel(lines)
 h=lines(k);children=get_param(h,'LineChildren');
 if ~isempty(children),continue;end
 dst=get_param(h,'DstPortHandle');src=get_param(h,'SrcPortHandle');
 p=h;
 while src==-1
  p=get_param(p,'LineParent');
  if p==-1,break;end
  src=get_param(p,'SrcPortHandle');
 end
 if src==-1||isempty(dst)||all(dst==-1),bad=bad+1;end
end
end
