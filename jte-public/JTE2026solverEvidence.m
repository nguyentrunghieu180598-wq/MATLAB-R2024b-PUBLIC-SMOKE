function evidence=JTE2026solverEvidence(folderCoarse,folderFine,evidenceFile)
% Cross-compare each physical model under DIFFERENT solver tolerances.
% Save real MATLAB evidence only; no default numeric tolerance.
coarse=load(fullfile(folderCoarse,'JTE2026B0C0raw.mat'),'B','C','receipt');
fine=load(fullfile(folderFine,'JTE2026B0C0raw.mat'),'B','C','receipt');
a=coarse.receipt;b=fine.receipt;
assert(a.modelRunSuccess && b.modelRunSuccess,'Both pairs must run successfully.');
assert(strcmp(a.B0L_sha,b.B0L_sha) && strcmp(a.C0_sha,b.C0_sha), ...
    'Different SLX hashes: not a solver sensitivity comparison.');
assert(a.horizon_s==b.horizon_s,'Different horizons.');
params={'RelTol','AbsTol','MaxStep','Solver'};
changed=false;
for k=1:numel(params)
    changed=changed || ~strcmp(a.solverConfig.(params{k}), b.solverConfig.(params{k}));
end
assert(changed,'Numerical solver configuration unchanged; not independent evidence.');
names={'jteTmaxTrue','jteTminTrue','jteUcore','jteAmbient'};
for m=1:2
    if m==1, ref=coarse.B; alt=fine.B; key='Baseline';
    else, ref=coarse.C; alt=fine.C; key='Study'; end
    for k=1:numel(names)
      [t1,x1]=JTE2026timeseries(ref,names{k});
      [t2,x2]=JTE2026timeseries(alt,names{k});
      v(m,k)=JTE2026compareTraces(t1,x1,t2,x2,[key '_' names{k}]); %#ok<AGROW>
    end
end
evidence=struct('created',datestr(now,31),'B0L_sha',a.B0L_sha, ...
    'C0_sha',a.C0_sha,'horizon_s',a.horizon_s, ...
    'configCoarse',a.solverConfig,'configFine',b.solverConfig, ...
    'comparisons',v, ...
    'maxTempSolverDeltaK',max([v(1,1).maxAbs,v(1,2).maxAbs, ...
      v(2,1).maxAbs,v(2,2).maxAbs]), ...
    'maxCommandSolverDelta',max([v(1,3).maxAbs,v(2,3).maxAbs]), ...
    'maxAmbientSolverDeltaK',max([v(1,4).maxAbs,v(2,4).maxAbs]), ...
    'status','REAL_RUNS_COMPARED_REVIEW_REQUIRED');
assert(~isfile(evidenceFile),'No overwriting solver evidence allowed.');
save(evidenceFile,'evidence');
fprintf('Solver evidence written, REVIEW REQUIRED: %s\n',evidenceFile);
end
