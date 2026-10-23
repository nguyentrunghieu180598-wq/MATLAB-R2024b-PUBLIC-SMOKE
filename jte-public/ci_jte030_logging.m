function ci_jte030_logging()
% Public code only. All values and diagnostics saved for encrypted transfer.
root=pwd; folder=fullfile(root,'private-jte030'); mkdir(folder);
try
    captured=evalc('payload=collect(root);');
    payload.console=captured;
    save(fullfile(folder,'logging_audit.mat'),'payload','-v7.3');
    fprintf('JTE030_LOGGING_EXECUTED_REVIEW_PENDING\n');
catch ME
    failure=struct('identifier',ME.identifier,'report',getReport(ME,'extended','hyperlinks','off'));
    save(fullfile(folder,'diagnostic_failure.mat'),'failure','-v7.3');
    fprintf('JTE030_LOGGING_FAILED_PRIVATE_DIAGNOSTIC_SAVED\n');
    error('JTE030:PrivateDiagnosticFailure','Diagnostic failed. Original error retained in private encrypted payload.');
end
end
function payload=collect(root)
assert(strcmp(version('-release'),'2024b'));
p=openProject(fullfile(root,'vendor-pack','batteryExamplesProjectSetup.prj'));
guard=onCleanup(@()quietClose(p));
files=JTE2026build(fullfile(root,'vendor-pack'),fullfile(root,'generated-jte030'));
paths={files.baseline,files.study}; payload=struct('version',version,'sourceSHA256',files.sourceSHA256);
for k=1:2
 [~,mdl]=fileparts(paths{k}); load_system(paths{k});
 bc=[mdl '/Battery Control']; block=[mdl '/Constant3'];
 assert(strcmp(get_param(block,'BlockType'),'Constant'));
 assert(strcmp(get_param(block,'SampleTime'),'inf'));
 value=slResolve(get_param(block,'Value'),block);
 assert(isnumeric(value)&&isscalar(value)&&isfinite(value));
 meta=struct('model',mdl,'constantPath',block,'expression',get_param(block,'Value'), ...
 'resolvedValue',value,'sampleTime',get_param(block,'SampleTime'), ...
 'modelHash',JTE2026sha256(paths{k}));
 reducers={[bc '/min-max T']};
 if k==2,reducers{2}=[bc '/JTE measured min-max T'];end
 meta.reducers=cell(size(reducers));
 for r=1:numel(reducers)
  blocks=find_system(reducers{r},'SearchDepth',1,'Type','Block');
  topology=cell(size(blocks));
  for z=1:numel(blocks)
   b=blocks{z}; entry=struct('path',b,'type',get_param(b,'BlockType'));
   if strcmp(entry.type,'MinMax'),entry.operation=get_param(b,'Function');end
   if strcmp(entry.type,'Outport')
    entry.port=get_param(b,'Port'); ph=get_param(b,'PortHandles');
    ln=get_param(ph.Inport(1),'Line');
    if ln~=-1,entry.source=get_param(get_param(ln,'SrcPortHandle'),'Parent');end
   end
   topology{z}=entry;
  end
  meta.reducers{r}=topology;
 end
 input=Simulink.SimulationInput(mdl);
 input=input.setModelParameter('StartTime','0','StopTime','20');
 if k==2
  input=input.setVariable('jteChannelIndex',1,'Workspace',mdl);
  input=input.setVariable('jteBiasK',0,'Workspace',mdl);
 end
 out=sim(input);
 names={'jteTtrue','jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient'};
 if k==2,names=[names,{'jteTmeas','jteTmaxMeas','jteTminMeas'}];end
 traces=struct();
 for z=1:numel(names)
  [t,x]=JTE2026timeseries(out,names{z});
  sig=out.get(names{z});
  traces.(names{z})=struct('time_s',t,'value',x,'units',sig.DataInfo.Units, ...
  'channels',size(x,2),'nSamples',numel(t));
  if strcmp(names{z},'jteAmbient')
   assert(all(x(:)==value),'Logged Ambient differs from resolved Constant3');
   traces.(names{z}).classification='constant_source_verified_no_synthetic_samples';
  else
   assert(numel(t)>1 && abs(t(1))<1e-8 && abs(t(end)-20)<1e-8);
   traces.(names{z}).classification='dynamic_full_horizon';
  end
 end
 record=struct('metadata',meta,'traces',traces);
 if k==1,payload.B0L=record;else,payload.C0=record;end
 close_system(mdl,0);
end
assert(isequal(payload.B0L.metadata.resolvedValue,payload.C0.metadata.resolvedValue));
payload.acceptance='G5_NOT_ACCEPTED_requires_private_2400s_solver_review';
end
function quietClose(p)
try,close(p);catch,end
end
