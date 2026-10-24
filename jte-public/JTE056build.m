function files=JTE056build(repoRoot,outputDir)
% Instrumented derivative only. Original builder/vendor bytes remain unchanged.
assert(nargin==2&&~isfolder(outputDir)&&~isfile(outputDir),'JTE056:FreshOutput','Choose nonexistent isolated outputDir.');
files=JTE2026build(repoRoot,outputDir);
paths={files.baseline,files.study};
try
 for k=1:numel(paths)
  [~,model]=fileparts(paths{k}); load_system(paths{k});
  % Legacy builder has already loaded/closed copied source once; its initial
  % PreLoadFcn/CloseFcn effects cannot be undone here (documented residual risk).
  set_param(model,'PreLoadFcn','','CloseFcn','');
  ctrl=[model '/Battery Control'];
  flow=[ctrl '/sensor dynamics 1']; f=[ctrl '/FlwR_calc'];
  assert(strcmp(get_param(flow,'BlockType'),'TransferFcn'),'JTE056:FlowBlock');
  assert(strcmp(get_param(flow,'SID'),'197'),'JTE056:FlowSID');
  assert(strcmp(get_param(flow,'Denominator'),'[1e-3 1]'),'JTE056:FlowFilter');
  ph=get_param(flow,'PortHandles'); fh=get_param(f,'PortHandles');
  assert(get_param(get_param(ph.Inport(1),'Line'),'SrcPortHandle')==fh.Outport(1),'JTE056:FlowWiring');
  sinks=get_param(get_param(ph.Outport(1),'Line'),'DstPortHandle');
  assert(~isempty(sinks),'JTE056:DisconnectedFlow');
  block=[ctrl '/JTE Downstream Flow'];
  assert(getSimulinkBlockHandle(block)==-1,'JTE056:LoggerConflict');
  add_block('simulink/Sinks/To Workspace',block,'VariableName','jteFlwR', ...
      'SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
  lh=get_param(block,'PortHandles');add_line(ctrl,ph.Outport(1),lh.Inport(1),'autorouting','on');
  logs=find_system(model,'LookUnderMasks','none','BlockType','ToWorkspace');
  for n=1:numel(logs)
   vn=get_param(logs{n},'VariableName');
   if startsWith(vn,'jte'),set_param(logs{n},'MaxDataPoints','inf','Decimation','1');end
  end
  ambient=[model '/Constant3'];
  assert(strcmp(get_param(ambient,'BlockType'),'Constant')&&strcmp(get_param(ambient,'SID'),'199'),'JTE056:AmbientSource');
  rootValue=slResolve(get_param(ambient,'Value'),ambient);
  validateattributes(rootValue,{'double'},{'real','scalar','finite'});
  mw=get_param(model,'ModelWorkspace');
  assignin(mw,'jte056AmbientProvenance',struct('block',ambient,'SID','199', ...
    'expression',get_param(ambient,'Value'),'valueK',rootValue,'unit','K','isConstant',true));
  save_system(model,paths{k});close_system(model,0);
  % Reopen and verify persisted downstream logger connection.
  load_system(paths{k}); lh=get_param(block,'PortHandles');ph=get_param(flow,'PortHandles');
  assert(get_param(get_param(lh.Inport(1),'Line'),'SrcPortHandle')==ph.Outport(1),'JTE056:SavedFlowWiring');
  close_system(model,0);
 end
 assert(strcmp(JTE2026sha256(fullfile(repoRoot,'Models','Battery_Pack_Thermal_Management.slx')),files.sourceSHA256),'JTE056:SourceChanged');
catch ME
 for k=1:numel(paths)
  [~,model]=fileparts(paths{k});
  if bdIsLoaded(model)
   try,set_param(model,'CloseFcn','');close_system(model,0);catch, end
  end
  if isfile(paths{k}),delete(paths{k});end
 end
 rethrow(ME);
end
end
