function JTE094_idealTFOracle()
% Independent continuous-time transfer-function mathematical oracle:
% tau*dy/dt + y = u_core, for u_core(t) == 0.25, tau=0.001 s.
tau = 1e-3;
t = linspace(0, 0.02, 1000)';
y0 = 0.4;
yideal = 0.25 + (y0 - 0.25)*exp(-t/tau);
assert(all(yideal <= y0 + 1e-12) && all(yideal >= 0.25 - 1e-12));
assert(all(diff(yideal) <= 1e-12), 'JTE094:IdealTFNonmonotone','JTE094 assertion failed: IdealTFNonmonotone');
assert(abs(yideal(end)-0.25) < 1e-9, 'JTE094:IdealTFNotSettled','JTE094 assertion failed: IdealTFNotSettled');
fprintf('JTE094_IDEAL_TF_ANALYTICAL_PASS\n');

end
