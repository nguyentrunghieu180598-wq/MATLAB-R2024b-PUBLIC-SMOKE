function JTE094_WORK_preflight()
% Independent WORK software preflight; NOT Chat's JTE094_ORACLE_TESTS.m.
% No plant simulation or raw research data. Do not report this as G5 PASS.
assert(strcmp(version('-release'),'2024b'),'JTE094:Release');
assert(contains(version,'24.2.0.3361896'),'JTE094:Update10');
q=linspace(.001,.95,1000001);
for v=[.25 .5 .75]
 bits=typecast(v,'uint64');
 q=[q typecast(bits-uint64(1),'double') v typecast(bits+uint64(1),'double')]; %#ok<AGROW>
end
old=max(.25,q-mod(q,.25));candidate=JTE094_quantizerCandidate(q);
quantizerAgreement=isequal(old,candidate);
assert(isequal(JTE094_quantizerCandidate([.001 .25 .5 .75 .95]),[.25 .25 .5 .75 .75]),'JTE094:Ties');
for qbad={NaN,Inf,.0009,.951,single(.5)}
 rejected=false;try,JTE094_quantizerCandidate(qbad{1});catch ME,rejected=strcmp(ME.identifier,'JTE094:CandidateDomain');end
 assert(rejected,'JTE094:InvalidDomainNotRejected');
end
empty=JTE094_evidenceRows(zeros(0,6),[330 338],[334 335]);
assert(all(strcmp({empty.phase.windowInputDifference},'UNAVAILABLE')),'JTE094:EmptyIsUnavailable');
rows=[0 2 0 0 NaN NaN;334 2 .1 .25 NaN NaN;334 3 .25 .25 NaN NaN;...
      333 2 .25 .25 NaN NaN;335 4 .25 .25 NaN NaN];
e=JTE094_evidenceRows(rows,[330 338],[334 335]);
assert(e.sourceTimeBacktrackObserved&&strcmp(e.causality,'NOT_ESTABLISHED'),'JTE094:NoCausalityInference');
assert(strcmp(e.phase(1).bracketInputDifference,'OBSERVED'),'JTE094:LocalInputObserved');
assert(strcmp(e.phase(2).bracketInputDifference,'NOT_OBSERVED_IN_CAPTURED_EVALUATIONS'),'JTE094:NegativeControl');
assert(strcmp(e.liveStateCheck,'UNAVAILABLE')&&~e.G5_ACCEPTED,'JTE094:NoAutomaticPass');
outside=JTE094_evidenceRows(rows,[330 338],[336 337]);
assert(all(strcmp({outside.phase.bracketInputDifference},'UNAVAILABLE')),'JTE094:NoBracketSamples');
nonfinite=rows;nonfinite(2,3)=NaN;
e=JTE094_evidenceRows(nonfinite,[330 338],[334 335]);
assert(strcmp(e.phase(1).bracketInputDifference,'UNAVAILABLE'),'JTE094:UnreadableIsUnavailable');
line=sprintf('JTE094_NEWLINE_CHECK\n');
assert(line(end)==char(10)&&~contains(line,'\n'),'JTE094:LiteralBackslashN');
fprintf('JTE094_WORK_EVIDENCE_AND_DOMAIN_TESTS_PASS quantizerAgreement=%d\n',quantizerAgreement);
assert(quantizerAgreement,'JTE094:NonEquivalentMATLABDouble');
fprintf('JTE094_WORK_PREFLIGHT_PASS MATLAB_double_cases=%d boundariesAndAdjacentULPs=PASS evidenceSemantics=PASS newline=PASS ChatOracleStatus=RUN_SEPARATELY fullPlantStatus=NOT_RUN G5_ACCEPTED=false\n',numel(q));
end
