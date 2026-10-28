function JTE115_guardedLawCanary(reportFile)
% Synthetic numerical-equivalence gate, NOT physical simulation or G5 acceptance.
assert(strcmp(version('-release'),'2024b') && contains(version,'24.2.0.3361896'),'JTE115:Release','JTE115 required invariant failed.');
rngState=rng; restore=onCleanup(@()rng(rngState)); %#ok<NASGU>
q=[0.001;0.249;0.25;0.251;0.374;0.375;0.376;0.499;0.5;0.501;0.749;0.75;0.751;0.95];
for v=[0.25,0.375,0.5,0.75]
 q=[q;v+(-2048:2048)'*eps(v)]; %#ok<AGROW>
end
rng(115,'twister');
q=[q;0.001+(0.95-0.001)*rand(200000,1)];
assert(all(isfinite(q)&q>=0.001&q<=0.95));
old=max(0.25,q-mod(q,0.25));
g=max(q,0.375);
candidate=max(0.25,g-mod(g,0.25));
% Optional private synthetic-only receipt preserves the exact failing inputs.
if nargin>0
 bitMismatch=typecast(old(:),'uint64')~=typecast(candidate(:),'uint64');
 diagnostic=struct('q',q,'original',old,'guarded',candidate,'bitMismatch',bitMismatch,...
  'valueEquality',isequal(old,candidate),'bitEquality',~any(bitMismatch),'runtime',version,...
  'sourceLaw','max(.25,q-mod(q,.25))','guardLaw','max(.25,max(q,.375)-mod(max(q,.375),.25))',...
  'syntheticOnly',true,'physicalSimulation',false,'G5_ACCEPTED',false);
 save(reportFile,'diagnostic','-v7.3');
end
assert(isequal(old,candidate)&&isequal(typecast(old(:),'uint64'),typecast(candidate(:),'uint64')), ...
 'JTE115:MATLAB_DOUBLE_NOT_EQUIVALENT','JTE115 required invariant failed.');
fprintf('JTE115_SOURCE_LAW_CANARY_PASS cases=%d MATLAB=R2024b sourceOutputBitwiseEqual=1\n',numel(q));
fprintf('JTE115_FULL_MODEL_NOT_RUN G5_ACCEPTED=false\n');
end
