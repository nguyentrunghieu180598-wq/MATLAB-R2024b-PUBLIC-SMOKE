function report=JTE116_converterAudit(model)
% Read-only discovery/config audit. Unavailable topology is never called PASS.
assert(bdIsLoaded(char(model)),'JTE116:ModelNotLoaded','Model must already be loaded.');
b=find_system(char(model),'LookUnderMasks','all','FollowLinks','on','Type','Block');
entries=struct('block',{},'reference',{},'mode',{},'suppliedDerivatives',{},'inputOrder',{},'timeConstant',{},'upstream',{},'upstreamType',{});
unavailable=struct('block',{},'maskType',{},'reference',{},'blockType',{},'reason',{},'canonicalName',{});
for k=1:numel(b)
 path=b{k};
 try,m=char(get_param(path,'MaskType'));catch,m='';end
 try,r=char(get_param(path,'ReferenceBlock'));catch,r='';end
 parts=strsplit(r,'/');leaf=parts{end};
 maskName=regexprep(lower(m),'[^a-z0-9]','');
 referenceLeaf=regexprep(lower(leaf),'[^a-z0-9]','');
 canonical=strcmp(maskName,'simulinkpsconverter')||strcmp(referenceLeaf,'simulinkpsconverter');
 try,dp=get_param(path,'DialogParameters');catch,dp=struct();end
 contract=isstruct(dp)&&isfield(dp,'FilteringAndDerivatives')&&isfield(dp,'UdotUserProvided');
 if ~(canonical||contract),continue;end
 h=get_param(path,'PortHandles');
 if isempty(h.Inport)
  unavailable(end+1)=struct('block',path,'maskType',m,'reference',r,'blockType',get_param(path,'BlockType'),...
   'reason','NO_SIMULINK_INPORT_ON_MATCHED_OBJECT','canonicalName',canonical); %#ok<AGROW>
  continue
 end
 e.block=path;e.reference=r;
 try,e.mode=get_param(path,'FilteringAndDerivatives');catch,e.mode='UNREADABLE';end
 try,e.suppliedDerivatives=get_param(path,'UdotUserProvided');catch,e.suppliedDerivatives='UNREADABLE';end
 try,e.inputOrder=get_param(path,'SimscapeFilterOrder');catch,e.inputOrder='UNREADABLE';end
 try,e.timeConstant=get_param(path,'InputFilterTimeConstant');catch,e.timeConstant='UNREADABLE';end
 line=get_param(h.Inport(1),'Line');
 if line==-1
  e.upstream='UNAVAILABLE_DISCONNECTED';e.upstreamType='UNAVAILABLE';
 else
  up=get_param(line,'SrcPortHandle');
  if up==-1,e.upstream='UNAVAILABLE_SOURCE_PORT';e.upstreamType='UNAVAILABLE';
  else,e.upstream=get_param(up,'Parent');e.upstreamType=get_param(e.upstream,'BlockType');end
 end
 entries(end+1)=e; %#ok<AGROW>
end
complete=~isempty(entries)&&isempty(unavailable)&&~any(strcmp({entries.mode},'UNREADABLE'))&&...
 ~any(strcmp({entries.suppliedDerivatives},'UNREADABLE'))&&~any(strcmp({entries.upstreamType},'UNAVAILABLE'));
report=struct('count',numel(entries),'entries',entries,'unavailable',unavailable,'discoveryComplete',complete,...
 'scope','Static converter configuration only. Unavailable objects remain explicit. No derivatives/filter changes; full retained-block parameter parity is a separate check.',...
 'modified',false);
fprintf('JTE116_CONVERTER_AUDIT complete=%d details=OWNER_PRIVATE_ONLY noModelChange=1 G5_ACCEPTED=false\n',complete);
end
