function JTE094_WORK_preflight()
% Retired mixed entry point: never promote a rejected-candidate test to PASS.
error('JTE096:RetiredMixedPreflight',...
 'Use independent JTE094_EVIDENCE_TESTS; rejected WORK oracle is explicit opt-in under rejected/. No sweep was rerun.');
end
