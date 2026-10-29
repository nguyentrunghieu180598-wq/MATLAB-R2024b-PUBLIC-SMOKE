function JTE113_entry()
% Keep all study console output owner-private, expose only safe execution flags.
taskRoot=pwd;run=getenv('GITHUB_RUN_ID');
privateConsole=evalc('JTE113_oneCandidate()');
save(fullfile(taskRoot,'jte113-private',['JTE113_' run '_PRIVATE_CONSOLE.mat']),'privateConsole','-v7.3');
f=jsondecode(fileread(fullfile(taskRoot,'jte113-private',['JTE113_' run '_PRIVATE_FLAGS.json'])));
if ischar(f.EXCURSION_PERSISTS),x=f.EXCURSION_PERSISTS;else,x=sprintf('%d',f.EXCURSION_PERSISTS);end
fprintf('JTE113_SAFE_RESULT DECISION=%s SOURCE_PARITY=%d ENVELOPE_FIRST_WINDOW_CONDITIONAL=%s EXCURSION_PERSISTS=%s ACCEPTED_STEP_PROVENANCE=%s THERMAL_COMPARISON_NOT_AUTHORIZED=true simulationStarted=%d horizonComplete=%d G5_ACCEPTED=false\n',...
 f.DECISION,f.SOURCE_PARITY,f.ENVELOPE_FIRST_WINDOW_CONDITIONAL,x,f.ACCEPTED_STEP_PROVENANCE,f.simulationStarted,f.horizonComplete);
end
