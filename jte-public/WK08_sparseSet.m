function S=WK08_sparseSet(count)
% Fixed geometry only. No baseline temperatures or rank selector accepted here.
assert(any(count==[312 16 8]),'WK08:Count','Invalid sensor count.');
if count==312,S=1:312;return;end
repo=fileparts(fileparts(mfilename('fullpath')));
t=readtable(fullfile(repo,'actuator-amendment','WK08_sparse_sets.csv'));
S=sort(t.channel_index(t.set_size==count))';
assert(numel(S)==count&&numel(unique(S))==count,'WK08:CSV','Malformed sensor CSV.');
end
