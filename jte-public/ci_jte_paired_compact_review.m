function ci_jte_paired_compact_review()
% G5 comparable 2400s B0L and C0 physical simulations.
% Runs sequentially, drops massive SimulationOutput between cases.
% Prints only diagnostic PASS/REVIEW; raw numeric residuals RSA-encrypted.
runnerRoot=pwd; addpath(fullfile(runnerRoot,'jte-public'));
assert(strcmpi(version('-release'),'2024b'),'Need MATLAB R2024b');
root=fullfile(runnerRoot,'vendor-pack');
project=openProject(fullfile(root,'batteryExamplesProjectSetup.prj'));
pGuard=onCleanup(@()closePrj(project)); %#ok<NASGU>
files=JTE2026build(root,fullfile(runnerRoot,'generated-comparison'));
names={'jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient'};
timeGrid=(0:1:2400)';
cases={'B0L','C0'};
data=cell(1,2);
meta=cell(1,2);
for idx=1:2
   caseName=cases{idx};
   if strcmp(caseName,'B0L'),f=files.baseline;else,f=files.study;end
   [~,mdl]=fileparts(f);
   load_system(f);
   input=Simulink.SimulationInput(mdl);
   input=input.setModelParameter('StartTime','0','StopTime','2400', ...
       'SaveTime','on','TimeSaveName','tout');
   if idx==2
       input=input.setVariable('jteChannelIndex',1,'Workspace',mdl);
       input=input.setVariable('jteBiasK',0,'Workspace',mdl);
   end
   fprintf('PAIR_LITE_START_%s_2400\n',caseName);
   tStart=tic;simResult=sim(input);
   tCPU=toc(tStart);
   tsolver=simResult.get('tout');
   assert(isnumeric(tsolver) && numel(tsolver)>1 ...
       && abs(double(tsolver(end))-2400)<1e-6, ...
       'Physical model did not reach 2400 seconds');
   desc=struct('caseName',caseName,'horizon_s',2400, ...
       'elapsedWall_s',tCPU,'solver',get_param(mdl,'Solver'), ...
       'solverPoints',numel(tsolver), ...
       'modelSHA256',JTE2026sha256(f));
   compact=struct();
   for k=1:numel(names)
       [t,x]=JTE2026timeseries(simResult,names{k});
       hasFull=(numel(t)>1 && abs(t(1))<=1e-6 ...
          && abs(t(end)-2400)<=1e-6);
       compact.(names{k})=struct('full',hasFull,'start_s',t(1), ...
            'finish_s',t(end),'samples',numel(t),'channels',size(x,2));
       if hasFull
           v=interp1(t,x,timeGrid,'linear');
           assert(all(isfinite(v(:))),'Bad sampled data');
           compact.(names{k}).value=v;
       else
           compact.(names{k}).value=[];
           compact.(names{k}).lastObserved=x(end,:);
       end
   end
   if idx==2
      [t1,x1]=JTE2026timeseries(simResult,'jteTmaxTrue');
      [t2,x2]=JTE2026timeseries(simResult,'jteTmaxMeas');
      zero=JTE2026compareTraces(t1,x1,t2,x2,'C0_Tmax_true_meas_b0');
      [t3,x3]=JTE2026timeseries(simResult,'jteTminTrue');
      [t4,x4]=JTE2026timeseries(simResult,'jteTminMeas');
      zeroMin=JTE2026compareTraces(t3,x3,t4,x4,'C0_Tmin_true_meas_b0');
   end
   data{idx}=compact;meta{idx}=desc;
   clear simResult input tsolver
   close_system(mdl,0);
   fprintf('PAIR_LITE_FINISHED_%s_2400 elapsed=%g\n',caseName,tCPU);
end
residual=struct();
coverage=true;
for k=1:numel(names)
    n=names{k};
    a=data{1}.(n);b=data{2}.(n);
    both=a.full && b.full && ~isempty(a.value) && ~isempty(b.value) ...
         && isequal(size(a.value),size(b.value));
    coverage=coverage && both;
    if both
        residual.(n)=max(abs(a.value(:)-b.value(:)));
        assert(isfinite(residual.(n)),'Non-finite paired numeric difference');
    else
        residual.(n)=NaN;
    end
end
zeroBiasVerified=zero.nCompare>=2 && zeroMin.nCompare>=2 ...
    && zero.timeStart_s<=1e-6 && zero.timeEnd_s>=2400-1e-6 ...
    && zeroMin.timeStart_s<=1e-6 && zeroMin.timeEnd_s>=2400-1e-6 ...
    && zero.maxAbs<=1e-10 && zeroMin.maxAbs<=1e-10;
review=struct('matlab',version,'B0L',meta{1},'C0',meta{2}, ...
    'sourceSHA256',files.sourceSHA256, ...
    'grid_s',timeGrid,'signals',{names},'data',{data}, ...
    'residual',residual, ...
    'fullLoggingCoverage',coverage,'zeroBiasTrueMeasuredVerified',zeroBiasVerified,...
    'zeroBiasMax',zero,'zeroBiasMin',zeroMin, ...
    'status','REQUIRES_SOLVER_SENSITIVITY_AND_REVIEW');
folder=fullfile(runnerRoot,'private-paired-lite');
if ~isfolder(folder),mkdir(folder);end
save(fullfile(folder,'JTE_G5_B0L_C0_2400_residuals.mat'),'review','-v7.3');
fprintf('G5_PAIR_2400_EXECUTED fullSignalCoverage=%d zeroBiasTrueMeasuredVerified=%d\n', ...
    coverage,zeroBiasVerified);
fprintf('G5_STILL_PENDING_SOLVER_REVIEW_UNITS_THRESHOLDS\n');
end
function closePrj(p)
try,close(p);catch,end
end
