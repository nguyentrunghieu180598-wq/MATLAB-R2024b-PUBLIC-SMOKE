function JTE094_EXPECTED_FAIL_REJECTED_CANDIDATE_WORK()
% EXPECTED_FAIL_REJECTED_CANDIDATE. OPT-IN ARCHIVE, NOT AN ACCEPTANCE GATE.
% Historical sweep is retained, not executed in JTE096.
q=linspace(.001,.95,1000001);
for v=[.25 .5 .75]
 bits=typecast(v,'uint64');
 q=[q typecast(bits-uint64(1),'double') v typecast(bits+uint64(1),'double')]; %#ok<AGROW>
end
old=max(.25,q-mod(q,.25));candidate=JTE094_quantizerCandidate(q);
quantizerAgreement=isequal(old,candidate);
assert(quantizerAgreement,'JTE094:NonEquivalentMATLABDouble','EXPECTED_FAIL_REJECTED_CANDIDATE: source mod and thresholds disagree.');
end
