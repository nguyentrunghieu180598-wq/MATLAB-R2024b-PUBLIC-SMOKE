function JTE088_tf_event_contract()
% JTE088: FIRST-EVENT SOURCE-LOCKED DIAGNOSTIC. No raw MAT in CI.
% Read real R2024b continuous TF state via xout and compare to native
% input/output, without editing vendor or generated physical connections.
assert(strcmp(version('-release'),'2024b'),'JTE088:Release');
root=pwd;vendor=fullfile(root,'vendor-pack');
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE088:BadVendor');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
cg=onCleanup(@()closeProjectQuiet(p)); %#ok<NASGU>
files=JTE056build(vendor,fullfile(root,'jte088-generated'));
[~,mdl]=fileparts(files.baseline);
load_system(files.baseline); cm=onCleanup(@()closeModelQuiet(mdl)); %#ok<NASGU>
tf=[mdl '/Battery Control/sensor dynamics 1'];
assert(strcmp(get_param(tf,'SID'),'197'),'JTE088:WrongTF');
assert(strcmp(get_param(tf,'Numerator'),'[1]') && strcmp(get_param(tf,'Denominator'),'[1e-3 1]'),'JTE088:WrongTFParams');
input=Simulink.SimulationInput(mdl);
input=input.setModelParameter('StartTime','0','StopTime','340', ...
 'SaveState','on','StateSaveName','jteXStates','SaveFormat','Dataset',...
 'SaveTime','on','TimeSaveName','tout');
fprintf('JTE088_MATLAB_NATIVE_STATE_PROBE_START model=%s sourcePinned=true dataPrivate=true\\n',mdl);
out=sim(input);
[t,u]=JTE2026timeseries(out,'jteUcore');
[tfTime,y]=JTE2026timeseries(out,'jteFlwR');
assert(numel(t)==numel(tfTime) && isequal(t,tfTime),'JTE088:InputOutputClockMismatch');
assert(all(u==0.25) && numel(t)>1000,'JTE088:InputNotConstant');
y=y(:);
inside=find(tfTime>=330 & tfTime<=338);
assert(~isempty(inside),'JTE088:NoEventWindow');
ix=find(abs(y-0.25)>0.005 & tfTime>300 & tfTime<340,1,'first');
assert(~isempty(ix) && ix>2,'JTE088:NoOriginalEvent');
dt=tfTime(ix)-tfTime(ix-1);
% For stable tau=.001 s and u=0.25, expected y at event is 0.25
% when previous y=0.25, independent of any step size. A difference
% shows a state or logged output discontinuity or a hidden input not
% captured by user-defined controller logger.
expected=0.25+(y(ix-1)-0.25)*exp(-dt/0.001);
assert(abs(y(ix-1)-0.25)<1e-10,'JTE088:NotAtEquilibriumBeforeEvent');
deviatesFromAnalytic=abs(y(ix)-expected)>0.005;
assert(deviatesFromAnalytic,'JTE088:NoAnalyticalBreak');
states=out.get('jteXStates');
assert(isa(states,'Simulink.SimulationData.Dataset'),'JTE088:StateDatasetMissing');
stateCount=states.numElements;
found=0;stateJump=NaN;stateNearMatch=NaN;stateInputOutputConsistency=NaN;stateNativeDuplicate=NaN;
for k=1:stateCount
   el=states.getElement(k);
   try
     name=char(el.BlockPath.getBlock(1));
   catch
     try,name=char(el.BlockPath);catch,name='';end
   end
   if contains(name,'sensor dynamics 1')
      found=found+1;
      sTime=double(el.Values.Time(:));
      sValue=double(squeeze(el.Values.Data));
      if isvector(sValue)
         sValue=sValue(:);
         assert(numel(sTime)==numel(sValue),'JTE088:StateTimeShape');
         [timeGap,ixState]=min(abs(sTime-tfTime(ix)));
         stateNearMatch=timeGap<=1e-6;
         if ixState>1
            % Dimensionless change in recorded continuous state,
            % without assuming the TransferFcn canonical state scale.
            stateJump=abs(sValue(ixState)-sValue(ixState-1))>1e-8;
            stateNativeDuplicate=abs(sTime(ixState)-sTime(ixState-1))<1e-8;
            % For numerator=[1], denominator=[tau 1], continuous state
            % is expected to be physically proportional to TF output.
            % Check local state change is present independently of logger.
            stateInputOutputConsistency=isequal(numel(sTime),numel(tfTime)) && all(abs(sTime-tfTime)<1e-7);
         end
      end
   end
end
fprintf('JTE088_NATIVE_STATE_AUDIT_RESULT TFstateLocated=%d stateSignalCount=%d analyticLTIInvalidAtEvent=%d stateTimeAligned=%d stateAbruptDelta=%d stateDatasetElements=%d coreConstant=1 nearDuplicateStateClock=%d exactLoggerClockAligned=%d\\n', ...
 found>0,found,deviatesFromAnalytic,logical(stateNearMatch),logical(stateJump),stateCount,logical(stateNativeDuplicate),logical(stateInputOutputConsistency));
assert(found>0,'JTE088:TransferFcnContinuousStateNotFound');
assert(strcmp(JTE2026sha256(fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx')),pin),'JTE088:ModifiedSource');
end
function closeProjectQuiet(p)
try,close(p);catch,end
end
function closeModelQuiet(name)
try
if bdIsLoaded(name),set_param(name,'CloseFcn','');close_system(name,0);end
catch,end
end
