function record=JTE056collect(out,model,files,caseName,profile,input)
% Call after successful simulation in fresh build directory. No interpolation.
isDiagnostic=strcmp(caseName,'C0_diagnostic20');
assert(isDiagnostic||ismember(caseName,{'B0L_original','C0_original','B0L_fine','C0_fine'}),'JTE056:UnknownCase');
if isDiagnostic,expectedStop=20;else,expectedStop=2400;end
record=struct('schema','JTE056_NATIVE_V1','caseName',caseName,'profile',profile, ...
 'matlabVersion',version,'matlabRelease',version('-release'),'products',ver, ...
 'sourceSHA256',files.sourceSHA256,'generatedModelSHA256','', ...
 'timestamps','native nondecreasing; duplicates retained in recorded order', ...
 'units',struct('temperature','K','time','s','jteUcore','1 normalized command', ...
 'jteFlwR','1 normalized post-TransferFcn actuator command, NOT volumetric flow or pump power'));
if startsWith(caseName,'B0L'), modelFile=files.baseline;else,modelFile=files.study;end
record.generatedModelSHA256=JTE2026sha256(modelFile);
assert(isa(input,'Simulink.SimulationInput'),'JTE056:MissingInputContract');
assert((isDiagnostic&&strcmp(profile,'original'))||endsWith(caseName,['_',profile]),'JTE056:ProfileMismatch');
record.simulationMetadata=out.SimulationMetadata;
record.inputOverrides=struct('Variables',{input.Variables},'ModelParameters',{input.ModelParameters});
required={'Solver','SolverType','StartTime','StopTime','MaxStep','MinStep','InitialStep', ...
 'RelTol','AbsTol','FixedStep','ZeroCrossControl','LoadInitialState','InitialState', ...
 'SaveFinalState','SaveOperatingPoint','SimulationMode'};
record.solver=struct();
for i=1:numel(required)
 key=required{i}; value=get_param(model,key);
 for j=1:numel(input.ModelParameters)
  if strcmp(input.ModelParameters(j).Name,key),value=input.ModelParameters(j).Value;end
 end
 record.solver.(key)=value;
end
assert(str2double(record.solver.StartTime)==0&&str2double(record.solver.StopTime)==expectedStop,'JTE056:G5Horizon');
record.solverEvidenceLimit='Merged pre-run model configuration and requested SimulationInput overrides; inspect SimulationMetadata warnings before declaring effective application. Local Simscape solver details remain source/mask-defined.';
assert(strcmp(record.solver.LoadInitialState,'off'),'JTE056:ExternalInitialState','External initial state requires separately hashed state asset.');
% Resolve load file from pinned FromFile source. Fail if path cannot be proved.
loadBlock=[model '/Current demand'];
assert(strcmp(get_param(loadBlock,'BlockType'),'FromFile'),'JTE056:LoadSource');
loadName=get_param(loadBlock,'FileName'); loadPath=which(loadName);
assert(~isempty(loadPath)&&isfile(loadPath),'JTE056:MissingLoadFile');
record.load=struct('block',loadBlock,'filename',loadName,'SHA256',JTE2026sha256(loadPath));
mw=get_param(model,'ModelWorkspace');
record.ambient=evalin(mw,'jte056AmbientProvenance');
% Snapshot cached, resolved variables after actual compile/sim. Includes IC
% parameters, load/config workspace inputs; NOT a complete Simscape state dump.
usage=Simulink.findVars(model,'SearchMethod','cached');
record.resolvedVariables=struct('name',{},'sourceType',{},'source',{},'value',{});
record.resolvedVariableNames={usage.Name};
for k=1:numel(usage)
 name=usage(k).Name; source=usage(k).Source; sourceType=usage(k).SourceType;
 assert(isvarname(name),'JTE056:VariableName');
 if strcmp(sourceType,'model workspace')
   sourceWorkspace=get_param(source,'ModelWorkspace');
   value=getVariable(sourceWorkspace,name);
 elseif strcmp(sourceType,'base workspace')
   value=evalin('base',name);
 elseif strcmp(sourceType,'mask workspace')
   % Public read-only mask API; preserve defining block and duplicate names.
   mask=Simulink.Mask.get(source);
   assert(~isempty(mask),'JTE056:MissingMask','No mask at %s',source);
   variables=mask.getWorkspaceVariables();
   ix=find(strcmp({variables.Name},name));
   assert(numel(ix)==1,'JTE056:MaskVariable','Cannot resolve %s in %s',name,source);
   value=variables(ix).Value;
 else
   error('JTE056:UnsupportedVariableSource','Uncaptured source for %s: %s',name,sourceType);
 end
 record.resolvedVariables(end+1)=struct('name',name,'sourceType',sourceType, ...
   'source',source,'value',{value}); %#ok<AGROW>
