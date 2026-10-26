function JTE094_WORK_staticSuite()
% Explicit independent software tests; not called by JTE096 hotfix CI because
% these tests already passed. No rejected candidate under acceptance gating.
JTE094_staticMaskingOracle();
JTE094_idealTFOracle();
JTE094_EVIDENCE_TESTS();
fprintf('JTE094_INDEPENDENT_SOFTWARE_SUITE_COMPLETE quantizer=REJECTED_NOT_RUN plant=NOT_RUN G5_ACCEPTED=false\n');
end
