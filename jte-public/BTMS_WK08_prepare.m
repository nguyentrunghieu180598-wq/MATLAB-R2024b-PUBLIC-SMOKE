function p=BTMS_WK08_prepare(source,target,privateDir,sourceSHA,stopTime,scenario)
% Isolated M2 B0L10ms clone; no initialize(), compile or simulation.
% Static synthetic-graph test entry: no source file, compile or simulation.
if nargin==3 && strcmp(source,'WK10_SCENARIO_ONLY')
 p=insertScenario(target,privateDir);return;
end
if nargin<6,scenario=[];end
assert(any(stopTime==[5 340]),'WK08:Horizon','Only owner-local 5s or R1 340s.');
p=BTMS_M2_prepare340NoRun(source,target,privateDir,sourceSHA);
[~,m]=fileparts(target);load_system(target);
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
bc=[m '/Battery Control'];
% R1 is neutral only. Non-neutral injection is source-delivered for later review.
p.injection=BTMS_WK08_inject(m,0,1,1:312);
assert(p.injection.identityBypass,'WK08:R1Fault','R1 must be unbiased/all sensed.');
% Retain four native roles, rebind to constant private basenames.
roles={'uCore','uSampled','actuatorY','Ttrue312'};
for k=1:4
 sink=p.fourLoggerPaths{k};file=fullfile(privateDir,['WK08_' roles{k} '.mat']);
 assert(~isfile(file),'WK08:OutputExists','Never overwrite evidence.');
 set_param(sink,'FileName',file,'MatrixName',['WK08_' roles{k}]);
 p.privateTargets{k}=file;
end
tp=p.injection.truePort;
mx=[bc '/WK08 true max'];
add_block('simulink/Math Operations/MinMax',mx,'Function','max','Inputs','1');
h=get_param(mx,'PortHandles');add_line(bc,tp,h.Inport(1),'autorouting','on');
red=get_param([bc '/min-max T'],'PortHandles');
pump=get_param([bc '/Pump power calc'],'PortHandles');
% Sampling is on an observer branch only; native Ttrue312 is also retained.
dec=[bc '/WK08 T observation 1s'];
add_block('simulink/Discrete/Zero-Order Hold',dec,'SampleTime','1');
d=get_param(dec,'PortHandles');add_line(bc,tp,d.Inport(1),'autorouting','on');
names={'TmaxTrue','TmaxMeas','pumpPower','Ttrue312_1s'};
ports=[h.Outport(1) red.Outport(2) pump.Outport(1) d.Outport(1)];
for k=1:4
 sink=[bc '/WK08 log ' names{k}];file=fullfile(privateDir,['WK08_' names{k} '.mat']);
 assert(~isfile(file),'WK08:OutputExists','Never overwrite evidence.');
 rate='-1';if k==4,rate='1';end
 add_block('simulink/Sinks/To File',sink,'FileName',file, ...
  'MatrixName',['WK08_' names{k}],'SaveFormat','Timeseries', ...
  'SampleTime',rate,'Decimation','1');
 s=get_param(sink,'PortHandles');add_line(bc,ports(k),s.Inport(1),'autorouting','on');
 p.privateTargets{end+1}=file;p.fourLoggerPaths{end+1}=sink;
end
set_param(m,'StopTime',num2str(stopTime));
assert(strcmp(get_param(m,'Solver'),'ode23t') && ...
 str2double(get_param(m,'MaxStep'))==.05 && ...
 str2double(get_param(m,'StartTime'))==0 && ...
 strcmp(get_param(m,'LoadInitialState'),'off'), ...
 'WK08:Config','Require pinned solver and direct source initialization.');
p.roles=[roles names];p.stopTime_s=stopTime;
if ~isempty(scenario)
 assert(stopTime==scenario.T,'WK10:Horizon','Scenario horizon mismatch.');
 p.scenarioDelta=insertScenario(m,scenario);
end
p.fingerprint=BTMS_WK08_structFingerprint(m);
p.t0='DIRECT_START_HIDDEN_SIMSCAPE_IC_NOT_CERTIFIED';
save_system(m,target);
p.derivativeSHA256=JTE2026sha256(target);
assert(strcmp(JTE2026sha256(source),sourceSHA),'WK08:SourceSHA','M2 source changed.');
end

function delta=insertScenario(m,s)
% A single declared root input change; all internal controller/plant blocks retained.
assert(strcmp(s.scenario_id,'D13_K2_T340_V1') && isequal(s.k,2) && isequal(s.T,340), ...
 'WK10:Scenario','Only the reviewed k=2 / 340s scenario is declared.');
