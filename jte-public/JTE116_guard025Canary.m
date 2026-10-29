function JTE116_guard025Canary(reportFile)
% Source-law canary, MATLAB R2024b Update10 only.
% No Simulink/Simscape model, no plant, no G5 acceptance.
% Critically qGuard=0.25; JTE115 qGuard=0.375 was rejected.
assert(strcmp(version('-release'),'2024b') && contains(version,'24.2.0.3361896'), ...
 'JTE116:WrongRelease','The frozen MATLAB runtime is unavailable.');
prev=rng; restore=onCleanup(@()rng(prev)); %#ok<NASGU>
q=[0.001;0.249;0.25;0.251;0.374;0.375;0.376;0.499;0.5;0.501;0.749;0.75;0.751;0.95];
for b=[0.25,0.375,0.5,0.75]
 q=[q;b+(-2048:2048)'*eps(b)]; %#ok<AGROW>
end
rng(116,'twister');
q=[q;0.001+(0.95-0.001)*rand(200000,1)];
assert(all(isfinite(q) & q>=0.001 & q<=0.95), ...
 'JTE116:InputDomain','Test input q outside source range.');
source=max(0.25,q-mod(q,0.25));
qGuard=max(q,0.25);
candidate=max(0.25,qGuard-mod(qGuard,0.25));
below=q<0.25;
underfloorOK=all(source(below)==0.25);
untouchedOK=isequal(qGuard(~below),q(~below));
mismatch=typecast(source(:),'uint64')~=typecast(candidate(:),'uint64');
if nargin>0
 diagnostic=struct('q',q,'source',source,'candidate',candidate, ...
  'bitMismatch',mismatch,'underfloorOK',underfloorOK, ...
  'untouchedOK',untouchedOK,'runtime',version, ...
  'syntheticOnly',true,'G5_ACCEPTED',false);
 save(reportFile,'diagnostic','-v7.3');
end
assert(underfloorOK,'JTE116:SubfloorViolation', ...
 'Original command is not 0.25 below q=0.25.');
assert(untouchedOK,'JTE116:AboveFloorMutation', ...
 'All source q >= 0.25 must be unchanged.');
assert(~any(mismatch),'JTE116:MATLAB_DOUBLE_MISMATCH', ...
 'Guarded and source commands differ in double bits.');
fprintf('JTE116_GUARD025_CANARY_PASS cases=%d sourceDoubleBitwiseEqual=1 noSimulinkRun=1 G5_ACCEPTED=false\n',numel(q));
end
