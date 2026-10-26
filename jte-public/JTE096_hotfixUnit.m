function JTE096_hotfixUnit()
% NEW tests of selective branch cleanup/audit/entry-point routing, no old oracles.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE096:Runtime','Wrong runtime.');
m='JTE096_WIRE_UNIT';new_system(m);g=onCleanup(@()close_system(m,0)); %#ok<NASGU>
add_block('simulink/Sources/In1',[m '/input']);
add_block('simulink/Sources/In1',[m '/Step size'],'Port','2');
add_block('simulink/Math Operations/Math Function',[m '/Mod'],'Operator','mod');
add_block('simulink/Math Operations/Sum',[m '/Subtract1'],'Inputs','+-');
add_block('simulink/Math Operations/MinMax',[m '/MinMax4'],'Function','max','Inputs','2');
add_block('simulink/Sinks/Out1',[m '/output']);
add_block('simulink/Sinks/To Workspace',[m '/Retained probe'],'VariableName','syntheticOnly');
add_line(m,'input/1','Mod/1');add_line(m,'Step size/1','Mod/2');
add_line(m,'input/1','Subtract1/1');add_line(m,'Mod/1','Subtract1/2');
add_line(m,'Subtract1/1','MinMax4/1');add_line(m,'Step size/1','MinMax4/2');
add_line(m,'MinMax4/1','output/1');add_line(m,'input/1','Retained probe/1');
before=JTE096_signalEdges(m);
% An isolated unconnected line must be detected; never blanket cleaned.
h=add_line(m,[400 300;450 300]);
assert(JTE096_orphanLines(m)>0,'JTE096:OrphanNegative','Orphan detector missed isolated line.');
try
 JTE096_replaceArithmetic(m);
 error('JTE096:BadCleanupAccepted','Source orphan must be reviewed before mutation.');
catch ME
 assert(strcmp(ME.identifier,'JTE096:SourceOrphan'),'JTE096:UnexpectedRejection','Unexpected negative-control error.');
end
assert(isequal(before,JTE096_signalEdges(m)),'JTE096:NegativeMutation','Rejected cleanup cut valid wiring.');
delete_line(h); % exact synthetic line handle created by this unit test
proof=JTE096_replaceArithmetic(m);
after=JTE096_signalEdges(m);
assert(any(strcmp(after,'input:1>Retained probe:1'))&&proof.orphans==0,'JTE096:ProbeCut','Unrelated branch lost.');
assert(numel(after)==numel(before)-2,'JTE096:EdgeCount','Wrong endpoint delta.');
% Independent auditor negative control catches a declared target change.
a=JTE096_modelAudit(m);
set_param([m '/MinMax4'],'Function','min');b=JTE096_modelAudit(m);
assert(~isequal(a.blocks,b.blocks),'JTE096:ParamAuditBlind','Auditor missed parameter mutation.');
set_param([m '/MinMax4'],'Function','max');
% Routing only, no rerun of historical PASS/FAIL numerical suites.
folder=fileparts(mfilename('fullpath'));
for n={'CHAT','WORK'}
 p=fullfile(folder,'rejected',['JTE094_EXPECTED_FAIL_REJECTED_CANDIDATE_' n{1} '.m']);
 assert(isfile(p)&&contains(fileread(p),'EXPECTED_FAIL_REJECTED_CANDIDATE'),'JTE096:Quarantine','Missing rejected archive.');
end
normal=fileread(fullfile(folder,'JTE094_WORK_staticSuite.m'));
assert(~contains(normal,'JTE094_WORK_preflight()')&&~contains(normal,'ALL_STATIC_ORACLES_PASS'),'JTE096:FalseGate','Rejected oracle is an acceptance gate.');
oracle=fileread(fullfile(folder,'JTE094_ORACLE_TESTS.m'));
assert(~contains(oracle,'assert(all(old == proposed)'),'JTE096:MixedOracle','Rejected assertion still on normal entry point.');
retired=false;
try,JTE094_WORK_preflight();catch ME,retired=strcmp(ME.identifier,'JTE096:RetiredMixedPreflight');end
assert(retired,'JTE096:Routing','Legacy sweep not retired.');
fprintf('JTE096_NEW_UNIT_PASS selectiveEndpointDeletion=1 unrelatedBranchRetained=1 orphanNegativeControl=1 declaredParamNegativeControl=1 rejectedOracleRerun=0 previousPassedTestsRerun=0 simulationRun=0\n');
end
