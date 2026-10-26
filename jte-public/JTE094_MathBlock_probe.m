function JTE094_MathBlock_probe()
% Synthetic diagnostic of the documented Simulink Math Function mod operator.
% Standard library operator, NOT a full source-controller/plant equivalence claim.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE094:Runtime');
q=[.001 .1 .25 .3 .5 .6 .75 .9 .95];
for b=[.25 .5 .75]
 bits=typecast(b,'uint64');
 for k=-8:8
  if k<0,z=bits-uint64(-k);else,z=bits+uint64(k);end
  q(end+1)=typecast(z,'double'); %#ok<AGROW>
 end
end
m='JTE094_SYNTHETIC_MOD_OPERATOR';
assert(~bdIsLoaded(m),'JTE094:AlreadyLoaded');new_system(m);
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
mw=get_param(m,'ModelWorkspace');assignin(mw,'syntheticQ',q);
add_block('simulink/Sources/Constant',[m '/Q'],'Value','syntheticQ');
add_block('simulink/Sources/Constant',[m '/Step'],'Value','.25');
add_block('simulink/Math Operations/Math Function',[m '/Mod'],'Operator','mod');
add_block('simulink/Math Operations/Sum',[m '/Subtract'],'Inputs','+-');
add_block('simulink/Math Operations/MinMax',[m '/MinimumCommand'],'Function','max','Inputs','2');
add_block('simulink/Sinks/To Workspace',[m '/Logged'],'VariableName','syntheticOldCore','SaveFormat','Timeseries');
add_line(m,'Q/1','Mod/1');add_line(m,'Step/1','Mod/2');
add_line(m,'Q/1','Subtract/1');add_line(m,'Mod/1','Subtract/2');
add_line(m,'Subtract/1','MinimumCommand/1');add_line(m,'Step/1','MinimumCommand/2');
add_line(m,'MinimumCommand/1','Logged/1');
in=Simulink.SimulationInput(m);in=in.setModelParameter('StartTime','0','StopTime','0','SimulationMode','normal');
out=sim(in);sig=out.get('syntheticOldCore');got=double(sig.Data);got=got(:).';
assert(numel(got)==numel(q)&&all(isfinite(got)),'JTE094:OperatorSchema');
old=max(.25,q-mod(q,.25));proposed=JTE094_quantizerCandidate(q);bad=find(got~=proposed);
fprintf('JTE094_SYNTHETIC_SIMULINK_MOD_RESULT cases=%d matchesMATLABMod=%d matchesThreshold=%d mismatchCount=%d fullPlantRun=0\n',...
 numel(q),isequal(got,old),isequal(got,proposed),numel(bad));
for k=1:min(20,numel(bad))
 j=bad(k);
 fprintf('JTE094_SYNTHETIC_SIMULINK_MOD_CASE q=%.17g qhex=%s block=%.17g MATLABold=%.17g threshold=%.17g\n',...
 q(j),num2hex(q(j)),got(j),old(j),proposed(j));
end
assert(isequal(got,proposed),'JTE094:SimulinkModThresholdMismatchNoPlantPermitted');
fprintf('JTE094_SYNTHETIC_SIMULINK_MOD_OPERATOR_EQUIVALENCE_PASS fullSourceGraphNotTested=1 G5_ACCEPTED=false\n');
end
