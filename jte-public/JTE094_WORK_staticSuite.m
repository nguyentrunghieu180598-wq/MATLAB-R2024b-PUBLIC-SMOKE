function JTE094_WORK_staticSuite()
% All numeric examples here are synthetic arithmetic, never research MAT.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE094:Runtime','JTE094 assertion failed: Runtime');
chatPass=false;workPass=false;
try
 JTE094_ORACLE_TESTS();chatPass=true;
catch ME
 fprintf('JTE094_CHAT_ORIGINAL_ORACLE_FAIL identifier=%s\n',ME.identifier);
end
try
 JTE094_WORK_preflight();workPass=true;
catch ME
 fprintf('JTE094_WORK_PREFLIGHT_FAIL identifier=%s\n',ME.identifier);
end
q=linspace(.001,.95,1000001);
for b=[.25 .5 .75]
 bits=typecast(b,'uint64');
 for k=-8:8
  if k<0,z=bits-uint64(-k);else,z=bits+uint64(k);end
  q(end+1)=typecast(z,'double'); %#ok<AGROW>
 end
end
old=max(.25,q-mod(q,.25));proposed=JTE094_quantizerCandidate(q);
bad=find(old~=proposed);
fprintf('JTE094_SYNTHETIC_DOUBLE_DIAG mismatchCount=%d tested=%d rawResearchData=0\n',numel(bad),numel(q));
for k=1:min(20,numel(bad))
 j=bad(k);
 fprintf('JTE094_SYNTHETIC_DOUBLE_CASE q=%.17g qhex=%s MATLABold=%.17g proposed=%.17g\n',...
  q(j),num2hex(q(j)),old(j),proposed(j));
end
JTE094_remainingOracles();
fprintf('JTE094_STATIC_SUITE_RESULT ChatOriginal=%d WorkStrict=%d fullPlantRun=0 G5_ACCEPTED=false\n',chatPass,workPass);
assert(chatPass&&workPass,'JTE094:StaticSuiteFailedNoPlantPermitted','JTE094 assertion failed: StaticSuiteFailedNoPlantPermitted');
end
