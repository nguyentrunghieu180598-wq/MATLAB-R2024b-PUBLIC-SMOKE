function S=BTMS_WK08_sparseSets(n)
% Fixed physical cell-order positions; no temperature/rank/results argument.
assert(ismember(n,[312 16 8]),'WK08:SensorCount','Use 312,16,8.');
csv=fullfile(fileparts(mfilename('fullpath')),'WK08_sparse_sets.csv');
t=readtable(csv);S=t.channel(t.sensor_count==n)';
assert(numel(S)==n && isequal(S,unique(S)) && all(S>=1 & S<=312), ...
 'WK08:CSV','Invalid committed sensor map.');
end
