function JTE060controllerEventFixture()
% JTE060: source-specific synthetic FlwR_calc and downstream filter probe.
% NO battery plant simulation, NO research values, NO claim that all hidden
% solver transitions are observed by To Workspace.
assert(strcmp(version('-release'),'2024b'),'JTE060:Release');
root=pwd; vendor=fullfile(root,'vendor-pack');
projectFile=fullfile(vendor,'batteryExamplesProjectSetup.prj');
sourceFile=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
sourceSHA='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(sourceFile),sourceSHA),'JTE060:SourceSHA');
p=openProject(projectFile);clp=onCleanup(@()closeProjectQuiet(p)); %#ok<NASGU>
load_system(sourceFile);[~,v]=fileparts(sourceFile);
source=[v '/Battery Control/FlwR_calc'];
filterSource=[v '/Battery Control/sensor dynamics 1'];
assert(getSimulinkBlockHandle(source)>0 && getSimulinkBlockHandle(filterSource)>0,'JTE060:PinnedPath');
assert(strcmp(get_param(filterSource,'BlockType'),'TransferFcn'),'JTE060:PinnedFilter');
% The source-pinned controller contains no hidden stateful block type.
blocks=find_system(source,'LookUnderMasks','all','FollowLinks','off','Type','Block');
allowed={'SubSystem','Inport','Outport','Constant','Sum','Gain','Saturate','MinMax','Math'};
for k=1:numel(blocks)
    assert(ismember(get_param(blocks{k},'BlockType'),allowed),'JTE060:UnknownControllerBlock');
end
assert(strcmp(get_param([source '/FlwR calc/Subtract'],'Inputs'),'+-'),'JTE060:InputSigns');
assert(str2double(get_param([source '/FlwR calc/Gain1'],'Gain'))==0.1,'JTE060:Gain');
assert(str2double(get_param([source '/FlwR calc/Saturation'],'LowerLimit'))==0.001,'JTE060:Lower');
assert(str2double(get_param([source '/FlwR calc/Saturation'],'UpperLimit'))==0.95,'JTE060:Upper');
assert(strcmp(get_param([source '/Step Change/Mod'],'Operator'),'mod'),'JTE060:Mod');
assert(str2double(get_param([source '/step'],'Value'))==0.25,'JTE060:Step');
model='JTE060_ACTUAL_PINNED_CONTROLLER_FIXTURE';
assert(~bdIsLoaded(model),'JTE060:AlreadyOpen');
new_system(model);clm=onCleanup(@()close_system(model,0)); %#ok<NASGU>
% Continuous piecewise-linear synthetic temperature-ambient difference.
% A 4-second 7-cycle sweep moves up/down over both 5K and 7.5K levels.
tin=(0:0.0125:4)';
d=6.25+1.8*sin(2*pi*1.75*tin+0.14);
ambient=300+zeros(size(tin)); Tmax=ambient+d;
for name={'Tmax','Ambient'}
    block=[model '/' name{1}];
    add_block('simulink/Sources/From Workspace',block,'VariableName',['fixture' name{1}], ...
        'Interpolate','on','SampleTime','0','OutputAfterFinalValue','Holding final value');
end
mw=get_param(model,'ModelWorkspace');
assignin(mw,'fixtureTmax',timeseries(Tmax,tin));
assignin(mw,'fixtureAmbient',timeseries(ambient,tin));
add_block(source,[model '/Actual pinned FlwR_calc']);
add_block(filterSource,[model '/Actual pinned postfilter']);
add_line(model,'Tmax/1','Actual pinned FlwR_calc/1');
add_line(model,'Ambient/1','Actual pinned FlwR_calc/2');
add_line(model,'Actual pinned FlwR_calc/1','Actual pinned postfilter/1');
for name={'Core','Postfilter'}
    add_block('simulink/Sinks/To Workspace',[model '/' name{1}], ...
      'VariableName',['fixture' name{1}],'SaveFormat','Timeseries', ...
      'MaxDataPoints','inf','Decimation','1');
end
add_line(model,'Actual pinned FlwR_calc/1','Core/1');
add_line(model,'Actual pinned postfilter/1','Postfilter/1');
s=Simulink.SimulationInput(model);
s=s.setModelParameter('StartTime','0','StopTime','4', ...
    'Solver','ode23t','MaxStep','0.03','RelTol','1e-6','AbsTol','1e-8');
