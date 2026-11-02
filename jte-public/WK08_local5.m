function WK08_local5(privateRoot,vendorRoot)
% OWNER LOCAL ONLY: fresh private bundle from reviewed Drive source receipt.
% This function executes exactly 5 simulated seconds and never uploads data.
privateRoot=char(java.io.File(privateRoot).getCanonicalPath());
vendorRoot=char(java.io.File(vendorRoot).getCanonicalPath());
assert(isfolder(privateRoot)&&isfolder(vendorRoot),'WK08:Paths','Local bundle/vendor required.');
M=jsondecode(fileread(fullfile(privateRoot,'m2340_manifest.json')));
localLogs=fullfile(privateRoot,'local5logs');assert(~isfolder(localLogs),'WK08:Fresh','Fresh local log directory required.');
mkdir(localLogs);M.privateDir=localLogs;
f=fopen(fullfile(privateRoot,'m2340_manifest.json'),'w');assert(f>=0);
fprintf(f,'%s',jsonencode(M));fclose(f);
WK08_run(privateRoot,vendorRoot,5);
end
