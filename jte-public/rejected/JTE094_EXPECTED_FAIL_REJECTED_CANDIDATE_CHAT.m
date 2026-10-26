function JTE094_EXPECTED_FAIL_REJECTED_CANDIDATE_CHAT()
% EXPECTED_FAIL_REJECTED_CANDIDATE. OPT-IN ARCHIVE, EXCLUDED FROM NORMAL CI.
% Original Chat quantizer conditions retained; no precision/tolerance relaxation.
% Do not rerun: R2024b counterexamples already established in PR48.
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

end
