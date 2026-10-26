function JTE079_short_solver_pole_case(profile)
% P0 targeted 0-340 s exploratory solver diagnostic, NOT 2400 s or G5 PASS.
% No private numeric log values and no MAT artifact. Preserves source physics.
assert(strcmp(version('-release'),'2024b'),'JTE079:WrongMATLAB');
profile=char(profile);
assert(any(strcmp(profile,{'original','strict340'})),'JTE079:InvalidProfile');
root=pwd; vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE079:WrongVendor');
proj=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cleanProject=onCleanup(@()quietProject(proj)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,['jte079-generated-' profile]));
[~,model]=fileparts(files.baseline);
load_system(files.baseline);
cleanModel=onCleanup(@()quietModel(model)); %#ok<NASGU>
assert(strcmp(get_param(model,'Solver'),'ode23t'),'JTE079:SolverDrift');
assert(strcmp(get_param(model,'SolverType'),'Variable-step'),'JTE079:NotVariable');
ctrl=[model '/Battery Control'];
flow=[ctrl '/sensor dynamics 1'];
assert(strcmp(get_param(flow,'Numerator'),'[1]') && strcmp(get_param(flow,'Denominator'),'[1e-3 1]'),'JTE079:TFSourceChanged');
in=Simulink.SimulationInput(model);
in=in.setModelParameter('StartTime','0','StopTime','340','SaveTime','on','TimeSaveName','tout');
if strcmp(profile,'strict340')
    % Exploratory 340s only; do not extrapolate full 2400s convergence.
    in=in.setModelParameter('RelTol','1e-4','AbsTol','1e-4','MaxStep','0.01');
end
fprintf('JTE079_LOCAL_SOLVER_340_START profile=%s sourcePin=true noG5=true\n',profile);
ticv=tic;
out=sim(in);
duration=toc(ticv);
[tc,u]=JTE2026timeseries(out,'jteUcore');
[tf,y]=JTE2026timeseries(out,'jteFlwR');
[tt,T]=JTE2026timeseries(out,'jteTtrue');
assert(size(T,2)==312 && tc(1)==0 && tf(1)==0 && tt(1)==0,'JTE079:NativeStart');
assert(abs(tc(end)-340)<1e-8 && abs(tf(end)-340)<1e-8 && abs(tt(end)-340)<1e-8,'JTE079:IncompleteHorizon');
assert(all(diff(tc)>=0) && all(diff(tf)>=0) && all(isfinite(y(:))) && all(isfinite(u(:))),'JTE079:BadNativeSignal');
assert(size(u,2)==1 && size(y,2)==1,'JTE079:LoggerShape');
coreConstant=all(u==0.25);
hasExcursion=any(abs(y(tf>320 & tf<338)-0.25)>0.0025);
fprintf('JTE079_340S_NATIVE_DIAGNOSTIC_DONE profile=%s coreConstant=%d postfilterExcursionAtFirstWindow=%d nativeLogger=true noG5=true\n', ...
    profile,coreConstant,hasExcursion);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE079:ModifiedVendor');
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(m)
try
if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end
catch,end
end
