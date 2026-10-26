function JTE088_profiler_contract()
% SOURCE-LOCKED 340s official MathWorks model solver event profiler.
% Uses MATLAB R2024b solverprofiler.profileModel, saves only in runner scratch.
% Do not print temperatures, event-time values, MAT arrays, or file IDs.
assert(strcmp(version('-release'),'2024b'),'JTE088:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE088:Pin');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
guard=onCleanup(@()quietProject(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte088-profiler-generated'));
[~,name]=fileparts(files.baseline);
load_system(files.baseline);mg=onCleanup(@()quietModel(name)); %#ok<NASGU>
assert(strcmp(get_param(name,'Solver'),'ode23t'),'JTE088:SolverChanged');
if ~isfolder(fullfile(root,'jte088-profiler-private')),mkdir(fullfile(root,'jte088-profiler-private'));end
dest=fullfile(root,'jte088-profiler-private','solver-profiler-private.mat');
fprintf('JTE088_PROFILER_START sourcePinned=true MATLAB=R2024b profileWindow=340s outputPrivate=true\\n');
stats=solverprofiler.profileModel(name,'StartTime',0,'StopTime',340,...
  'BufferSize',50000,'SaveStates','off','SaveSimscapeStates','off',...
  'SaveZCSignals','on','DataFullFile',dest,'OpenSP','off');
assert(isfield(stats,'summary')&&isfield(stats,'file'),'JTE088:MissingProfilerResult');
assert(isfile(stats.file),'JTE088:MissingPrivateEventMAT');
summ=stats.summary;
assert(summ.tStart==0 && summ.tStop==340,'JTE088:WrongHorizon');
fprintf('JTE088_REAL_SOURCE_SOLVER_PROFILER_PASS hadZeroCrossing=%d hadSolverReset=%d hadSolverException=%d actualSolverOde23t=%d proprietaryOutputNeverPublished=true\\n',...
 summ.zcNumber>0,summ.resetNumber>0,summ.exceptionNumber>0,strcmp(summ.solver,'ode23t'));
info=whos('-file',stats.file);
fprintf('JTE088_EVENT_MAT_PRIVATE_STATE_RECORDED schemaVariableCount=%d\\n',numel(info));
raw=load(stats.file);
rootNames=fieldnames(raw);
fprintf('JTE088_PROFILE_SCHEMA_FIELDS=%s\\n',strjoin(rootNames,','));
for kk=1:numel(rootNames)
  elem=raw.(rootNames{kk});
  fprintf('JTE088_PROFILE_SESSION_CLASS=%s ISSTRUCT=%d ISOBJECT=%d ISCELL=%d\\n',...
    class(elem),isstruct(elem),isobject(elem),iscell(elem));
  if isobject(elem)
    try
      pname=properties(elem);
      fprintf('JTE088_PROFILE_SESSION_PUBLIC_PROPERTIES=%s\\n',strjoin(pname,','));
    catch
      fprintf('JTE088_PROFILE_SESSION_PROPERTIES_NOT_PUBLIC\\n');
    end
  elseif iscell(elem)
    fprintf('JTE088_PROFILE_SESSION_CELL_COUNT=%d\\n',numel(elem));
    if ~isempty(elem),fprintf('JTE088_PROFILE_FIRST_CELL_CLASS=%s\\n',class(elem{1}));end
  end
end
% The R2024b session is a serialized internal object. It is NOT a
% supported struct of zcEvents/resetTime. No causal time alignment can be
% established from the high-level counts alone. Explicit fail-closed flag.
hasPublicEventTimestamps=false;
for k=1:numel(rootNames)
    obj=raw.(rootNames{k});
    if isstruct(obj) && isfield(obj,'zcEvents') && isfield(obj,'resetTime')
        hasPublicEventTimestamps=true;
    end
end
fprintf('JTE088_PROFILE_PUBLIC_EVENT_TIME_STATUS accessible=%d causalAttributionEstablished=0 supportedR2024bGUIRequired=%d\\n', ...
 hasPublicEventTimestamps,~hasPublicEventTimestamps);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE088:VendorChanged');
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(model)
try
if bdIsLoaded(model),set_param(model,'CloseFcn','');close_system(model,0);end
catch,end
end
