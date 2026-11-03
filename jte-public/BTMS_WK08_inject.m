function p=BTMS_WK08_inject(m,b,j,S,forcePipeline)
% Prepare measurement path only. No compile/simulation; T_true stays untouched.
if nargin<5,forcePipeline=false;end
validateattributes(forcePipeline,{'logical'},{'scalar'});
validateattributes(b,{'double'},{'real','scalar','finite'});
validateattributes(j,{'double'},{'real','vector','nonempty','integer','>=',1,'<=',312});
j=j(:)';assert(isequal(j,unique(j)),'WK08:BiasChannels','Sorted unique biased channels required.');
validateattributes(S,{'double'},{'real','vector','integer','>=',1,'<=',312});
S=S(:)';assert(ismember(numel(S),[312 16 8]) && ...
 isequal(S,unique(S)),'WK08:Subset','Sorted unique 312/16/8 subset required.');
assert(isequal(S,BTMS_WK08_sparseSets(numel(S))), ...
 'WK08:FixedGeometry','Use the committed fixed geometric subset only.');
bc=[m '/Battery Control'];red=[bc '/min-max T'];ctrl=[bc '/FlwR_calc'];
r=get_param(red,'PortHandles');c=get_param(ctrl,'PortHandles');
source=upstream(r.Inport(1));
assert(upstream(c.Inport(1))==r.Outport(2) && ...
 strcmp(get_param([red '/MinMax3'],'Function'),'max'), ...
 'WK08:SourceEdge','Expected existing vector/max/controller chain.');
assert(getSimulinkBlockHandle([bc '/JTE local bias'])==-1 && ...
 getSimulinkBlockHandle([bc '/WK08 measurement'])==-1, ...
 'WK08:PriorFault','Use the unbiased B0L template only.');
before=BTMS_WK08_structFingerprint(m);
p=struct('truePort',source,'measuredPort',source,'bias_K',b,'channel',j, ...
 'subset',S,'identityBypass',false);
if b==0 && isequal(S,1:312) && ~forcePipeline
 % Literal no-op, including workspace, chart, blocks and lines.
 p.identityBypass=true;
 assert(isequaln(before,BTMS_WK08_structFingerprint(m)), ...
  'WK08:IdentityFingerprint','Neutral injection changed structure.');
 return
end
assert(all(ismember(j,S)),'WK08:BiasNotSensed', ...
 'Biased channel must be in the sensed subset.');
% Select actual channels, never zero-pad/replace unsensed channels for MinMax.
block=[bc '/WK08 measurement'];
add_block('simulink/User-Defined Functions/MATLAB Function',block);
sf=sfroot;chart=sf.find('-isa','Stateflow.EMChart','Path',block);
assert(numel(chart)==1,'WK08:Chart','Injection chart unavailable.');
chart.Script=sprintf(['function Tm=wk08measurement(T)\n%%#codegen\n' ...
 'assert(numel(T)==312);\nv=T(:);\nv(%s)=v(%s)+%.17g;\n' ...
 'Tm=v(%s);\nend\n'],mat2str(j),mat2str(j),b,mat2str(S));
h=get_param(block,'PortHandles');
assert(numel(h.Inport)==1 && numel(h.Outport)==1, ...
 'WK08:ChartPorts','Injection chart port discovery failed.');
delete_line(bc,source,r.Inport(1));
add_line(bc,source,h.Inport(1),'autorouting','on');
add_line(bc,h.Outport(1),r.Inport(1),'autorouting','on');
assert(upstream(h.Inport(1))==source && upstream(r.Inport(1))==h.Outport(1), ...
 'WK08:InjectionEdge','Only selected measured vector may enter min-max T.');
p.measuredPort=h.Outport(1);
% Retained law/config/workspace/scripts must match apart from this new chart.
after=BTMS_WK08_structFingerprint(m);
newPath='$ROOT/Battery Control/WK08 measurement';
keep=~(strcmp(after.blocks(:,1),newPath) | ...
 startsWith(after.blocks(:,1),[newPath '/']));
assert(isequaln(before.blocks,after.blocks(keep,:)), ...
 'WK08:RetainedParameters','A retained block parameter changed.');
% Only the true-source output and reducer input may gain/lose destinations.
endpoints={strrep(get_param(source,'Parent'),m,'$ROOT'), ...
 '$ROOT/Battery Control/min-max T'};
a=before.connectivity;bconn=after.connectivity;
a=a(~ismember(a(:,1),endpoints),:);
keep=~ismember(bconn(:,1),endpoints) & ...
 ~(strcmp(bconn(:,1),newPath)|startsWith(bconn(:,1),[newPath '/']));
assert(isequaln(a,bconn(keep,:)), ...
 'WK08:RetainedGraph','Connectivity outside measurement endpoints changed.');
assert(isequaln(before.config,after.config) && ...
 isequaln(before.workspace,after.workspace), ...
 'WK08:InjectionConfig','Injection changed solver or initialization workspace.');
old=before.scripts;now=after.scripts;
now=now(~strcmp(now(:,1),'$ROOT/Battery Control/WK08 measurement'),:);
assert(isequaln(old,now),'WK08:Law','Retained controller scripts changed.');
end
function p=upstream(h)
l=get_param(h,'Line');assert(l~=-1,'WK08:Line','Disconnected input.');
p=get_param(l,'SrcPortHandle');assert(p>0,'WK08:Line','Missing source.');
end
