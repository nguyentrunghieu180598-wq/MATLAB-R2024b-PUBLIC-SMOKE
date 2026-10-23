function result=JTE2026compareTraces(tA,xA,tB,xB,label)
% Explicit time alignment for variable-step simulation traces, NOT free PASS.
% LINEAR interpolation on union grid ONLY WITHIN THE COMMON CLOSED INTERVAL.
% Return time grid / interpolation diagnostics for numeric reviewer.
arguments
    tA (:,1) double
    xA double
    tB (:,1) double
    xB double
    label (1,:) char
end
assert(numel(tA)>=2 && numel(tB)>=2, 'Insufficient time stamps: %s',label);
assert(all(isfinite(tA)) && all(isfinite(tB)) && ...
    all(diff(tA)>0) && all(diff(tB)>0),'Bad timestamps: %s',label);
assert(size(xA,1)==numel(tA) && size(xB,1)==numel(tB), ...
    'Data/time mismatch: %s',label);
assert(all(isfinite(xA(:))) && all(isfinite(xB(:))), ...
    'NaN/Inf in trace %s',label);
assert(isequal(size(xA,2),size(xB,2)) && ismatrix(xA) && ismatrix(xB), ...
    'Signal dimension mismatch: %s',label);
% Require same start and finish: no extrapolation, no truncation of a run.
scale=max([1;abs(tA);abs(tB)]);
endpointTol=32*eps(scale);
assert(abs(tA(1)-tB(1))<=endpointTol && ...
    abs(tA(end)-tB(end))<=endpointTol, ...
    'Different simulation endpoints in %s (no extrapolation permitted).',label);
if isequal(tA,tB)
    yA=xA; yB=xB; method='identical_time_grid';
    grid=tA;
else
    grid=unique([tA;tB]);
    % Remove endpoint rounding discrepancies before using interp1.
    grid=grid(grid>=max(tA(1),tB(1)) & grid<=min(tA(end),tB(end)));
    assert(numel(grid)>=2,'No overlap: %s',label);
    yA=interp1(tA,xA,grid,'linear');
    yB=interp1(tB,xB,grid,'linear');
    method='linear_on_union_grid_no_extrapolation';
end
assert(all(isfinite(yA(:))) && all(isfinite(yB(:))), ...
    'Interpolation failed for %s',label);
result=struct('name',label,'maxAbs',max(abs(yA(:)-yB(:))), ...
    'nA',numel(tA),'nB',numel(tB),'nCompare',numel(grid), ...
    'maxStepA_s',max(diff(tA)),'maxStepB_s',max(diff(tB)), ...
    'timeStart_s',grid(1),'timeEnd_s',grid(end),'method',method, ...
    'interpolationApplied',~isequal(tA,tB));
% This is a diagnostic. Reviewer must assess solver sensitivity and
% discontinuities (e.g. relay, saturation, step change) before G5 PASS.
end
