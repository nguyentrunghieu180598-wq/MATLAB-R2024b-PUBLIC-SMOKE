function u=JTE094_quantizerCandidate(q)
% WORK candidate, not the missing Chat JTE094_ORACLE_TESTS.m.
% Valid only for double q AFTER unchanged source saturation [0.001,0.95].
% Same final observable levels/ties as max(.25,q-mod(q,.25)).
% Experimental derivative only; never edit the pinned vendor.
assert(isa(q,'double')&&all(isfinite(q(:)))&&all(q(:)>=.001&q(:)<=.95),...
 'JTE094:CandidateDomain','JTE094 assertion failed: CandidateDomain');
u=.25+.25*double(q>=.5)+.25*double(q>=.75);
end