end
record.initialConditionsCoverage='Resolved workspace IC parameters plus effective config. Internal Simscape default ICs remain source-model-defined; compare source SHA and identical snapshots.';
names={'jteTtrue','jteTmaxTrue','jteTminTrue','jteUcore','jteFlwR','jteAmbient'};
if startsWith(caseName,'C0'),names=[names,{'jteTmeas','jteTmaxMeas','jteTminMeas'}];end
record.signalData=struct();
for k=1:numel(names)
 [t,x]=JTE2026timeseries(out,names{k});
 record.signalData.(names{k})=struct('time_s',t,'values',x);
end
trueT=record.signalData.jteTtrue;
assert(size(trueT.values,2)==312,'JTE056:ChannelCount');
assert(trueT.time_s(1)==0&&trueT.time_s(end)==str2double(record.solver.StopTime),'JTE056:Horizon');
checkReducer(record.signalData,'True');
if startsWith(caseName,'C0')
 measT=record.signalData.jteTmeas;
 assert(size(measT.values,2)==312,'JTE056:ChannelCount');
 assert(isequal(trueT.time_s,measT.time_s),'JTE056:ZeroBiasClockMismatch');
 assert(isequal(trueT.values,measT.values),'JTE056:ZeroBiasVectorMismatch');
 checkReducer(record.signalData,'Meas');
 vars=input.Variables; foundBias=false;foundChannel=false;
 for j=1:numel(vars)
  if strcmp(vars(j).Name,'jteBiasK')&&strcmp(vars(j).Workspace,model)
   assert(~foundBias&&isequal(vars(j).Value,0),'JTE056:BiasInjection');foundBias=true;
  elseif strcmp(vars(j).Name,'jteChannelIndex')&&strcmp(vars(j).Workspace,model)
   validateattributes(vars(j).Value,{'double'},{'scalar','integer','>=',1,'<=',312});foundChannel=true;
  end
 end
 assert(foundBias&&foundChannel,'JTE056:MissingInjectionContract');
 record.injectionEvidenceLimit='Explicit SimulationInput overrides plus output vector identity; zero output identity alone cannot distinguish zero parameter from a callback resetting it. Pre-run callback suppression/check remains required.';
end
amb=record.signalData.jteAmbient;
assert(all(amb.values(:)==record.ambient.valueK),'JTE056:AmbientMismatch');
record.signalData.jteTminTrue.columns={'Tmin_K','Tmax_K'};
if startsWith(caseName,'C0'),record.signalData.jteTminMeas.columns={'Tmin_K','Tmax_K'};end
record.clocks.tout=out.get('tout');
end
function checkReducer(data,suffix)
if strcmp(suffix,'True'),vec=data.jteTtrue;else,vec=data.jteTmeas;end
pair=data.(['jteTmin' suffix]); mx=data.(['jteTmax' suffix]);
assert(size(pair.values,2)==2&&size(mx.values,2)==1,'JTE056:ReducerSchema');
assert(isequal(pair.time_s,vec.time_s)&&isequal(mx.time_s,vec.time_s),'JTE056:ReducerClock');
assert(isequal(pair.values(:,1),min(vec.values,[],2)),'JTE056:ReducerMin');
assert(isequal(pair.values(:,2),max(vec.values,[],2))&&isequal(mx.values,max(vec.values,[],2)),'JTE056:ReducerMax');
end
