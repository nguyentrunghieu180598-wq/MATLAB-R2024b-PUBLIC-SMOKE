function spec=BTMS_M3_instrument(m,ports,actuator,folder)
% Runtime observation metadata only. No save_system, compile or simulation.
names={'m3Core','m3Held','m3Y','m3T312'};spec=struct;
for k=1:4
 set_param(ports(k),'DataLogging','on','DataLoggingNameMode','Custom','DataLoggingName',names{k},...
  'DataLoggingLimitDataPoints','on','DataLoggingMaxPoints','2','DataLoggingDecimateData','off');
end
assert(isempty(get_param(m,'StartFcn')),'M3:Callback','Unexpected preexisting StartFcn.');
set_param(m,'SignalLogging','on','SignalLoggingName','m3Signals',...
 'SaveState','on','StateSaveName','m3States','SaveFormat','Dataset',...
 'SaveTime','on','TimeSaveName','m3Time','SaveFinalState','on','SaveOperatingPoint','on',...
 'FinalStateName','m3FinalOP','LimitDataPoints','on','MaxDataPoints','2',...
 'StartFcn','BTMS_M3_events(''start'');');
spec.phaseFile=fullfile(folder,'PHASE_NATIVE.csv');
BTMS_M3_events('init',actuator,spec.phaseFile);
spec.names=names;
end
