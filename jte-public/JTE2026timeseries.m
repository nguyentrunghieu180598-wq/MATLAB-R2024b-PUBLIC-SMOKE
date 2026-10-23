function [t,x]=JTE2026timeseries(simOut,name)
% Read Simulink To Workspace timeseries, preserving every recorded value.
% Normalize time dimension to rows; no interpolation or data modification.
try
    sig=simOut.get(name);
catch ME
    error('Missing logged variable %s: %s',name,ME.message);
end
assert(isa(sig,'timeseries'),'Expected timeseries for %s, got %s.',name,class(sig));
t=double(sig.Time(:));
raw=double(sig.Data);
assert(~isempty(t) && all(isfinite(t)), 'Invalid time stamps: %s',name);
if numel(t)>1,assert(all(diff(t)>0),'Non-increasing time for %s',name);end
assert(~isempty(raw) && all(isfinite(raw(:))),'Nonfinite/empty data for %s',name);
nT=numel(t);
sz=size(raw); nd=ndims(raw);
if nT==1
    x=reshape(raw,1,[]);
elseif isvector(raw) && numel(raw)==nT
    x=reshape(raw,nT,1);
elseif size(raw,1)==nT
    x=reshape(raw,nT,[]);
elseif sz(end)==nT
    order=[nd,1:(nd-1)];
    x=reshape(permute(raw,order),nT,[]);
elseif nd==2 && size(raw,2)==nT
    x=raw.';
else
    error('Signal %s cannot identify time dimension: Time=%d, DataSize=%s', ...
        name,nT,mat2str(sz));
end
assert(size(x,1)==nT,'Signal %s normalized time/data mismatch.',name);
end
