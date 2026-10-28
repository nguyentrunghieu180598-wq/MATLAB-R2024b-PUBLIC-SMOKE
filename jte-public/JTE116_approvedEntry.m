function JTE116_approvedEntry(phase)
root=pwd;prefix=fullfile(root,'jte116-one-private',['JTE116ONE_' getenv('GITHUB_RUN_ID') '_' upper(phase)]);
try
 if strcmp(phase,'toy')
  assert(nargin('JTE116_oneApprovedPlant')==0,'JTE116:Code','Plant driver parse/signature unavailable; no toy/plant run.');
  console=evalc('JTE116_majorStepToy();');
 elseif strcmp(phase,'plant'),console=evalc('JTE116_oneApprovedPlant();');
 else,error('JTE116:Mode','Unrecognized phase.');end
catch ME
 console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');
end
save([prefix '_CONSOLE.mat'],'console','-v7.3');
if isfile([prefix '_FLAGS.json'])
 f=jsondecode(fileread([prefix '_FLAGS.json']));
 if strcmp(phase,'toy'),fprintf('JTE116ONE_TOY LOGGER_QUALIFIED=%d PHYSICAL_SIMULATION_STARTED=0 G5_ACCEPTED=false\n',f.LOGGER_QUALIFIED);
 else,fprintf('JTE116ONE_PLANT DECISION=%s SOURCE_PARITY=%d T0_SAVED_STATE_PARITY=%d ACCEPTED_MAJOR_PROVENANCE=%s PHYSICAL_ATTEMPT_ENTERED=%d TIME_ADVANCEMENT_ENTERED=%d HORIZON_340_COMPLETE=%d SECOND_EVENT_NOT_COVERED_340=1 G5_ACCEPTED=false\n',...
  f.DECISION,f.SOURCE_PARITY,f.T0_SAVED_STATE_PARITY,f.ACCEPTED_MAJOR_PROVENANCE,f.PHYSICAL_ATTEMPT_ENTERED,f.TIME_ADVANCEMENT_ENTERED,f.HORIZON_340_COMPLETE);end
else,fprintf('JTE116ONE_RESULT phase=%s DECISION=UNQUALIFIED_LOGGING_OR_RESOURCE G5_ACCEPTED=false\n',phase);end
end
