function JTE056selftest()
% MATLAB fixture tests ONLY; no model simulation and no research data.
assert(strcmp(version('-release'),'2024b'),'JTE056:WrongRelease');
t=[0;1;1;2]; x=reshape(1:1248,4,312);
[a,b]=JTE056normalize(t,x,true);
assert(isequal(a,t)&&isequal(b,x)&&b(2,1)~=b(3,1));
[a,b]=JTE056normalize(t,x.',false);
assert(isequal(a,t)&&isequal(b,x));
sq=reshape(1:16,4,4);[~,b]=JTE056normalize(t,sq,false);
assert(isequal(b,sq.')); % orientation must not be guessed from equal dimensions
[~,b]=JTE056normalize(0,reshape(1:312,1,1,312),true);
assert(isequal(b,1:312));
[~,b]=JTE056normalize(t,reshape(x.',312,1,4),false);
assert(isequal(b,x));
expectError(@()JTE056normalize([0;2;1;3],x,true),'JTE056:TimeReversal');
expectError(@()JTE056normalize(t,x.',true),'JTE056:TimeShape');
expectError(@()JTE056normalize(t,single(x),true),'MATLAB:');
% Real MATLAB timeseries and SimulationOutput interface (no simulator).
ts=timeseries(x,t); out=Simulink.SimulationOutput; out.fixture=ts;
[a,b]=JTE2026timeseries(out,'fixture');
assert(isequal(a,t)&&isequal(b,x),'JTE056:TimeseriesRoundtrip');
% Distinct min/max pair and full-vector math, including duplicate event rows.
T=[315 314 308;315 314 303;315 314 302;316 314 302];
pair=[min(T,[],2),max(T,[],2)];
assert(isequal(pair(:,1),[308;303;302;302]));
assert(isequal(pair(:,2),[315;315;315;316]));
assert(isequal(T,T+0));
fprintf('JTE056_NATIVE_FIXTURE_PASS release=%s version=%s rows=4 channels=312 duplicateRows=1 no_simulation=true\n',version('-release'),version);
end
function expectError(f,id)
try,f();catch ME
    assert(startsWith(ME.identifier,id),'JTE056:UnexpectedError','Wrong rejection: %s',ME.identifier);
    return;
end
error('JTE056:MissingRejection','Invalid fixture was accepted.');
end