out=sim(s);
[tc,u]=JTE2026timeseries(out,'fixtureCore');
[tp,y]=JTE2026timeseries(out,'fixturePostfilter');
assert(size(u,2)==1&&size(y,2)==1,'JTE060:ScalarOutput');
assert(abs(tc(1))<1e-10&&abs(tc(end)-4)<1e-8,'JTE060:FullHorizon');
assert(abs(tp(1))<1e-10&&abs(tp(end)-4)<1e-8,'JTE060:FilterHorizon');
assert(all(ismember(round(u*1000000)/1000000,[0.25;0.5;0.75])),'JTE060:Levels');
% At all logged sample times away from boundary ambiguity, verify output
% of copied real source block against exact pinned source algebra.
sourceDelta=interp1(tin,d,tc,'linear');
q=min(0.95,max(0.001,0.1*sourceDelta));
oracle=max(0.25,q-mod(q,0.25));
margin=min(abs(sourceDelta-5),abs(sourceDelta-7.5));
away=(margin>1e-7);
assert(any(away)&&sum(away)>20,'JTE060:InsufficientAwaySamples');
res=max(abs(u(away)-oracle(away)));
assert(res<1e-10,'JTE060:ControllerLawDisagreement');
% Count SOURCE-MATH switching times that are known for our synthetic,
% piecewise-linear input. Count what ToWorkspace ACTUALLY saw separately.
expectedTimes=zeros(0,1);
for th=[5,7.5]
    e0=d(1:end-1)-th;e1=d(2:end)-th;
    crossings=find(e0.*e1<0);
    for j=crossings(:).'
        expectedTimes(end+1,1)=tin(j)+(tin(j+1)-tin(j))*(th-d(j))/(d(j+1)-d(j)); %#ok<AGROW>
    end
end
expectedTimes=sort(expectedTimes);
change=find(diff(u(:,1))~=0)+1;
brackets=[tc(change-1),tc(change)];
matched=false(size(expectedTimes));
for k=1:numel(expectedTimes)
    % This is a conservative OBSERVED bracket, not an exact event time.
    matched(k)=any(brackets(:,1)<=expectedTimes(k)+1e-8 & ...
                  brackets(:,2)>=expectedTimes(k)-1e-8);
end
% The synthetic source d(t) has known interpolation segments and all
% threshold crossing instants can be solved analytically from that input.
% Compare the sampled right-hold integral with exact source-law segments.
% This is NOT a bound on full-plant event capture; only this fixture.
exactKnots=[0;expectedTimes;4];
midpoints=0.5*(exactKnots(1:end-1)+exactKnots(2:end));
dMid=interp1(tin,d,midpoints,'linear');
qMid=min(0.95,max(0.001,0.1*dMid));
oracleMid=max(0.25,qMid-mod(qMid,0.25));
trueFixtureArea=sum(diff(exactKnots).*oracleMid);
sampledFixtureArea=sum(diff(tc).*u(1:end-1));
bracketWidths=tc(change)-tc(change-1);
conditionalAreaBound=sum(abs(u(change)-u(change-1)).*bracketWidths);
fixtureAreaError=abs(sampledFixtureArea-trueFixtureArea);
if all(matched) && numel(change)==numel(expectedTimes)
    assert(fixtureAreaError<=conditionalAreaBound+1e-9,'JTE060:SyntheticTimingErrorBound');
end
fprintf('JTE060_SYNTHETIC_EVENT_TIMING exactFixtureArea=%.12g sampledRightHoldArea=%.12g absoluteAreaError=%.12g conditionalBracketAreaBound=%.12g maxObservedBracketSeconds=%.12g FULL_PLANT_VALIDATION=false\n', ...
    trueFixtureArea,sampledFixtureArea,fixtureAreaError,conditionalAreaBound,max(bracketWidths));
postDynamic=any(abs(y-interp1(tc,u,tp,'previous','extrap'))>1e-6);
assert(postDynamic,'JTE060:FilterMustBeDynamic');
assert(strcmp(JTE2026sha256(sourceFile),sourceSHA),'JTE060:VendorModified');
fprintf('JTE060_PINNED_SOURCE_SYNTHETIC_PASS matlab=%s sourceSHA=%s loggedCoreRows=%d loggedPostRows=%d sampledLawResidual=%.4g\n', ...
    version('-release'),sourceSHA,numel(tc),numel(tp),res);
fprintf('JTE060_EVENT_COVERAGE_DIAGNOSTIC expectedSyntheticCrossings=%d observedLoggedChanges=%d matchedWithinObservedBrackets=%d exactLoggedDuplicateRows=%d SOURCE_SPECIFIC_REAL_PLANT_EVENT_COVERAGE_NOT_PROVEN=true\n', ...
    numel(expectedTimes),numel(change),sum(matched),sum(diff(tc)==0));
% A test fixture can find missing transitions; even a pass in this synthetic
% context CANNOT certify absence of missed events in the future battery run.
if ~all(matched)||numel(change)~=numel(expectedTimes)
    fprintf('JTE060_EVENT_CAPTURE_LIMITATION synthetic expected/observed mismatch; reject unqualified switch-time precision\n');
end
end
function closeProjectQuiet(project)
try,close(project);catch,end
end
