function report=JTE2026inspectGraph(modelFile,isStudy)
% Structural check of one compiled/updatable clone. No data substitution.
assert(isfile(modelFile),'Missing candidate SLX');
[~,model]=fileparts(modelFile);
assert(~bdIsLoaded(model),'Close model before graph inspection.');
load_system(modelFile);clean=onCleanup(@()close_system(model,0));
ctrl=[model '/Battery Control'];
r=get_param([ctrl '/min-max T'],'PortHandles');
c=get_param([ctrl '/FlwR_calc'],'PortHandles');
a=get_param(c.Inport(2),'Line');
assert(a~=-1,'Ambient Inport 2 must remain connected.');
aSrc=get_param(a,'SrcPortHandle');
if isStudy
    mr=get_param([ctrl '/JTE measured min-max T'],'PortHandles');
    expectedSrc=mr.Outport(2);
    b=get_param([ctrl '/JTE local bias'],'PortHandles');
    biasOutputLine=get_param(b.Outport(1),'Line');
    assert(biasOutputLine~=-1,'Bias output disconnected.');
    outLine=get_param(mr.Inport(1),'Line');
    assert(outLine~=-1 && get_param(outLine,'SrcPortHandle')==b.Outport(1), ...
      'Measured extrema not fed from local bias.');
else
    expectedSrc=r.Outport(2);
end
l=get_param(c.Inport(1),'Line');
assert(l~=-1 && get_param(l,'SrcPortHandle')==expectedSrc, ...
    'Controller MaxT feedback graph mismatch.');
report=struct('PASS_GRAPH',true,'model',model,'ambientSrcPortHandle',aSrc, ...
    'controllerInput1Source',expectedSrc,'study',logical(isStudy));
fprintf('GRAPH PASS for %s; actual compile still separately required.\n',model);
end
