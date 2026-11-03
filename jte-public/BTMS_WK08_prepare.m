function p=BTMS_WK08_prepare(source,target,privateDir,sourceSHA,stopTime)
% Isolated M2 B0L10ms clone; no initialize(), compile or simulation.
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
p.fingerprint=BTMS_WK08_structFingerprint(m);
p.t0='DIRECT_START_HIDDEN_SIMSCAPE_IC_NOT_CERTIFIED';
save_system(m,target);
p.derivativeSHA256=JTE2026sha256(target);
assert(strcmp(JTE2026sha256(source),sourceSHA),'WK08:SourceSHA','M2 source changed.');
end
