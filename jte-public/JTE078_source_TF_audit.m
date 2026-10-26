function JTE078_source_TF_audit()
% JTE078 only SOURCE/DERIVATIVE structural test; no 2400 s run and no private MAT.
assert(strcmp(version('-release'),'2024b'),'JTE078:WrongRelease');
root=pwd;
vendor=fullfile(root,'vendor-pack');
source=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(source),pin),'JTE078:WrongSource');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
projectCleanup=onCleanup(@()safeProject(project)); %#ok<NASGU>
folder=fullfile(root,'jte078-generated-source-audit');
files=JTE056build(vendor,folder);
paths={files.baseline,files.study};
for k=1:numel(paths)
    [~,name]=fileparts(paths{k});
    load_system(paths{k});
    guard=onCleanup(@()safeModel(name)); %#ok<NASGU>
    ctrl=[name '/Battery Control'];
    f=[ctrl '/FlwR_calc'];
    tf=[ctrl '/sensor dynamics 1'];
    logger=[ctrl '/JTE Downstream Flow'];
    assert(strcmp(get_param(tf,'SID'),'197'),'JTE078:TFSourceSID');
    assert(strcmp(get_param(tf,'BlockType'),'TransferFcn'),'JTE078:WrongBlockType');
    assert(strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE078:UnexpectedTau');
    inputs=get_param(tf,'PortHandles');
    ctrlPorts=get_param(f,'PortHandles');
    loggerPorts=get_param(logger,'PortHandles');
    inputLine=get_param(inputs.Inport(1),'Line');
    outputLine=get_param(inputs.Outport(1),'Line');
    loggingLine=get_param(loggerPorts.Inport(1),'Line');
    assert(inputLine~=-1 && outputLine~=-1 && loggingLine~=-1,'JTE078:MissingSignalLine');
    assert(get_param(inputLine,'SrcPortHandle')==ctrlPorts.Outport(1), ...
        'JTE078:FilterInputNotSameAsLoggedCore');
    assert(get_param(loggingLine,'SrcPortHandle')==inputs.Outport(1), ...
        'JTE078:PostFilterLoggerNotConnectedToTF');
    destinations=get_param(outputLine,'DstPortHandle');
    assert(any(destinations==loggerPorts.Inport(1)),'JTE078:MissingLoggerDestination');
    numerator=get_param(tf,'Numerator');
    initialStates=get_param(tf,'InitialStates');
    assert(ischar(numerator) && ~isempty(numerator),'JTE078:EmptyNumerator');
    fprintf('JTE078_SOURCE_TF_PATH_PASS model=%s tfSID=197 inputSameAsCore=true postfilterLogger=true numerator=%s denominator=[1e-3 1] initialStates=%s sourceSHA=%s\n', ...
        name,numerator,initialStates,files.sourceSHA256);
    clear guard
    safeModel(name);
end
assert(strcmp(JTE2026sha256(source),pin),'JTE078:SourceModified');
fprintf('JTE078_SOURCE_ONLY_REVIEW_REQUIRED modelPhysicsOriginal=true G5_ACCEPTED=false\n');
end
function safeProject(p)
try,close(p);catch,end
end
function safeModel(n)
try
if bdIsLoaded(n),set_param(n,'CloseFcn','');close_system(n,0);end
catch,end
end
