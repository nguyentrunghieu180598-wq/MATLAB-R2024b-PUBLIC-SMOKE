function JTE115_canaryOnly()
% Single corrected diagnostic of failed canary; NO model load/compile/sim.
root=pwd;prefix=fullfile(root,'jte115-private',['JTE115_' getenv('GITHUB_RUN_ID')]);
flags=struct('DECISION','GUARDED_REJECTED_BITWISE_OR_MODEL_PARITY','CANARY_BITWISE_PASS',false,...
 'READY_FOR_ONE_SIM',false,'STATIC_MODEL_PARITY',false,'SOURCE_PARITY',false,...
 'simulationStarted',false,'horizonComplete',false,'G5_ACCEPTED',false);
summary=struct('flags',flags,'scope','Correct assert reporting only; model execution is permanently disabled in this run.','G5_ACCEPTED',false);
try
 console=evalc('JTE115_guardedLawCanary([prefix ''_CANARY_PROOF.mat'']);');
 flags.CANARY_BITWISE_PASS=true;
 flags.DECISION='CANARY_PASS_PRIOR_ERROR_UNRESOLVED_NO_PLANT';
catch ME
 console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');
 summary.failure=struct('stage','CANARY','identifier',ME.identifier,'message',ME.message,'stack',{ME.stack},'simulationStarted',false);
end
summary.flags=flags;
save([prefix '_PREPARE_CONSOLE.mat'],'console','-v7.3');
f=fopen([prefix '_PREPARE_FLAGS.json'],'w');fprintf(f,'%s',jsonencode(flags));fclose(f);
f=fopen([prefix '_PREPARE_SUMMARY.json'],'w');fprintf(f,'%s',jsonencode(summary));fclose(f);
fprintf('JTE115_CORRECTED_CANARY DECISION=%s CANARY_BITWISE_PASS=%d PLANT_DISABLED=1 G5_ACCEPTED=false\n',flags.DECISION,flags.CANARY_BITWISE_PASS);
end
