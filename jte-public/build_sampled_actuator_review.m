function proof=build_sampled_actuator_review(sourceFile,destFile,Ts,y0)
% Static model-method amendment ONLY. Never simulate or overwrite source.
assert(isfile(sourceFile)&&~isfile(destFile),'ActReview:Fresh','Fresh isolated destination required.');
validateattributes(Ts,{'double'},{'real','scalar','finite','positive'});
validateattributes(y0,{'double'},{'real','scalar','finite'});
sourceSHA=JTE2026sha256(sourceFile);copyfile(sourceFile,destFile);
[~,m]=fileparts(destFile);load_system(destFile);done=onCleanup(@()quietClose(m)); %#ok<NASGU>
parent=[m '/Battery Control'];old=[parent '/sensor dynamics 1'];ctrl=[parent '/FlwR_calc'];
assert(strcmp(get_param(old,'BlockType'),'TransferFcn')&&strcmp(get_param(old,'SID'),'197')&&...
 strcmp(get_param(old,'Numerator'),'[1]')&&strcmp(get_param(old,'Denominator'),'[1e-3 1]'),...
 'ActReview:Source','Expected immutable source filter.');
oldh=get_param(old,'PortHandles');ch=get_param(ctrl,'PortHandles');
assert(numel(oldh.Inport)==1&&numel(oldh.Outport)==1&&src(oldh.Inport(1))==ch.Outport(1),...
 'ActReview:Source','Controller/filter source edge differs.');
dests=destinations(parent,oldh.Outport(1));
assert(~isempty(dests)&&all(dests~=-1),'ActReview:Source','No intact source filter destinations.');
before=JTE096_modelAudit(m,{old});
oldEdges=string(JTE096_signalEdges(parent));
deleted=label(ch.Outport(1),parent)+">"+label(oldh.Inport(1),parent);
allowed={relative(ctrl,m)};
for k=1:numel(dests)
 deleted(end+1,1)=label(oldh.Outport(1),parent)+">"+label(dests(k),parent); %#ok<AGROW>
 allowed{end+1}=relative(get_param(dests(k),'Parent'),m); %#ok<AGROW>
end
for k=1:numel(deleted),assert(sum(oldEdges==deleted(k))==1,'ActReview:EdgeMultiplicity','Source edge not unique.');end
assert(JTE096_orphanLines(parent)==0,'ActReview:SourceOrphans','Source control hierarchy has orphan line.');
delete_line(parent,ch.Outport(1),oldh.Inport(1));
for k=1:numel(dests),delete_line(parent,oldh.Outport(1),dests(k));end
assert(get_param(oldh.Inport(1),'Line')==-1,'ActReview:Detach','Old filter input not detached.');
for k=1:numel(dests),assert(get_param(dests(k),'Line')==-1,'ActReview:Detach','Old destination branch not detached.');end
oldPosition=get_param(old,'Position');delete_block(old);
hold=[parent '/Amended command sample hold'];act=[parent '/Amended sampled actuator'];
alpha=exp(-Ts/.001);beta=1-alpha;
assert(isfinite(alpha)&&alpha>0&&alpha<1&&beta>0&&beta<=1,'ActReview:Coefficients','Invalid unmodified exponential coefficients.');
add_block('simulink/Discrete/Zero-Order Hold',hold,'SampleTime',mat2str(Ts,17),'Position',oldPosition+[ -70 0 -70 0]);
add_block('simulink/Discrete/Discrete State-Space',act,'A',mat2str(alpha,17),'B',mat2str(beta,17),'C','1','D','0',...
 'InitialCondition',mat2str(y0,17),'SampleTime',mat2str(Ts,17),'StateName','amendedActuatorOutputState','Position',oldPosition+[20 0 40 0]);
hh=get_param(hold,'PortHandles');ah=get_param(act,'PortHandles');
add_line(parent,ch.Outport(1),hh.Inport(1),'autorouting','on');
add_line(parent,hh.Outport(1),ah.Inport(1),'autorouting','on');
newEdges=[label(ch.Outport(1),parent)+">"+label(hh.Inport(1),parent);label(hh.Outport(1),parent)+">"+label(ah.Inport(1),parent)];
for k=1:numel(dests)
 add_line(parent,ah.Outport(1),dests(k),'autorouting','on');
 newEdges(end+1,1)=label(ah.Outport(1),parent)+">"+label(dests(k),parent); %#ok<AGROW>
