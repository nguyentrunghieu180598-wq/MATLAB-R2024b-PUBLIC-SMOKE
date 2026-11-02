function p=WK08_prepare(sourceSLX,targetSLX,privateDir,sourceSHA,horizon)
% Prepare a fresh B0L clone; called only in a separately approved MATLAB process.
assert(any(horizon==[5 340]),'WK08:Horizon','Only local5 or R1 allowed.');
p=BTMS_M2_prepare340NoRun(sourceSLX,targetSLX,privateDir,sourceSHA);
[~,m]=fileparts(targetSLX);load_system(targetSLX);
c=onCleanup(@()close_system(m,0)); %#ok<NASGU>
bc=[m '/Battery Control'];
p.injection=WK08_inject(m,0,1,1:312);
assert(p.injection.defaultStructuralParity,'WK08:Parity','B0L injection must be bypassed.');
% Existing M2 taps retain command, held command, actuator output and true T.
% Periodic sampling at 1 s is time decimation, independent of variable solver steps.
oldT=[m '/BTMS_M2_Ttrue312'];
if getSimulinkBlockHandle(oldT)<0
 sinks=find_system(m,'LookUnderMasks','all','FollowLinks','off','BlockType','ToFile');
 oldT=sinks{find(cellfun(@(s)strcmp(get_param(s,'Name'),'BTMS_M2_Ttrue312'),sinks),1)};
end
set_param(oldT,'SampleTime','1','Decimation','1');
roles={'uCore','uSampled','actuatorY','Ttrue312'};
for k=1:4
 sink=p.fourLoggerPaths{k};file=fullfile(privateDir,['WK08_R1_' roles{k} '.mat']);
 assert(~isfile(file),'WK08:Overwrite','Never overwrite a run.');
 set_param(sink,'FileName',file,'MatrixName',['wk08_' roles{k}]);
end
truePort=p.injection.truePort;
p.maxTrue=reduce(bc,'WK08 true max',truePort);
p.maxMeasured=reduce(bc,'WK08 measured max',p.injection.measuredPort);
pump=get_param([bc '/Pump power calc'],'PortHandles');
ports=[p.maxTrue p.maxMeasured pump.Outport(1)];extra={'TmaxTrue','TmaxMeasured','pumpPower'};
for k=1:3
 s=[bc '/WK08 ' extra{k}];file=fullfile(privateDir,['WK08_R1_' extra{k} '.mat']);
 assert(~isfile(file),'WK08:Overwrite','Never overwrite a run.');
 add_block('simulink/Sinks/To File',s,'FileName',file, ...
  'MatrixName',['wk08_' extra{k}],'SaveFormat','Timeseries','SampleTime','-1','Decimation','1');
 h=get_param(s,'PortHandles');add_line(bc,ports(k),h.Inport(1),'autorouting','on');
end
set_param(m,'StopTime',num2str(horizon));
p.roles=[roles extra];
p.privateTargets=cellfun(@(r)fullfile(privateDir,['WK08_R1_' r '.mat']),p.roles,'UniformOutput',false);p.sourceSHA256=sourceSHA;p.horizon=horizon;
p.fingerprint=WK08_structFingerprint(m);save_system(m,targetSLX);
close_system(m,0);load_system(targetSLX);
assert(isequaln(p.fingerprint,WK08_structFingerprint(m)), ...
 'WK08:SavedStructure','Saved derivative fingerprint differs.');
p.derivativeSHA256=JTE2026sha256(targetSLX);
end
function out=reduce(bc,name,src)
s=[bc '/' name];add_block('simulink/Math Operations/MinMax',s,'Function','max','Inputs','1');
h=get_param(s,'PortHandles');add_line(bc,src,h.Inport(1),'autorouting','on');out=h.Outport(1);
end
