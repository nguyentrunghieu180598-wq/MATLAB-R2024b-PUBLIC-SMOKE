function sampled_actuator_review_entry()
root=pwd;prefix=fullfile(root,'actuator-review-private',['ACTUATOR_REVIEW_' getenv('GITHUB_RUN_ID')]);
try
 assert(nargin('build_sampled_actuator_review')==4,'ActReview:Code','Builder parse/signature unavailable.');
 console=evalc('prepare_sampled_actuator_review();');
catch ME,console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');end
save([prefix '_CONSOLE.mat'],'console','-v7.3');
if isfile([prefix '_FLAGS.json'])
 f=jsondecode(fileread([prefix '_FLAGS.json']));
 fprintf('ACTUATOR_REVIEW_RESULT DECISION=%s PHYSICAL_GRAPH_PARITY=%d CONTROLLER_BIAS_PRESERVED=%d IC_PARAMETERS_PRESERVED=%d ARCHIVED_Y0_USED=%d COMPILE_ALL=%d UNIT_METADATA_PARITY=%d UNIT_METADATA_EXPLICIT=%d OWNER_METHOD_APPROVAL=0 TOY_RUN=0 PHYSICAL_RUN=0 SOURCE_G5_FINAL_THERMAL_REJECTED=1 G5_ACCEPTED=false\n',...
  f.DECISION,f.PHYSICAL_GRAPH_PARITY,f.CONTROLLER_BIAS_PRESERVED,f.IC_PARAMETERS_PRESERVED,f.ARCHIVED_Y0_USED,f.COMPILE_ALL,f.UNIT_METADATA_PARITY,f.UNIT_METADATA_EXPLICIT);
else
 fprintf('ACTUATOR_REVIEW_RESULT DECISION=STATIC_REVIEW_UNQUALIFIED TOY_RUN=0 PHYSICAL_RUN=0 G5_ACCEPTED=false\n');
end
end
