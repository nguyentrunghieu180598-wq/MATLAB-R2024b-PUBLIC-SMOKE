function d=JTE116_nativeData(o,tf,model)
[t,u]=JTE2026timeseries(o,'jteUcore');[ty,y]=JTE2026timeseries(o,'jteFlwR');[tt,T]=JTE2026timeseries(o,'jteTtrue');
logs=o.get('jte116Signals');names={'JTE116ActualInput','JTE116Postfilter','JTE116Q','JTE116QStar','JTE116T312'};
v=cell(1,5);times=cell(1,5);same=isequal(t,ty)&&isequal(t,tt);
for k=1:5,e=logs.getElement(names{k});[times{k},v{k}]=JTE056normalize(e.Values.Time,e.Values.Data,e.Values.IsTimeFirst);same=same&&isequal(t,times{k});end
ds=o.get('jte116States');ix=[];
for k=1:ds.numElements,e=ds.getElement(k);
 if e.BlockPath.getLength()==1&&strcmp(char(e.BlockPath.getBlock(1)),tf),ix(end+1)=k;end %#ok<AGROW>
end
assert(numel(ix)==1,'JTE116:Logging','Native TF state unavailable.');
e=ds.getElement(ix);[tx,x]=JTE056normalize(e.Values.Time,e.Values.Data,e.Values.IsTimeFirst);
d=struct('time',t,'core',u,'output',y,'actualInput',v{1},'loggedOutput',v{2},'q',v{3},'qstar',v{4},...
 'T312',T,'loggedT312',v{5},'state',x,'clocksExact',same&&isequal(t,tx),...
 'initialMap',JTE116_savedStateMap(ds,model),'nativeTimeSemantics','No sorting/deduplication/interpolation; not every native row is an accepted major step.');
end
