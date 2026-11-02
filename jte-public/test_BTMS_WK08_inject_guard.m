function tests=test_BTMS_WK08_inject_guard
% Synthetic graph only; no compile/simulation. Not run by Codex.
tests=functiontests(localfunctions);
end
function testRejectsUnsensedBiasWithoutEditingGraph(testCase)
[~,m]=fileparts(tempname);
new_system(m);
cleanup=onCleanup(@()close_system(m,0)); %#ok<NASGU>
bc=[m '/Battery Control'];
add_block('built-in/Subsystem',bc);
add_block('simulink/Sources/Constant',[bc '/Ttrue'],'Value','300*ones(312,1)');
red=[bc '/min-max T'];
add_block('built-in/Subsystem',red);
add_block('built-in/Inport',[red '/T']);
add_block('simulink/Math Operations/MinMax',[red '/MinMax3'], ...
 'Function','max','Inputs','1');
add_block('built-in/Outport',[red '/plot T'],'Port','1');
add_block('built-in/Outport',[red '/max T'],'Port','2');
add_line(red,'T/1','MinMax3/1');
add_line(red,'T/1','plot T/1');
add_line(red,'MinMax3/1','max T/1');
ctrl=[bc '/FlwR_calc'];
add_block('built-in/Subsystem',ctrl);
add_block('built-in/Inport',[ctrl '/Tmax']);
add_block('built-in/Inport',[ctrl '/Ambient'],'Port','2');
add_block('built-in/Outport',[ctrl '/u']);
add_line(ctrl,'Tmax/1','u/1');
add_block('simulink/Sources/Constant',[bc '/ambient'],'Value','300');
add_line(bc,'Ttrue/1','min-max T/1');
add_line(bc,'min-max T/2','FlwR_calc/1');
add_line(bc,'ambient/1','FlwR_calc/2');
before=BTMS_WK08_structFingerprint(m);
for n=[8 16]
 S=BTMS_WK08_sparseSets(n);
 j=1;verifyFalse(testCase,ismember(j,S));
 % Include zero-bias sparse preparation: it is still a non-neutral path.
 for b=[-4 -2 0 2]
  verifyError(testCase,@()BTMS_WK08_inject(m,b,j,S),'WK08:BiasNotSensed');
  verifyEqual(testCase,BTMS_WK08_structFingerprint(m),before);
 end
end
end
