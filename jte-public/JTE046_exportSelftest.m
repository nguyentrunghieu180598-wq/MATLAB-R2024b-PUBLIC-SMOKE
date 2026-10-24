function JTE046_exportSelftest()
% Synthetic storage fixtures only, no MATLAB plant simulation or real MAT data.
work=tempname;mkdir(work);guard=onCleanup(@()rmdir(work,'s')); %#ok<NASGU>
t=[0;1;1;2];X=[300 299 298;301 300 299;302 301 300;303 302 301];
r=struct();
r.jteTtrue=struct('Time',t,'Data',X,'IsTimeFirst',true);
r.jteTmeas=struct('Time',t,'Data',permute(reshape(X,[4 3 1]),[2 3 1]),'IsTimeFirst',false);
r.jteAmbient=struct('Time',0,'Data',300,'IsTimeFirst',true);
original=r;out=fullfile(work,'export');m=JTE046_exportNative(r,out);
A=readmatrix(fullfile(out,'jteTtrue.csv'));B=readmatrix(fullfile(out,'jteTmeas.csv'));
assert(isequal(A,B)&&isequal(A(:,1),t)&&isequal(A(:,2:end),X),'JTE046:Fixture','Layouts or duplicate rows changed');
assert(isequaln(r,original),'JTE046:Fixture','Native source records mutated');
reject(@()JTE046_exportNative(r,out),'JTE046:Exists');
bad=r;bad.jteTtrue.Time=[0;2;1;3];
reject(@()JTE046_exportNative(bad,fullfile(work,'badclock')),'JTE046:Clock');
assert(~isfolder(fullfile(work,'badclock')));
bad=r;bad.jteTmeas.IsTimeFirst=true;
reject(@()JTE046_exportNative(bad,fullfile(work,'badaxis')),'JTE046:TimeAxis');
assert(~isfolder(fullfile(work,'badaxis')));
amb=m(strcmp({m.variable},'jteAmbient'));v=m(strcmp({m.variable},'jteTtrue'));
assert(amb.nRows==1&&amb.nChannels==1&&v.duplicateTimePairs==1);
assert(~amb.unitVerified&&~v.eventConventionVerified);
fprintf('JTE046 MATLAB NATIVE EXPORT SYNTHETIC PASS: 6 checks; no research data or plant simulation.\n');
end
function reject(f,id)
caught=false;try,f();catch ME,caught=strcmp(ME.identifier,id);end
assert(caught,'JTE046:Fixture','Expected fail-closed validation');
end
