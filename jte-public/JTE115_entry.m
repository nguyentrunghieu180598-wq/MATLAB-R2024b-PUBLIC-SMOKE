function JTE115_entry(mode)
% Capture all potentially private MATLAB warnings/details before public flags.
taskRoot=pwd;priv=fullfile(taskRoot,'jte115-private');
if strcmp(mode,'prepare'),phase='PREPARE';else,phase='STUDY';end
prefix=fullfile(priv,['JTE115_' getenv('GITHUB_RUN_ID') '_' phase]);
try
 console=evalc('JTE115_run(mode);');
catch ME
 console=evalc('disp(getReport(ME,''extended'',''hyperlinks'',''off''));');
end
save([prefix '_CONSOLE.mat'],'console','-v7.3');
if isfile([prefix '_FLAGS.json'])
 f=jsondecode(fileread([prefix '_FLAGS.json']));
 fprintf('JTE115_RESULT phase=%s DECISION=%s CANARY_BITWISE_PASS=%d STATIC_MODEL_PARITY=%d SOURCE_PARITY=%d simulationStarted=%d horizonComplete=%d G5_ACCEPTED=false\n',...
  phase,f.DECISION,f.CANARY_BITWISE_PASS,f.STATIC_MODEL_PARITY,f.SOURCE_PARITY,f.simulationStarted,f.horizonComplete);
else
 fprintf('JTE115_RESULT phase=%s DECISION=UNQUALIFIED_RESOURCE privateConsoleOnly=1 G5_ACCEPTED=false\n',phase);
end
end