assert(strcmp(s.model_sha256,'0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0') && ...
 strcmp(s.vendor_mat_sha256,'a6b9e9353cadf2819255e55c1bcaf7beee439345311d2d0de30220e8e36e6986') && ...
 strcmp(s.gain_block_path,'$ROOT/WK10 scenario current scale') && ...
 strcmp(s.expected_edge.source,'$ROOT/Current demand') && s.expected_edge.source_port==1 && ...
 strcmp(s.expected_edge.destination,'$ROOT/Battery Control') && s.expected_edge.destination_port==2, ...
 'WK10:Scenario','Scenario provenance or edge mismatch.');
src=[m '/Current demand'];dst=[m '/Battery Control'];gain=[m '/WK10 scenario current scale'];
assert(getSimulinkBlockHandle(gain)==-1 && strcmp(get_param(src,'BlockType'),'FromFile') && ...
 strcmp(get_param(src,'FileName'),'Battery_Pack_Thermal_Management_Ivst.mat') && ...
 strcmp(get_param(src,'SampleTime'),'0'),'WK10:Demand','Unexpected demand source.');
sp=get_param(src,'PortHandles');dp=get_param(dst,'PortHandles');
assert(numel(sp.Outport)==1 && numel(dp.Inport)>=2,'WK10:Edge','Unexpected ports.');
line=get_param(dp.Inport(2),'Line');
assert(line~=-1 && get_param(line,'SrcPortHandle')==sp.Outport(1) && ...
 isequal(get_param(line,'DstPortHandle'),dp.Inport(2)), ...
 'WK10:Edge','Require the original unbranched demand edge.');
before=BTMS_WK08_structFingerprint(m);
delete_line(line);
add_block('simulink/Math Operations/Gain',gain,'Gain',num2str(s.k,17), ...
 'Multiplication','Element-wise(K.*u)','Position',[35 -825 75 -785]);
gp=get_param(gain,'PortHandles');
add_line(m,sp.Outport(1),gp.Inport(1),'autorouting','on');
add_line(m,gp.Outport(1),dp.Inport(2),'autorouting','on');
assert(isequal(get_param(get_param(gp.Inport(1),'Line'),'DstPortHandle'),gp.Inport(1)) && ...
 get_param(get_param(gp.Inport(1),'Line'),'SrcPortHandle')==sp.Outport(1) && ...
 isequal(get_param(get_param(dp.Inport(2),'Line'),'DstPortHandle'),dp.Inport(2)) && ...
 get_param(get_param(dp.Inport(2),'Line'),'SrcPortHandle')==gp.Outport(1), ...
 'WK10:Edge','Scaled edge differs from declared bridge.');
after=BTMS_WK08_structFingerprint(m);retained=after;
g='$ROOT/WK10 scenario current scale';source='$ROOT/Current demand';dest='$ROOT/Battery Control';
ix=strcmp(retained.blocks(:,1),g);
assert(nnz(ix)==1,'WK10:Delta','Exactly one new Gain required.');
retained.blocks(ix,:)=[];
retained.comments(strcmp(retained.comments(:,1),g),:)=[];
retained.connectivity(strcmp(retained.connectivity(:,1),g),:)=[];
% Undo only the two canonical endpoint substitutions in the comparison copy.
% The actual model and saved fingerprint retain the Gain and both new edges.
for k=1:size(retained.connectivity,1)
 c=retained.connectivity{k,2};
 for j=1:numel(c)
  if strcmp(retained.connectivity{k,1},source)
   c{j}{4}=cellfun(@(x)strrep(x,[g ':index0#0'],[dest ':index0#1']),c{j}{4},'UniformOutput',false);
  elseif strcmp(retained.connectivity{k,1},dest)
   c{j}{2}=cellfun(@(x)strrep(x,g,source),c{j}{2},'UniformOutput',false);
  end
 end
 retained.connectivity{k,2}=c;
end
assert(isequaln(before,retained),'WK10:RetainedGraph', ...
 'Anything beyond the declared input Gain/edge changed (including solver, workspace, IC or scripts).');
delta=struct('scenario',s,'before',before,'after',after, ...
 'addedBlock',s.gain_block_path,'originalEdge',s.expected_edge, ...
 'retainedGraphConfigWorkspaceScriptsEqual',true);
end
