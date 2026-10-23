function JTE034_crossing_test()
t=[0;1]; T=[300 295 290;300 295 290];
B=struct('time_s',t,'Ttrue_K',T,'u_norm',[0.8;0.2]);
S=struct('time_s',t,'Ttrue_K',T,'Tmeas_K',T,'u_norm',[0.2;0.8]);
o=struct('channelIndex',1,'bias_K',0,'commandSemantics','continuous_linear');
r=JTE034_metrics(B,S,o);
fprintf('SYNTHETIC_JU_COMPUTED=%.17g EXPECTED=0.3\n',r.Ju_absDifference_s);
assert(abs(r.Ju_absDifference_s-0.3)<1e-12,'JTE034:CrossingAbsoluteArea','Linear commands cross at t=0.5; exact absolute area must be 0.3.');
fprintf('JTE034 CROSSING REGRESSION PASS: SYNTHETIC ONLY\n');
end
