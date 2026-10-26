function JTE086_tf_state_accuracy_340()
% JTE086: mechanistic hypothesis test of under-resolved tiny TF state.
% Only override numeric tolerance for source TransferFcn SID197 in
% isolated generated B0L derivative; ALL physics, input and global solver unchanged.
% No original SLX edits, no numerical study values in public logs.
assert(strcmp(version('-release'),'2024b'),'JTE086:MATLABRelease');
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE086:VendorPin');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
pg=onCleanup(@()closeProjectQuiet(p)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte086-generated'));
[~,mdl]=fileparts(files.baseline);
load_system(files.baseline); mg=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
tf=[mdl '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'BlockType'),'TransferFcn'),'JTE086:WrongBlock');
assert(strcmp(get_param(tf,'Numerator'),'[1]') && strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE086:TFPhysicsDrift');
previous=get_param(tf,'AbsoluteTolerance');
assert(any(strcmp(previous,{'auto','-1'})),'JTE086:SourceTFAbstolAlreadyModified');
% Source block can inherit global AbsTol 1e-3, while canonical TF
% state response is expected ~2.5e-4. Tighten ONLY this block state.
set_param(tf,'AbsoluteTolerance','1e-9');
assert(strcmp(get_param(tf,'AbsoluteTolerance'),'1e-9'),'JTE086:ToleranceWriteFailed');
save_system(mdl,files.baseline);
assert(strcmp(get_param(mdl,'Solver'),'ode23t')&&strcmp(get_param(mdl,'SolverType'),'Variable-step'),'JTE086:SourceSolverChanged');
in=Simulink.SimulationInput(mdl);
in=in.setModelParameter('StartTime','0','StopTime','340','SaveTime','on','TimeSaveName','tout');
fprintf('JTE086_SOURCE_LOCKED_TF_STATE_ABSTOL_TEST_START originalGlobalSolver=true originalInput=true tfStateToleranceOnly=true\\n');
out=sim(in);
[t,u]=JTE2026timeseries(out,'jteUcore');
[tfTime,y]=JTE2026timeseries(out,'jteFlwR');
[tt,T]=JTE2026timeseries(out,'jteTtrue');
assert(isequal(t,tfTime)&&isequal(tfTime,tt)&&size(T,2)==312,'JTE086:BadNative');
assert(tt(1)==0&&abs(tt(end)-340)<1e-8,'JTE086:WrongHorizon');
assert(all(u==0.25),'JTE086:CoreChanged');
assert(all(isfinite(y)) && all(diff(tfTime)>=0),'JTE086:BadTF');
w=tfTime>320 & tfTime<338;
assert(any(w),'JTE086:FirstWindowNotCovered');
excursion=any(abs(y(w)-0.25)>0.0025);
fprintf('JTE086_SOURCE_NUMERIC_TOL_ONLY_RESULT sourcePinned=true coreConstant=1 firstEventExcursionPresent=%d loggerNative=true noG5=true\\n',excursion);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE086:SourceModified');
end
function closeProjectQuiet(p)
try,close(p);catch,end
end
function closeModelQuiet(model)
try
if bdIsLoaded(model),set_param(model,'CloseFcn','');close_system(model,0);end
catch,end
end
