function JTE094_atomicFullPlant()
% One new B0L counterfactual, not JTE092 replay and not G5 acceptance.
% Atomic Step Change retains the original q-mod(q,step), not three thresholds.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE094:Runtime','Wrong MATLAB release/update.');
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
source=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmp(JTE2026sha256(source),pin),'JTE094:Source','Vendor pin mismatch.');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()quietProject(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte094-generated'));
[~,mdl]=fileparts(files.baseline);load_system(files.baseline);
mg=onCleanup(@()quietModel(mdl)); %#ok<NASGU>
core=[mdl '/Battery Control/FlwR_calc'];step=[core '/Step Change'];
tf=[mdl '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE094:TF','Filter changed.');
keys={'Solver','SolverType','RelTol','AbsTol','MaxStep','SolverResetMethod','ZeroCrossControl','LoadInitialState','InitialState'};
config=cellfun(@(k)get_param(mdl,k),keys,'UniformOutput',false);
assert(strcmp(config{1},'ode23t')&&strcmp(config{8},'off'),'JTE094:Config','Preserve source solver and IC.');
outsideBefore=outsideSnapshot(mdl,step);
% Verify the original Step Change graph itself, not only an algebraic label.
ip=find_system(step,'SearchDepth',1,'BlockType','Inport');
op=find_system(step,'SearchDepth',1,'BlockType','Outport');
assert(numel(ip)==2&&numel(op)==1,'JTE094:StepPorts','Unexpected source quantizer interface.');
modblock=[step '/Mod'];mp=get_param(modblock,'PortHandles');
assert(strcmp(get_param(modblock,'Operator'),'mod'),'JTE094:Mod','Unexpected source operator.');
qport=sourcePort(mp.Inport(1));sport=sourcePort(mp.Inport(2));
qin=get_param(qport,'Parent');sin=get_param(sport,'Parent');
assert(any(strcmp(qin,ip))&&any(strcmp(sin,ip))&&~strcmp(qin,sin),'JTE094:StepInputs','Mod inputs must be source inports.');
oh=get_param(op{1},'PortHandles');sumport=sourcePort(oh.Inport(1));sub=get_param(sumport,'Parent');
assert(strcmp(get_param(sub,'BlockType'),'Sum')&&strcmp(get_param(sub,'Inputs'),'+-'),'JTE094:Subtract','Source output must be q minus mod.');
sh=get_param(sub,'PortHandles');
assert(sourcePort(sh.Inport(1))==qport&&sourcePort(sh.Inport(2))==mp.Outport(1),'JTE094:StepLaw','Source operation order changed.');
outer=get_param(step,'PortHandles');qnum=str2double(get_param(qin,'Port'));snum=str2double(get_param(sin,'Port'));
calc=get_param([core '/FlwR calc'],'PortHandles');const=get_param([core '/step'],'PortHandles');
assert(sourcePort(outer.Inport(qnum))==calc.Outport(1)&&sourcePort(outer.Inport(snum))==const.Outport(1),'JTE094:OuterInputs','Unexpected q or step source.');
assert(str2double(get_param([core '/step'],'Value'))==.25,'JTE094:Quarter','Step changed.');
% Copy port blocks before replacing only this virtual subsystem's contents.
backup='JTE094_PORT_BACKUP';new_system(backup);bg=onCleanup(@()quietModel(backup)); %#ok<NASGU>
ports=[ip;op];names=cellfun(@(b)get_param(b,'Name'),ports,'UniformOutput',false);
for k=1:numel(ports),add_block(ports{k},[backup '/' names{k}]);end
qname=get_param(qin,'Name');sname=get_param(sin,'Name');oname=get_param(op{1},'Name');
Simulink.SubSystem.deleteContents(step);
for k=1:numel(ports),add_block([backup '/' names{k}],[step '/' names{k}]);end
block=[step '/JTE094 Atomic Quantization'];
add_block('simulink/User-Defined Functions/MATLAB Function',block);
sf=sfroot;chart=sf.find('-isa','Stateflow.EMChart','Path',block);
assert(numel(chart)==1,'JTE094:Chart','Missing atomic chart.');
chart.Script=sprintf('function y=atomicQuantization(q,step)\n%%#codegen\ny=q-mod(q,step);\nend\n');
qh=get_param([step '/' qname],'PortHandles');sth=get_param([step '/' sname],'PortHandles');
ah=get_param(block,'PortHandles');outh=get_param([step '/' oname],'PortHandles');
assert(numel(ah.Inport)==2,'JTE094:AtomicPorts','Atomic ports unavailable.');
add_line(step,qh.Outport(1),ah.Inport(1),'autorouting','on');
add_line(step,sth.Outport(1),ah.Inport(2),'autorouting','on');
add_line(step,ah.Outport(1),outh.Inport(1),'autorouting','on');
quietModel(backup);
assert(isequal(outsideBefore,outsideSnapshot(mdl,step)),'JTE094:OutsideChanged','A block outside quantization changed.');
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
fprintf('JTE094_ATOMIC_FULL_MODEL_START sourcePinned=1 sourceSolverUnchanged=1 physicsOutsideQuantizationUnchanged=1 originalFloatingPointLawRetained=1 horizon340=1\n');
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
fprintf(['JTE094_ATOMIC_FULL_MODEL_RESULT recordedLawExact=%d recordedCoreConstant=%d ' ...
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
function s=outsideSnapshot(m,excluded)
blocks=sort(find_system(m,'LookUnderMasks','all','FollowLinks','off','Type','Block'));
s=cell(0,3);
for k=1:numel(blocks)
 b=blocks{k};
 if strcmp(b,excluded)||startsWith(b,[excluded '/']),continue;end
 dp=get_param(b,'DialogParameters');if isempty(dp),keys={};else,keys=sort(fieldnames(dp));end
 values=cell(size(keys));
 for j=1:numel(keys),values{j}=get_param(b,keys{j});end
 s(end+1,:)={b,get_param(b,'BlockType'),{keys,values}}; %#ok<AGROW>
end
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
