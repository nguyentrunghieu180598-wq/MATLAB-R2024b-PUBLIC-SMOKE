function JTE094_remainingOracles()
% Original Chat masking/ideal-TF tests, separated because quantizer test fails.
% Static masking oracle: ONLY same physical T vector at same instant.
% Do NOT use this identity to compare two evolving feedback trajectories.
T = [310; 309; 308];
delta = 2;
for j = 1:numel(T)
    biased = T;
    biased(j) = biased(j)-delta;
    other = max(T([1:j-1,j+1:end]));
    loss = max(T) - max(biased);
    oracle = max(0, min(delta, T(j) - other));
    assert(abs(loss-oracle) < 1e-12, 'JTE094:MaskingOracleMismatch','JTE094 assertion failed: MaskingOracleMismatch');
    assert(loss >= 0 && loss <= delta, 'JTE094:MaskingBounds','JTE094 assertion failed: MaskingBounds');
end
Ttie = [310;310;307];
biased = Ttie; biased(1) = biased(1)-delta;
assert(max(Ttie)==max(biased), 'JTE094:TieMaskingFailed','JTE094 assertion failed: TieMaskingFailed');
assert(max(T-delta) == max(T)-delta, 'JTE094:CommonModeFailed','JTE094 assertion failed: CommonModeFailed');
fprintf('JTE094_STATIC_MASKING_ORACLE_PASS\n');

% Independent continuous-time transfer-function mathematical oracle:
% tau*dy/dt + y = u_core, for u_core(t) == 0.25, tau=0.001 s.
tau = 1e-3;
t = linspace(0, 0.02, 1000)';
y0 = 0.4;
yideal = 0.25 + (y0 - 0.25)*exp(-t/tau);
assert(all(yideal <= y0 + 1e-12) && all(yideal >= 0.25 - 1e-12));
assert(all(diff(yideal) <= 1e-12), 'JTE094:IdealTFNonmonotone','JTE094 assertion failed: IdealTFNonmonotone');
assert(abs(yideal(end)-0.25) < 1e-9, 'JTE094:IdealTFNotSettled','JTE094 assertion failed: IdealTFNotSettled');
fprintf('JTE094_IDEAL_TF_ANALYTICAL_PASS\n');

fprintf('JTE094_REMAINING_STATIC_ORACLES_PASS quantizerAcceptance=FAIL fullPlantRun=0\n');
end
