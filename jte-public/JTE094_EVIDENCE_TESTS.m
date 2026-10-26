function JTE094_EVIDENCE_TESTS()
% No simulation or interpretation of private data; synthetic row semantics only.
assert(strcmp(version('-release'),'2024b'),'JTE094:Release','Expected R2024b.');
empty=JTE094_evidenceRows(zeros(0,6),[330 338],[334 335]);
assert(all(strcmp({empty.phase.windowInputDifference},'UNAVAILABLE')),'JTE094:Empty','Empty capture is unavailable.');
rows=[0 2 0 0 NaN NaN;334 2 .1 .25 NaN NaN;334 3 .25 .25 NaN NaN;...
      333 2 .25 .25 NaN NaN;335 4 .25 .25 NaN NaN];
e=JTE094_evidenceRows(rows,[330 338],[334 335]);
assert(e.sourceTimeBacktrackObserved&&strcmp(e.causality,'NOT_ESTABLISHED'),'JTE094:Causality','Keep evaluation order and no causal inference.');
assert(strcmp(e.phase(1).bracketInputDifference,'OBSERVED'),'JTE094:Positive','Expected local input difference.');
assert(strcmp(e.phase(2).bracketInputDifference,'NOT_OBSERVED_IN_CAPTURED_EVALUATIONS'),'JTE094:Negative','Expected negative control.');
assert(strcmp(e.liveStateCheck,'UNAVAILABLE')&&~e.G5_ACCEPTED,'JTE094:Gate','No automatic acceptance.');
outside=JTE094_evidenceRows(rows,[330 338],[336 337]);
assert(all(strcmp({outside.phase.bracketInputDifference},'UNAVAILABLE')),'JTE094:Missing','No bracket samples.');
nonfinite=rows;nonfinite(2,3)=NaN;e=JTE094_evidenceRows(nonfinite,[330 338],[334 335]);
assert(strcmp(e.phase(1).bracketInputDifference,'UNAVAILABLE'),'JTE094:Unreadable','Nonfinite is unavailable.');
s=fileread(which('JTE092_internal_eval_probe'));
assert(~contains(s,'\\n'),'JTE094:EscapedNewline','Legacy log must not contain double backslash-n.');
assert(~contains(s,'tfEvalChangedAtEvent')&&~contains(s,'modBranchDiscontinuityNearEvent'),...
 'JTE094:LegacyCausalLabel','Ambiguous causal labels must be removed.');
assert(contains(s,'liveStateOutputCheck=%s')&&contains(s,'solverResetActorStatus=UNAVAILABLE'),...
 'JTE094:AvailabilityLabel','Explicit unavailable statuses required.');
record=sprintf('A status=UNAVAILABLE\nB sampleKind=CALLBACK_EVALUATIONS\n');
lines=splitlines(string(record));
assert(numel(lines)==3&&startsWith(lines(1),'A ')&&startsWith(lines(2),'B '),...
 'JTE094:LineParser','One record per line.');
fprintf('JTE094_EVIDENCE_TESTS_PASS scope=software_synthetic legacyProbeNotRerun=1 availabilityAndPhaseAndNewline=PASS G5_ACCEPTED=false\n');
end
