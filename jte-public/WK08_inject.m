function proof=WK08_inject(m,b,j,S)
% Static measurement-path edit only. The default is an exact structural no-op.
if nargin<2,b=0;end
if nargin<3,j=1;end
if nargin<4,S=1:312;end
validateattributes(b,{'double'},{'scalar','real','finite'});
validateattributes(j,{'double'},{'scalar','integer','>=',1,'<=',312});
S=S(:)';assert(any(numel(S)==[312 16 8]) && numel(unique(S))==numel(S) && ...
 all(isfinite(S)&S==fix(S)&S>=1&S<=312),'WK08:Subset','Invalid sensed subset.');
if numel(S)==312,assert(isequal(S,1:312),'WK08:Order','Full subset must preserve order.');end
bc=[m '/Battery Control'];target=[bc '/min-max T'];ph=get_param(target,'PortHandles');
src=get_param(get_param(ph.Inport(1),'Line'),'SrcPortHandle');
before=WK08_structFingerprint(m);measured=src;
if b~=0 || ~isequal(S,1:312)
 % Single channel edit in original coordinates, followed by actual vector
 % selection: excluded channels cannot reach either min or max reduction.
 p=[bc '/WK08 measurement'];add_block('simulink/User-Defined Functions/MATLAB Function',p);
 sf=sfroot;ch=sf.find('-isa','Stateflow.EMChart','Path',p);
 ch.Script=sprintf(['function y=measurement(T)\n%%#codegen\n' ...
  'x=T;\nx(%d)=T(%d)+%.17g;\ny=x(%s);\nend\n'],j,j,b,mat2str(S));
 h=get_param(p,'PortHandles');delete_line(bc,src,ph.Inport(1));
 add_line(bc,src,h.Inport(1),'autorouting','on');
 add_line(bc,h.Outport(1),ph.Inport(1),'autorouting','on');measured=h.Outport(1);
else
 assert(isequaln(before,WK08_structFingerprint(m)), ...
  'WK08:DefaultParity','Default injection changed the model structure.');
end
proof=struct('bias_K',b,'channel',j,'subset',S,'truePort',src, ...
 'measuredPort',measured,'defaultStructuralParity',b==0&&isequal(S,1:312));
end
