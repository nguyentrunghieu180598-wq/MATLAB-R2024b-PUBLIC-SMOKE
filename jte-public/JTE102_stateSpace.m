function JTE102_stateSpace(mode)
% One conditional controller-connected equivalent continuous realization.
P=paths();M=jsondecode(fileread(fullfile(P.private,'b_manifest.json')));
for k=1:numel(M.files)
 item=M.files(k);assert(strcmp(JTE2026sha256(fullfile(P.private,item.local)),item.sha256),'JTE102:InputSHA','Private input changed.');
end
A=jsondecode(fileread(fullfile(P.private,'audit.json')));
assert(strcmp(A.flags.B,'NEEDS_RUN')&&strcmp(A.run,'40462103051'),'JTE102:StageA','Candidate not justified.');
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE102:Runtime','Wrong runtime.');
assert(strcmp(JTE2026sha256(P.source),P.pin),'JTE102:Source','Vendor pin.');
project=openProject(fullfile(P.vendor,'batteryExamplesProjectSetup.prj'));
pg=onCleanup(@()quietProject(project)); %#ok<NASGU>
W=load(fullfile(P.private,'source_workspace.mat'),'workspaceSnapshot');
names=fieldnames(W.workspaceSnapshot);
for k=1:numel(names),value=W.workspaceSnapshot.(names{k});assignin('base',names{k},value);assert(isequaln(evalin('base',names{k}),value),'JTE102:Workspace','Exact frozen source workspace not restored.');end
if strcmp(mode,'prepare'),prepare(P,A);return;end
assert(strcmp(mode,'simulate'),'JTE102:Mode','Unknown mode.');
S=load(fullfile(P.private,'candidate_prepared.mat'),'prepared');prepared=S.prepared;
assert(strcmp(JTE2026sha256(P.modelFile),prepared.modelSHA),'JTE102:ModelSHA','Candidate changed.');
load_system(P.modelFile);cg=onCleanup(@()quietModel(P.model)); %#ok<NASGU>
verifyConfig(P.model,A.cases.B0L_original.metadata.solver);verifySS(P.tf,prepared.X0);
h=get_param(P.tf,'PortHandles');core=get_param(P.core,'PortHandles');
assert(source(h.Inport(1))==core.Outport(1),'JTE102:SourceWire','Core-to-filter wire changed.');
marker=fullfile(P.private,'STATESPACE340_ENTERED.json');assert(~isfile(marker),'JTE102:Repeat','No repeat.');
writeJSON(marker,struct('run',P.run,'phase','SIM_CALL_ENTERED'));
input=Simulink.SimulationInput(P.model);
input=input.setModelParameter('StartTime','0','StopTime','340','SimulationMode','normal',...
 'SaveState','on','StateSaveName','jte102States','SaveFormat','Dataset','SaveTime','on','TimeSaveName','tout',...
 'SignalLogging','on','SignalLoggingName','jte102Inputs');
before=JTE096_modelAudit(P.model);
fprintf('JTE102_SS340_SIM_CALL_START sourceOriginalRerun=0 oneNewDerivative=1 solverUnchanged=1 controllerUnchanged=1\n');
out=sim(input);
fprintf('JTE102_SS340_SIM_RETURNED resultCaptured=1\n');
record=struct('schema','JTE102_EQUIVALENT_REALIZATION_RAW_NOT_G5','run',P.run,'commit',P.commit,...
 'simulationOutput',out,'sourceSHA256',P.pin,'modelSHA256',prepared.modelSHA,'prepared',prepared,...
 'referenceRun','40449421507','stageARun','40462103051','requestedOverrides',{input.ModelParameters},...
 'acceptedStepCertification','UNAVAILABLE','G5_ACCEPTED',false);