end
expected=sort([setdiff(oldEdges,deleted);newEdges]);
assert(isequal(sort(string(JTE096_signalEdges(parent))),expected),'ActReview:Graph','Unexpected local signal edge change.');
assert(JTE096_orphanLines(parent)==0,'ActReview:Orphans','Created an orphan line.');
after=JTE096_modelAudit(m,{hold,act});
initialDifference=struct('blockRowsEqual',isequal(before.blocks,after.blocks),'configEqual',isequal(before.config,after.config),...
 'configurationChanges',{configDiff(before.config,after.config)});
save([destFile '.AUDIT_DIFF.mat'],'before','after','initialDifference','-v7.3');
solverRestored=false;
if ~isequal(before.config,after.config)
 changes=initialDifference.configurationChanges;
 if ~isempty(changes)&&all(ismember(changes(:,1),{'Solver','SolverType'}))
  keys=before.config{1};vals=before.config{2};
  set_param(m,'SolverType',vals{strcmp(keys,'SolverType')},'Solver',vals{strcmp(keys,'Solver')});
  solverRestored=true;after=JTE096_modelAudit(m,{hold,act});
 end
end
save([destFile '.AUDIT_DIFF.mat'],'before','after','initialDifference','solverRestored','-v7.3');
assert(isequal(before.blocks,after.blocks)&&isequal(before.config,after.config),...
 'ActReview:Parameters','Retained controller/physical/IC parameters or source solver changed.');
a=before.connectivity;b=after.connectivity;allowed=unique(allowed);
a=a(~ismember(a(:,1),allowed),:);b=b(~ismember(b(:,1),allowed),:);
assert(isequal(a,b),'ActReview:Connectivity','Connectivity changed outside the exact replaced endpoints.');
save_system(m,destFile);
assert(strcmp(JTE2026sha256(sourceFile),sourceSHA),'ActReview:SourceBytes','Original source bytes changed.');
proof=struct('sourceModelSHA',sourceSHA,'amendedModelSHA',JTE2026sha256(destFile),...
 'methodAmendment',true,'originalSolverPolicyRestoredAfterEditorAutoChange',solverRestored,'initialEditorConfigurationChanges',{initialDifference.configurationChanges},'sourceBitwiseEquivalenceClaimed',false,'physicalParameterParity',true,...
 'retainedControllerParameterParity',true,'retainedInitializationParameterParity',true,...
 'outsideExactEndpointsConnectivityParity',true,'localEdgesExact',true,...
 'removedContinuousFilterCount',1,'newDiscreteActuatorCount',1,'newInputSampleHoldCount',1,...
 'removedBlock',relative(old,m),'newActuator',relative(act,m),'newHold',relative(hold,m),...
 'removedEdges',{cellstr(deleted)},'newEdges',{cellstr(newEdges)},'changedConnectivityRows',{allowed},...
 'Ts_s',Ts,'tau_s',.001,'A',alpha,'B',beta,'C',1,'D',0,'initialStateFromActualArchivedOutput',y0,...
 'samplingOffset_s',0,'outputHold',true,'solvedICParity','UNPROVEN_STATIC_ONLY',...
 'physicalSimulation',false,'toySimulation',false,'originalG5Accepted',false);
end
function rows=configDiff(a,b)
rows=cell(0,3);keys=a{1};va=a{2};vb=b{2};
assert(isequal(keys,b{1}),'ActReview:ConfigKeys','Configuration audit key set differs.');
for k=1:numel(keys),if ~isequaln(va{k},vb{k}),rows(end+1,:)={keys{k},va{k},vb{k}};end;end
end
function d=destinations(sys,p)
lines=find_system(sys,'FindAll','on','SearchDepth',1,'Type','line');d=[];
for k=1:numel(lines)
 h=lines(k);if ~isempty(get_param(h,'LineChildren')),continue;end
 s=get_param(h,'SrcPortHandle');q=h;
 while s==-1,q=get_param(q,'LineParent');if q==-1,break;end;s=get_param(q,'SrcPortHandle');end
 if s==p
  x=get_param(h,'DstPortHandle');d=[d;x(x~=-1)]; %#ok<AGROW>
 end
end
d=unique(d);d=d(:);
end
function p=src(h)
ln=get_param(h,'Line');assert(ln~=-1,'ActReview:Line','Missing line.');p=get_param(ln,'SrcPortHandle');
end
function s=label(p,sys)
b=get_param(p,'Parent');assert(startsWith(b,[sys '/']),'ActReview:Hierarchy','Cross-hierarchy signal edge.');
s=string(b(numel(sys)+2:end))+":"+string(get_param(p,'PortNumber'));
end
function s=relative(b,m)
s=['$ROOT' b(numel(m)+1:end)];
end
function quietClose(m)
try,close_system(m,0);catch,end
end
