function records=JTE043_nativeCapture(out,names)
% PRIVATE use only for real study data. Never resample, sort or drop duplicates.
records=struct();
for k=1:numel(names)
 sig=out.get(names{k});assert(isa(sig,'timeseries'),'JTE043:NeedNativeTimeseries');
 assert(all(isfinite(sig.Time(:)))&&all(diff(sig.Time(:))>=0),'JTE043:NativeClock');
 record=struct('Time',sig.Time,'Data',sig.Data,'TimeInfo',sig.TimeInfo, ...
 'DataInfo',sig.DataInfo,'IsTimeFirst',sig.IsTimeFirst, ...
 'note','Native logged output times, NOT proof that all solver minor/root events were emitted');
 records.(names{k})=record;
 assert(isequaln(record.Time,sig.Time)&&isequaln(record.Data,sig.Data),'JTE043:NativeCopyChanged');
end
end
