function JTE036_pump_guard_test()
% Synthetic regression tests; no pack experiment and no study data.
t=[0;1];T=[300 295 290;300 295 290];
B=struct('time_s',t,'Ttrue_K',T,'u_norm',[0.8;0.2]);
S=struct('time_s',t,'Ttrue_K',T,'Tmeas_K',T,'u_norm',[0.2;0.8]);
opts=struct('channelIndex',1,'bias_K',0,'commandSemantics','continuous_linear',...
 'pumpLinkVerified',true,'commandNormVerified',true,'pumpScale_W',500);
caught=false;
try
  JTE034_metrics(B,S,opts);
catch ME
  caught=strcmp(ME.identifier,'JTE034:PumpSignalMismatch');
end
assert(caught,'JTE036:UnsafePumpEnergyShouldFail',...
 'Calculating pump power from jteUcore must be rejected');
opts2=struct('pumpPowerOutputVerified',true,'sampling','verified_zoh');
r=JTE036_pumpEnergyFromLoggedPower([0;10],[100;100],[150;150],opts2);
assert(abs(r.energyBaseline_J-1000)<1e-9 && ...
  abs(r.energyStudy_J-1500)<1e-9 && abs(r.deltaEnergy_J-500)<1e-9);
opts2.pumpPowerOutputVerified=false;
caught=false;
try
 JTE036_pumpEnergyFromLoggedPower([0;10],[100;100],[150;150],opts2);
catch
 caught=true;
end
assert(caught,'JTE036:MissingProvenanceShouldFail');
fprintf('JTE036 SYNTHETIC PUMP SAFETY REGRESSION PASS. NOT STUDY RESULTS.\n');
end
