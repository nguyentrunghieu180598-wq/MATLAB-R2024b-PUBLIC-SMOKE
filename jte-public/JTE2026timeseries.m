function [t,x]=JTE2026timeseries(simOut,name)
% Retrieve logged To Workspace timeseries from SimulationOutput.
try
    sig=simOut.get(name);
catch ME
    error('Missing logged variable %s: %s',name,ME.message);
end
assert(isa(sig,'timeseries'),'Expected timeseries for %s, not %s.',name,class(sig));
t=double(sig.Time(:));
x=double(sig.Data);
assert(all(isfinite(t)) && numel(t)>=2,'Invalid time for %s.',name);
assert(all(diff(t)>0),'Non-increasing time for %s.',name);
assert(all(isfinite(x(:))),'Nonfinite signal %s.',name);
if isvector(x),x=x(:);end
assert(size(x,1)==numel(t),'Signal %s time/data length mismatch.',name);
end
