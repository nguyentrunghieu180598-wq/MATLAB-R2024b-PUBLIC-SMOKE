function dictionary=JTE043_instrumentNative(mdl)
% Read-only logger branches on an existing JTE derivative only.
assert(ismember(mdl,{'JTE2026B0L','JTE2026LocalBias'}),'JTE043:DerivativeOnly');
bc=[mdl '/Battery Control']; f=[bc '/FlwR_calc']; filt=[bc '/sensor dynamics 1'];
pump=[bc '/Pump power calc']; reducer=[bc '/min-max T'];
fh=get_param(f,'PortHandles'); hh=get_param(filt,'PortHandles');
ph=get_param(pump,'PortHandles'); rh=get_param(reducer,'PortHandles');
assert(src(hh.Inport(1))==fh.Outport(1),'JTE043:FilterInput');
assert(src(ph.Inport(1))==hh.Outport(1),'JTE043:PumpAfterFilter');
% Root P converter explicitly consumes power in J/s in the pinned model.
assert(ismember(get_param([mdl '/P'],'Unit'),{'J/s','W'}),'JTE043:PowerUnitSource');
addLogger(bc,hh.Outport(1),'JTE Native Filtered','jteUfiltered');
addLogger(bc,ph.Outport(1),'JTE Native Pump Power','jtePumpPower');
blocks=find_system(bc,'LookUnderMasks','all','FollowLinks','off','BlockType','ToWorkspace');
dictionary=struct('variable',{},'path',{},'source',{},'saveFormat',{},'decimation',{},'sampleTime',{},'maxDataPoints',{});
for k=1:numel(blocks)
 b=blocks{k};set_param(b,'SaveFormat','Timeseries','Decimation','1','SampleTime','-1','MaxDataPoints','inf');
 h=get_param(b,'PortHandles'); sp=src(h.Inport(1));
 dictionary(end+1)=struct('variable',get_param(b,'VariableName'),'path',b, ...
 'source',get_param(sp,'Parent'),'saveFormat',get_param(b,'SaveFormat'), ...
 'decimation',get_param(b,'Decimation'),'sampleTime',get_param(b,'SampleTime'), ...
 'maxDataPoints',get_param(b,'MaxDataPoints')); %#ok<AGROW>
end
for k=1:numel(dictionary)
 if strcmp(dictionary(k).variable,'jteUcore')
  assert(strcmp(dictionary(k).source,f),'JTE043:CoreNotPrefilter');
 end
end
assert(strcmp(get_param([reducer '/MinMax2'],'Function'),'min'),'JTE043:FirstExtremumNotMin');
assert(strcmp(get_param([reducer '/MinMax3'],'Function'),'max'),'JTE043:SecondExtremumNotMax');
% Raw extraction must copy each timeseries Time/Data without interpolation,
% sorting, unique(), squeeze(), decimation or merging clocks.
end
function p=src(in)
ln=get_param(in,'Line');assert(ln~=-1);p=get_param(ln,'SrcPortHandle');
end
function addLogger(bc,port,name,var)
b=[bc '/' name];assert(getSimulinkBlockHandle(b)==-1);
add_block('simulink/Sinks/To Workspace',b,'VariableName',var,'SaveFormat','Timeseries');
h=get_param(b,'PortHandles');add_line(bc,port,h.Inport(1),'autorouting','on');
end
