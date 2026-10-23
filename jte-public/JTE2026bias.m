function [Tmeas, ex] = JTE2026bias(Ttrue, channel, biasK)
% Numeric oracle, independent of Simulink: one fixed channel, K offset.
% Ttrue: vector of temperatures [K]; biasK <= 0 [K].
validateattributes(Ttrue,{'double'},{'real','finite','vector','nonempty'});
validateattributes(channel,{'double'},{'real','finite','scalar','integer','positive'});
validateattributes(biasK,{'double'},{'real','finite','scalar','nonpositive'});
assert(numel(Ttrue)>=2,'Need at least 2 temperature channels.');
assert(channel<=numel(Ttrue),'Channel exceeds vector length.');
Tmeas = Ttrue;
Tmeas(channel) = Tmeas(channel)+biasK;
ex = struct('TmaxTrue',max(Ttrue),'TminTrue',min(Ttrue), ...
    'TmaxMeas',max(Tmeas),'TminMeas',min(Tmeas));
end
