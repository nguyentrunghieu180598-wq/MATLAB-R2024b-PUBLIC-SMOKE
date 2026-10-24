function [t,x]=JTE056normalize(time,data,isTimeFirst)
% No sorting, deduplication, interpolation, resampling or value conversion.
validateattributes(time,{'double'},{'real','vector','nonempty','finite'});
validateattributes(data,{'double'},{'real','nonempty','finite'});
validateattributes(isTimeFirst,{'logical'},{'scalar'});
t=time(:); n=numel(t);
assert(all(diff(t)>=0),'JTE056:TimeReversal','Native timestamps reverse.');
sz=size(data); nd=ndims(data);
if n==1
    x=reshape(data,1,[]);
elseif isTimeFirst
    assert(size(data,1)==n,'JTE056:TimeShape','First dimension must be time.');
    x=reshape(data,n,[]);
else
    % timeseries.IsTimeFirst is authoritative even if dimensions are equal.
    assert(sz(end)==n,'JTE056:TimeShape','Last dimension must be time.');
    x=reshape(permute(data,[nd,1:(nd-1)]),n,[]);
end
assert(size(x,1)==n,'JTE056:TimeShape','Native row count changed.');
end
