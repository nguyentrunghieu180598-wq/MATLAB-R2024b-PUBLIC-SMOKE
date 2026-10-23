function report = JTE2026selftest()
% G0 algebraic checks only: NOT Simulink compile/thermal simulation.
rng(20261023,'twister');
checks=0;
for n=2:24
    for trial=1:120
        v=273.15 + 10 + 70*rand(n,1); j=randi(n); beta=5*rand;
        [v2,e]=JTE2026bias(v,j,-beta); checks=checks+1;
        assert(all(abs(v2([1:j-1,j+1:end])-v([1:j-1,j+1:end]))<eps));
        assert(abs(v2(j)-(v(j)-beta))<1e-10);
        assert(abs(e.TmaxMeas-max(v2))<1e-11);
        assert(abs(e.TminMeas-min(v2))<1e-11);
        assert(e.TmaxMeas<=e.TmaxTrue+1e-10);
        assert(e.TminMeas<=e.TminTrue+1e-10);
        [~,z]=JTE2026bias(v,j,0); checks=checks+1;
        assert(z.TmaxMeas==z.TmaxTrue && z.TminMeas==z.TminTrue);
    end
end
v=[320;315;300]; [~,e]=JTE2026bias(v,1,-9);
assert(abs((e.TmaxTrue-e.TmaxMeas)-5)<1e-10); checks=checks+1;
[~,e]=JTE2026bias(v,3,-9);
assert(e.TmaxTrue==e.TmaxMeas); checks=checks+1;
report = struct('passed',true,'numericCases',checks,'type','ALGEBRA_ONLY');
fprintf('MATLAB algebra self-test PASS: %d numeric checks. No Simulink run.\n',checks);
end
