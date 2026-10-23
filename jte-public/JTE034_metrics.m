function R = JTE034_metrics(B, S, opts)
% JTE034_metrics - paper 1: audited POSTPROCESSING ONLY, no plant/controller edits.
% Candidate MATLAB R2024b: not claimed runtime verified until Work executes.
% B: struct time_s [N,1], Ttrue_K [N,n], u_norm [N,1] (unbiased baseline)
% S: same plus Tmeas_K [N,n] (single-channel biased closed-loop study)
% opts required: channelIndex, bias_K (<=0), commandSemantics
%     'continuous_linear' or 'verified_zoh'.
% opts optional: matchedInputsVerified, G5Accepted, temperatureUnitVerifiedK,
%     pumpLinkVerified, pumpScale_W, thermalLimit_K, loggedTmaxTrue_K,
%     loggedTmaxMeasured_K.
% B and S must ALREADY be aligned on identical, audited timestamps.
% No time resampling, extrapolation or unit conversion is performed here.
if nargin ~= 3 || ~isstruct(opts) || ~isscalar(opts)
    error('JTE034:Config','Provide scalar opts struct');
end
needed={'channelIndex','bias_K','commandSemantics'};
for q=1:numel(needed)
    assert(isfield(opts,needed{q}),'JTE034:MissingOption %s',needed{q});
end
requireFields(B,{'time_s','Ttrue_K','u_norm'},'B');
requireFields(S,{'time_s','Ttrue_K','Tmeas_K','u_norm'},'S');
t=double(S.time_s(:));tb=double(B.time_s(:));
assert(numel(t)>=2 && isequal(size(t),size(tb)) && all(isfinite(t)) && ...
    all(diff(t)>0) && t(end)>t(1), 'JTE034:InvalidTime');
assert(isequal(t,tb),'JTE034:TimeGridMismatch; Work must align audited raw traces first');
T=double(S.Ttrue_K); Tm=double(S.Tmeas_K); Tb=double(B.Ttrue_K);
u=double(S.u_norm(:));ub=double(B.u_norm(:));
n=numel(t);
assert(ismatrix(T) && size(T,1)==n && size(T,2)>=2, 'JTE034:TtrueShape');
assert(isequal(size(T),size(Tm),size(Tb)),'JTE034:TemperatureShapes');
assert(numel(u)==n && numel(ub)==n,'JTE034:CommandShape');
assert(all(isfinite(T(:))) && all(isfinite(Tm(:))) && ...
       all(isfinite(Tb(:))) && all(isfinite(u)) && all(isfinite(ub)), ...
       'JTE034:InvalidValue');
validateattributes(opts.channelIndex,{'numeric'},{'scalar','positive','integer'});
validateattributes(opts.bias_K,{'numeric'},{'scalar','real','finite'});
assert(opts.bias_K<=0 && opts.channelIndex<=size(T,2),'JTE034:FaultConfiguration');
mode=char(opts.commandSemantics);
assert(ismember(mode,{'continuous_linear','verified_zoh'}), ...
       'JTE034:CommandSemanticsUnknown; prove ZOH/continuity first');
% Don't take a normalized command's physical units on faith.
commandUnitVerified=logicalOption(opts,'commandNormVerified',false);
if commandUnitVerified
    assert(all(u>=-1e-10 & u<=1+1e-10) && ...
           all(ub>=-1e-10 & ub<=1+1e-10),'JTE034:CommandRange');
end
j=opts.channelIndex; b=opts.bias_K;
TmExpected=T;TmExpected(:,j)=TmExpected(:,j)+b;
selectorTol=64*eps(max(1,max(abs(T(:)))));
injectionResidual=max(abs(Tm(:)-TmExpected(:)));
assert(injectionResidual<=selectorTol,'JTE034:BiasOracleMismatch');

% D3: exact algebraic identity at the SAME study state, not cross-run dynamics.
other=[1:j-1 j+1:size(T,2)];
gap=T(:,j)-max(T(:,other),[],2);
lossPred=min(abs(b),max(0,gap));
trueMax=max(T,[],2); measuredMax=max(Tm,[],2);
lossActual=trueMax-measuredMax;
maskResidual=max(abs(lossPred-lossActual));
assert(maskResidual<=selectorTol,'JTE034:MaxSelectorIdentityFailed');
if isfield(opts,'loggedTmaxTrue_K')
    v=double(opts.loggedTmaxTrue_K(:));
    assert(numel(v)==n && all(isfinite(v)) && ...
        max(abs(v-trueMax))<=selectorTol,'JTE034:LoggedTrueMaxMismatch');
end
if isfield(opts,'loggedTmaxMeasured_K')
    v=double(opts.loggedTmaxMeasured_K(:));
    assert(numel(v)==n && all(isfinite(v)) && ...
        max(abs(v-measuredMax))<=selectorTol,'JTE034:LoggedMeasuredMaxMismatch');
end
baseMax=max(Tb,[],2);
R=struct();
R.status='DIAGNOSTIC_ONLY_UNTIL_G5_AND_PROVENANCE_ARE_ACCEPTED';
R.horizon_s=[t(1),t(end)];R.nSamples=n;R.nSensorChannels=size(T,2);
R.channelIndex=j;R.bias_K=b;R.commandSemantics=mode;
R.unitTemperature='K, UNVERIFIED unless temperatureUnitVerifiedK=true';
R.unitCommand='normalized 0..1, UNVERIFIED unless commandNormVerified=true';
R.algebraBiasResidual_K=injectionResidual;
R.selectorIdentityResidual_K=maskResidual;
R.selectorLossPeak_K=max(lossActual);
R.selectorLossPeakOverBias_fraction=NaN;
if b~=0,R.selectorLossPeakOverBias_fraction=max(lossActual)/abs(b);end
% Percent of simulated time Max T is UNAFFECTED by fault (not fault-detection rate).
% Boolean trapz is an approximation, since transition instants may lie between samples.
R.selectorUnaffectedTimeFraction_est=NaN;
R.selectorAffectedTimeFraction_est=NaN;
if b~=0
    R.selectorUnaffectedTimeFraction_est=trapz(t,double(abs(lossActual)<=selectorTol))/(t(end)-t(1));
    R.selectorAffectedTimeFraction_est=1-R.selectorUnaffectedTimeFraction_est;
