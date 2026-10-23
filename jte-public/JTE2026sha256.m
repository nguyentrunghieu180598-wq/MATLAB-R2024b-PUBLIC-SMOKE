function h = JTE2026sha256(filename)
% Hash exact file bytes; SHA256 provenance only, requires JVM.
validateattributes(filename,{'char','string'},{'nonempty'});
filename = char(filename);
assert(isfile(filename),'Missing file for SHA256: %s',filename);
fid=fopen(filename,'rb'); assert(fid>=0,'Cannot read %s',filename);
c=onCleanup(@()fclose(fid));
md=java.security.MessageDigest.getInstance('SHA-256');
while true
    bytes=fread(fid,1024*1024,'*uint8');
    if isempty(bytes), break; end
    md.update(typecast(bytes,'int8'));
end
h=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
