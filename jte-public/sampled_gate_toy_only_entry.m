function sampled_gate_toy_only_entry()
P=fullfile(pwd,'actuator-review-private');console='';failure=[];
try,console=evalc('sampled_gate_toy()');catch ME,failure=struct('identifier',ME.identifier,'message',ME.message,'report',getReport(ME,'extended','hyperlinks','off'));end
save(fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_TOY_ONLY_CONSOLE.mat']),'console','failure','-v7.3');
fprintf('BTMS_TOY_ONLY_ENTRY_COMPLETE newBatteryRun=0 baselineRerun=0 sourceInputRerun=0 G5_ACCEPTED=false\n');
end
