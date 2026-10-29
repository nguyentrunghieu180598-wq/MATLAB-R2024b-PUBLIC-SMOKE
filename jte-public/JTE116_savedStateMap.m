function v=JTE116_savedStateMap(ds,model)
v=struct('key',{},'time',{},'value',{});
for k=1:ds.numElements
 e=ds.getElement(k);paths=cell(1,e.BlockPath.getLength());
 for j=1:numel(paths),paths{j}=char(e.BlockPath.getBlock(j));end
 [t,x]=JTE056normalize(e.Values.Time,e.Values.Data,e.Values.IsTimeFirst);
 key=strrep([strjoin(paths,'::') '|' char(e.Name)],model,'$ROOT');
 v(end+1)=struct('key',key,'time',t(1),'value',x(1,:)); %#ok<AGROW>
end
assert(numel(unique({v.key}))==numel(v),'JTE116:ModelIC','Duplicate saved-state keys.');
end