file=fullfile(P.private,['JTE102_' P.run '_STATESPACE340_RAW.mat']);save(file,'record','-v7.3');
copyfile(P.modelFile,fullfile(P.private,['JTE102_' P.run '_STATESPACE340_MODEL.slx']));
after=JTE096_modelAudit(P.model);
assert(isequal(before.config,after.config)&&strcmp(JTE2026sha256(P.source),P.pin),'JTE102:Drift','Source or solver changed.');
R=load(fullfile(P.private,'reference_compact.mat'),'reference');r=R.reference;
d=extract(out,P);
law=isequal(d.core,max(.25,d.q-mod(d.q,.25)));
sameInitial=isequal(d.T(1,:),r.T0)&&d.output(1)==r.y0&&d.state(1)==prepared.X0&&...
 initialMapsEqual(r.initialMap,r.initialMapAvailable,d.initialMap,d.initialMapAvailable,P.filterSuffix);
stateOutput=all(abs(d.output-d.state)<=1e-9);
sameInput=isequal(d.input,d.core);held=all(d.input==.25)&&all(d.core==.25);
window=d.time>=330&d.time<=338;excursion=any(abs(d.output(window)-.25)>.005);
qualified=d.clocksQualified&&sameInitial&&stateOutput&&sameInput&&law;
candidate='INCONCLUSIVE_TOPOLOGY_OR_EVENT_CHANGE';e='INCONCLUSIVE';
if qualified&&held
 if excursion,candidate='EQUIVALENT_REALIZATION_DID_NOT_FIX';e='YES';
 else,candidate='CANDIDATE_NUMERICAL_REALIZATION_ONLY';e='NO';end
end
comparison=struct('qualified',qualified,'candidate',candidate,'excursion',e,'inputEqualsAuthenticCore',sameInput,...
 'sourceLawNativeExact',law,'nativeInputHeld',held,'nativeClocksQualified',d.clocksQualified,...
 'initialSavedStateAndThermalQualified',sameInitial,'stateOutputQualified',stateOutput,...
 'stateOutputMaxAbsResidual',max(abs(d.output-d.state)),...
 'legitimateRecordedCommandTransitionTimes_s',d.time([false;diff(d.core)~=0]),...
 'coreTransitionsAreNotSuppressedByIntervention',true,...
 'eventTopologyEquivalence','NOT_PROVEN','SECOND_EVENT','NOT_COVERED','G5_ACTUATION_EVENT','ACTUATION_EVENT_UNRESOLVED',...
 'solverCoordinateCaution','Same declared tolerances; changed state coordinates can alter solver error weighting and schedule. This is a numerical candidate only.',...
 'G5_ACCEPTED',false);
record.observed=d;record.comparison=comparison;save(file,'record','-v7.3');
writeJSON(fullfile(P.private,['JTE102_' P.run '_STATESPACE340_FLAGS.json']),comparison);
fprintf('JTE102_SS340_RESULT qualified=%d CANDIDATE=%s EXCURSION=%s sourceLawNativeExact=%d nativeInputHeld=%d initialQualified=%d stateOutputQualified=%d nativeClocksQualified=%d G5_ACTUATION_EVENT=ACTUATION_EVENT_UNRESOLVED SECOND_EVENT=NOT_COVERED G5_ACCEPTED=false\n',...
 qualified,candidate,e,law,held,sameInitial,stateOutput,d.clocksQualified);
end
function prepare(P,A)
assert(~isfolder(P.generated),'JTE102:Fresh','Fresh derivative required.');mkdir(P.generated);
Q=load(fullfile(P.private,'original_raw.mat'),'record');r=Q.record;
assert(strcmp(r.schema,'JTE101_TF_340_RAW_NOT_G5')&&strcmp(r.run,'40449421507')&&r.qualification.qualified,'JTE102:Reference','Unqualified original.');
assert(strcmp(JTE2026sha256(fullfile(P.private,'source_workspace.mat')),r.prepared.workspaceSHA256),'JTE102:WorkspaceSHA','Source snapshot changed.');
reference=struct('T0',r.observed.trueTemperature(1,:),'y0',r.observed.output(1),'canonicalTFx0',r.observed.state(1),...
 'Ctf',r.calibration.C,'initialMap',r.observed.initialStateMap,'initialMapAvailable',r.observed.initialStateMapAvailable,...
 'firstEvent',r.qualification.event,'sourceSHA',r.sourceSHA256,'modelSHA',r.modelSHA256);
