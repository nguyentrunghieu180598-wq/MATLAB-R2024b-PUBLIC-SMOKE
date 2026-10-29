function sampled_gate_entry()
% Independent package branches; failure in one never authorizes any physical run.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID')]);
names={'sampled_gate_toy','sampled_gate_load_only'};
for k=1:numel(names)
 console='';failure=[];
 try,console=evalc([names{k} '()']);catch ME,failure=struct('identifier',ME.identifier,'message',ME.message,'stack',{ME.stack});end
 save([pre '_' names{k} '_CONSOLE.mat'],'console','failure','-v7.3');
 fprintf('FEASIBILITY_COMPONENT_FINISHED component=%s topLevelError=%d batteryRun=0 G5_ACCEPTED=false\n',names{k},~isempty(failure));
end
end
