function JTE094_staticMaskingOracle()
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

end
