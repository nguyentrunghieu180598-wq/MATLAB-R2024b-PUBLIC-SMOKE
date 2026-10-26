function JTE085_solver_event_audit()
% SOURCE-LOCKED 340s official MathWorks model solver event profiler.
% Uses MATLAB R2024b solverprofiler.profileModel, saves only in runner scratch.
% Do not print temperatures, event-time values, MAT arrays, or file IDs.
assert(strcmp(version('-release'),'2024b'),'JTE085:WrongRelease');
root=pwd; vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE085:Pin');
project=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
guard=onCleanup(@()quietProject(project)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte085-generated'));
[~,name]=fileparts(files.baseline);
load_system(files.baseline);mg=onCleanup(@()quietModel(name)); %#ok<NASGU>
assert(strcmp(get_param(name,'Solver'),'ode23t'),'JTE085:SolverChanged');
if ~isfolder(fullfile(root,'jte085-private')),mkdir(fullfile(root,'jte085-private'));end
dest=fullfile(root,'jte085-private','solver-profiler-private.mat');
fprintf('JTE085_PROFILER_START sourcePinned=true MATLAB=R2024b profileWindow=340s outputPrivate=true\\n');
stats=solverprofiler.profileModel(name,'StartTime',0,'StopTime',340,...
  'BufferSize',50000,'SaveStates','off','SaveSimscapeStates','off',...
  'SaveZCSignals','on','DataFullFile',dest,'OpenSP','off');
assert(isfield(stats,'summary')&&isfield(stats,'file'),'JTE085:MissingProfilerResult');
assert(isfile(stats.file),'JTE085:MissingPrivateEventMAT');
summ=stats.summary;
assert(summ.tStart==0 && summ.tStop==340,'JTE085:WrongHorizon');
fprintf('JTE085_REAL_SOURCE_SOLVER_PROFILER_PASS hadZeroCrossing=%d hadSolverReset=%d hadSolverException=%d actualSolverOde23t=%d proprietaryOutputNeverPublished=true\\n',...
 summ.zcNumber>0,summ.resetNumber>0,summ.exceptionNumber>0,strcmp(summ.solver,'ode23t'));
info=whos('-file',stats.file);
fprintf('JTE085_EVENT_MAT_PRIVATE_STATE_RECORDED schemaVariableCount=%d\\n',numel(info));
raw=load(stats.file);
rootNames=fieldnames(raw);
fprintf('JTE085_PROFILE_SCHEMA_FIELDS=%s\\n',strjoin(rootNames,','));
target=334.87941079024;
foundZC=false;foundReset=false;atZC=false;atReset=false;
for k=1:numel(rootNames)
  obj=raw.(rootNames{k});
  if isstruct(obj)
    member=fieldnames(obj);
    fprintf('JTE085_PROFILE_SCHEMA_ROOT_MEMBER=%s\\n',strjoin(member,','));
    if isfield(obj,'profilerData') && isstruct(obj.profilerData),obj=obj.profilerData;end
    if isfield(obj,'zcEvents')
      z=obj.zcEvents;
      if isstruct(z) && isfield(z,'t')
        times=double([z.t]); foundZC=true;
        atZC=any(abs(times-target)<.05);
      end
    end
    if isfield(obj,'resetTime')
      t=obj.resetTime;
      if isnumeric(t)
        foundReset=true;atReset=any(abs(double(t(:))-target)<.05);
      end
    end
  end
end
fprintf('JTE085_PROFILE_EVENT_BRACKET_CHECK zcTimesAvailable=%d resetTimesAvailable=%d zeroCrossNearNativeTFEvent=%d solverResetNearNativeTFEvent=%d\\n',...
 foundZC,foundReset,atZC,atReset);
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE085:VendorChanged');
end
function quietProject(p)
try,close(p);catch,end
end
function quietModel(model)
try
if bdIsLoaded(model),set_param(model,'CloseFcn','');close_system(model,0);end
catch,end
end
