function q=JTE116_completedMajor(s,expected,tf)
% Call ONLY after step(s) returns; expected is s.Time captured BEFORE step.
o=s.SimulationOutput;logs=o.get('jte116Signals');
names={'JTE116ActualInput','JTE116Postfilter','JTE116Q','JTE116QStar','JTE116T312'};
v=cell(1,5);ts=zeros(1,5);
for k=1:5
 e=logs.getElement(names{k});[ts(k),v{k}]=tail(e.Values);
end
ds=o.get('jte116States');ix=[];
for k=1:ds.numElements
 e=ds.getElement(k);
 if e.BlockPath.getLength()==1&&strcmp(char(e.BlockPath.getBlock(1)),tf),ix(end+1)=k;end %#ok<AGROW>
end
assert(numel(ix)==1,'JTE116:Logging','TF state unavailable or ambiguous.');
e=ds.getElement(ix);[tx,x]=tail(e.Values);
assert(all(ts==expected)&&tx==expected&&numel(v{5})==312&&numel(x)==1,...
 'JTE116:Logging','Last output/state clocks do not equal processed prior top-of-step time.');
assert(s.Time>=expected,'JTE116:Logging','Next top-of-step reverses.');
q=struct('time',expected,'processedPriorTime',expected,'nextTopOfStepTime',s.Time,...
 'actualInput',v{1},'core',v{1},'y',v{2},'q',v{3},'qstar',v{4},'T312',v{5},'x',x,...
 'lastSignalTimes',ts,'lastStateTime',tx,'phase','',...
 'coreScope','Core and actual input are the same statically verified source output port. Independent ToWorkspace core is cross-checked in final native data.',...
 'clockScope','Completed-major checkpoint only; other native rows/rejected stages are not certified by this record.');
end
function [t,v]=tail(ts)
t=ts.Time(end);a=ts.Data;N=numel(ts.Time);
if N==1,a=reshape(a,1,[]);
elseif ts.IsTimeFirst,a=reshape(a,N,[]);
else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),N,[]);end
v=a(end,:);
assert(isfinite(t)&&all(isfinite(v)),'JTE116:Logging','Nonfinite checkpoint.');
end
