function JTE116_entry()
root=pwd;prefix=fullfile(root,'jte116-private',['JTE116_' getenv('GITHUB_RUN_ID')]);
try,console=evalc('JTE116_prepare();');
catch ME,console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');end
save([prefix '_CONSOLE.mat'],'console','-v7.3');
if isfile([prefix '_FLAGS.json'])
 f=jsondecode(fileread([prefix '_FLAGS.json']));
 fprintf('JTE116_RESULT DECISION=%s ARCHIVE_CLASSIFIED=%d CANARY_BITWISE_PASS=%d STATIC_MODEL_PARITY=%d COMPILED_DOUBLE=%d PHYSICAL_SIMULATION_STARTED=0 OWNER_NEW_PLANT_AUTHORIZATION=0 G5_ACCEPTED=false\n',...
  f.DECISION,f.ARCHIVED_MISMATCH_CLASSIFICATION_COMPLETE,f.CANARY_BITWISE_PASS,f.STATIC_MODEL_PARITY,f.COMPILED_DOUBLE);
 if isfile([prefix '_SUMMARY.json'])
  s=jsondecode(fileread([prefix '_SUMMARY.json']));
  if isfield(s,'failure'),fprintf('JTE116_PRIVATE_FAILURE_CAPTURED stage=%s details=OWNER_PRIVATE_ONLY\n',s.failure.stage);end
 end
else
 fprintf('JTE116_RESULT DECISION=UNQUALIFIED_RESOURCE PHYSICAL_SIMULATION_STARTED=0 G5_ACCEPTED=false\n');
end
end
