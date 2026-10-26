function JTE094_ORACLE_TESTS()
% JTE094: PURE NUMERICAL/ALGEBRAIC ORACLE; NO BATTERY SIMULATION.
% Designed for MATLAB R2024b with base MATLAB only.
% NO private data, model modification, Simulink, Work credentials or output MAT.
% Source-law q and u are taken from project JTE060/JTE092 handoff and MUST
% be verified against pinned source in the target MATLAB environment.

rng(26010, 'twister');
q = [0.001; 0.25; 0.5; 0.75; 0.95];
boundaries = [0.25; 0.5; 0.75];
for k = 1:numel(boundaries)
    b = boundaries(k);
    q = [q; b-eps(b); b+eps(b); b-2*eps(b); b+2*eps(b)]; %#ok<AGROW>
end
q = [q; 0.001 + (0.95-0.001).*rand(200000,1)];
q = min(0.95, max(0.001, q));
old = max(0.25, q - mod(q, 0.25));
proposed = 0.25 * ones(size(q));
proposed(q >= 0.5) = 0.5;
proposed(q >= 0.75) = 0.75;
assert(all(old == proposed), 'JTE094:QuantizerOracleMismatch','JTE094 assertion failed: QuantizerOracleMismatch');
assert(all(ismember(unique(old), [0.25 0.5 0.75])), ...
    'JTE094:UnexpectedCoreLevel','JTE094 assertion failed: UnexpectedCoreLevel');
fprintf('JTE094_QUANTIZER_ALGEBRA_PASS N=%d\n', numel(q));

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

fprintf(['JTE094_ALL_STATIC_ORACLES_PASS; NO MATLAB/Simulink PLANT' ...
         ' RUN OR G5 ACCEPTANCE IMPLIED\n']);
end
