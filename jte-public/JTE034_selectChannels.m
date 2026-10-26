function selection=JTE034_selectChannels(t,Ttrue_K,window_s)
% Pre-register hot/mid/cold channels ONLY from unbiased B0L simulation.
% Means computed by time integral over specified final window, not sample mean.
% Test candidate in MATLAB R2024b; no bias outcome is used here.
if nargin<3,window_s=600;end
t=double(t(:));T=double(Ttrue_K);
assert(numel(t)>=2 && all(isfinite(t)) && all(diff(t)>0), 'Invalid baseline time');
assert(size(T,1)==numel(t) && size(T,2)>=3 && all(isfinite(T(:))),...
    'Require unbiased N x >=3 temperature array');
validateattributes(window_s,{'numeric'},{'scalar','real','positive','finite'});
assert(t(end)-t(1)>=window_s,'Window exceeds baseline horizon');
start=t(end)-window_s;
ix=find(t>start);
assert(~isempty(ix),'No baseline samples in selection interval');
% Interpolation only to the exact window START for thermal traces; no extrapolation.
Ts=interp1(t,T,start,'linear');
tw=[start;t(ix)]; X=[Ts;T(ix,:)];
means=trapz(tw,X,1)/window_s;
indices=(1:size(T,2))';
[~,ordering]=sortrows([-means(:),indices],[1 2]);
selection=struct('hotIndex',ordering(1), ...
    'middleIndex',ordering(ceil(numel(ordering)/2)), ...
    'coldIndex',ordering(end), ...
    'windowStart_s',start,'windowEnd_s',t(end), ...
    'means_K',means,'descendingIndices',ordering(:)', ...
    'tiePolicy','ascending channel index breaks exact mean ties', ...
    'status','CANDIDATE_BASELINE_SELECTION_NOT_G6_ACCEPTED');
end
