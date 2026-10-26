function JTE094_ORACLE_TESTS()
% Only independent masking/ideal-TF tests. Original failed quantizer preserved
% at rejected/JTE094_EXPECTED_FAIL_REJECTED_CANDIDATE_CHAT.m (explicit opt-in).
% Historical exact source and actual FAIL remain at PR48 immutable commits.
JTE094_staticMaskingOracle();
JTE094_idealTFOracle();
fprintf('JTE094_INDEPENDENT_STATIC_TESTS_COMPLETE quantizer=REJECTED_NOT_TESTED G5_ACCEPTED=false\n');
end
