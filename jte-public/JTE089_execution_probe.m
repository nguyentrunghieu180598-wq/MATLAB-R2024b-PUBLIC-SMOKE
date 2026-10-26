function JTE089_execution_probe()
% No solver/tolerance/physical edits. Fresh derivative, source-only diagnostics.
% No MAT, state values, event times or plots published by this workflow.
assert(strcmp(version('-release'),'2024b'),'JTE089:Release');
assert(contains(version,'24.2.0.3361896'),'JTE089:Update10');
calibration=canary();
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE089:Pin');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()closeProjectQuiet(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte089-generated'));
[~,mdl]=fileparts(files.baseline);load_system(files.baseline);
mg=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
tf=[mdl '/Battery Control/sensor dynamics 1'];core=[mdl '/Battery Control/FlwR_calc'];
assert(strcmp(get_param(tf,'SID'),'197'),'JTE089:SID');
assert(strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE089:TF');
ph=get_param(tf,'PortHandles');ch=get_param(core,'PortHandles');
assert(get_param(get_param(ph.Inport(1),'Line'),'SrcPortHandle')==ch.Outport(1),'JTE089:Wiring');
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','SolverResetMethod','ZeroCrossControl'};
before=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(strcmp(before{1},'ode23t'),'JTE089:Solver');
assert(isempty(get_param(mdl,'StartFcn')),'JTE089:ExistingCallback');
cap=JTE089Capture(tf,core,[330 338]);assignin('base','jte089Capture',cap);
set_param(mdl,'StartFcn','jte089Capture.attach();');
clean=onCleanup(@()clearCapture(cap)); %#ok<NASGU>
in=Simulink.SimulationInput(mdl);
in=in.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
 'SaveState','on','StateSaveName','jte089States','SaveFormat','Dataset',...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE089_EXECUTION_PROBE_START sourcePinned=1 solverUnchanged=1 horizon340=1 noPublicValues=1\n');
out=sim(in);
after=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(isequal(before,after),'JTE089:ConfigDrift');
[t,u]=JTE2026timeseries(out,'jteUcore');[ty,y]=JTE2026timeseries(out,'jteFlwR');
assert(isequal(t,ty),'JTE089:LoggerClock');
rows=cap.data();
assert(all(cap.Counts>0)&&~cap.Overflow&&cap.N>0,'JTE089:IncompleteListeners');
assert(all(u==.25),'JTE089:ChangedRecordedCore');
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
assert(found==1,'JTE089:StateIdentity');
fprintf(['JTE089_EXECUTION_EVIDENCE recordedCoreConstant=1 observedCoreEvaluationChanged=%d ' ...
 'observedTFPreInputChanged=%d observedTFDerivativeInputChanged=%d stateReadable=%d derivativesReadable=%d ' ...
 'postOutputMatchesCalibratedState=%d derivativeMatchesCalibratedODE=%d ' ...
 'savedOutputExcursion=%d livePostOutputsExcursion=%d savedStateExcursion=%d ' ...
 'savedStateExactClock=%d allListenerTypesExecuted=1 overflow=0 ' ...
 'acceptedStepClassificationAvailable=0 exactRootActorProven=0 G5_ACCEPTED=false\n'],...
 cap.InputChanged(1),cap.InputChanged(2),cap.InputChanged(4),cap.StateReadable,...
 cap.DerivativeReadable,stateOutputConsistent,odeRhsConsistent,hasExcursion,...
 liveExcursion,stateExcursion,exactClock);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE089:VendorChanged');
fprintf('JTE089_DIAGNOSTIC_EXECUTED_NOT_ROOT_CAUSE_PASS\n');
end
function cal=canary()
% Positive input-change detection and an independent canonical scale check.
% This small synthetic model does not validate the full plant.
mdl='JTE089Synthetic';new_system(mdl);guard=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
add_block('simulink/Sources/Step',[mdl '/input'],'Time','.01','Before','.25','After','.35');
add_block('simulink/Continuous/Transfer Fcn',[mdl '/TF'],'Numerator','[1]','Denominator','[1e-3 1]');
add_line(mdl,'input/1','TF/1');
set_param(mdl,'Solver','ode23t','RelTol','1e-6','AbsTol','1e-9','MaxStep','.0001','StopTime','.02');
cap=JTE089Capture([mdl '/TF'],'',[0 .02]);assignin('base','jte089Capture',cap);
set_param(mdl,'StartFcn','jte089Capture.attach();');
clean=onCleanup(@()clearCapture(cap)); %#ok<NASGU>
sim(mdl);r=cap.data();p=r(r(:,2)==3,:);d=r(r(:,2)==4,:);
assert(all(cap.Counts(2:4)>0)&&cap.InputChanged(4)&&~cap.Overflow,'JTE089:CanaryInputDetection');
cal=struct('stateReadable',cap.StateReadable,'rhsVerified',false,'C',NaN,'B',NaN);
if cal.stateReadable
 good=abs(p(:,5))>1e-12;ratio=p(good,4)./p(good,5);
 cal.C=median(ratio);
 assert(isfinite(cal.C)&&all(abs(p(:,4)-cal.C*p(:,5))<1e-9),'JTE089:CanaryStateOutput');
 if cap.DerivativeReadable
  z=(d(:,6)+1000*d(:,5))./d(:,3);cal.B=median(z);
  cal.rhsVerified=all(abs(d(:,6)-(-1000*d(:,5)+cal.B*d(:,3)))<1e-7);
  assert(cal.rhsVerified&&abs(cal.C*cal.B-1000)<1e-6,'JTE089:CanaryRHS');
 end
end
fprintf('JTE089_SYNTHETIC_LISTENER_CANARY_PASS inputChangeDetected=1 stateReadable=%d derivativeReadable=%d canonicalCalibrationVerified=%d\n',...
 cal.stateReadable,cap.DerivativeReadable,cal.rhsVerified);
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
