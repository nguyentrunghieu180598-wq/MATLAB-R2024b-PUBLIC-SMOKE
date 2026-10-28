function sampled_gate_toy()
% Exactly ONE non-battery trajectory, both frozen periods. No vendor model.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_TOY']);
m='BTMS_SAMPLED_SEMANTICS_TOY';dt=.00025;stop=.12;specs=struct([]);out=[];simCount=0;tr={};
flags=struct('MATLAB_TOY_COMPLETE',false,'ACTUAL_PRE_POST_STATE_AVAILABLE',false,'MATLAB_PHASE_CHECKS',false,...
 'INDEPENDENT_DECIMAL_ORACLE','PENDING','PHYSICAL_RUN',false,'G5_ACCEPTED',false);
r=struct('runtime',version,'scope','Synthetic discrete semantics only; no battery/source simulation','simCount',0);
try
 assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'Gate:Runtime','R2024bU10 required.');
 A=jsondecode(fileread(fullfile(P,'toy_Ref.json')));B=jsondecode(fileread(fullfile(P,'toy_Fine.json')));proofs={A,B};
 new_system(m);set_param(m,'SolverType','Fixed-step','Solver','FixedStepDiscrete','FixedStep',mat2str(dt,17),...
  'StartTime','0','StopTime',mat2str(stop,17),'SimulationMode','normal','ReturnWorkspaceOutputs','on',...
  'BlockReduction','off','OptimizeBlockIOStorage','off','SaveState','on','StateSaveName','toyStates','SaveFormat','Dataset');
 t=(0:round(stop/dt))'*dt;mw=get_param(m,'ModelWorkspace');j=0;
 for ri=1:2
  q=proofs{ri};p=q.proof;Ts=p.Ts_s;frozen=[.01 .005];assert(Ts==frozen(ri),'Gate:Period','Frozen Ts differs.'); %#ok<NBRAK>
  assert(p.C==1&&p.D==0&&p.tau_s==.001&&p.sourceWireNamesPreserved&&q.unitsMetadataParity,'Gate:SourceProof','Wrong approved static primitive.');
  for kind=1:4
   j=j+1;id=['b' num2str(j)];source=[m '/' id '_raw'];hold=[m '/' id '_hold'];act=[m '/' id '_actuator'];
   v=.25*ones(size(t));x0=.25;
   switch kind
    case 1,x0=p.initialStateFromActualArchivedOutput;pattern='STARTUP_ACTUAL_ARCHIVED_Y0';
    case 2,v(t>=.02)=.5;v(t>=.04)=.75;v(t>=.08)=.25;pattern='TWO_STEP_AND_RETURN';
    case 3,v(t>=.02&t<.03)=.5;pattern='CAPTURED_TEN_MS_PULSE';
    case 4,v(t>=.021&t<.023)=.5;pattern='MISSED_TWO_MS_PULSE';
   end
   % All input switches are on explicit250us source ticks. FromWorkspace is ZOH.
   z=struct('time',t,'signals',struct('values',v,'dimensions',1));var=['toyInput' num2str(j)];assignin(mw,var,z);
   add_block('simulink/Sources/From Workspace',source,'VariableName',var,'Interpolate','off','SampleTime','0');
   add_block('simulink/Discrete/Zero-Order Hold',hold,'SampleTime',mat2str(Ts,17));
   add_block('simulink/Discrete/Discrete State-Space',act,'A',mat2str(p.A,17),'B',mat2str(p.B,17),'C','1','D','0',...
    'InitialCondition',mat2str(x0,17),'SampleTime',mat2str(Ts,17),'StateName','amendedActuatorOutputState');
   add_line(m,[id '_raw/1'],[id '_hold/1']);add_line(m,[id '_hold/1'],[id '_actuator/1']);
   for s=1:3
    nn={'raw','hold','actuator'};tap=[m '/' id '_log' num2str(s)];vn=[id '_' nn{s}];
    add_block('simulink/Sinks/To Workspace',tap,'VariableName',vn,'SaveFormat','Timeseries','SampleTime',mat2str(dt,17));
    add_line(m,[id '_' nn{s} '/1'],[id '_log' num2str(s) '/1']);
   end
   zspec=struct('id',id,'path',act,'pattern',pattern,'Ts_s',Ts,'tau_s',.001,'A',p.A,'B',p.B,'C',1,'D',0,'x0',x0,...
    'coefficientsCopiedFromActualStaticProof',true,'inputTimes',t,'inputValues',v);
   if j==1,specs=zspec;else,specs(end+1)=zspec;end %#ok<AGROW>
  end
 end
 sampled_gate_events('init',specs);set_param(m,'StartFcn','sampled_gate_events(''start'')');
 save_system(m,[pre '_MODEL.slx']);[~,saved]=fileparts([pre '_MODEL.slx']);if bdIsLoaded(saved),m=saved;end
 % Save-as changed root. Refresh listener paths ONLY, never coefficients/wiring.
 for j=1:numel(specs),specs(j).path=[m '/' specs(j).id '_actuator'];end
 sampled_gate_events('init',specs);
 simCount=simCount+1;out=sim(m); % ONLY simulation call in entire authorized package.
 tr=sampled_gate_events('get');flags.MATLAB_TOY_COMPLETE=true;
 data=cell(1,numel(specs));allState=true;phase=true;clockTol=32*eps(max(1,stop));
 for j=1:numel(specs)
  s=specs(j);raw=out.get([s.id '_raw']);held=out.get([s.id '_hold']);y=out.get([s.id '_actuator']);
  assert(isequal(raw.Time,held.Time)&&isequal(raw.Time,y.Time)&&raw.Time(1)==0&&abs(raw.Time(end)-stop)<=clockTol,'Gate:ToyClock','Dense observation clocks differ.');
  dense=[raw.Time(:),raw.Data(:),held.Data(:),y.Data(:)];writematrix(dense,[pre '_' s.id '_DENSE.csv']);
  e=tr(cellfun(@(z)z.branch==j,tr));N=round(stop/s.Ts_s);ticks=nan(N,6);available=true;
  for k=0:N-1
   tk=k*s.Ts_s;at=e(cellfun(@(z)abs(z.time_s-tk)<=clockTol,e));
   po=at(cellfun(@(z)strcmp(z.phase,'PostOutputs'),at));
   pu=at(cellfun(@(z)strcmp(z.phase,'PreUpdate'),at));qu=at(cellfun(@(z)strcmp(z.phase,'PostUpdate'),at));
   if numel(po)~=1||numel(pu)~=1||numel(qu)~=1,available=false;continue;end
   po=po{1};pu=pu{1};qu=qu{1};
   if ~po.actualStateReadable||~pu.actualStateReadable||~qu.actualStateReadable,available=false;continue;end
   assert(po.sequence<pu.sequence&&pu.sequence<qu.sequence,'Gate:ToyPhase','Callback method order differs.');
   assert(po.output==po.actualDState&&pu.actualDState==po.actualDState&&qu.output==pu.output&&pu.heldInput==qu.heldInput,...
    'Gate:ToyPhase','D0 output staging or held input is inconsistent.');
   ticks(k+1,:)=[k,tk,pu.heldInput,pu.actualDState,qu.actualDState,po.output];
  end
  allState=allState&&available;phase=phase&&available;
  writematrix(ticks,[pre '_' s.id '_TICKS.csv']);
  data{j}=struct('spec',s,'actualPhaseReadable',available,'tickRows',N,'denseRows',size(dense,1),'stateEvidence','Only runtime DWork explicitly marked discrete-state; no recurrence-derived state substituted.');
 end
 flags.ACTUAL_PRE_POST_STATE_AVAILABLE=allState;flags.MATLAB_PHASE_CHECKS=phase;r.branches=data;
 if ~allState,r.qualification='UNQUALIFIED_ACTUAL_STATE_OR_CLOCK_UNAVAILABLE';else,r.qualification='MATLAB_PHASE_COMPLETE_PENDING_INDEPENDENT_DECIMAL';end
catch ME
 r.failure=struct('identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});
 try,tr=sampled_gate_events('get');catch,end
end
r.flags=flags;r.simCount=simCount;r.rawEvents=tr;r.simulationOutput=out;r.specs=specs;
save([pre '_RAW.mat'],'r','-v7.3');
simple=rmfield(r,intersect(fieldnames(r),{'simulationOutput','rawEvents'}));writeJSON([pre '_SUMMARY.json'],simple);
writeJSON([pre '_EVENTS.json'],tr);writeJSON([pre '_FLAGS.json'],flags);
sampled_gate_events('clear');try,close_system(m,0);catch,end
fprintf('SAMPLED_TOY_EXECUTION simulationCalls=%d complete=%d actualPrePostState=%d phaseQualified=%d batteryRun=0 G5_ACCEPTED=false\n',...
 simCount,flags.MATLAB_TOY_COMPLETE,flags.ACTUAL_PRE_POST_STATE_AVAILABLE,flags.MATLAB_PHASE_CHECKS);
end
function writeJSON(p,v)
f=fopen(p,'w');assert(f~=-1,'Gate:Write','Private file write failed.');fprintf(f,'%s',jsonencode(v));fclose(f);
end
