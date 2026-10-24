function metadata=JTE046_exportNative(records,outDir)
% PRIVATE bridge from JTE043 records to one CSV per native clock.
% Does not decrypt, authenticate MAT, infer units, or resolve event conventions.
assert(isstruct(records)&&isscalar(records),'JTE046:Records','Expected native records');
outDir=char(outDir);assert(~isfolder(outDir)&&~isfile(outDir),'JTE046:Exists','No overwrite');
parent=fileparts(outDir);assert(isfolder(parent),'JTE046:Parent','Parent must exist');
stage=tempname(parent);mkdir(stage);guard=onCleanup(@()cleanup(stage)); %#ok<NASGU>
names=fieldnames(records);metadata=struct([]);
for k=1:numel(names)
 name=names{k};assert(isvarname(name),'JTE046:Name','Invalid signal name');
 r=records.(name);assert(isfield(r,'Time')&&isfield(r,'Data')&&isfield(r,'IsTimeFirst'),'JTE046:Fields','Missing native fields');
 t=double(r.Time(:));a=r.Data;
 assert(~isempty(t)&&all(isfinite(t))&&all(diff(t)>=0),'JTE046:Clock','Time must be finite and ordered; duplicates retained');
 assert(isnumeric(a)&&isreal(a)&&~isempty(a)&&all(isfinite(a(:))),'JTE046:Values','Require finite real numeric data');
 assert(islogical(r.IsTimeFirst)&&isscalar(r.IsTimeFirst),'JTE046:TimeFlag','Explicit logical IsTimeFirst required');
 n=numel(t);
 if n==1
  x=reshape(double(a),1,[]);
 elseif r.IsTimeFirst
  assert(size(a,1)==n,'JTE046:TimeAxis','Declared first time dimension mismatch');
  x=reshape(double(a),n,[]);
 else
  nd=ndims(a);assert(size(a,nd)==n,'JTE046:TimeAxis','Declared last time dimension mismatch');
  x=reshape(permute(double(a),[nd 1:nd-1]),n,[]);
 end
 file=[name '.csv'];p=fullfile(stage,file);fid=fopen(p,'w');assert(fid>=0);
 try
  fprintf(fid,'time_s');fprintf(fid,',value_%d',1:size(x,2));fprintf(fid,'\n');
  for j=1:n
   fprintf(fid,'%.17g',t(j));fprintf(fid,',%.17g',x(j,:));fprintf(fid,'\n');
  end
  fclose(fid);
 catch ME
  fclose(fid);rethrow(ME);
 end
 unit='';
 if isfield(r,'DataInfo')
  u=r.DataInfo.Units;
  if ischar(u)||isstring(u),unit=char(u);
  elseif isobject(u)&&isprop(u,'Name'),unit=char(u.Name);
  elseif isstruct(u)&&isfield(u,'Name'),unit=char(u.Name);
  end
 end
 entry=struct('variable',name,'file',file,'sha256',fileSHA(p), ...
 'nativeTimeShape',size(r.Time),'nativeDataShape',size(a),'IsTimeFirst',r.IsTimeFirst, ...
 'sourceDataClass',class(a),'nRows',n,'nChannels',size(x,2),'duplicateTimePairs',sum(diff(t)==0), ...
 'rawLoggedUnit',unit,'unitVerified',false,'eventConventionVerified',false, ...
 'conversion','Declared time axis to rows only; no interpolation, sorting or duplicate removal');
 if isempty(metadata),metadata=entry;else,metadata(end+1)=entry;end %#ok<AGROW>
end
result=struct('scope','PRIVATE_NATIVE_EXPORT_NOT_AUTHENTICATION','signals',metadata);
fid=fopen(fullfile(stage,'export_manifest.json'),'w');assert(fid>=0);
fprintf(fid,'%s',jsonencode(result));fclose(fid);
assert(~isfolder(outDir)&&~isfile(outDir),'JTE046:Exists','Destination appeared during export');
[ok,msg]=movefile(stage,outDir);assert(ok,'JTE046:Move','Export commit failed: %s',msg);
end
function h=fileSHA(p)
md=java.security.MessageDigest.getInstance('SHA-256');
fid=fopen(p,'rb');assert(fid>=0);g=onCleanup(@()fclose(fid)); %#ok<NASGU>
while true
 bytes=fread(fid,1048576,'*uint8');if isempty(bytes),break;end
 md.update(typecast(bytes,'int8'));
end
h=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
function cleanup(p)
if isfolder(p),rmdir(p,'s');end
end
