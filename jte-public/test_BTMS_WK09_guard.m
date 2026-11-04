function tests=test_BTMS_WK09_guard
% Owner-local STATIC tests only. Authored here; NOT RUN by Codex.
tests=functiontests(localfunctions);
end
function testEverySavedCasePreservesUndeclaredActuatorAndToleranceStrings(testCase)
% Owner supplies the unchanged archived M2 SLX and its already-restored workspace
% and vendor project paths. No simulation/compile/initialization in this test.
fixture=getenv('WK09_STATIC_M2_FIXTURE');assumeTrue(testCase,isfile(fixture));
code=fileparts(mfilename('fullpath'));R=jsondecode(fileread(fullfile(code,'WK09_runs.json')));
A=jsondecode(fileread(fullfile(code,R.selector_file)));order=A.ranking_descending(:)';
[~,original]=fileparts(fixture);load_system(fixture);c=onCleanup(@()close_system(original,0)); %#ok<NASGU>
before=parameters(original);
for k=1:numel(R.runs)
 D=R.runs(k);D.subset=BTMS_WK08_sparseSets(D.sensors);
 switch D.channel_rule
  case 'top_three',J=sort(order(1:3));
  case 'rank_156',J=order(156);
  case {'rank_1','hottest_in_subset'},J=order(find(ismember(order,D.subset),1));
  otherwise,J=D.subset(1);
 end
 D.bias_channels=J;D.selector_sha256=R.selector_sha256;D.scenario_sha256=R.scenario_sha256;
 D.predictions_sha256=R.predictions_sha256;D.baseline_receipt_sha256=R.baseline.receipt_sha256;
 D.subset_sha256=JTE2026sha256(fullfile(code,'WK08_sparse_sets.csv'));
 folder=tempname;mkdir(folder);native=fullfile(folder,'native');mkdir(native);
 f=fullfile(folder,'definition.json');fid=fopen(f,'w');fprintf(fid,'%s',jsonencode(D));fclose(fid);
 target=fullfile(folder,['WK09_' D.id '.slx']);
 p=BTMS_WK09_prepare(fixture,target,native,JTE2026sha256(fixture),f);
 [~,m]=fileparts(target);load_system(target);after=parameters(m);
 if ~strcmp(D.id,'R3')
  verifyEqual(testCase,after.actuator,before.actuator,D.id);
 else
  verifyEqual(testCase,str2double(after.actuator.SampleTime),.005);
  verifyEqual(testCase,str2double(after.actuator.holdSampleTime),.005);
  verifyEqual(testCase,str2double(after.actuator.A),exp(-.005/.001));
  verifyEqual(testCase,str2double(after.actuator.B),1-exp(-.005/.001));
 end
 if ~strcmp(D.id,'R4')
  verifyEqual(testCase,after.tolerances,before.tolerances,D.id);
 else
  verifyEqual(testCase,after.tolerances,struct('RelTol','1e-4','AbsTol','1e-4'));
 end
 verifyEqual(testCase,p.injection.identityBypass,any(strcmp(D.id,{'R3','R4'})));
 verifyEqual(testCase,p.fingerprint,BTMS_WK08_structFingerprint(m));close_system(m,0);
 % Test evidence stays in the owner's private temp directory for inspection.
end
end
function a=parameters(m)
bc=[m '/Battery Control'];act=[bc '/Amended sampled actuator'];hold=[bc '/Amended command sample hold'];
a.actuator=struct('A',get_param(act,'A'),'B',get_param(act,'B'),'SampleTime',get_param(act,'SampleTime'), ...
 'holdSampleTime',get_param(hold,'SampleTime'));
a.tolerances=struct('RelTol',get_param(m,'RelTol'),'AbsTol',get_param(m,'AbsTol'));
end
function testOneUnsensedVectorMemberRejectsBeforeAnyEdit(testCase)
[m]=measurementGraph();c=onCleanup(@()close_system(m,0)); %#ok<NASGU>
before=BTMS_WK08_structFingerprint(m);
for n=[8 16]
 S=BTMS_WK08_sparseSets(n);J=sort([S(1) 1]);verifyFalse(testCase,ismember(1,S));
 for b=[-2 0 2]
  verifyError(testCase,@()BTMS_WK08_inject(m,b,J,S,true),'WK08:BiasNotSensed');
  verifyEqual(testCase,BTMS_WK08_structFingerprint(m),before);
 end
end
verifyError(testCase,@()BTMS_WK08_inject(m,-2,[202 202],1:312,true),'WK08:BiasChannels');
verifyEqual(testCase,BTMS_WK08_structFingerprint(m),before);
for J={[],0,313,[202 313],NaN}
 rejected=false;try,BTMS_WK08_inject(m,-2,J{1},1:312,true);catch,rejected=true;end
 verifyTrue(testCase,rejected);verifyEqual(testCase,BTMS_WK08_structFingerprint(m),before);
end
p=BTMS_WK08_inject(m,0,1,1:312);verifyTrue(testCase,p.identityBypass);
verifyEqual(testCase,BTMS_WK08_structFingerprint(m),before);
end
function testScalarVectorPositiveNegativeAndForcedZeroChart(testCase)
for b=[-2 0 2]
 for J={202,[202 203 204]}
  m=measurementGraph();p=BTMS_WK08_inject(m,b,J{1},1:312,true);
  verifyFalse(testCase,p.identityBypass);verifyEqual(testCase,p.channel,J{1});
  sf=sfroot;chart=sf.find('-isa','Stateflow.EMChart','Path',[m '/Battery Control/WK08 measurement']);
  expected=sprintf('v(%s)=v(%s)+%.17g;',mat2str(J{1}),mat2str(J{1}),b);
  verifyTrue(testCase,contains(chart.Script,expected));close_system(m,0);
 end
end
end
function m=measurementGraph()
[~,m]=fileparts(tempname);new_system(m);
bc=[m '/Battery Control'];add_block('built-in/Subsystem',bc);
add_block('simulink/Sources/Constant',[bc '/T'],'Value','300*ones(312,1)');
red=[bc '/min-max T'];add_block('built-in/Subsystem',red);
add_block('built-in/Inport',[red '/T']);
add_block('simulink/Math Operations/MinMax',[red '/MinMax3'],'Function','max','Inputs','1');
add_block('built-in/Outport',[red '/plot'],'Port','1');add_block('built-in/Outport',[red '/max'],'Port','2');
add_line(red,'T/1','MinMax3/1');add_line(red,'T/1','plot/1');add_line(red,'MinMax3/1','max/1');
ctrl=[bc '/FlwR_calc'];add_block('built-in/Subsystem',ctrl);
add_block('built-in/Inport',[ctrl '/T']);add_block('built-in/Outport',[ctrl '/u']);add_line(ctrl,'T/1','u/1');
add_line(bc,'T/1','min-max T/1');add_line(bc,'min-max T/2','FlwR_calc/1');
end
