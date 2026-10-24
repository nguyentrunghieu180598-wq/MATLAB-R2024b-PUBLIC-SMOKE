function u=JTE043_law(Tmax_K,Ambient_K)
% Exact algebra of pinned 24.2.1.5 FlwR_calc, subject to compiled regression.
% This is offline analysis; never connect shadow output to the plant.
q=min(0.95,max(0.001,0.1.*(Tmax_K-Ambient_K)));
u=max(0.25,q-mod(q,0.25));
end
