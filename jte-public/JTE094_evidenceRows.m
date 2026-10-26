function e=JTE094_evidenceRows(rows,window,bracket)
% Read-only callback summary. Callbacks are evaluations, not accepted steps.
% Neither equal times nor event-bracket coincidence establish causality.
assert(isnumeric(rows)&&size(rows,2)==6,'JTE094:RowSchema','JTE094 assertion failed: RowSchema');
assert(numel(window)==2&&all(isfinite(window))&&window(2)>=window(1),'JTE094:Window','JTE094 assertion failed: Window');
assert(numel(bracket)==2&&all(isfinite(bracket))&&bracket(2)>=bracket(1),'JTE094:Bracket','JTE094 assertion failed: Bracket');
assert(all(isfinite(rows(:,1)))&&all(ismember(rows(:,2),[1 2 3 4])),'JTE094:TimeOrPhase','JTE094 assertion failed: TimeOrPhase');
e=struct('sampleKind','CALLBACK_EVALUATIONS_NOT_CERTIFIED_ACCEPTED_STEPS',...
 'causality','NOT_ESTABLISHED','sourceRowCount',size(rows,1),...
 'sourceTimeBacktrackObserved',any(diff(rows(:,1))<0));
e.phase=struct('tag',{},'windowCount',{},'bracketCount',{},'windowInputDifference',{},'bracketInputDifference',{});
for tag=2:4
 r=rows(rows(:,2)==tag & rows(:,1)>=window(1)&rows(:,1)<=window(2),:);
 b=r(r(:,1)>=bracket(1)&r(:,1)<=bracket(2),:);
 e.phase(end+1)=struct('tag',tag,'windowCount',size(r,1),'bracketCount',size(b,1),...
  'windowInputDifference',status(r),'bracketInputDifference',status(b));
end
e.liveStateCheck='UNAVAILABLE';e.acceptedStepClassification='UNAVAILABLE';
e.G5_ACCEPTED=false;
end
function s=status(r)
if isempty(r)||any(~isfinite(r(:,3))),s='UNAVAILABLE';
elseif any(abs(r(:,3)-.25)>1e-12),s='OBSERVED';
else,s='NOT_OBSERVED_IN_CAPTURED_EVALUATIONS';end
end
