function ci_jte043_controller_native()
% Metadata/source-only publication. Real pack values never enter public artifacts.
root=pwd;safe=fullfile(root,'jte043-safe-metadata');mkdir(safe);
try
 captured=evalc('receipt=runAudit(root);'); %#ok<NASGU>
 fid=fopen(fullfile(safe,'receipt.json'),'w');assert(fid>=0);
 fprintf(fid,'%s',jsonencode(receipt));fclose(fid);
 fprintf('JTE043_SOURCE_CONTROLLER_NATIVE_METADATA_PASS\n');
 fprintf('W43-01/02/03 scope: source compile + synthetic controller + new native logger20s diagnostic; G5 NOT ACCEPTED\n');
 fprintf('SYNTHETIC samples=%d lawResidual=%.17g decompositionResidual=%.17g\n', ...
 receipt.controller.samples,max(receipt.controller.lawMaxAbsResidual),receipt.controller.decompositionMaxAbsResidual);
catch ME
 fprintf('JTE043_SANITIZED_FAILURE identifier=%s\n',ME.identifier);
    for z=1:min(4,numel(ME.stack))
      fprintf('JTE043_FAILURE_SITE name=%s line=%d\n',ME.stack(z).name,ME.stack(z).line);
    end
    for z=1:numel(ME.cause),fprintf('JTE043_CAUSE identifier=%s\n',ME.cause{z}.identifier);end
 % Do not publish captured simulation console, error report, private values or MAT.
 error('JTE043:AuditFailed','Source/native audit failed; no research data published.');
end
end
function receipt=runAudit(root)
assert(strcmp(version('-release'),'2024b'));
vendor=fullfile(root,'vendor-pack');
p=openProject(fullfile(vendor,'batteryExamplesProjectSetup.prj'));
guard=onCleanup(@()closePrj(p)); %#ok<NASGU>
sourceFile=fullfile(vendor,'Models','Battery_Pack_Thermal_Management.slx');
expected='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
assert(strcmp(JTE2026sha256(sourceFile),expected));
controller=JTE043_controllerTest(sourceFile);
fid=fopen(fullfile(root,'jte043-safe-metadata','controller_only.json'),'w');assert(fid>=0);
fprintf(fid,'%s',jsonencode(struct('status','CONTROLLER_SYNTHETIC_PASS_ONLY_NATIVE_PENDING','sourceSHA256',expected,'controller',controller)));fclose(fid);
files=JTE2026build(vendor,fullfile(root,'jte043-ephemeral-models'));
load_system(files.study);mdl='JTE2026LocalBias';
dictionary=JTE043_instrumentNative(mdl);
bc=[mdl '/Battery Control'];
assert(strcmp(get_param([mdl '/Constant3'],'SampleTime'),'inf'));
assert(strcmp(get_param([bc '/Ambient'],'Unit'),'K'));
lawBefore=graphSignature([bc '/FlwR_calc']);
filterDen=get_param([bc '/sensor dynamics 1'],'Denominator');
assert(isequal(str2num(filterDen),[1e-3 1])); %#ok<ST2NM>
set_param(mdl,'ReturnWorkspaceOutputs','on');
save_system(mdl,files.study);
% Compile NEW native logger configuration, not a re-run of old G1-G4 gate.
feval(mdl,[],[],[],'compile');
compiled=struct();
for k=1:numel(dictionary)
 b=dictionary(k).path;
 compiled.(dictionary(k).variable)=struct('dimensions',get_param(b,'CompiledPortDimensions'), ...
 'sampleTime',{sampleText(get_param(b,'CompiledSampleTime'))});
