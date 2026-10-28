function report=JTE115_converterAudit(model)
% Read-only converter derivative-settings audit; no modifications/simulation.
assert(bdIsLoaded(char(model)),'JTE115:ModelNotLoaded');
b=find_system(char(model),'LookUnderMasks','all','FollowLinks','on','Type','Block');
entries=struct('block',{},'reference',{},'mode',{},'suppliedDerivatives',{},'inputOrder',{},'timeConstant',{},'upstream',{},'upstreamType',{});
for k=1:numel(b)
 path=b{k};
 try,m=char(get_param(path,'MaskType'));catch,m='';end
 try,r=char(get_param(path,'ReferenceBlock'));catch,r='';end
 if ~(contains(lower(m),'simulink-ps converter')||contains(lower(r),'simulink-ps converter')),continue;end
 e.block=path;e.reference=r;
 try,e.mode=get_param(path,'FilteringAndDerivatives');catch,e.mode='UNREADABLE';end
 try,e.suppliedDerivatives=get_param(path,'UdotUserProvided');catch,e.suppliedDerivatives='UNREADABLE';end
 try,e.inputOrder=get_param(path,'SimscapeFilterOrder');catch,e.inputOrder='UNREADABLE';end
 try,e.timeConstant=get_param(path,'InputFilterTimeConstant');catch,e.timeConstant='UNREADABLE';end
 h=get_param(path,'PortHandles');
 assert(~isempty(h.Inport),'JTE115:InputPortUnavailable');
 line=get_param(h.Inport(1),'Line');
 assert(line~=-1,'JTE115:InputDisconnected');
 up=get_param(line,'SrcPortHandle');
 assert(up~=-1,'JTE115:UpstreamUnavailable');
 e.upstream=get_param(up,'Parent');e.upstreamType=get_param(e.upstream,'BlockType');
 entries(end+1)=e; %#ok<AGROW>
end
assert(~isempty(entries),'JTE115:NoConvertsFound');
report=struct('count',numel(entries),'entries',entries,'scope','Static only: signal derivative correctness and solver compatibility remain unverified','modified',false);
fprintf('JTE115_CONVERTER_AUDIT_SOURCE_STATIC count=%d noModelChange=1 G5_ACCEPTED=false\n',numel(entries));
end
