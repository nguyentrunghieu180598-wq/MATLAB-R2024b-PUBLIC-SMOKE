function JTE058syntheticFixtures()
% SYNTHETIC MATLAB + tiny Simulink fixture only; NO battery model/data.
assert(strcmp(version('-release'),'2024b'),'JTE058:WrongRelease','Synthetic/staging contract assertion failed.');
t=[0;1;1;2];T=reshape(1:1248,4,312);
out=Simulink.SimulationOutput;out.fixture=timeseries(T,t);
[a,b]=JTE2026timeseries(out,'fixture');assert(isequal(a,t)&&isequal(b,T)&&b(2,1)~=b(3,1));
assert(abs(thermalRMSE([0;1],[0;1],[0;.5;1],[0;0;0])-1/sqrt(3))<1e-12);
assert(thermalRMSE(t,[0;1;1;2],[0;2],[0;2])==0);
reject(@()thermalRMSE(t,[0;1;9;2],[0;2],[0;2]),'JTE058:ThermalJump');
assert(thermalRMSE([0;.25;2],[0;.25;2],[0;1;1.5;2],[0;1;1.5;2])==0);
reject(@()thermalRMSE([0;2],[0;2],[1;3],[1;3]),'JTE058:Horizon');
assert(rightArea([0;1;1;1;2],[0;0;1;0;0],[0;2],[0;0])==0);
assert(rightArea([0;2;2],[0;0;1],[0;2],[0;0])==0);
assert(rightArea(t,[0;0;1;1],[0;2],[0;0])==1);
physical=330*ones(4,312);physical(3:4,:)=331;
measured=physical;measured(:,8)=physical(:,8)-2;
JTE058validateC1(t,physical,t,measured,8,-2);
wrong=measured;wrong(:,9)=wrong(:,9)-2;
reject(@()JTE058validateC1(t,physical,t,wrong,8,-2),'JTE058:C1Identity');
reject(@()JTE058validateC1(t,physical,t,physical,8,0),'JTE058:C1Bias');
% Source-independent toy: Step's documented >=event-time final value.
% It does NOT prove all events are logged by pinned FlwR_calc's quantizer.
m='JTE058_SYNTHETIC_EVENT_FIXTURE';assert(~bdIsLoaded(m),'JTE058:ExistingFixture','Synthetic/staging contract assertion failed.');
new_system(m);cl=onCleanup(@()close_system(m,0)); %#ok<NASGU>
add_block('simulink/Sources/Step',[m '/Step'],'Time','1','SampleTime','0');
add_block('simulink/Continuous/Transfer Fcn',[m '/Filter'],'Numerator','1','Denominator','[0.2 1]');
add_block('simulink/Sinks/To Workspace',[m '/Core'],'VariableName','fixtureCore','SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
add_block('simulink/Sinks/To Workspace',[m '/Post'],'VariableName','fixturePost','SaveFormat','Timeseries','MaxDataPoints','inf','Decimation','1');
add_line(m,'Step/1','Filter/1');add_line(m,'Step/1','Core/1');add_line(m,'Filter/1','Post/1');
s=Simulink.SimulationInput(m);s=s.setModelParameter('StopTime','2','Solver','ode45','MaxStep','0.1','RelTol','1e-8','AbsTol','1e-10');
z=sim(s);[tc,u]=JTE2026timeseries(z,'fixtureCore');[tp,y]=JTE2026timeseries(z,'fixturePost');
assert(all(u(tc<1)==0)&&all(u(tc>1)==1),'JTE058:StepSides','Synthetic/staging contract assertion failed.');
at=find(tc==1);rightAtExactEvent=~isempty(at)&&u(at(end))==1;
% Logging side/clock precision is measured, NEVER forced to match assumption.
near=find(tc>=.99 & tc<=1.01);
for q=near(:).',fprintf('JTE058_SYNTHETIC_EVENT_ROW t=%.17g u=%.17g\n',tc(q),u(q));end
fprintf('JTE058_SYNTHETIC_EVENT_PROBE exact_event_rows=%d last_exact_row_post=%d raw_duplicate_rows=%d\n',numel(at),rightAtExactEvent,sum(diff(tc)==0));
if ~rightAtExactEvent
 fprintf('JTE058_RIGHT_HOLD_UNQUALIFIED clock/event-side assumption not established; no rounding or event-time repair performed\n');
end
assert(any(y(tp>1)>0&y(tp>1)<1),'JTE058:PostIsDynamic','Synthetic/staging contract assertion failed.');
expected=zeros(size(tp));ix=tp>=1;expected(ix)=1-exp(-(tp(ix)-1)/.2);
assert(max(abs(y-expected))<1e-5,'JTE058:ContinuousTransfer','Synthetic/staging contract assertion failed.');
meta=JTE058metadataSnapshot(z);assert(strcmp(meta.modelInfo.SolverInfo.Solver,'ode45'));
assert(meta.modelInfo.StartTime==0&&meta.modelInfo.StopTime==2);
fprintf('JTE058_SYNTHETIC_CONTRACT_FIXTURES_PASS release=%s version=%s duplicate_input_rows_retained=true C1_within_case=true postfilter_continuous=true toy_log_right_hold_qualified=%d PINNED_CONTROLLER_SEMANTICS_NOT_VALIDATED=true NO_BATTERY_MODEL=true NO_G5=true\n',version('-release'),version,rightAtExactEvent);
end
function r=thermalRMSE(ta,a,tb,b)
assert(ta(1)==tb(1)&&ta(end)==tb(end),'JTE058:Horizon','Synthetic/staging contract assertion failed.');
[ta,a]=continuousKnots(ta,a);[tb,b]=continuousKnots(tb,b);
k=union(ta,tb);d=interp1(ta,a,k,'linear')-interp1(tb,b,k,'linear');
r=sqrt(sum(diff(k).*(d(1:end-1).^2+d(1:end-1).*d(2:end)+d(2:end).^2)/3)/(k(end)-k(1)));
end
function [t,x]=continuousKnots(t,x)
assert(all(diff(t)>=0),'JTE058:Clock','Synthetic/staging contract assertion failed.');
for i=find(diff(t)==0).',assert(isequal(x(i,:),x(i+1,:)),'JTE058:ThermalJump','Synthetic/staging contract assertion failed.');end
keep=[diff(t)~=0;true];t=t(keep);x=x(keep,:);
end
function area=rightArea(ta,a,tb,b)
assert(ta(1)==tb(1)&&ta(end)==tb(end),'JTE058:Horizon','Synthetic/staging contract assertion failed.');
k=union(ta,tb);area=0;
for i=1:numel(k)-1
 ia=find(ta<=k(i),1,'last');ib=find(tb<=k(i),1,'last');
 area=area+abs(a(ia)-b(ib))*(k(i+1)-k(i));
end
end
function reject(f,id)
try,f();catch ME,assert(strcmp(ME.identifier,id),'JTE058:UnexpectedRejection','Unexpected rejection %s; expected %s',ME.identifier,id);return;end
error('JTE058:MissingRejection','Expected fixture to be rejected.');
end
