function BTMS_M3_requalifyEntry()
% Exactly one tiny non-battery probe after lint. No source model is loaded.
root=fullfile(pwd,'actuator-review-private');
files={'BTMS_M3_loggerProbe.m','BTMS_M3_completed.m','BTMS_M3_instrument.m','BTMS_M3_events.m'};
lint=cell(1,numel(files));parseError=false;
for k=1:numel(files)
 p=which(files{k});assert(~isempty(p),'M3:LintFile','Candidate helper missing.');
 info=checkcode(p,'-id');lint{k}=struct('file',files{k},'messages',info);
 for j=1:numel(info)
  parseError=parseError||startsWith(info(j).id,'SYNER')||...
   ~isempty(regexpi(info(j).message,'parse error|invalid syntax|invalid expression|syntax error','once'));
 end
end
save(fullfile(root,'LINT_R2024B.mat'),'lint','parseError','-v7.3');
f=fopen(fullfile(root,'LINT_FLAGS.json'),'w');assert(f>=0,'M3:LintWrite','Private lint write failed.');
fprintf(f,'%s',jsonencode(struct('parseError',parseError,'files',{files},'physicalRun',false)));fclose(f);
assert(~parseError,'M3:LintParseError','MATLAB syntax qualification rejected before synthetic trajectory.');
assert(~isfile(fullfile(root,'PROBE_DISPATCHED.json')),'M3:OneProbe','Probe was already attempted.');
f=fopen(fullfile(root,'PROBE_DISPATCHED.json'),'w');assert(f>=0,'M3:ProbeWrite','Cannot record one-probe dispatch.');
fprintf(f,'{"syntheticOnly":true,"oneAttempt":true,"physicalApprovalConsumed":false}');fclose(f);
fprintf('M3_R2024B_LINT_PARSE=PASS oneSyntheticProbe=STARTING physicalRun=0\n');
BTMS_M3_loggerProbe();
% Keep the MATLAB action red when the synthetic probe reports UNQUALIFIED.
% An independent if:always() private publisher may still preserve evidence.
p=fullfile(root,'PROBE_FLAGS.json');
assert(isfile(p),'WK02:FlagsMissing','Private qualification flags absent.');
r=jsondecode(fileread(p));
assert(isfield(r,'status')&&strcmp(r.status,'M3_LOGGER_CLOCK_STATE_FIRST_PAUSED_OP_ONLY'),...
 'WK02:QualificationNoPass','Logger UNQUALIFIED; private publisher must retain diagnostics.');
end
