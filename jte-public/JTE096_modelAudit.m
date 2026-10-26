function a=JTE096_modelAudit(m,excluded)
% Static independently loaded model audit. No solved Simscape IC equivalence.
if nargin<2,excluded={};end
blocks=sort(find_system(m,'LookUnderMasks','all','FollowLinks','off','Type','Block'));
a.blocks=cell(0,3);a.connectivity=cell(0,2);
for k=1:numel(blocks)
 b=blocks{k};
 if any(cellfun(@(x)strcmp(b,x)||startsWith(b,[x '/']),excluded)),continue;end
 type=get_param(b,'BlockType');
 if any(strcmp(type,{'Scope','Display'}))
  d='DISPLAY_UI_DIALOG_NOT_INSPECTED';
 else
  dp=get_param(b,'DialogParameters');keys={};
  if ~isempty(dp),keys=sort(fieldnames(dp));end
  vals=cell(size(keys));
  for j=1:numel(keys),vals{j}=normal(get_param(b,keys{j}),m);end
  d={keys,vals};
 end
 a.blocks(end+1,:)={relative(b,m),type,d}; %#ok<AGROW>
 pc=get_param(b,'PortConnectivity');c=cell(numel(pc),1);
 for j=1:numel(pc)
  dst=cell(numel(pc(j).DstBlock),1);
  for z=1:numel(dst)
   dst{z}=[handleName(pc(j).DstBlock(z),m) ':' num2str(pc(j).DstPort(z))];
  end
  src=arrayfun(@(h)handleName(h,m),pc(j).SrcBlock,'UniformOutput',false);
  c{j}={pc(j).Type,src,pc(j).SrcPort,sort(dst)};
 end
 a.connectivity(end+1,:)={relative(b,m),c}; %#ok<AGROW>
end
a.config={};
if strcmp(get_param(m,'Type'),'block_diagram')
 keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','MinStep','InitialStep',...
 'SolverResetMethod','ZeroCrossControl','LoadInitialState','InitialState',...
 'StartTime','StopTime','InitFcn','StartFcn','StopFcn','PreLoadFcn','CloseFcn'};
 vals=cell(size(keys));
 for j=1:numel(keys),vals{j}=normal(get_param(m,keys{j}),m);end
 a.config={keys,vals};
end
a.solvedSimscapeIC='UNAVAILABLE_STATIC_ONLY';
end
function n=handleName(h,m)
if h==-1,n='NO_BLOCK';else,n=relative(getfullname(h),m);end
end
function n=relative(b,m)
if strcmp(b,m),n='$ROOT';else,n=['$ROOT' b(numel(m)+1:end)];end
end
function v=normal(v,m)
if ischar(v),v=strrep(v,m,'$ROOT');
elseif isstring(v),v=replace(v,m,'$ROOT');
elseif iscell(v),v=cellfun(@(x)normal(x,m),v,'UniformOutput',false);
elseif isstruct(v)
 f=fieldnames(v);
 for k=1:numel(v),for j=1:numel(f),v(k).(f{j})=normal(v(k).(f{j}),m);end;end
end
end
