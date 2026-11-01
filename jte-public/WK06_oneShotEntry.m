function WK06_oneShotEntry()
% One R2024b process, toy only. Source-only until independently enabled.
p=fullfile(pwd,'actuator-review-private');
gateFile=fullfile(p,'WK04_PREPARE_GATE.json');
flagsFile=fullfile(p,'WK04_FLAGS.json');
gate=jsondecode(fileread(gateFile));
try
 observed=char(version);
 assert(strcmp(observed,'24.2.0.3361896 (R2024b) Update 10'), ...
  'WK06:BuildMismatch','Pinned MATLAB R2024b Update 10 mismatch.');
 BTMS_WK04_t0Fixture(p,gateFile);
catch err
 if ~isfile(flagsFile)
  flags=struct('status','UNQUALIFIED','stage','WK06_BUILD_OR_ENTRY', ...
   'identifier',err.identifier,'reason',err.message, ...
   'observedVersion',char(version),'run',gate.run,'commit',gate.commit, ...
   'physicalRun',false,'MATLAB_API_QUALIFIED',false, ...
   'PRIVATE_TRANSPORT_VERIFIED',false,'PHYSICAL_G5_ACCEPTED',false);
  fid=fopen(flagsFile,'w');
  assert(fid>=0,'WK06:PrivateFlagsWrite','Private failure flags unavailable.');
  fprintf(fid,'%s',jsonencode(flags));fclose(fid);
 end
 safeID=regexprep(err.identifier,'[^A-Za-z0-9_:]','_');
 if isempty(safeID),safeID='UNSPECIFIED';end
 error('WK06:Unqualified','Private diagnostic saved; identifier=%s',safeID);
end
end