assert(reference.y0==0&&reference.canonicalTFx0==0&&reference.y0==reference.Ctf*reference.canonicalTFx0,'JTE102:InitialOutput','Source fixed-zero IC conflicts with actual initial output.');
clear Q r;
original=fullfile(P.private,'JTE101Original.slx');
assert(strcmp(JTE2026sha256(original),reference.modelSHA),'JTE102:ArchivedModelSHA','Wrong archived original model.');
load_system(original);og=onCleanup(@()quietModel('JTE101Original')); %#ok<NASGU>
sourceTF=['JTE101Original' P.filterSuffix];verifyTF(sourceTF);
sourceDeclaration=dialogSnapshot(sourceTF);
assert(~any(ismember({'InitialCondition','X0'},sourceDeclaration.keys)),'JTE102:TFICDeclaration','Unexpected editable TransferFcn IC requires explicit review.');
verifyConfig('JTE101Original',A.cases.B0L_original.metadata.solver);
copyfile(original,P.modelFile);load_system(P.modelFile);cg=onCleanup(@()quietModel(P.model)); %#ok<NASGU>
tf=P.tf;h=get_param(tf,'PortHandles');src=source(h.Inport(1));core=get_param(P.core,'PortHandles');
assert(src==core.Outport(1),'JTE102:Core','Authentic source core not feeding original filter.');
line=get_param(h.Outport(1),'Line');dest=get_param(line,'DstPortHandle');dest=dest(dest~=-1);
assert(~isempty(dest),'JTE102:OutputWire','No filter output sinks.');
edges=JTE096_signalEdges(P.ctrl);
before=JTE096_modelAudit(P.model,{tf});orphan=JTE096_orphanLines(P.model);
pos=get_param(tf,'Position');orientation=get_param(tf,'Orientation');
delete_line(P.ctrl,src,h.Inport(1));
for k=1:numel(dest),delete_line(P.ctrl,h.Outport(1),dest(k));end
delete_block(tf);
% C=1,D=0 => xSS0=ySource0; never reuse canonical TF xout scale.
X0=reference.y0;
add_block('simulink/Continuous/State-Space',tf,'A','-1000','B','1000','C','1','D','0',...
 'InitialCondition',mat2str(X0,17),'Position',pos,'Orientation',orientation);
nh=get_param(tf,'PortHandles');add_line(P.ctrl,src,nh.Inport(1),'autorouting','on');
for k=1:numel(dest),add_line(P.ctrl,nh.Outport(1),dest(k),'autorouting','on');end
% Preserve a declared block absolute tolerance when exposed by both realizations.
newDP=get_param(tf,'DialogParameters');
if any(strcmp(sourceDeclaration.keys,'AbsoluteTolerance'))&&isfield(newDP,'AbsoluteTolerance')
 ix=find(strcmp(sourceDeclaration.keys,'AbsoluteTolerance'));set_param(tf,'AbsoluteTolerance',sourceDeclaration.values{ix});
end
verifySS(tf,X0);
assert(isequal(edges,JTE096_signalEdges(P.ctrl)),'JTE102:Edges','Signal graph changed beyond one realization node.');
after=JTE096_modelAudit(P.model,{tf});
flags=struct('blocksEqual',isequal(before.blocks,after.blocks),'connectivityEqual',isequal(before.connectivity,after.connectivity),'configEqual',isequal(before.config,after.config));
if ~flags.blocksEqual||~flags.connectivityEqual||~flags.configEqual
 diff=struct('flags',flags,'blockRows',{{}},'connectionRows',{{}},'beforeConfig',{before.config},'afterConfig',{after.config});
 for ii=1:size(before.blocks,1)
  if ii>size(after.blocks,1)||~isequal(before.blocks(ii,:),after.blocks(ii,:))
   row=struct('index',ii,'before',{before.blocks(ii,:)},'after',[]);
   if ii<=size(after.blocks,1),row.after=after.blocks(ii,:);end
   diff.blockRows{end+1}=row;
  end
 end
 for ii=1:size(before.connectivity,1)
  if ii>size(after.connectivity,1)||~isequal(before.connectivity(ii,:),after.connectivity(ii,:))
   row=struct('index',ii,'before',{before.connectivity(ii,:)},'after',[]);
   if ii<=size(after.connectivity,1),row.after=after.connectivity(ii,:);end
   diff.connectionRows{end+1}=row;
  end
 end
 prefix=fullfile(P.private,['JTE102_' P.run '_PREPARE_STATIC_FAILURE']);
 writeJSON([prefix '.json'],diff);save([prefix '.mat'],'before','after','diff','-v7.3');
 fprintf('JTE102_STATIC_DELTA_REJECTED blocksEqual=%d connectivityEqual=%d configEqual=%d canaryRun=0 physicalSimulationRun=0 privateDiffWritten=1\n',flags.blocksEqual,flags.connectivityEqual,flags.configEqual);
