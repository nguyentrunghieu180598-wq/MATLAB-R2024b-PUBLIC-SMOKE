function ci_jte_bias_exploratory_hot()
% EARLY NONCERTIFIED PILOT. G5 scientific acceptance is REQUIRED for use in Results.
% Run source-informed fixed hot channel selected from independent baseline.
runnerRoot=pwd; addpath(fullfile(runnerRoot,'jte-public'));
assert(strcmp(version('-release'),'2024b'),'Need R2024b');
source=fullfile(runnerRoot,'vendor-pack');
p=openProject(fullfile(source,'batteryExamplesProjectSetup.prj'));
pguard=onCleanup(@()closeProjectQuiet(p)); %#ok<NASGU>
models=JTE2026build(source,fullfile(runnerRoot,'generated-pilot'));
T=(0:1:2400)';
% Baseline used only to PRESELECT the channel and provide reference trace.
load_system(models.baseline);
s=Simulink.SimulationInput('JTE2026B0L');
s=s.setModelParameter('StartTime','0','StopTime','2400');
fprintf('EXPLORATORY_BASELINE_START\n');
B=sim(s);
[tv,xv]=JTE2026timeseries(B,'jteTtrue');
assert(size(xv,2)>=3,'Need >=3 resolved channels to rank');
mask=tv>=1800 & tv<=2400;
assert(nnz(mask)>=3,'Baseline thermal ranking not sampled sufficiently');
rankMean=mean(xv(mask,:),1);
[~,order]=sort(rankMean,'descend');
jHot=order(1);
assert(isfinite(jHot),'Hot-channel ranking invalid');
metric={'jteTmaxTrue','jteUcore','jteAmbient'};
base=struct();
for k=1:numel(metric)
    [t,x]=JTE2026timeseries(B,metric{k});
    full=numel(t)>1 && abs(t(1))<1e-6 && abs(t(end)-2400)<1e-6;
    sig=struct('full',full,'samples',numel(t),'sourceStart',t(1),'sourceEnd',t(end));
    if full,sig.values=interp1(t,x,T,'linear');
    else,sig.values=[];sig.originalEnd=x(end,:);end
    base.(metric{k})=sig;
end
clear B s xv tv
close_system('JTE2026B0L',0);
fprintf('EXPLORATORY_C1_START_NOMINAL_BIAS_NEGATIVE_K\n');
load_system(models.study);
Cinput=Simulink.SimulationInput('JTE2026LocalBias');
Cinput=Cinput.setVariable('jteChannelIndex',jHot,'Workspace','JTE2026LocalBias');
Cinput=Cinput.setVariable('jteBiasK',-2,'Workspace','JTE2026LocalBias');
Cinput=Cinput.setModelParameter('StartTime','0','StopTime','2400');
C=sim(Cinput);
tSolver=C.get('tout');
assert(numel(tSolver)>1 && abs(double(tSolver(end))-2400)<1e-6,'C1 did not reach full 2400s');
biased=struct();differences=struct();
for k=1:numel(metric)
    [t,x]=JTE2026timeseries(C,metric{k});
    full=numel(t)>1 && abs(t(1))<1e-6 && abs(t(end)-2400)<1e-6;
    sig=struct('full',full,'samples',numel(t),'sourceStart',t(1),'sourceEnd',t(end));
    if full,sig.values=interp1(t,x,T,'linear');
    else,sig.values=[];sig.originalEnd=x(end,:);end
    biased.(metric{k})=sig;
    if full && base.(metric{k}).full && ...
       isequal(size(sig.values),size(base.(metric{k}).values))
        differences.(metric{k})=max(abs(sig.values(:)-base.(metric{k}).values(:)));
    else
        differences.(metric{k})=NaN;
    end
end
pilot=struct('phase','EXPLORATORY_G6_NOT_FOR_MANUSCRIPT', ...
 'biasK',-2,'jHot',jHot,'rankingMethod','highest baseline mean 1800..2400s', ...
 'channelCount',numel(rankMean),'selectedMeanReferenceK',rankMean(jHot), ...
 'sourceSHA256',models.sourceSHA256, ...
 'baselineSHA256',JTE2026sha256(models.baseline), ...
 'studySHA256',JTE2026sha256(models.study), ...
 'Tgrid_s',T,'baseline',base,'biased',biased, ...
 'differences',differences,'status','G5_ACCEPTANCE_PENDING');
folder=fullfile(runnerRoot,'private-bias-pilot');
if ~isfolder(folder),mkdir(folder);end
save(fullfile(folder,'G6_EXPLORATORY_HOT_NEG2K.mat'),'pilot','-v7.3');
fprintf('EXPLORATORY_C1_HOT_2400_FINISH_SAVED_ENCRYPT_NEXT\n');
fprintf('Do not label these observations as accepted JTE Results until G5 is approved.\n');
end
function closeProjectQuiet(p)
try,close(p);catch,end
end