end
R.selectorFractionMethod='trapezoid_on_sampled_boolean: transition-time approximate';
% D5: closed-loop outcomes referenced to MATCHED baseline (not masking identity).
R.TmaxPeakBaseline_K=max(baseMax);
R.TmaxPeakStudy_K=max(trueMax);
R.deltaPeakOverRun_K=R.TmaxPeakStudy_K-R.TmaxPeakBaseline_K;
R.maxInstantaneousTmaxIncrease_K=max(trueMax-baseMax);
R.minInstantaneousTmaxChange_K=min(trueMax-baseMax);
R.maxSpatialSpreadStudy_K=max(max(T,[],2)-min(T,[],2));
R.maxAbsCommandDifference=max(abs(u-ub));
R.Ju_absDifference_s=integrateAbsDifference(t,u-ub,mode);
R.integralCommandBaseline_s=integrate(t,ub,mode);
R.integralCommandStudy_s=integrate(t,u,mode);
R.commandIntegralMethod=mode;

% Optional model pump estimate only after provenance AND relationship P=scale*u verified.
R.pumpEnergyBaseline_J=NaN;R.pumpEnergyStudy_J=NaN;
R.deltaPumpEnergy_J=NaN;
if logicalOption(opts,'pumpLinkVerified',false)
    assert(commandUnitVerified,'JTE034:PumpCommandMustBeVerified');
    assert(isfield(opts,'pumpScale_W'),'JTE034:MissingPumpScale');
    validateattributes(opts.pumpScale_W,{'numeric'},{'scalar','finite','nonnegative'});
    R.pumpEnergyBaseline_J=opts.pumpScale_W*R.integralCommandBaseline_s;
    R.pumpEnergyStudy_J=opts.pumpScale_W*R.integralCommandStudy_s;
    R.deltaPumpEnergy_J=R.pumpEnergyStudy_J-R.pumpEnergyBaseline_J;
end
R.pumpDisclaimer='MathWorks-model assumption only; not vehicle measurement';
% Thermal limit optional. Linear interpolation of sampled Tmax assumed; not physical certification.
R.overLimitDurationBaseline_s=NaN;R.overLimitDurationStudy_s=NaN;
if isfield(opts,'thermalLimit_K') && ~isempty(opts.thermalLimit_K)
    validateattributes(opts.thermalLimit_K,{'numeric'},{'scalar','finite','real'});
    R.overLimitDurationBaseline_s=aboveLimitPiecewiseLinear(t,baseMax,opts.thermalLimit_K);
    R.overLimitDurationStudy_s=aboveLimitPiecewiseLinear(t,trueMax,opts.thermalLimit_K);
end
R.overLimitMethod='linear-between-logged-extrema crossing estimate';
R.unitsVerified=logicalOption(opts,'temperatureUnitVerifiedK',false) && ...
                commandUnitVerified;
R.matchedInputsVerified=logicalOption(opts,'matchedInputsVerified',false);
R.G5Accepted=logicalOption(opts,'G5Accepted',false);
if R.unitsVerified && R.matchedInputsVerified && R.G5Accepted
    R.status='METRICS_COMPUTED__SCIENTIFIC_REVIEW_STILL_REQUIRED';
end
end

function y=integrateAbsDifference(t,d,mode)
% Exact integral of |piecewise-linear command difference|; split sign crossings.
if strcmp(mode,'verified_zoh')
    y=sum(diff(t).*abs(d(1:end-1)));
    return;
end
a=d(1:end-1);b=d(2:end);dt=diff(t);
area=dt.*(abs(a)+abs(b))/2;
cross=(a<0 & b>0) | (a>0 & b<0);
area(cross)=dt(cross).*(a(cross).^2+b(cross).^2)./(2*(abs(a(cross))+abs(b(cross))));
y=sum(area);
end

function y=integrate(t,x,mode)
if strcmp(mode,'verified_zoh')
    y=sum(diff(t).*x(1:end-1));
else
    y=trapz(t,x);
end
end
function seconds=aboveLimitPiecewiseLinear(t,y,threshold)
seconds=0;
for k=1:numel(t)-1
    a=y(k)-threshold;b=y(k+1)-threshold;dt=t(k+1)-t(k);
    if a>0 && b>0,seconds=seconds+dt;
    elseif a<=0 && b<=0,continue;
    elseif a>0 && b<=0
        if a==b,continue;end
        seconds=seconds+dt*a/(a-b);
    elseif a<=0 && b>0
        if a==b,continue;end
        seconds=seconds+dt*b/(b-a);
    end
end
end
function v=logicalOption(opts,name,default)
if isfield(opts,name)
    v=opts.(name);
    assert(islogical(v) && isscalar(v),'JTE034:OptionMustBeLogical %s',name);
else
    v=default;
end
end
function requireFields(s,fields,label)
assert(isstruct(s) && isscalar(s),'JTE034:InputStruct %s',label);
for k=1:numel(fields)
    assert(isfield(s,fields{k}),'JTE034:MissingField %s.%s',label,fields{k});
end
end
