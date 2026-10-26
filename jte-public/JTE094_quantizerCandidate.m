function u=JTE094_quantizerCandidate(q)
% REJECTED threshold candidate; synthetic negative-control fixture ONLY.
% Valid only for double q AFTER unchanged source saturation [0.001,0.95].
% NOT equivalent to max(.25,q-mod(q,.25)) near MATLAB double ULP boundaries.
% Do not use for plant control or acceptance; no precision/tolerance workaround.
% Experimental derivative only; never edit the pinned vendor.
assert(isa(q,'double')&&all(isfinite(q(:)))&&all(q(:)>=.001&q(:)<=.95),...
 'JTE094:CandidateDomain','JTE094 assertion failed: CandidateDomain');
u=.25+.25*double(q>=.5)+.25*double(q>=.75);
end
