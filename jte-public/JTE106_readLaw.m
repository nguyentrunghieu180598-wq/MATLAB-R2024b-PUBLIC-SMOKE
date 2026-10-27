function law=JTE106_readLaw(root,prefix)
% Read only archived source control blocks; never compile, simulate or save.
file=fullfile(root,'JTE101Original.slx');before=JTE2026sha256(file);
A=jsondecode(fileread(fullfile(root,'accepted_audit.json')));
assert(strcmp(before,A.cases.ORIGINAL340.metadata.modelSHA),'JTE106:ModelSHA','Wrong source-control archive.');
law=struct('verified',false,'sourceModelSHA',before,'gain',.1,'lower',.001,'upper',.95,'step',.25,...
 'scope','MATLAB native arithmetic; source actual recorded core remains the authority at sampled thresholds. No new Simulink oracle simulation.',...
 'priorNearULPSourceCanaryRun','40464385622','newSimulinkThresholdTest',false);
try
 load_system(file);g=onCleanup(@()quiet('JTE101Original')); %#ok<NASGU>
 m='JTE101Original';core=[m '/Battery Control/FlwR_calc'];calc=[core '/FlwR calc'];step=[core '/Step Change'];
 law.static=JTE096_modelAudit(core);
 sat=[calc '/Saturation'];sh=get_param(sat,'PortHandles');
 gain=get_param(src(sh.Inport(1)),'Parent');
 assert(strcmp(get_param(gain,'BlockType'),'Gain'),'JTE106:GainPath','Unrecognized source gain path.');
 law.gain=slResolve(get_param(gain,'Gain'),gain);
 law.lower=slResolve(get_param(sat,'LowerLimit'),sat);law.upper=slResolve(get_param(sat,'UpperLimit'),sat);
 gh=get_param(gain,'PortHandles');sumBlock=get_param(src(gh.Inport(1)),'Parent');
 law.preGainSource=sumBlock;law.preGainType=get_param(sumBlock,'BlockType');
 if strcmp(law.preGainType,'Sum'),law.preGainSigns=get_param(sumBlock,'Inputs');else,law.preGainSigns='UNRECOGNIZED';end
 modBlock=[step '/Mod'];mh=get_param(modBlock,'PortHandles');assert(strcmp(get_param(modBlock,'Operator'),'mod'),'JTE106:Mod','Not source mod.');
 q=src(mh.Inport(1));s=src(mh.Inport(2));sp=get_param(step,'PortHandles');
 qPort=str2double(get_param(get_param(q,'Parent'),'Port'));sPort=str2double(get_param(get_param(s,'Parent'),'Port'));
 qp=get_param(calc,'PortHandles');assert(src(sp.Inport(qPort))==qp.Outport(1),'JTE106:QuantizerInput','Quantizer no longer fed by source saturation subsystem.');
 sb=get_param(src(sp.Inport(sPort)),'Parent');assert(strcmp(get_param(sb,'BlockType'),'Constant'),'JTE106:StepSource','Step not constant.');
 law.step=slResolve(get_param(sb,'Value'),sb);
 op=find_system(step,'SearchDepth',1,'BlockType','Outport');assert(numel(op)==1,'JTE106:Output','Source interface.');
 oh=get_param(op{1},'PortHandles');maxBlock=get_param(src(oh.Inport(1)),'Parent');
 assert(strcmp(get_param(maxBlock,'BlockType'),'MinMax')&&strcmp(get_param(maxBlock,'Function'),'max'),'JTE106:Floor','Source floor not max.');
 xh=get_param(maxBlock,'PortHandles');assert(src(xh.Inport(2))==s,'JTE106:FloorWire','Floor step changed.');
 sub=get_param(src(xh.Inport(1)),'Parent');bh=get_param(sub,'PortHandles');
 assert(strcmp(get_param(sub,'BlockType'),'Sum')&&strcmp(erase(get_param(sub,'Inputs'),'|'),'+-')&&src(bh.Inport(1))==q&&src(bh.Inport(2))==mh.Outport(1),'JTE106:Subtract','Quantizer arithmetic changed.');
 law.paths=struct('gain',gain,'saturation',sat,'mod',modBlock,'stepConstant',sb,'floor',maxBlock,'subtraction',sub);
 law.verified=law.gain==.1&&law.lower==.001&&law.upper==.95&&law.step==.25&&strcmp(erase(law.preGainSigns,'|'),'+-');
catch err
 law.failure=struct('identifier',err.identifier,'message',err.message);
end
assert(strcmp(JTE2026sha256(file),before),'JTE106:SourceMutation','Read-only source bytes changed.');
save([prefix '_SOURCE_LAW.mat'],'law','-v7.3');
h=fopen([prefix '_SOURCE_LAW.json'],'w');fprintf(h,'%s',jsonencode(law));fclose(h);
end
function p=src(dst)
line=get_param(dst,'Line');assert(line~=-1,'JTE106:Line','Missing source line.');p=get_param(line,'SrcPortHandle');
end
function quiet(m)
try,if bdIsLoaded(m),set_param(m,'CloseFcn','');close_system(m,0);end;catch,end
end
