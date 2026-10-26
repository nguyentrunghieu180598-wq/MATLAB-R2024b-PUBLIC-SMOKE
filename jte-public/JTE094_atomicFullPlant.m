function JTE094_atomicFullPlant(mode)
% Default is static/compile hotfix verification; explicit diagnostic mode only.
if nargin==0,mode='compileOnly';end
assert(any(strcmp(mode,{'compileOnly','diagnostic340'})),'JTE096:Mode','Unknown mode.');
% Compile-only by default. Optional legacy diagnostic is not G5 acceptance.
% Atomic Step Change retains the original q-mod(q,step), not three thresholds.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE094:Runtime','Wrong MATLAB release/update.');
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
source=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmp(JTE2026sha256(source),pin),'JTE094:Source','Vendor pin mismatch.');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()quietProject(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte094-generated'));
baselineSHA=JTE2026sha256(files.baseline);
[~,sourceModel]=fileparts(files.baseline);
derivative=fullfile(root,'jte094-generated','JTE096Derivative.slx');
copyfile(files.baseline,derivative);
load_system(files.baseline);load_system(derivative);
[~,mdl]=fileparts(derivative);
sg=onCleanup(@()quietModel(sourceModel)); %#ok<NASGU>
mg=onCleanup(@()quietModel(mdl)); %#ok<NASGU>
core=[mdl '/Battery Control/FlwR_calc'];step=[core '/Step Change'];
tf=[mdl '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE094:TF','Filter changed.');
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','SolverResetMethod','ZeroCrossControl','LoadInitialState','InitialState'};
config=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(strcmp(config{1},'ode23t')&&strcmp(config{8},'off'),'JTE094:Config','Preserve source solver and IC.');
sourceStep=[sourceModel '/Battery Control/FlwR_calc/Step Change'];
sourceStatic=JTE096_modelAudit(sourceModel,{sourceStep});
sourceOrphans=JTE096_orphanLines(sourceModel);
% Same already-tested arithmetic, exact five endpoint removals BEFORE blocks.
proof=JTE096_replaceArithmetic(step);
derivedStatic=JTE096_modelAudit(mdl,{step});
assert(isequal(sourceStatic.blocks,derivedStatic.blocks),'JTE096:IndependentParams','Independent declared block/IC targets differ outside patch.');
assert(isequal(sourceStatic.connectivity,derivedStatic.connectivity),'JTE096:IndependentWiring','Independent PortConnectivity differs outside patch.');
assert(isequal(sourceStatic.config,derivedStatic.config),'JTE096:IndependentConfig','Independent solver/declared model IC settings differ.');
assert(JTE096_orphanLines(mdl)==sourceOrphans,'JTE096:OrphanDelta','Derivative introduced orphan lines.');
assert(strcmp(JTE2026sha256(files.baseline),baselineSHA),'JTE096:BaselineChanged','Pristine B0L file modified.');
fprintf('JTE096_STATIC_SOURCE_DERIVATIVE_PASS scope=declared_params_wiring_solver_modelIC runtimeSimscapeIC=UNAVAILABLE physicalEquivalence=NOT_ESTABLISHED\n');
if strcmp(mode,'compileOnly')
 % These compile checks exercise the NEW graph hotfix; no time simulation.
 originalLog=evalc('set_param(sourceModel,''SimulationCommand'',''update'');');
 derivativeLog=evalc('set_param(mdl,''SimulationCommand'',''update'');');
 [sw,sl]=warningCounts(originalLog);[dw,dl]=warningCounts(derivativeLog);
 assert(dl<=sl,'JTE096:AddedWarning','New unintended unconnected-line warning.');
 assert(JTE096_orphanLines(mdl)==sourceOrphans,'JTE096:CompiledOrphan','Compile introduced orphan.');
 assert(strcmp(JTE2026sha256(files.baseline),baselineSHA)&&strcmp(JTE2026sha256(source),pin),'JTE096:Persistence','Source file changed.');
 fprintf(['JTE096_COMPILE_RESULT originalWarningCount=%d derivativeWarningCount=%d ' ...
  'originalUnconnectedLineWarnings=%d derivativeUnconnectedLineWarnings=%d ' ...
  'sourceOrphanLeaves=%d derivativeOrphanLeaves=%d deletedEndpointPairs=%d ' ...
  'newUnintendedUnconnectedWarnings=0 simulationRun=0 negativeOracleRerun=0 priorPassedTestsRerun=0\n'],sw,dw,sl,dl,sourceOrphans,JTE096_orphanLines(mdl),proof.removedEndpoints);
 fprintf('JTE096_HOTFIX_COMPILE_PASS EVENT_ACTOR=UNAVAILABLE FIRST_SECOND_EVENT_COVERAGE=NOT_EXTENDED G5_BLOCKED=1\n');
 return;
end
sat=[core '/FlwR calc/Saturation'];satH=get_param(sat,'PortHandles');
calc=get_param([core '/FlwR calc'],'PortHandles');
calcout=find_system([core '/FlwR calc'],'SearchDepth',1,'BlockType','Outport');
assert(numel(calcout)==1,'JTE094:QOut','Expected scalar q subsystem output.');
coh=get_param(calcout{1},'PortHandles');
assert(sourcePort(coh.Inport(1))==satH.Outport(1),'JTE094:QPath','q logger must trace the saturation output.');
sink=[core '/JTE094 q logger'];
add_block('simulink/Sinks/To Workspace',sink,'VariableName','jte094Q','SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
lh=get_param(sink,'PortHandles');add_line(core,calc.Outport(1),lh.Inport(1),'autorouting','on');
in=Simulink.SimulationInput(mdl);
in=in.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
 'SaveState','on','StateSaveName','jte094X','SaveFormat','Dataset','SaveTime','on','TimeSaveName','tout');
fprintf('JTE094_ATOMIC_FULL_MODEL_START sourcePinned=1 sourceSolverUnchanged=1 staticDeclaredWiringParamsChecked=1 runtimeSimscapeIC=UNAVAILABLE physicalEquivalence=NOT_ESTABLISHED horizon340=1\n');
out=sim(in);
assert(isequal(config,cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false)),'JTE094:ConfigDrift','Numerical settings changed.');
[t,u]=JTE2026timeseries(out,'jteUcore');[tq,q]=JTE2026timeseries(out,'jte094Q');
[ty,y]=JTE2026timeseries(out,'jteFlwR');[tt,T]=JTE2026timeseries(out,'jteTtrue');
assert(isequal(t,tq)&&isequal(t,ty),'JTE094:Clock','Cannot compare unequal recorded clocks silently.');
assert(t(1)==0&&t(end)==340&&size(T,2)==312&&tt(end)==340,'JTE094:Horizon','Incomplete source-model trace.');
assert(all(isfinite(q(:)))&&all(q(:)>=.001&q(:)<=.95),'JTE094:QDomain','Invalid source q.');
expected=max(.25,q-mod(q,.25));lawExact=isequal(u,expected);
firstWindow=ty>=330&ty<=338;
assert(any(firstWindow),'JTE094:Window','First source event window missing.');
excursion=any(abs(y(firstWindow)-.25)>.005);
states=out.get('jte094X');found=0;stateClock=false;
for k=1:states.numElements
 el=states.getElement(k);try,path=char(el.BlockPath.getBlock(1));catch,path='';end
 if strcmp(path,tf),found=found+1;stateClock=isequal(double(el.Values.Time(:)),ty);end
