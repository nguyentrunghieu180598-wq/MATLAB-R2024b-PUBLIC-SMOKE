function JTE101_stageA()
% Actual existing native MAT audit only. No model build/compile/simulation.
assert(strcmp(version('-release'),'2024b')&&contains(version,'24.2.0.3361896'),'JTE101:Runtime','Wrong release/update.');
root=fullfile(pwd,'jte101-private');manifest=jsondecode(fileread(fullfile(root,'input_manifest.json')));
pin='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0';
audit=struct('schema','JTE101_STAGE_A_PRIVATE_V1','run',getenv('GITHUB_RUN_ID'),...
 'commit',getenv('GITHUB_SHA'),'sourceSHA256',pin,'accessPreflight','REUSED_40441621436',...
 'simulationRun',false,'G5_ACCEPTED',false,'cases',[],'inputManifest',manifest);
for k=1:numel(manifest.references)
 spec=manifest.references(k);path=fullfile(root,spec.local);
 assert(strcmp(JTE2026sha256(path),spec.sha256),'JTE101:LocalSHA','Reference changed.');
 inventory=whos('-file',path);loaded=load(path);
 assert(isfield(loaded,'record')&&isscalar(loaded.record),'JTE101:Record','Missing scalar record.');
 r=loaded.record;
 required={'schema','caseName','sourceSHA256','load','generatedModelSHA256','solver','units','signalData','clocks','inputOverrides','resolvedVariables'};
 assert(all(isfield(r,required)),'JTE101:Schema','Missing recorded provenance.');
 assert(strcmp(r.schema,'JTE056_NATIVE_V1')&&strcmp(r.caseName,spec.key),'JTE101:Identity','Wrong record schema/case.');
 assert(strcmp(r.sourceSHA256,pin)&&validSHA(r.load.SHA256)&&validSHA(r.generatedModelSHA256),'JTE101:Provenance','Invalid source/load/model provenance.');
 assert(strcmp(r.solver.Solver,'ode23t')&&strcmp(r.solver.LoadInitialState,'off'),'JTE101:Solver','Unexpected original algorithm or initial-state contract.');
 assert(str2double(r.solver.StartTime)==0&&str2double(r.solver.StopTime)==2400,'JTE101:Horizon','Wrong existing horizon.');
 assert(strcmp(r.units.temperature,'K')&&strcmp(r.units.time,'s')&&contains(lower(r.units.jteFlwR),'normalized'),'JTE101:Units','Unqualified signal units.');
 names={'jteTtrue','jteTmaxTrue','jteTminTrue','jteUcore','jteFlwR','jteAmbient'};
 assert(all(isfield(r.signalData,names)),'JTE101:Signals','Missing required native signal.');
 clocks=struct();repeats=struct();
 for j=1:numel(names)
  name=names{j};sig=r.signalData.(name);
  assert(isa(sig.time_s,'double')&&isa(sig.values,'double')&&all(isfinite(sig.time_s(:)))&&all(isfinite(sig.values(:))),'JTE101:NativeType','Bad native values.');
  t=sig.time_s(:);assert(size(sig.values,1)==numel(t)&&all(diff(t)>=0)&&t(1)==0,'JTE101:NativeClock','Invalid native clock/order.');
  if ~strcmp(name,'jteAmbient'),assert(t(end)==2400,'JTE101:NativeEnd','Incomplete nonconstant signal.');end
  clocks.(name)=isequal(t,r.signalData.jteTtrue.time_s(:));
  repeats.(name)=sum(diff(t)==0);
 end
 T=r.signalData.jteTtrue;u=r.signalData.jteUcore;y=r.signalData.jteFlwR;
 assert(size(T.values,2)==312&&size(u.values,2)==1&&size(y.values,2)==1,'JTE101:Dimensions','Wrong native vector dimensions.');
 assert(isequal(u.time_s(:),y.time_s(:))&&isequal(u.time_s(:),T.time_s(:)),'JTE101:ClockAlignment','Existing command/actuator/T clocks differ.');
 stateFound=findTFState(loaded,0);
 tf=y.time_s(:);yv=y.values(:);
 first=find(tf>=330&tf<=338&abs(yv-.25)>.005);
 second=find(tf>2000&abs(yv-.25)>.005);
 item=struct('key',spec.key,'schemaPass',true,'inventory',{inventory},'solver',r.solver,...
  'units',r.units,'load',r.load,'generatedModelSHA256',r.generatedModelSHA256,...
  'TFStateAvailable',stateFound,'nativeClocks',clocks,'duplicateRows',repeats,...
  'recordedCoreConstant',all(u.values(:)==.25),'firstSignalEvidence',~isempty(first),...
  'secondSignalEvidence',~isempty(second),'firstBracket',bracket(tf,first),...
  'secondBracket',bracket(tf,second),'stateEvidenceSecond','UNAVAILABLE_UNLESS_EXPLICIT_STATE');
 if isempty(audit.cases),audit.cases=item;else,audit.cases(end+1)=item;end %#ok<AGROW>
 if strcmp(spec.key,'B0L_original')
  audit.primary=r; % private actual native reference, retained without modification
  audit.primaryInputSHA256=spec.sha256;
 end
 clear loaded r;
