function JTE034_selftest()
% Synthetic tests only: does NOT validate MATLAB Simscape simulations.
t=(0:1:10)';
B=struct('time_s',t, ...
    'Ttrue_K',[300+0*t,295+0*t,290+0*t],...
    'u_norm',0.2+0*t);
S=struct('time_s',t,'Ttrue_K',B.Ttrue_K, ...
    'Tmeas_K',[298+0*t,295+0*t,290+0*t], ...
    'u_norm',0.3+0*t);
o=struct('channelIndex',1,'bias_K',-2,'commandSemantics','continuous_linear', ...
    'temperatureUnitVerifiedK',true,'commandNormVerified',true, ...
    'matchedInputsVerified',true,'G5Accepted',false);
r=JTE034_metrics(B,S,o);
assert(abs(r.selectorLossPeak_K-2)<1e-12);
assert(abs(r.Ju_absDifference_s-1)<1e-12);
assert(abs(r.deltaPeakOverRun_K)<1e-12);
assert(abs(r.selectorUnaffectedTimeFraction_est)<1e-12);
% Bias of a cold channel is completely hidden by Max-selector.
o.channelIndex=3;
S.Tmeas_K=S.Ttrue_K;S.Tmeas_K(:,3)=S.Tmeas_K(:,3)-2;
r=JTE034_metrics(B,S,o);
assert(r.selectorLossPeak_K==0);
assert(r.selectorUnaffectedTimeFraction_est==1);
% ZOH integration must differ from trapezoidal when commands step.
o.channelIndex=1;
o.commandSemantics='verified_zoh';
S.Tmeas_K=S.Ttrue_K;S.Tmeas_K(:,1)=S.Tmeas_K(:,1)-2;
S.u_norm=zeros(size(t));S.u_norm(end)=1;
r=JTE034_metrics(B,S,o);
assert(abs(r.integralCommandStudy_s)<1e-12);
% No invented command semantics permitted.
o.commandSemantics='unknown';
failed=false;
try,JTE034_metrics(B,S,o);catch,failed=true;end
assert(failed,'Unknown command semantics should block');
% Hot/mid/cold indices frozen from B0L only.
sel=JTE034_selectChannels(t,B.Ttrue_K,4);
assert(sel.hotIndex==1 && sel.middleIndex==2 && sel.coldIndex==3);
fprintf('JTE034 SYNTHETIC SELFTEST PASS. No real MATLAB study data evaluated.\n');
end