end
assert(found==1,'JTE094:State','TF state identity unavailable.');
fprintf(['JTE094_ATOMIC_FULL_MODEL_RESULT derivativeRecordedLawSelfConsistency=%d recordedCoreConstant=%d ' ...
 'firstWindowPostfilterExcursion=%d TFstateFound=1 TFstateClockMatches=%d ' ...
 'secondEventWindow=NOT_COVERED acceptedStepClassification=UNAVAILABLE ' ...
 'solverResetActorStatus=UNAVAILABLE rawEvidenceRetention=NOT_ARCHIVED ' ...
 'causalRepairAccepted=0 G5_ACCEPTED=false\n'],lawExact,all(u==.25),excursion,stateClock);
assert(lawExact,'JTE094:LawMismatch','Rollback: candidate changed recorded original controller law.');
assert(strcmp(JTE2026sha256(source),pin),'JTE094:VendorChanged','Vendor modified.');
fprintf('JTE094_ATOMIC_FULL_MODEL_DIAGNOSTIC_EXECUTED_NOT_G5_PASS\n');
end
function p=sourcePort(dst)
line=get_param(dst,'Line');
assert(line~=-1,'JTE094:Line','Source line missing.');
p=get_param(line,'SrcPortHandle');
end
function [total,lines]=warningCounts(log)
total=numel(regexp(log,'Warning:','match'));
lines=numel(regexp(lower(log),'unconnected\s+(?:output\s+|input\s+)?line','match'));
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
