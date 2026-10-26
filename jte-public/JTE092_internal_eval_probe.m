function JTE092_internal_eval_probe()
% No solver/tolerance/physical edits. Fresh derivative, source-only diagnostics.
% No MAT, state values, event times or plots published by this workflow.
assert(strcmp(version('-release'),'2024b'),'JTE092:Release');
assert(contains(version,'24.2.0.3361896'),'JTE092:Update10');
calibration=canary();
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE092:Pin');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()closeProjectQuiet(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte092-generated'));
[~,mdl]=fileparts(files.baseline);load_system(files.baseline);
mg=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
tf=[mdl '/Battery Control/sensor dynamics 1'];core=[mdl '/Battery Control/FlwR_calc'];
assert(strcmp(get_param(tf,'SID'),'197'),'JTE092:SID');
assert(strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE092:TF');
ph=get_param(tf,'PortHandles');ch=get_param(core,'PortHandles');
assert(get_param(get_param(ph.Inport(1),'Line'),'SrcPortHandle')==ch.Outport(1),'JTE092:Wiring');
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','SolverResetMethod','ZeroCrossControl'};
before=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(strcmp(before{1},'ode23t'),'JTE092:Solver');
assert(isempty(get_param(mdl,'StartFcn')),'JTE092:ExistingCallback');
cap=JTE089Capture(tf,core,[330 338]);assignin('base','jte089Capture',cap);
srcBlocks={[core '/FlwR calc/Gain1'],[core '/FlwR calc/Saturation'],[core '/Step Change/Mod']};
for z=1:numel(srcBlocks)
 assert(getSimulinkBlockHandle(srcBlocks{z})>0,'JTE092:SourceInternalBlock');
end
srcCap=JTE092BlockCapture(srcBlocks,[330 338]);
assignin('base','jte092Cap',srcCap);
set_param(mdl,'StartFcn','jte089Capture.attach(); jte092Cap.attach();');
clean=onCleanup(@()clearCapture(cap)); %#ok<NASGU>
cleanSource=onCleanup(@()clearSourceCapture(srcCap)); %#ok<NASGU>
in=Simulink.SimulationInput(mdl);
in=in.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
 'SaveState','on','StateSaveName','jte089States','SaveFormat','Dataset',...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE089_EXECUTION_PROBE_START sourcePinned=1 solverUnchanged=1 horizon340=1 noPublicValues=1\n');
out=sim(in);
after=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(isequal(before,after),'JTE092:ConfigDrift');
[t,u]=JTE2026timeseries(out,'jteUcore');[ty,y]=JTE2026timeseries(out,'jteFlwR');
assert(isequal(t,ty),'JTE092:LoggerClock');
rows=cap.data();
assert(all(cap.Counts(2:4)>0)&&~cap.Overflow&&cap.N>0,'JTE092:IncompleteListeners');
assert(all(u==.25),'JTE092:ChangedRecordedCore');
post=rows(rows(:,2)==3,:);der=rows(rows(:,2)==4,:);
hasExcursion=any(abs(y(ty>300)-.25)>.005);
liveExcursion=any(abs(post(:,4)-.25)>.005);
stateOutputConsistent=false;odeRhsConsistent=false;
if cap.StateReadable&&calibration.stateReadable
 stateOutputConsistent=all(abs(post(:,4)-calibration.C*post(:,5))<1e-9);
end
if cap.DerivativeReadable&&cap.StateReadable&&calibration.rhsVerified
 odeRhsConsistent=all(abs(der(:,6)-(-1000*der(:,5)+calibration.B*der(:,3)))<1e-7);
end
states=out.get('jte089States');found=0;exactClock=false;stateExcursion=false;
for k=1:states.numElements
 el=states.getElement(k);
 try,path=char(el.BlockPath.getBlock(1));catch,path='';end
 if strcmp(path,tf)
  found=found+1;ts=double(el.Values.Time(:));xs=double(squeeze(el.Values.Data));xs=xs(:);
  exactClock=isequal(ts,ty);
  if calibration.stateReadable&&numel(ts)==numel(xs)
   stateExcursion=any(abs(calibration.C*xs(ts>300)-.25)>.005);
  end
 end
end
assert(found==1,'JTE092:StateIdentity');
coreChanged=-1;if cap.CoreListenerAvailable,coreChanged=double(cap.InputChanged(1));end
fprintf(['JTE089_EXECUTION_EVIDENCE recordedCoreConstant=1 coreListenerAvailable=%d observedCoreEvaluationChanged=%d ' ...
 'observedTFPreInputChanged=%d observedTFDerivativeInputChanged=%d stateReadable=%d derivativesReadable=%d ' ...
 'liveStateCheckAvailable=%d postOutputMatchesCalibratedState=%d derivativeMatchesCalibratedODE=%d ' ...
 'savedOutputExcursion=%d livePostOutputsExcursion=%d savedStateExcursion=%d ' ...
 'savedStateExactClock=%d allListenerTypesExecuted=1 overflow=0 ' ...
 'acceptedStepClassificationAvailable=0 exactRootActorProven=0 G5_ACCEPTED=false\n'],...
 cap.CoreListenerAvailable,coreChanged,cap.InputChanged(2),cap.InputChanged(4),cap.StateReadable,...
 cap.DerivativeReadable,cap.StateReadable&&calibration.stateReadable,stateOutputConsistent,odeRhsConsistent,hasExcursion,...
 liveExcursion,stateExcursion,exactClock);
% Independent case-focused instrumentation audit: JTE089 InputChanged was
% global across 0-340 s. Never label global PreOutputs as causal.
% Callbacks are evaluations (may be rejected), NOT accepted solver steps.
ix=find(ty>=330 & ty<=338 & abs(y-.25)>.005,1,'first');
assert(~isempty(ix)&&ix>1,'JTE092:MissingWindowExcursion');
eventTime=ty(ix); beforeEvent=ty(ix-1);
pre=rows(rows(:,2)==2,:); post=rows(rows(:,2)==3,:);
der=rows(rows(:,2)==4,:);
assert(~isempty(pre)&&~isempty(post)&&~isempty(der),'JTE092:CallbacksMissing');
thresh=1e-12;
preWindow=any(abs(pre(:,3)-.25)>thresh);
postWindow=any(abs(post(:,3)-.25)>thresh);
derWindow=any(abs(der(:,3)-.25)>thresh);
closeTol=1e-6;
preNear=any(abs(pre(:,1)-eventTime)<=closeTol & abs(pre(:,3)-.25)>thresh);
postNear=any(abs(post(:,1)-eventTime)<=closeTol & abs(post(:,3)-.25)>thresh);
derNear=any(abs(der(:,1)-eventTime)<=closeTol & abs(der(:,3)-.25)>thresh);
observedBracket=(rows(:,1)>=beforeEvent-1e-9 & rows(:,1)<=eventTime+1e-9);
bracketChanges=zeros(1,3);
for eventTag=2:4
    bracketChanges(eventTag-1)=any(observedBracket & rows(:,2)==eventTag & abs(rows(:,3)-.25)>thresh);
end
% Evaluation-only outputs can be different from recorded native-grid data.
postOutputNear=any(abs(post(:,1)-eventTime)<=closeTol & abs(post(:,4)-.25)>.005);
preCount=sum(rows(:,2)==2);postCount=sum(rows(:,2)==3);derCount=sum(rows(:,2)==4);
fprintf(['JTE092_FIRST_EVENT_WINDOW_EVIDENCE recordedCoreConstant=1 ' ...
 'globalPreChanged=%d globalDerivativeChanged=%d ' ...
 'windowPreChanged=%d windowPostChanged=%d windowDerivativeChanged=%d ' ...
 'withinRecordedFirstBracketPreChanged=%d withinRecordedFirstBracketPostChanged=%d ' ...
 'withinRecordedFirstBracketDerivativeChanged=%d ' ...
 'timeCoincidentPreChanged=%d timeCoincidentPostChanged=%d ' ...
 'timeCoincidentDerivativeChanged=%d liveOutputExcursionNearNative=%d ' ...
 'preEvaluationCount=%d postEvaluationCount=%d derivativeEvaluationCount=%d ' ...
 'acceptedStepClassificationAvailable=0 rootActorProven=0 noG5Acceptance=1\n'], ...
 cap.InputChanged(2),cap.InputChanged(4), ...
 preWindow,postWindow,derWindow, ...
 bracketChanges(1),bracketChanges(2),bracketChanges(3), ...
 preNear,postNear,derNear,postOutputNear, ...
 preCount,postCount,derCount);
% Compare source internal execution outputs with TF input event evaluations.
sourceRows=srcCap.data();
assert(all(srcCap.Counts>0)&&~srcCap.Overflow,'JTE092:MissingSourceListener');
assert(srcCap.InputOutputReadable,'JTE092:CannotReadInternalPorts');
gain=sourceRows(sourceRows(:,2)==1,:);
sat=sourceRows(sourceRows(:,2)==2,:);
mod=sourceRows(sourceRows(:,2)==3,:);
assert(~isempty(gain)&&~isempty(sat)&&~isempty(mod),'JTE092:MissingWindowSourceRows');
near=1e-6; t0=ty(ix);
modNear=mod(abs(mod(:,1)-t0)<=near,:);
gainNear=gain(abs(gain(:,1)-t0)<=near,:);
satNear=sat(abs(sat(:,1)-t0)<=near,:);
assert(~isempty(modNear),'JTE092:NoSourceBoundaryEval');
% The sub-block Mod output discontinuity may occur without a change in
% recorded core command. No claimed exact actor/solver reset.
modBoundaryValueObserved=any(abs(modNear(:,3)-0.25)<1e-6);
modOutputBranched=(max(modNear(:,4))-min(modNear(:,4)))>0.1;
gainNearBoundary=any(abs(gainNear(:,4)-0.25)<1e-6);
satNearBoundary=any(abs(satNear(:,4)-0.25)<1e-6);
fprintf(['JTE092_SOURCE_INTERNAL_EVALUATIONS sourcePinned=1 ' ...
 'modNearFirstNativeEvent=%d modInputAtBoundary=%d modBranchDiscontinuityNearEvent=%d ' ...
 'gainNearQuantizerBoundary=%d saturationNearQuantizerBoundary=%d ' ...
 'sourceGainEvaluations=%d sourceSaturationEvaluations=%d sourceModuloEvaluations=%d ' ...
 'coreRecordedNativeConstant=1 tfEvalChangedAtEvent=%d ' ...
 'acceptedStepClassificationAvailable=0 exactResetActorProven=0 G5_ACCEPTED=false\n'], ...
 ~isempty(modNear),modBoundaryValueObserved,modOutputBranched, ...
 gainNearBoundary,satNearBoundary,size(gain,1),size(sat,1),size(mod,1),preNear&&postNear);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE092:VendorChanged');
fprintf('JTE092_DIAGNOSTIC_EXECUTED_NOT_ROOT_CAUSE_PASS\n');
end
function cal=canary()
% Positive input-change detection and an independent canonical scale check.
% This small synthetic model does not validate the full plant.
mdl='JTE089Synthetic';new_system(mdl);guard=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
add_block('simulink/Sources/Step',[mdl '/input'],'Time','.01','Before','.25','After','.35');
add_block('simulink/Continuous/Transfer Fcn',[mdl '/TF'],'Numerator','[1]','Denominator','[1e-3 1]');
add_line(mdl,'input/1','TF/1');
add_block('simulink/Sinks/To Workspace',[mdl '/Y'],'VariableName','jte089CanaryY','SaveFormat','Timeseries');
add_line(mdl,'TF/1','Y/1');
set_param(mdl,'Solver','ode23t','RelTol','1e-6','AbsTol','1e-9','MaxStep','.0001','StopTime','.02','SaveState','on','StateSaveName','jte089CanaryX','SaveFormat','Dataset');
cap=JTE089Capture([mdl '/TF'],'',[0 .02]);assignin('base','jte089Capture',cap);
set_param(mdl,'StartFcn','jte089Capture.attach();');
clean=onCleanup(@()clearCapture(cap)); %#ok<NASGU>
out=sim(Simulink.SimulationInput(mdl));r=cap.data();p=r(r(:,2)==3,:);d=r(r(:,2)==4,:);
assert(all(cap.Counts(2:4)>0)&&cap.InputChanged(4)&&~cap.Overflow,'JTE092:CanaryInputDetection');
cal=struct('stateReadable',false,'rhsVerified',false,'C',NaN,'B',NaN);
% Built-in TransferFcn runtime objects need not expose states/derivatives.
% Obtain independent calibration only from aligned saved Dataset + output.
ds=out.get('jte089CanaryX');sig=out.get('jte089CanaryY');found=0;
for k=1:ds.numElements
 el=ds.getElement(k);
 try,path=char(el.BlockPath.getBlock(1));catch,path='';end
 if strcmp(path,[mdl '/TF'])
  found=found+1;ts=double(el.Values.Time(:));xs=double(squeeze(el.Values.Data));xs=xs(:);
  ys=double(sig.Data(:));
  assert(isequal(ts,double(sig.Time(:)))&&numel(xs)==numel(ys),'JTE092:CanaryClock');
  good=abs(xs)>1e-12;cal.C=median(ys(good)./xs(good));
  assert(isfinite(cal.C)&&all(abs(ys-cal.C*xs)<1e-9),'JTE092:CanarySavedStateOutput');
  cal.stateReadable=true;
 end
end
assert(found==1&&cal.stateReadable,'JTE092:CanaryStateMissing');
fprintf('JTE089_SYNTHETIC_LISTENER_CANARY_PASS inputChangeDetected=1 liveStateReadable=%d liveDerivativeReadable=%d savedCanonicalCalibrationVerified=1\n',...
 cap.StateReadable,cap.DerivativeReadable);
end
function clearCapture(cap)
cap.detach();evalin('base','clear jte089Capture');
end
function closeProjectQuiet(p)
try,close(p);catch,end
end
function closeModelQuiet(m)
try,if bdIsLoaded(m),set_param(m,'StartFcn','','CloseFcn','');close_system(m,0);end;catch,end
end

function clearSourceCapture(cap)
cap.detach();evalin('base','clear jte092Cap');
end
