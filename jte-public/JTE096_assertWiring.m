function JTE096_assertWiring(a,b,stage)
% Static public graph diagnostic only: never print masks/state/private arrays.
if isequal(a.connectivity,b.connectivity),return;end
fprintf('JTE096_STATIC_WIRING_DIFFERENCE stage=%s sourceRows=%d derivativeRows=%d\n',stage,size(a.connectivity,1),size(b.connectivity,1));
n=min(size(a.connectivity,1),size(b.connectivity,1));shown=0;
for k=1:n
 if ~isequal(a.connectivity(k,:),b.connectivity(k,:))
  fprintf('JTE096_STATIC_PORT_SOURCE %s\n',jsonencode(a.connectivity(k,:)));
  fprintf('JTE096_STATIC_PORT_DERIVATIVE %s\n',jsonencode(b.connectivity(k,:)));
  shown=shown+1;if shown>=5,break;end
 end
end
error('JTE096:IndependentWiring','Static source/derivative PortConnectivity difference: %s. No compile or simulation acceptance.',stage);
end