end
compiled.coreSampleTime=sampleText(get_param([bc '/FlwR_calc'],'CompiledSampleTime'));
feval(mdl,[],[],[],'term');
input=Simulink.SimulationInput(mdl);
input=input.setModelParameter('StartTime','0','StopTime','20');
input=input.setVariable('jteChannelIndex',1,'Workspace',mdl);
input=input.setVariable('jteBiasK',0,'Workspace',mdl);
out=sim(input);
names={dictionary.variable};
records=JTE043_nativeCapture(out,names);
shapeMap=struct();
for k=1:numel(names)
 name=names{k};r=records.(name);
 % Counts/dimensions/coverage only; NO temperature, command, power, or time arrays published.
 t=r.Time(:);
 coverage=numel(t)>1&&abs(t(1))<1e-8&&abs(t(end)-20)<1e-8;
 shapeMap.(name)=struct('timeShape',size(r.Time),'dataShape',size(r.Data), ...
 'nLoggedTimes',numel(t),'duplicateTimePairs',sum(diff(t)==0), ...
 'full20sCoverage',coverage,'nativeCopiedWithoutInterpolation',true, ...
 'loggedUnits',r.DataInfo.Units,'IsTimeFirst',r.IsTimeFirst);
 if ~strcmp(name,'jteAmbient'),assert(coverage,'JTE043:NativeCoverage');end
end
assert(isequaln(records.jteTtrue.Time,records.jteTmeas.Time),'JTE043:ZeroBiasClock');
viewTrue=timeRows(records.jteTtrue);viewMeasured=timeRows(records.jteTmeas);
assert(all(isfinite(viewTrue(:)))&&all(isfinite(viewMeasured(:))),'JTE043:InvalidVector','Nonfinite native vector');
assert(isequaln(viewTrue,viewMeasured),'JTE043:ZeroBiasVector','Canonical zero-bias channel views differ');
assert(strcmp(lawBefore,graphSignature([bc '/FlwR_calc'])),'JTE043:ControllerChanged');
assert(strcmp(JTE2026sha256(sourceFile),expected),'JTE043:VendorChanged');
receipt=struct('scope','METADATA_AND_SYNTHETIC_ONLY_G5_NOT_ACCEPTED','matlab',version, ...
 'sourceSHA256',expected,'controller',controller,'loggerDictionary',dictionary, ...
 'compiled',compiled,'nativeShapeMap',shapeMap,'zeroBiasCanonicalViewEqual',true,'canonicalVectorShape',size(viewTrue), ...
 'derivativeSLXSHA256',JTE2026sha256(files.study), ...
 'filterDenominator',filterDen,'pumpPowerUnitEvidence',get_param([mdl '/P'],'Unit'), ...
 'extremaOrder',{{get_param([bc '/min-max T/MinMax2'],'Function'),get_param([bc '/min-max T/MinMax3'],'Function')}}, ...
 'eventCompleteness','Native logger output clocks only; no claim all solver minor/root event sides logged', ...
 'studyAcceptance',false);
clear out records;
close_system(mdl,0);
end
function s=graphSignature(path)
% Internal controller blocks/parameters and endpoint paths; no layout/solver change.
b=find_system(path,'LookUnderMasks','all','FollowLinks','off','Type','Block');
r=cell(size(b));
for k=1:numel(b)
 keys=get_param(b{k},'DialogParameters');values=struct();
 if ~isempty(keys)
  fields=fieldnames(keys);
  for j=1:numel(fields),values.(fields{j})=get_param(b{k},fields{j});end
 end
 r{k}=struct('path',b{k},'type',get_param(b{k},'BlockType'),'parameters',values);
end
s=jsonencode(r);
end
function closePrj(p)
try,close(p);catch,end
end

function x=timeRows(r)
% Canonical comparison view only; raw Time/Data in records remain untouched.
a=double(r.Data);n=numel(r.Time);
if n==1,x=reshape(a,1,[]);
elseif r.IsTimeFirst
 assert(size(a,1)==n,'JTE043:TimeAxis','Declared first time axis mismatch');x=reshape(a,n,[]);
else
 nd=ndims(a);assert(size(a,nd)==n,'JTE043:TimeAxis','Declared last time axis mismatch');
 x=reshape(permute(a,[nd 1:nd-1]),n,[]);
end
end
function out=sampleText(st)
if iscell(st),out=cellfun(@mat2str,st,'UniformOutput',false);else,out=mat2str(st);end
end
