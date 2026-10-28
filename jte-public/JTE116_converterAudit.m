function report=JTE116_converterAudit(model)
% Read-only converter derivative-settings audit; no modifications/simulation.
assert(bdIsLoaded(char(model)),'JTE115:ModelNotLoaded','JTE115 required invariant failed.');
b=find_system(char(model),'LookUnderMasks','all','FollowLinks','on','Type','Block');
entries=struct('block',{},'reference',{},'mode',{},'suppliedDerivatives',{},'inputOrder',{},'timeConstant',{},'upstream',{},'upstreamType',{});
for k=1:numel(b)
 path=b{k};
 try,m=char(get_param(path,'MaskType'));catch,m='';end
 try,r=char(get_param(path,'ReferenceBlock'));catch,r='';end
 % Simscape library references may contain newline/formatting in display names.
 marker=regexprep(lower([m ' ' r]),'[^a-z0-9]','');
 try,dp=get_param(path,'DialogParameters');catch,dp=struct();end
 derivativeContract=isstruct(dp)&&isfield(dp,'FilteringAndDerivatives')&&isfield(dp,'UdotUserProvided');
 if ~(contains(marker,'simulinkpsconverter')||derivativeContract),continue;end
 e.block=path;e.reference=r;
 try,e.mode=get_param(path,'FilteringAndDerivatives');catch,e.mode='UNREADABLE';end
 try,e.suppliedDerivatives=get_param(path,'UdotUserProvided');catch,e.suppliedDerivatives='UNREADABLE';end
 try,e.inputOrder=get_param(path,'SimscapeFilterOrder');catch,e.inputOrder='UNREADABLE';end
 try,e.timeConstant=get_param(path,'InputFilterTimeConstant');catch,e.timeConstant='UNREADABLE';end
 h=get_param(path,'PortHandles');
 assert(~isempty(h.Inport),'JTE115:InputPortUnavailable','JTE115 required invariant failed.');
 line=get_param(h.Inport(1),'Line');
 assert(line~=-1,'JTE115:InputDisconnected','JTE115 required invariant failed.');
 up=get_param(line,'SrcPortHandle');
 assert(up~=-1,'JTE115:UpstreamUnavailable','JTE115 required invariant failed.');
 e.upstream=get_param(up,'Parent');e.upstreamType=get_param(e.upstream,'BlockType');
 entries(end+1)=e; %#ok<AGROW>
end
assert(~isempty(entries),'JTE115:NoConvertsFound','JTE115 required invariant failed.');
assert(~any(strcmp({entries.mode},'UNREADABLE'))&&~any(strcmp({entries.suppliedDerivatives},'UNREADABLE')),...
 'JTE116:UnreadableConverterContract','Converter derivative contract cannot be read.');
report=struct('count',numel(entries),'entries',entries,'scope','Static only: signal derivative correctness and solver compatibility remain unverified','modified',false);
fprintf('JTE115_CONVERTER_AUDIT_SOURCE_STATIC count=%d noModelChange=1 G5_ACCEPTED=false\n',numel(entries));
end
