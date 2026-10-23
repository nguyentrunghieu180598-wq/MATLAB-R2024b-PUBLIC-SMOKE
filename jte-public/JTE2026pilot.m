function receipt=JTE2026pilot(modelsFolder,baselineFolder,channel,biasK,horizon,outDir)
% G6 local bias only after explicit human scientific acceptance of B0/C0.
% Protects model file; stores exact inputs, outputs and provenance.
validateattributes(channel,{'double'},{'scalar','integer','positive','finite'});
validateattributes(biasK,{'double'},{'scalar','real','finite','negative'});
validateattributes(horizon,{'double'},{'scalar','real','finite','positive'});
modelsFolder=char(modelsFolder);baselineFolder=char(baselineFolder);outDir=char(outDir);
model='JTE2026LocalBias';mdl=fullfile(modelsFolder,[model '.slx']);
assert(isfile(mdl),'Generated study SLX missing.');
assert(isfile(fullfile(baselineFolder,'JTE2026B0C0receipt.mat')), ...
    'G5 receipt absent; STOP.');
L=load(fullfile(baselineFolder,'JTE2026B0C0receipt.mat'),'receipt');
assert(isfield(L,'receipt') && isfield(L.receipt,'G5_PASS') && L.receipt.G5_PASS, ...
 'Recorded G5 acceptance missing/false; STOP.');
assert(L.receipt.horizon_s==horizon,'B0/C0 comparison must use same horizon.');
assert(strcmp(L.receipt.C0_sha,JTE2026sha256(mdl)), ...
  'Study SLX changed after G5 PASS. Revalidate paired B0/C0.');
if ~isfolder(outDir),mkdir(outDir);end
assert(~bdIsLoaded(model),'Model is already loaded.');
load_system(mdl);done=onCleanup(@()close_system(model,0));
in=Simulink.SimulationInput(model);
in=in.setVariable('jteChannelIndex',channel,'Workspace',model);
in=in.setVariable('jteBiasK',biasK,'Workspace',model);
in=in.setModelParameter('StopTime',num2str(horizon,17));
result=sim(in);
[tTrue,xTrue]=JTE2026timeseries(result,'jteTmaxTrue');
[tMeas,xMeas]=JTE2026timeseries(result,'jteTmaxMeas');
assert(isequal(tTrue,tMeas),'Missing matched true/measured Tmax time grids');
receipt=struct('scenario','LOCAL_SINGLE_CHANNEL_NEGATIVE_BIAS', ...
  'channel',channel,'biasK',biasK,'horizon_s',horizon, ...
  'modelSHA256',JTE2026sha256(mdl),'solver',get_param(model,'Solver'), ...
  'time',datestr(now,31),'peakTmaxTrue_K',max(xTrue(:)), ...
  'minMeasuredMinusTrueTmax_K',min(xMeas(:)-xTrue(:)));
% Do NOT label FlwR_calc output as physical mass flow or pump energy.
save(fullfile(outDir,'JTE2026BiasRaw.mat'),'result','receipt','-v7.3');
writetable(table(tTrue,xTrue(:),xMeas(:), ...
   'VariableNames',{'time_s','TmaxTrue_K','TmaxMeasured_K'}), ...
   fullfile(outDir,'JTE2026BiasTmax.csv'));
fprintf('PILOT RUN completed, not yet scientifically validated.\n');
end
