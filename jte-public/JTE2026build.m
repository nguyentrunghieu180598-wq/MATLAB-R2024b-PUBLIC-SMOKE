function files = JTE2026build(repoRoot,outputDir)
% Build B0L (instrumented baseline) and C0/C1 (local single-channel bias).
% Compiles NOTHING; never overwrites upstream or existing generated files.
% Must be launched after official MathWorks project dependencies are ready.
info=JTE2026preflight(repoRoot);
if nargin<2 || isempty(outputDir)
    outputDir=fullfile(fileparts(repoRoot),'JTE2026Generated');
end
outputDir=char(outputDir);
if ~isfolder(outputDir), mkdir(outputDir); end
bname='JTE2026B0L'; cname='JTE2026LocalBias';
bfile=fullfile(outputDir,[bname '.slx']); cfile=fullfile(outputDir,[cname '.slx']);
assert(~isfile(bfile)&&~isfile(cfile),'Generated models exist. Choose a NEW outputDir; no overwrite.');
assert(~bdIsLoaded(bname)&&~bdIsLoaded(cname),'Close prior generated model windows first.');
files=struct('baseline',bfile,'study',cfile,'sourceSHA256',info.originalSHA256);
completed=false;
finish=onCleanup(@cleanup);
copyfile(info.source,bfile); copyfile(info.source,cfile);
try
    buildOne(bname,bfile,false);
    buildOne(cname,cfile,true);
    assert(strcmpi(JTE2026sha256(info.source),info.originalSHA256), ...
      'Original model changed; STOP.');
    completed=true;
    fprintf('GENERATED, NOT COMPILED: %s\n%s\n',bfile,cfile);
catch ME
    rethrow(ME);
end
    function cleanup()
       if bdIsLoaded(bname),close_system(bname,0);end
       if bdIsLoaded(cname),close_system(cname,0);end
       if ~completed
           if isfile(bfile),delete(bfile);end
           if isfile(cfile),delete(cfile);end
       end
    end
end

function buildOne(model,path,addBias)
load_system(path);
ctrl=[model '/Battery Control'];
reducer=[ctrl '/min-max T']; flw=[ctrl '/FlwR_calc'];
assert(getSimulinkBlockHandle(reducer)>0 && getSimulinkBlockHandle(flw)>0, ...
    'Pinned block paths changed; cannot proceed.');
assert(strcmpi(get_param([reducer '/MinMax3'],'Function'),'max'), ...
    'Expected Max T at reducer Outport 2.');
r=get_param(reducer,'PortHandles'); f=get_param(flw,'PortHandles');
assert(numel(r.Inport)==1 && numel(r.Outport)==2 && numel(f.Inport)==2, ...
    'Unexpected source port count.');
trueL=get_param(r.Inport(1),'Line');
assert(trueL~=-1,'Missing true vector line.');
trueSrc=get_param(trueL,'SrcPortHandle');
f1L=get_param(f.Inport(1),'Line'); f2L=get_param(f.Inport(2),'Line');
assert(f1L~=-1 && f2L~=-1,'Missing controller input.');
assert(get_param(f1L,'SrcPortHandle')==r.Outport(2), ...
    'Source controller In1 is not upstream Max T!');
ambientSource=get_param(f2L,'SrcPortHandle');
assert(ambientSource~=-1,'Source controller In2 Ambient disconnected.');
% Diagnostic logging is branched: no physical signal is altered.
logger(ctrl,trueSrc,'JTE Vector True','jteTtrue',[760 500 855 520]);
logger(ctrl,r.Outport(2),'JTE Tmax True','jteTmaxTrue',[760 540 855 560]);
logger(ctrl,r.Outport(1),'JTE Tmin True','jteTminTrue',[760 580 855 600]);
logger(ctrl,f.Outport(1),'JTE Command','jteUcore',[760 620 855 640]);
logger(ctrl,ambientSource,'JTE Ambient','jteAmbient',[760 660 855 680]);
if addBias
    bias=[ctrl '/JTE local bias']; meas=[ctrl '/JTE measured min-max T'];
    add_block(reducer,meas,'Position',[560 710 680 770]);
    add_block('simulink/User-Defined Functions/MATLAB Function',bias, ...
      'Position',[350 700 485 780]);
    sf=sfroot;
    chart=sf.find('-isa','Stateflow.EMChart','Path',bias);
    assert(numel(chart)==1,'Cannot locate MATLAB Function chart (Stateflow).');
    chart.Script = sprintf([ ...
      'function Tm=localBias(T,j,b)\n' ...
      '%%#codegen\n' ...
      'Tm=T;\n' ...
      'Tm(j)=T(j)+b;\n' ...
      'end\n']);
    mw=get_param(model,'ModelWorkspace');
    assignin(mw,'jteChannelIndex',1);assignin(mw,'jteBiasK',0);
    add_block('simulink/Sources/Constant',[ctrl '/JTE channel'], ...
      'Value','jteChannelIndex','Position',[180 715 290 735]);
    add_block('simulink/Sources/Constant',[ctrl '/JTE bias K'], ...
      'Value','jteBiasK','Position',[180 755 290 775]);
    % Stateflow should refresh inports on Script assignment; no partial compile.
    p=get_param(bias,'PortHandles'); m=get_param(meas,'PortHandles');
    assert(numel(p.Inport)==3 && numel(p.Outport)==1, ...
      'Bias function ports not available. Investigate chart generation.');
    add_line(ctrl,trueSrc,p.Inport(1),'autorouting','on');
    add_line(ctrl,'JTE channel/1','JTE local bias/2','autorouting','on');
    add_line(ctrl,'JTE bias K/1','JTE local bias/3','autorouting','on');
    add_line(ctrl,p.Outport(1),m.Inport(1),'autorouting','on');
    delete_line(ctrl,r.Outport(2),f.Inport(1));
    add_line(ctrl,m.Outport(2),f.Inport(1),'autorouting','on');
    logger(ctrl,p.Outport(1),'JTE Vector Measured','jteTmeas',[940 700 1060 720]);
    logger(ctrl,m.Outport(2),'JTE Tmax Measured','jteTmaxMeas',[940 740 1060 760]);
    logger(ctrl,m.Outport(1),'JTE Tmin Measured','jteTminMeas',[940 780 1060 800]);
    assert(get_param(get_param(f.Inport(1),'Line'),'SrcPortHandle')==m.Outport(2), ...
        'Study controller In1 does not receive measured Tmax.');
end
assert(get_param(get_param(f.Inport(2),'Line'),'SrcPortHandle')==ambientSource, ...
    'Controller Ambient In2 changed unexpectedly!');
assert(get_param(get_param(r.Inport(1),'Line'),'SrcPortHandle')==trueSrc, ...
    'True vector branch changed!');
set_param(model,'Description','JTE 2026 candidate; math/reference fixed; runtime pending.');
save_system(model,path);
close_system(model,0);
end

function logger(subsystem,sourcePort,label,varName,position)
blk=[subsystem '/' label];
assert(getSimulinkBlockHandle(blk)==-1,'Logger name conflict: %s',blk);
add_block('simulink/Sinks/To Workspace',blk, ...
  'VariableName',varName,'SaveFormat','Timeseries','Position',position);
h=get_param(blk,'PortHandles');
add_line(subsystem,sourcePort,h.Inport(1),'autorouting','on');
end
