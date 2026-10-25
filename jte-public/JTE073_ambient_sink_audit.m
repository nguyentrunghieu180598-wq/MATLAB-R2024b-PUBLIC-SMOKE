function JTE073_ambient_sink_audit()
% Source-only structural proof of ALL destinations of source Constant3.
% No simulation, no confidential temperature results.
assert(strcmp(version('-release'),'2024b'),'JTE073:Release');
root=pwd;vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));clean=onCleanup(@()closeQuiet(p)); %#ok<NASGU>
src=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
assert(strcmp(JTE2026sha256(src),'0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0'),'JTE073:WrongVendor');
load_system(src);
model=bdroot('Battery_Pack_Thermal_Management');
block=[model '/Constant3'];
assert(getSimulinkBlockHandle(block)~=-1,'JTE073:NoConstant');
ph=get_param(block,'PortHandles');
assert(numel(ph.Outport)==1,'JTE073:BadOutputs');
ln=get_param(ph.Outport(1),'Line');
assert(ln~=-1,'JTE073:NotConnected');
dest=get_param(ln,'DstPortHandle');
assert(~isempty(dest),'JTE073:Disconnected');
fprintf('JTE073_SOURCE_CONSTANT3_DESTINATIONS=%d\n',numel(dest));
for k=1:numel(dest)
 parent=get_param(dest(k),'Parent');
 typ=get_param(parent,'BlockType');
 fprintf('JTE073_SOURCE_CONSTANT3_DEST_%d_REL=%s TYPE=%s\n',k,erase(parent,[model '/']),typ);
end
fprintf('JTE073_AMBIENT_GRAPH_AUDIT_SOURCE_ONLY_PASS\n');
close_system(model,0);
end
function closeQuiet(p)
try,close(p);catch,end
end
