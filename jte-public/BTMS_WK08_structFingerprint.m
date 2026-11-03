function fp=BTMS_WK08_structFingerprint(m)
% Extended WK07 fingerprint: physical connectivity, dialog/config, IC and code.
% Output paths alone are normalized. StopTime/InitialState are NOT hidden.
fp=BTMS_M2340_nominalAudit(m);
ix=find(strcmp(fp.blocks(:,2),'ToFile'));
for k=ix(:)'
 p=fp.blocks{k,3};j=find(strcmpi(p{1},'FileName'));
 assert(numel(j)==1,'WK08:Fingerprint','Missing To File path parameter.');
 p{2}{j}='<private output path>';fp.blocks{k,3}=p;
end
bs=sort(find_system(m,'LookUnderMasks','all','FollowLinks','off', ...
 'IncludeCommented','on','Type','Block'));
fp.comments=cell(numel(bs),2);
for k=1:numel(bs)
 fp.comments(k,:)={strrep(bs{k},m,'$ROOT'),get_param(bs{k},'Commented')};
end
mw=get_param(m,'ModelWorkspace');v=whos(mw);fp.workspace=struct();
for k=1:numel(v),fp.workspace.(v(k).name)=getVariable(mw,v(k).name);end
sf=sfroot;charts=sf.find('-isa','Stateflow.EMChart');fp.scripts=cell(0,2);
for k=1:numel(charts)
 p=char(charts(k).Path);
 if startsWith(p,[m '/'])
  fp.scripts(end+1,:)={strrep(p,m,'$ROOT'),char(charts(k).Script)}; %#ok<AGROW>
 end
end
if ~isempty(fp.scripts),fp.scripts=sortrows(fp.scripts,1);end
end
