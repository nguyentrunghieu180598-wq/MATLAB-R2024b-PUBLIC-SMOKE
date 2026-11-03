function tests=test_BTMS_WK10_scenario_guard
% Static synthetic graph only; no compile, initialize, step or simulation.
% Source delivered for independent MATLAB review; NOT run by Codex.
tests=functiontests(localfunctions);
end
function testDeclaredGainIsTheOnlyDeltaAndSurvivesReload(testCase)
[m,s,cleanup]=fixture(); %#ok<ASGLU>
before=BTMS_WK08_structFingerprint(m);
d=BTMS_WK08_prepare('WK10_SCENARIO_ONLY',m,s);
verifyTrue(testCase,d.retainedGraphConfigWorkspaceScriptsEqual);
verifyEqual(testCase,d.before,before);
verifyEqual(testCase,d.after,BTMS_WK08_structFingerprint(m));
verifyEqual(testCase,get_param([m '/WK10 scenario current scale'],'Gain'),'2');
% Every sign is multiplied, including rest/regen. No synthetic plant run.
verifyEqual(testCase,s.k*[.49086580150495024 0 -57.66325022468845 90.21430363314232], ...
 [ .98173160300990048 0 -115.3265004493769 180.42860726628464],'AbsTol',1e-12);
file=fullfile(tempdir,[m '.slx']);assert(~isfile(file));
fileCleanup=onCleanup(@()delete(file)); %#ok<NASGU>
save_system(m,file);close_system(m,0);load_system(file);[~,reloaded]=fileparts(file);
reloadCleanup=onCleanup(@()close_system(reloaded,0)); %#ok<NASGU>
verifyEqual(testCase,d.after,BTMS_WK08_structFingerprint(reloaded));
end
function testMalformedOrK1ScenarioDoesNotEditGraph(testCase)
[m,s,cleanup]=fixture(); %#ok<ASGLU>
before=BTMS_WK08_structFingerprint(m);
bad=s;bad.k=1;
verifyError(testCase,@()BTMS_WK08_prepare('WK10_SCENARIO_ONLY',m,bad),'WK10:Scenario');
bad=s;bad.expected_edge.destination_port=1;
verifyError(testCase,@()BTMS_WK08_prepare('WK10_SCENARIO_ONLY',m,bad),'WK10:Scenario');
bad=s;bad.vendor_mat_sha256=repmat('0',1,64);
verifyError(testCase,@()BTMS_WK08_prepare('WK10_SCENARIO_ONLY',m,bad),'WK10:Scenario');
verifyEqual(testCase,before,BTMS_WK08_structFingerprint(m));
end
function testBranchedDemandIsRejectedWithoutEdits(testCase)
[m,s,cleanup]=fixture(); %#ok<ASGLU>
add_block('simulink/Sinks/Terminator',[m '/extra']);
add_line(m,'Current demand/1','extra/1');
before=BTMS_WK08_structFingerprint(m);
verifyError(testCase,@()BTMS_WK08_prepare('WK10_SCENARIO_ONLY',m,s),'WK10:Edge');
verifyEqual(testCase,before,BTMS_WK08_structFingerprint(m));
end
function [m,s,cleanup]=fixture()
[~,m]=fileparts(tempname);new_system(m);
cleanup=onCleanup(@()quietClose(m));
s=jsondecode(fileread(fullfile(fileparts(mfilename('fullpath')),'WK10_scenario.json')));
add_block('simulink/Sources/From File',[m '/Current demand'], ...
 'FileName','Battery_Pack_Thermal_Management_Ivst.mat','SampleTime','0');
bc=[m '/Battery Control'];add_block('built-in/Subsystem',bc);
add_block('built-in/Inport',[bc '/unused'],'Port','1');
add_block('built-in/Inport',[bc '/DC'],'Port','2');
add_line(m,'Current demand/1','Battery Control/2');
end
function quietClose(m)
if bdIsLoaded(m),close_system(m,0);end
end
