function sampled_gate_native_extract()
% Deserialize saved actual toy only. No model load, compile or simulation.
P=fullfile(pwd,'actuator-review-private');pre=fullfile(P,['BTMS_FEASIBILITY_' getenv('GITHUB_RUN_ID') '_NATIVE']);
S=load(fullfile(P,'SavedToyRaw.mat'),'r');r=S.r;
assert(r.simCount==1&&r.flags.MATLAB_TOY_COMPLETE&&strcmp(r.failure.identifier,'Gate:ToyClock'),'Gate:Source','Wrong saved toy.');
o=r.simulationOutput;specs=r.specs;meta=cell(1,numel(specs));
for j=1:numel(specs)
 s=specs(j);tags={'raw','hold','actuator'};clocks=cell(1,3);parts=cell(1,3);
 for z=1:3
  ts=o.get([s.id '_' tags{z}]);t=ts.Time(:);v=ts.Data;assert(numel(v)==numel(t),'Gate:Scalar','Non-scalar native trace.');v=v(:);
  assert(all(isfinite(t))&&all(isfinite(v))&&all(diff(t)>=0),'Gate:Native','Invalid native trace.');
  file=[pre '_' s.id '_' tags{z} '.csv'];f=fopen(file,'w');assert(f~=-1);fprintf(f,'%.17g,%.17g\n',[t,v]');fclose(f);
  clocks{z}=t;parts{z}=struct('signal',tags{z},'nativeRows',numel(t),'start_s',t(1),'end_s',t(end),...
   'duplicates',sum(diff(t)==0),'dataFile',file,'CSVPrecision','17 significant digits, no interpolation/dedup or clock replacement');
 end
 q=struct('branch',j,'id',s.id,'Ts_s',s.Ts_s,'signals',{parts},...
  'rawHoldTimeExact',isequal(clocks{1},clocks{2}),'rawOutputTimeExact',isequal(clocks{1},clocks{3}),...
  'rawHoldSameLength',numel(clocks{1})==numel(clocks{2}),'rawOutputSameLength',numel(clocks{1})==numel(clocks{3}));
 if q.rawHoldSameLength,q.rawHoldMaxClockDifference_s=max(abs(clocks{1}-clocks{2}));end
 if q.rawOutputSameLength,q.rawOutputMaxClockDifference_s=max(abs(clocks{1}-clocks{3}));end
 meta{j}=q;
end
a=struct('scope','READ_ONLY_ACTUAL_SAVED_TOY','sourceRun','40683965769','runtime',version,'branches',{meta},'originalClockGateStillUnqualified',true,...
 'noNewSimulation',true,'G5Accepted',false);
f=fopen([pre '_CLOCK_DICTIONARY.json'],'w');fprintf(f,'%s',jsonencode(a));fclose(f);
fprintf('SAVED_TOY_NATIVE_EXTRACTION_COMPLETE newSimulation=0 originalGateUnchanged=1 G5_ACCEPTED=false\n');
end