end
assert(numel(audit.cases)==4&&isfield(audit,'primary'),'JTE101:FourCases','Incomplete existing references.');
audit.archivedTFStateAvailable=false;
if numel(manifest.stateArchives)==1
 spec=manifest.stateArchives(1);p=fullfile(root,spec.local);
 assert(strcmp(JTE2026sha256(p),spec.sha256),'JTE101:ArchiveSHA','Archive changed.');
 archived=load(p);audit.archivedTFStateAvailable=findTFState(archived,0);
 % A state alone does not establish source/config/clock/IC alignment.
 audit.archivedTFStateAlignment='UNQUALIFIED_REQUIRES_INDEPENDENT_PROVENANCE';
end
primaryIndex=find(strcmp({audit.cases.key},'B0L_original'));
audit.referenceTFStateAvailable=audit.cases(primaryIndex).TFStateAvailable;
audit.original340Required=~audit.referenceTFStateAvailable;
audit.referenceSchema='PASS';
if audit.referenceTFStateAvailable||audit.archivedTFStateAvailable
 % No automatic original rerun if unexpected archived state exists.
 audit.referenceSchema='INCOMPLETE_STATE_REFERENCE_ALIGNMENT';
 audit.original340Required=false;
end
audit.firstBracket=audit.cases(primaryIndex).firstBracket;
audit.secondBracket=audit.cases(primaryIndex).secondBracket;
audit.nativeInterpolation=false;audit.toutIsNotState=true;
run=getenv('GITHUB_RUN_ID');prefix=fullfile(root,['JTE101_' run '_STAGE_A_AUDIT']);
save([prefix '.mat'],'audit','-v7.3');
publicReceipt=struct('ACCESS_PREFLIGHT','PASS_REUSED','REFERENCE_SCHEMA',audit.referenceSchema,...
 'TF_STATE_AVAILABLE',audit.referenceTFStateAvailable,'ORIGINAL340_REQUIRED',audit.original340Required,...
 'FIRST_SIGNAL_EVIDENCE',audit.cases(primaryIndex).firstSignalEvidence,...
 'SECOND_SIGNAL_EVIDENCE',audit.cases(primaryIndex).secondSignalEvidence,...
 'simulationRun',false,'G5','BLOCKED');
fid=fopen([prefix '.json'],'w');assert(fid~=-1,'JTE101:Receipt','Cannot write receipt.');
fprintf(fid,'%s',jsonencode(publicReceipt));fclose(fid);
fprintf('JTE101_STAGE_A_RESULT REFERENCE_SCHEMA=%s TF_STATE_AVAILABLE=%d ORIGINAL340_REQUIRED=%d FIRST_SIGNAL_EVIDENCE=%d SECOND_SIGNAL_EVIDENCE=%d simulationRun=0 ACCESS_PREFLIGHT=REUSED G5=BLOCKED\n',...
 audit.referenceSchema,audit.referenceTFStateAvailable,audit.original340Required,...
 audit.cases(primaryIndex).firstSignalEvidence,audit.cases(primaryIndex).secondSignalEvidence);
end
function yes=validSHA(s)
yes=ischar(s)&&~isempty(regexp(s,'^[a-f0-9]{64}$','once'));
end
function b=bracket(t,indices)
b=[];if isempty(indices)||indices(1)==1,return;end
i=indices(1);b=[t(i-1),t(i)];
end
function found=findTFState(value,depth)
found=false;if depth>6,return;end
if isa(value,'Simulink.SimulationData.Dataset')
 for k=1:value.numElements
  el=value.getElement(k);
  try,p=char(el.BlockPath.getBlock(1));catch,p='';end
  if endsWith(p,'/Battery Control/sensor dynamics 1'),found=true;return;end
 end
elseif isstruct(value)&&isscalar(value)
 names=fieldnames(value);
 for k=1:numel(names)
  if any(strcmp(names{k},{'signalData','resolvedVariables','products','simulationMetadata','tout'})),continue;end
  if findTFState(value.(names{k}),depth+1),found=true;return;end
 end
end
end
