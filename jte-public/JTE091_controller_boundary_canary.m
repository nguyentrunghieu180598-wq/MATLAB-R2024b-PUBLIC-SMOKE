function JTE091_controller_boundary_canary()
% Isolated source-pinned controller vs constant-command counterfactual.
% A controlled Tmax ramp crosses the original MOD boundary at 302.5 K
% while accepted core law remains fixed at 0.25. Not a battery-plant run,
% does not alter upstream vendor, cannot by itself validate G5.
assert(strcmp(version('-release'),'2024b'),'JTE091:Release');
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
file=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmp(JTE2026sha256(file),pin),'JTE091:SourceSha');
prj=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
onPrj=onCleanup(@()safeProject(prj)); %#ok<NASGU>
load_system(file);
[~,src]=fileparts(file);
from=[src '/Battery Control/FlwR_calc'];
filter=[src '/Battery Control/sensor dynamics 1'];
assert(getSimulinkBlockHandle(from)>0&&getSimulinkBlockHandle(filter)>0,'JTE091:SourceBlocks');
assert(strcmp(get_param(filter,'Numerator'),'[1]')&&strcmp(get_param(filter,'Denominator'),'[1e-3 1]'),'JTE091:FilterParams');
assert(strcmp(get_param([from '/Step Change/Mod'],'Operator'),'mod'),'JTE091:ModBlock');
assert(str2double(get_param([from '/FlwR calc/Gain1'],'Gain'))==0.1,'JTE091:GainChanged');
m='JTE091_CONTROLLER_BOUNDARY_CANARY';
assert(~bdIsLoaded(m),'JTE091:AlreadyLoaded');new_system(m);
clean=onCleanup(@()safeModel(m)); %#ok<NASGU>
add_block('simulink/Sources/Ramp',[m '/TmaxRamp'],'slope','0.1','start','0','InitialOutput','302.4');
add_block('simulink/Sources/Constant',[m '/Ambient'],'Value','300');
add_block('simulink/Sources/Constant',[m '/ConstantCommand'],'Value','0.25');
add_block(from,[m '/OriginalFlwR']);
add_block(filter,[m '/TFWithController']);
add_block(filter,[m '/TFWithConstant']);
add_line(m,'TmaxRamp/1','OriginalFlwR/1');
add_line(m,'Ambient/1','OriginalFlwR/2');
add_line(m,'OriginalFlwR/1','TFWithController/1');
add_line(m,'ConstantCommand/1','TFWithConstant/1');
links={'OriginalFlwR','jte091Command';'TFWithController','jte091ControllerTF';'TFWithConstant','jte091ConstantTF'};
for kk=1:size(links,1)
  block=links{kk,1};v=links{kk,2};sink=[m '/' v];
  add_block('simulink/Sinks/To Workspace',sink,'VariableName',v,'SaveFormat','Timeseries');
  add_line(m,[block '/1'],[v '/1']);
end
s=Simulink.SimulationInput(m);
s=s.setModelParameter('Solver','ode23t','SolverType','Variable-step', ...
    'RelTol','0.001','AbsTol','0.001','MaxStep','0.05', ...
    'StartTime','0','StopTime','2');
out=sim(s);
[tu,u]=JTE2026timeseries(out,'jte091Command');
[ta,ya]=JTE2026timeseries(out,'jte091ControllerTF');
[tb,yb]=JTE2026timeseries(out,'jte091ConstantTF');
assert(all(isfinite(u))&&all(isfinite(ya))&&all(isfinite(yb)),'JTE091:Nonfinite');
assert(tu(1)==0&&tu(end)==2&&ta(end)==2&&tb(end)==2,'JTE091:Incomplete');
steady=(tu>0.1 & tu<1.9);
assert(any(steady)&&all(abs(u(steady)-.25)<1e-10),'JTE091:UnexpectedCoreState');
windowA=ta>0.8 & ta<1.2;
windowB=tb>0.8 & tb<1.2;
assert(any(windowA)&&any(windowB),'JTE091:NoBoundaryWindow');
controllerExcursion=any(abs(ya(windowA)-.25)>0.005);
constantExcursion=any(abs(yb(windowB)-.25)>0.005);
fprintf(['JTE091_PINNED_CONTROLLER_BOUNDARY_CHECK modBoundaryCrossed=1 ' ...
 'sourceCoreConstantNearBoundary=1 isolatedControllerTFExcursion=%d ' ...
 'constantCommandTFExcursion=%d sourcePinned=1 ' ...
 'noPlantSimulation=1 sourceEventCauseUnproven=1 G5_ACCEPTED=false\\n'], ...
 controllerExcursion,constantExcursion);
assert(strcmp(JTE2026sha256(file),pin),'JTE091:VendorAltered');
end
function safeProject(p)
try,close(p);catch,end
end
function safeModel(m)
try
if bdIsLoaded(m),set_param(m,'StartFcn','','CloseFcn','');close_system(m,0);end
catch,end
end
