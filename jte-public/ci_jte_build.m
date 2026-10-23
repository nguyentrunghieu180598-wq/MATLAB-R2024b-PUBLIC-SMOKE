function ci_jte_build()
% CI gate for cleared PUBLIC MathWorks-reference-only code.
% No private model files, unpublished data, paper material or study results.
assert(strcmp(version('-release'),'2024b'),'R2024b required');
addpath(fullfile(pwd,'jte-public'));
reports=fullfile(pwd,'reports');
if ~isfolder(reports),mkdir(reports);end
diary(fullfile(reports,'jte-build-gates.log'));diary on;
d=onCleanup(@()diary('off')); %#ok<NASGU>
r=JTE2026selftest();
assert(r.passed && strcmp(r.type,'ALGEBRA_ONLY'),'Algebra selftest not PASS');
fprintf('G1 algebra selftest PASS: %d checks\n',r.numericCases);
root=fullfile(pwd,'vendor-pack');
projectFile=fullfile(root,'batteryExamplesProjectSetup.prj');
assert(isfile(projectFile),'Pinned upstream project absent');
p=openProject(projectFile);
closePrj=onCleanup(@()safeCloseProject(p)); %#ok<NASGU>
info=JTE2026preflight(root);
fprintf('G1 source preflight hash: %s\n',info.originalSHA256);
generatedDir=fullfile(pwd,'generated');
models=JTE2026build(root,generatedDir);
fprintf('G3 generated models: %s / %s\n',models.baseline,models.study);
g1=JTE2026inspectGraph(models.baseline,false);
g2=JTE2026inspectGraph(models.study,true);
assert(g1.PASS_GRAPH && g2.PASS_GRAPH,'Graph audit not PASS');
c1=JTE2026compile(models.baseline);
c2=JTE2026compile(models.study);
assert(c1.updated && c2.updated,'Compile/update not PASS');
report=struct('algebraNumericCases',r.numericCases, ...
 'sourceSHA256',info.originalSHA256, ...
 'baselineSHA256',c1.fileSHA256,'studySHA256',c2.fileSHA256, ...
 'matlab',version,'status','G3_MODEL_BUILD_COMPILE_ONLY_NOT_SIMULATED');
save(fullfile(reports,'jte-build-compile-receipt.mat'),'report');
fprintf('JTE generated public models BUILD+COMPILE PASS. B0/C0 not run.\n');
end
function safeCloseProject(p)
try,close(p);catch,end
end
