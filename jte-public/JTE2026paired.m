function receipt=JTE2026paired(modelsFolder,horizon,outputFolder,solverOverride)
% G4/G5: run instrumented baseline B0L and zero-bias C0,
% on matched solver/load/IC/horizon; explicitly align unequal variable-step grids.
% NOT a numeric PASS until independent solver convergence evidence exists.
validateattributes(horizon,{'double'},{'scalar','finite','positive'});
if nargin<4 || isempty(solverOverride), solverOverride=struct(); end
assert(isstruct(solverOverride) && isscalar(solverOverride), ...
 'solverOverride must be a scalar struct.');
allowed={'RelTol','AbsTol','MaxStep'};
provided=fieldnames(solverOverride);
assert(all(ismember(provided,allowed)), ...
 'Unsupported solverOverride field; no solver change permitted.');
for z=1:numel(provided)
    v=solverOverride.(provided{z});
    assert(ischar(v)||isstring(v),'Override must be string-like.');
    v=char(v);
    if ~(strcmp(v,'auto') && ~strcmp(provided{z},'RelTol'))
        assert(isfinite(str2double(v)) && str2double(v)>0, ...
            'Only positive numeric solver override or supported auto allowed.');
    end
    solverOverride.(provided{z})=v;
end
modelsFolder=char(modelsFolder);outputFolder=char(outputFolder);
bFile=fullfile(modelsFolder,'JTE2026B0L.slx');
cFile=fullfile(modelsFolder,'JTE2026LocalBias.slx');
assert(isfile(bFile)&&isfile(cFile),'Both generated model files are required.');
assert(~bdIsLoaded('JTE2026B0L')&&~bdIsLoaded('JTE2026LocalBias'), ...
    'Please close model windows before paired run.');
if ~isfolder(outputFolder),mkdir(outputFolder);end
receipt=struct('G5_PASS',false,'started',datestr(now,31),'horizon_s',horizon, ...
   'B0L_sha',JTE2026sha256(bFile),'C0_sha',JTE2026sha256(cFile));
base='JTE2026B0L';caseName='JTE2026LocalBias';
load_system(bFile);load_system(cFile);
cleanupObj=onCleanup(@()localClose());
params={'Solver','SolverType','RelTol','AbsTol','MaxStep','StartTime'};
for k=1:numel(params)
    assert(isequal(get_param(base,params{k}),get_param(caseName,params{k})), ...
        'B0/C0 config mismatch at %s.',params{k});
end

inB=Simulink.SimulationInput(base);
inC=Simulink.SimulationInput(caseName);
inC=inC.setVariable('jteChannelIndex',1,'Workspace',caseName);
inC=inC.setVariable('jteBiasK',0,'Workspace',caseName);
inB=inB.setModelParameter('StopTime',num2str(horizon,17));
inC=inC.setModelParameter('StopTime',num2str(horizon,17));
for z=1:numel(provided)
  key=provided{z};
  inB=inB.setModelParameter(key,solverOverride.(key));
  inC=inC.setModelParameter(key,solverOverride.(key));
end
B=sim(inB); C=sim(inC);
save(fullfile(outputFolder,'JTE2026B0C0raw.mat'),'B','C','receipt','-v7.3');
names={'jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient'};
epsVal=zeros(1,numel(names));
for i=1:numel(names)
    [tB,xB]=JTE2026timeseries(B,names{i});
    [tC,xC]=JTE2026timeseries(C,names{i});
    align(i)=JTE2026compareTraces(tB,xB,tC,xC,names{i}); %#ok<AGROW>
    epsVal(i)=align(i).maxAbs;
end
[tTrue,vTrue]=JTE2026timeseries(C,'jteTmaxTrue');
[tMeas,vMeas]=JTE2026timeseries(C,'jteTmaxMeas');
zeroAlign=JTE2026compareTraces(tTrue,vTrue,tMeas,vMeas,'C0 true vs measured');
residualZero=zeroAlign.maxAbs;
receipt.signalNames=names; receipt.maxAbsResidual=epsVal;
receipt.alignment=align; receipt.zeroBiasAlignment=zeroAlign;
receipt.alignmentWarning='Linear union grid: discontinuity and solver convergence review needed';
receipt.solverConfig=struct('Solver',get_param(base,'Solver'), ...
 'RelTol',get_param(base,'RelTol'),'AbsTol',get_param(base,'AbsTol'), ...
 'MaxStep',get_param(base,'MaxStep'), ...
 'StartTime',get_param(base,'StartTime'));
for z=1:numel(provided)
  receipt.solverConfig.(provided{z})=solverOverride.(provided{z});
end
assert(all(isfinite(epsVal)) && isfinite(residualZero),'Invalid residual values.');
receipt.zeroBiasExtremaResidual_K=residualZero;
receipt.solver=get_param(base,'Solver');
receipt.modelRunSuccess=true;
receipt.G5_PASS=false; % Requires justified numerical tolerance review.
receipt.status='RUN COMPLETED; tolerance/sensitivity REVIEW REQUIRED';
save(fullfile(outputFolder,'JTE2026B0C0raw.mat'),'B','C','receipt','-v7.3');
writetable(table(names',epsVal','VariableNames',{'signal','maxAbsResidual'}), ...
   fullfile(outputFolder,'JTE2026B0C0residuals.csv'));
save(fullfile(outputFolder,'JTE2026B0C0receipt.mat'),'receipt');
fprintf('PAIRED RUN COMPLETE. Numerical gate G5 awaits tolerance review.\n');
for i=1:numel(names),fprintf('%s max abs residual=%g\n',names{i},epsVal(i));end
    function localClose()
      if bdIsLoaded(base),close_system(base,0);end
      if bdIsLoaded(caseName),close_system(caseName,0);end
    end
end