end
assert(isequal(before.blocks,after.blocks)&&isequal(before.connectivity,after.connectivity)&&isequal(before.config,after.config),...
 'JTE102:OutsideDelta','Retained plant/control/solver changed.');
assert(JTE096_orphanLines(P.model)==orphan,'JTE102:Orphan','Replacement left orphan wires.');
logger=get_param([P.ctrl '/JTE Command'],'PortHandles');
assert(source(logger.Inport(1))==core.Outport(1),'JTE102:CoreLogger','Authentic source core logger changed.');
set_param(src,'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName','JTE101ActualTFInput',...
 'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
calc=[P.core '/FlwR calc'];sat=[calc '/Saturation'];sh=get_param(sat,'PortHandles');
op=find_system(calc,'SearchDepth',1,'BlockType','Outport');assert(numel(op)==1,'JTE102:QOut','Q source interface.');
oh=get_param(op{1},'PortHandles');assert(source(oh.Inport(1))==sh.Outport(1),'JTE102:QSource','Q not saturation output.');
qh=get_param(calc,'PortHandles');
set_param(qh.Outport(1),'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName','JTE102SourceQ',...
 'DataLoggingLimitDataPoints','off','DataLoggingDecimateData','off');
loadFile=which(get_param([P.model '/Current demand'],'FileName'));
assert(strcmp(JTE2026sha256(loadFile),A.cases.B0L_original.metadata.loadSHA),'JTE102:Load','Frozen load changed.');
canary=canaryTest(P,'JTE101Original',X0);
assert(canary.passed,'JTE102:Canary','New equivalent realization canary failed; do not run plant.');
set_param(P.model,'SimulationCommand','update'); % compile only, no source simulation
save_system(P.model,P.modelFile);
prepared=struct('schema','JTE102_ONE_EQUIVALENT_REALIZATION','modelSHA',JTE2026sha256(P.modelFile),...
 'sourceSHA',P.pin,'archivedOriginalModelSHA',reference.modelSHA,'X0',X0,...
 'sourceICDeclaration','R2024b TransferFcn fixed-zero initial state, no editable X0; confirmed against archived native y0 and canonical x0.',...
 'sourceTFDialog',sourceDeclaration,'sourceTFDocs','https://www.mathworks.com/help/releases/R2024b/simulink/slref/transferfcn.html',...
 'stateSpaceDocs','https://www.mathworks.com/help/releases/R2024b/simulink/slref/statespace.html',...
 'stateCoordinateRelation','xSS=yTF=Ctf*xCanonicalTF; C=1,D=0. Common zero initial physical output; no steady-state .25 initialization.',...
 'canary',canary,'outsideStaticProof',before,'signalEdges',{edges},'soleRealizationNodeDelta',true,...
 'modelDeclaredSolverUnchanged',true,'sourceWorkspaceSHA',JTE2026sha256(fullfile(P.private,'source_workspace.mat')),...
 'eventTopologyEquivalence','NOT_PROVEN','acceptedStepCertification','UNAVAILABLE','G5_ACCEPTED',false);
save(fullfile(P.private,'candidate_prepared.mat'),'prepared','-v7.3');
save(fullfile(P.private,'reference_compact.mat'),'reference','-v7.3');
prefix=fullfile(P.private,['JTE102_' P.run '_PREPARE']);
copyfile(P.modelFile,[prefix '_MODEL.slx']);copyfile(fullfile(P.private,'candidate_prepared.mat'),[prefix '_PROOF.mat']);
copyfile(fullfile(P.private,'source_workspace.mat'),[prefix '_WORKSPACE.mat']);
save([prefix '_REFERENCE_COMPACT.mat'],'reference','-v7.3');
writeJSON([prefix '_FLAGS.json'],struct('canary',true,'nearULPSourceLaw',true,'compile',true,'soleRealizationNodeDelta',true,'originalSimulationRerun',false,'G5_ACCEPTED',false));
assert(strcmp(JTE2026sha256(original),reference.modelSHA)&&strcmp(JTE2026sha256(P.source),P.pin),'JTE102:SourceMutation','Source changed.');
fprintf('JTE102_B_PREPARE_PASS sourceICNativeConfirmed=1 X0DerivedFromSourceOutput=1 soleRealizationNodeDelta=1 unchangedAuthenticControllerWire=1 syntheticCanary=PASS nearULPSourceLaw=PASS derivativeCompile=PASS originalSimulationRerun=0\n');
end
function result=canaryTest(P,original,X0)
m='JTE102NewRealizationCanary';new_system(m);g=onCleanup(@()quietModel(m)); %#ok<NASGU>
set_param(m,'Solver','ode45','StopTime','.02','MaxStep','1e-5','RelTol','1e-10','AbsTol','1e-12',...
 'SaveTime','on','TimeSaveName','tout','ReturnWorkspaceOutputs','on');
sourceStep=[original '/Battery Control/FlwR_calc/Step Change'];
ip=find_system(sourceStep,'SearchDepth',1,'BlockType','Inport');assert(numel(ip)==2,'JTE102:CanaryInterface','Source law two inputs.');
mh=get_param([sourceStep '/Mod'],'PortHandles');
qPort=str2double(get_param(get_param(source(mh.Inport(1)),'Parent'),'Port'));
sPort=str2double(get_param(get_param(source(mh.Inport(2)),'Parent'),'Port'));
qvals=[];for b=[.25 .5 .75],qvals=[qvals neighbor(b,-1) b neighbor(b,1)];end %#ok<AGROW>
for k=1:11
 base=[m '/case' num2str(k)];
 if k==1
  add_block('simulink/Sources/Constant',[base 'Input'],'Value','.25','SampleTime','0');input=[base 'Input/1'];
 elseif k==2
  add_block('simulink/Sources/Step',[base 'Input'],'Time','.005','Before','.25','After','.75','SampleTime','0');input=[base 'Input/1'];
 else
  law=[base 'SourceLaw'];add_block(sourceStep,law);
  add_block('simulink/Sources/Constant',[base 'Q'],'Value',mat2str(qvals(k-2),17),'SampleTime','0');
  add_block('simulink/Sources/Constant',[base 'Step'],'Value','.25','SampleTime','0');
  add_line(m,[get_param([base 'Q'],'Name') '/1'],[get_param(law,'Name') '/' num2str(qPort)]);
  add_line(m,[get_param([base 'Step'],'Name') '/1'],[get_param(law,'Name') '/' num2str(sPort)]);
  assert(isequal(JTE096_signalEdges(sourceStep),JTE096_signalEdges(law)),'JTE102:TieSourceLaw','Source-law copy edges changed.');
  input=[law '/1'];
 end
 add_block('simulink/Continuous/Transfer Fcn',[base 'TF'],'Numerator','[1]','Denominator','[1e-3 1]');
 add_block('simulink/Continuous/State-Space',[base 'SS'],'A','-1000','B','1000','C','1','D','0','InitialCondition',mat2str(X0,17));
 for suffix={'U','TFY','SSY'}
  add_block('simulink/Sinks/To Workspace',[base suffix{1}],'VariableName',['c' num2str(k) suffix{1}],...
   'SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
 end
 in=erase(input,[m '/']);
 add_line(m,in,[get_param([base 'TF'],'Name') '/1']);add_line(m,in,[get_param([base 'SS'],'Name') '/1']);add_line(m,in,[get_param([base 'U'],'Name') '/1']);
 add_line(m,[get_param([base 'TF'],'Name') '/1'],[get_param([base 'TFY'],'Name') '/1']);
 add_line(m,[get_param([base 'SS'],'Name') '/1'],[get_param([base 'SSY'],'Name') '/1']);
end
out=sim(m);errors=zeros(11,3);
for k=1:11
 [t,u]=JTE2026timeseries(out,['c' num2str(k) 'U']);[ty,y]=JTE2026timeseries(out,['c' num2str(k) 'TFY']);[tz,z]=JTE2026timeseries(out,['c' num2str(k) 'SSY']);
 assert(isequal(t,ty)&&isequal(t,tz),'JTE102:CanaryClock','Synthetic clocks differ.');
 if k==2
  expected=.25*(1-exp(-t/.001));mask=t>=.005;ys=.25*(1-exp(-.005/.001));expected(mask)=.75+(ys-.75)*exp(-(t(mask)-.005)/.001);
 elseif k==1
  assert(all(u==.25),'JTE102:CanaryInput','Constant input changed.');expected=.25*(1-exp(-t/.001));
 else
  cmd=max(.25,qvals(k-2)-mod(qvals(k-2),.25));
  assert(all(u==cmd),'JTE102:NearULPLaw','Near-ULP source command changed.');
  expected=cmd*(1-exp(-t/.001));
 end
 errors(k,:)=[max(abs(y-z)),max(abs(y-expected)),max(abs(z-expected))];
end
assert(all(errors(:)<=1e-8),'JTE102:CanaryEquivalence','LTI or analytic response mismatch.');
result=struct('passed',true,'cases',11,'sourceNearULPCases',9,'tolerance',1e-8,'maxErrors',errors,...
 'syntheticSolverOnly','ode45 MaxStep1e-5 RelTol1e-10 AbsTol1e-12; full plant retains original ode23t',...
 'qNearULP',qvals,'sourceLawCopiedUnchanged',true,'G5_ACCEPTED',false);
save(fullfile(P.private,['JTE102_' P.run '_PREPARE_SYNTHETIC_CANARY.mat']),'out','result','-v7.3');
fprintf('JTE102_NEW_REALIZATION_CANARY_PASS constantAndStep=1 sourceNearULPTies=1 noQuantizerRewrite=1 physicalSimulationRun=0\n');
end
function d=extract(out,P)
[t,u]=JTE2026timeseries(out,'jteUcore');[ty,y]=JTE2026timeseries(out,'jteFlwR');[tt,T]=JTE2026timeseries(out,'jteTtrue');
logs=out.get('jte102Inputs');a=logs.getElement('JTE101ActualTFInput');b=logs.getElement('JTE102SourceQ');
[ti,input]=JTE056normalize(a.Values.Time,a.Values.Data,a.Values.IsTimeFirst);
[tq,q]=JTE056normalize(b.Values.Time,b.Values.Data,b.Values.IsTimeFirst);
ds=out.get('jte102States');found=0;initial=struct('key',{},'time',{},'value',{});available=true;tx=[];x=[];
for k=1:ds.numElements
 el=ds.getElement(k);paths={};
 try,for z=1:el.BlockPath.getLength(),paths{z}=char(el.BlockPath.getBlock(z));end;catch,available=false;continue;end %#ok<AGROW>
 path=strjoin(paths,'::');
 try
  [ts,v]=JTE056normalize(el.Values.Time,el.Values.Data,el.Values.IsTimeFirst);
  if strcmp(path,P.tf),found=found+1;tx=ts;x=v;end
  initial(end+1)=struct('key',strrep([path '|' char(el.Name)],P.model,'$ROOT'),'time',ts(1),'value',v(1,:)); %#ok<AGROW>
 catch,available=false;
 end
end
assert(found==1&&size(x,2)==1&&size(T,2)==312&&t(1)==0&&t(end)==340,'JTE102:RawTrace','Required native state/T trace missing.');
available=available&&numel(unique({initial.key}))==numel(initial);
d=struct('time',t,'core',u,'outputTime',ty,'output',y,'trueTime',tt,'T',T,'inputTime',ti,'input',input,'qTime',tq,'q',q,...
 'stateTime',tx,'state',x,'initialMap',initial,'initialMapAvailable',available,'tout',out.get('tout'),...
 'clocksQualified',isequal(t,ty)&&isequal(t,tt)&&isequal(t,ti)&&isequal(t,tq)&&isequal(t,tx),...
 'acceptedStepCertification','UNAVAILABLE_NATIVE_SAVED_POINTS_ONLY');
end
function ok=initialMapsEqual(a,aa,b,bb,suffix)
ok=false;if ~aa||~bb,return;end
a=a(~startsWith({a.key},['$ROOT' suffix '|']));b=b(~startsWith({b.key},['$ROOT' suffix '|']));
[ka,ia]=sort({a.key});[kb,ib]=sort({b.key});if ~isequal(ka,kb),return;end
ok=true;for k=1:numel(ia),if a(ia(k)).time~=0||b(ib(k)).time~=0||~isequaln(a(ia(k)).value,b(ib(k)).value),ok=false;return;end;end
end
function d=dialogSnapshot(b)
dp=get_param(b,'DialogParameters');d.keys=sort(fieldnames(dp));d.values=cell(size(d.keys));
for k=1:numel(d.keys),d.values{k}=get_param(b,d.keys{k});end
end
function verifyConfig(m,s)
for name={'Solver','SolverType','RelTol','AbsTol','MaxStep','MinStep','InitialStep','FixedStep','ZeroCrossControl','LoadInitialState','InitialState','SimulationMode'}
 assert(strcmp(get_param(m,name{1}),s.(name{1})),'JTE102:Config','Locked source config differs.');
end
for name={'InitFcn','StartFcn','StopFcn','PostLoadFcn'},assert(isempty(get_param(m,name{1})),'JTE102:Callback','Unexpected runtime callback.');end
end
function verifyTF(tf)
assert(strcmp(get_param(tf,'SID'),'197')&&strcmp(get_param(tf,'BlockType'),'TransferFcn')&&strcmp(get_param(tf,'Numerator'),'[1]')&&strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE102:TF','Wrong archived source filter.');
end
function verifySS(tf,x)
assert(strcmp(get_param(tf,'BlockType'),'StateSpace')&&strcmp(get_param(tf,'A'),'-1000')&&strcmp(get_param(tf,'B'),'1000')&&strcmp(get_param(tf,'C'),'1')&&strcmp(get_param(tf,'D'),'0')&&strcmp(get_param(tf,'AllowTunableDMatrix'),'off')&&str2double(get_param(tf,'InitialCondition'))==x,'JTE102:SS','Wrong continuous equivalent realization.');
end
function x=neighbor(x,dir)
b=typecast(double(x),'uint64');if dir<0,b=b-uint64(1);else,b=b+uint64(1);end;x=typecast(b,'double');
end
function p=source(dst)
line=get_param(dst,'Line');assert(line~=-1,'JTE102:Line','Missing source line.');p=get_param(line,'SrcPortHandle');
end
function P=paths()
P.root=pwd;P.vendor=fullfile(pwd,'vendor-pack');P.private=fullfile(pwd,'jte102-private');P.generated=fullfile(pwd,'jte102-generated');
P.model='JTE102StateSpace';P.modelFile=fullfile(P.generated,[P.model '.slx']);P.ctrl=[P.model '/Battery Control'];P.core=[P.ctrl '/FlwR_calc'];
P.filterSuffix='/Battery Control/sensor dynamics 1';P.tf=[P.model P.filterSuffix];
P.pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';P.source=fullfile(P.vendor,'Models','Battery_Pack_Thermal_Management.slx');
P.run=getenv('GITHUB_RUN_ID');P.commit=getenv('GITHUB_SHA');
end
function writeJSON(file,v)
f=fopen(file,'w');assert(f~=-1,'JTE102:JSON','Cannot write private JSON.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
function quietModel(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
function quietProject(p)
try,close(p);catch,end
end
