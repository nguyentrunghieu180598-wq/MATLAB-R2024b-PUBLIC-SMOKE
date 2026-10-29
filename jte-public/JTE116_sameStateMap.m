function ok=JTE116_sameStateMap(a,b)
ok=false;[ka,ia]=sort({a.key});[kb,ib]=sort({b.key});
if ~isequal(ka,kb),return;end
for k=1:numel(ia)
 if a(ia(k)).time~=0||b(ib(k)).time~=0||~isequaln(a(ia(k)).value,b(ib(k)).value),return;end
end
ok=true;
end
