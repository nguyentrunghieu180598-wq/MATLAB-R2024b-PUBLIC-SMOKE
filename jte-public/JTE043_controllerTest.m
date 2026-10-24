function result=JTE043_controllerTest(sourceFile)
% Clone the ACTUAL source controller; all inputs/outputs below are synthetic.
load_system(sourceFile);[~,vendor]=fileparts(sourceFile);
source=[vendor '/Battery Control/FlwR_calc'];
blocks=find_system(source,'LookUnderMasks','all','FollowLinks','off','Type','Block');
allowed={'SubSystem','Inport','Outport','Constant','Sum','Gain','Saturate','MinMax','Math'};
meta=struct('path',{},'type',{},'parameters',{});
for k=1:numel(blocks)
 b=blocks{k};ty=get_param(b,'BlockType');
 assert(ismember(ty,allowed),'JTE043:StatefulOrUnknownBlock');
 pars=struct();keys={'Value','Gain','Inputs','Function','Operator','UpperLimit','LowerLimit','SampleTime'};
 obj=get_param(b,'ObjectParameters');
 for z=1:numel(keys),if isfield(obj,keys{z}),pars.(keys{z})=get_param(b,keys{z});end,end
 meta(end+1)=struct('path',b,'type',ty,'parameters',pars); %#ok<AGROW>
end
assert(strcmp(get_param([source '/FlwR calc/Subtract'],'Inputs'),'+-'));
assert(str2double(get_param([source '/FlwR calc/Gain1'],'Gain'))==0.1);
assert(str2double(get_param([source '/FlwR calc/Saturation'],'LowerLimit'))==0.001);
assert(str2double(get_param([source '/FlwR calc/Saturation'],'UpperLimit'))==0.95);
assert(strcmp(get_param([source '/Step Change/Mod'],'Operator'),'mod'));
assert(strcmp(get_param([source '/Step Change/Subtract1'],'Inputs'),'+-'));
assert(strcmp(get_param([source '/Step Change/MinMax4'],'Function'),'max'));
assert(str2double(get_param([source '/step'],'Value'))==0.25);
h='JTE043SyntheticController';new_system(h);
guard=onCleanup(@()close_system(h,0)); %#ok<NASGU>
set_param(h,'SolverType','Fixed-step','Solver','FixedStepDiscrete','FixedStep','1','ReturnWorkspaceOutputs','on');
d=[-10 0 2.5 5-1e-9 5 5+1e-9 7.5-1e-9 7.5 7.5+1e-9 9.5 20]';
a=kron([280;300;320],ones(numel(d),1));delta=repmat(d,3,1);
% Forward then reverse history with identical values at corresponding samples.
a=[a;flipud(a)];delta=[delta;flipud(delta)];
n=numel(a);t=(0:n-1)';m=a+delta;
T=[m,m-3,m-5];Tm=T;Tm(:,1)=Tm(:,1)-2;
baseline=m+0.4*sin(t);
arrays={max(Tm,[],2),m,baseline,a};vars={'faultInput','shadowInput','baselineInput','ambientInput'};
for k=1:4
 add_block('simulink/Sources/From Workspace',[h '/' vars{k}], ...
  'VariableName',vars{k},'Interpolate','off','SampleTime','1','OutputAfterFinalValue','Holding final value');
end
labels={'fault','shadow','baseline'};
for k=1:3
 add_block(source,[h '/' labels{k}]);
 add_line(h,[vars{k} '/1'],[labels{k} '/1']);
 add_line(h,'ambientInput/1',[labels{k} '/2']);
 add_block('simulink/Sinks/To Workspace',[h '/' labels{k} 'Log'], ...
  'VariableName',[labels{k} 'Output'],'SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1','SampleTime','1');
 add_line(h,[labels{k} '/1'],[labels{k} 'Log/1']);
end
set_param(h,'StopTime',num2str(t(end)));
mw=get_param(h,'ModelWorkspace');
for k=1:4,assignin(mw,vars{k},timeseries(arrays{k},t));end
feval(h,[],[],[],'compile');
sampleTime=get_param([h '/fault'],'CompiledSampleTime');
ports=get_param([h '/fault'],'CompiledPortDimensions');
feval(h,[],[],[],'term');
in=Simulink.SimulationInput(h);
for k=1:4,in=in.setVariable(vars{k},timeseries(arrays{k},t),'Workspace',h);end
out=sim(in);
u=cell(1,3);res=zeros(1,3);
for k=1:3
 sig=out.get([labels{k} 'Output']);assert(isa(sig,'timeseries'));
 assert(isequal(sig.Time(:),t),'JTE043:SyntheticTimeMismatch');
 u{k}=double(sig.Data(:));
 ref=JTE043_law(arrays{k},a);res(k)=max(abs(u{k}-ref));
 assert(res(k)<1e-12,'JTE043:ActualControllerLawMismatch');
end
half=n/2;
assert(max(abs(u{1}(1:half)-flipud(u{1}(half+1:end))))<1e-12,'JTE043:HistoryDependence');
direct=u{1}-u{2};state=u{2}-u{3};total=u{1}-u{3};
decomp=max(abs(total-(direct+state)));assert(decomp<1e-12);
levels=unique(u{2});assert(isequal(levels(:),[0.25;0.5;0.75]));
result=struct('scope','SYNTHETIC_CONTROLLER_ONLY_NOT_BATTERY_RESULTS', ...
 'blocks',{meta},'memorylessSupportedByWhitelistAndHistoryProbe',true, ...
 'compiledSampleTime',{sampleText(sampleTime)},'compiledPortDimensions',ports, ...
 'samples',n,'lawMaxAbsResidual',res,'decompositionMaxAbsResidual',decomp, ...
 'syntheticLevels',levels,'effectiveTemperatureOffsets_K',[5 7.5], ...
 'rawSaturationThresholdOffsets_K',[0.01 9.5], ...
 'warning','0.01 and 9.5 K are saturation breakpoints, not effective output switching thresholds; finite precision near boundaries applies');
fprintf('JTE043 ACTUAL CONTROLLER SYNTHETIC PASS samples=%d lawResidual=%.17g decompResidual=%.17g\n',n,max(res),decomp);
end

function out=sampleText(st)
if iscell(st),out=cellfun(@mat2str,st,'UniformOutput',false);else,out=mat2str(st);end
end
