function [t,x]=JTE2026timeseries(simOut,name)
% Native reader: preserve every pre/post event row, including equal times.
try
    sig=simOut.get(name);
catch ME
    error('JTE056:MissingSignal','Missing %s: %s',name,ME.message);
end
assert(isa(sig,'timeseries'),'JTE056:WrongLogType','Expected timeseries.');
[t,x]=JTE056normalize(sig.Time,sig.Data,sig.IsTimeFirst);
end
