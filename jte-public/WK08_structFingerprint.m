function fp=WK08_structFingerprint(m)
% Extend WK04 structFingerprint with canonical Simscape ports, workspace,
% chart source, comments and complete config-set values. No unreadable fallback.
fp=BTMS_M2340_nominalAudit(m);
for k=1:size(fp.blocks,1)
 if strcmp(fp.blocks{k,2},'ToFile')
  p=fp.blocks{k,3};ix=find(strcmpi(p{1},'Filename'));
  assert(numel(ix)==1,'WK08:Fingerprint','Missing filename parameter.');
  p{2}{ix}='<private output>';fp.blocks{k,3}=p;
 end
end
fp=rmfield(fp,'canonicalPortHandles'); % session handle count is diagnostic only
b=sort(find_system(m,'LookUnderMasks','all','FollowLinks','off', ...
 'IncludeCommented','on','Type','Block'));
fp.comments=cell(numel(b),2);
for k=1:numel(b),fp.comments(k,:)={strrep(b{k},m,'$ROOT'),get_param(b{k},'Commented')};end
mw=get_param(m,'ModelWorkspace');w=whos(mw);fp.workspace=struct;
for k=1:numel(w),fp.workspace.(w(k).name)=getVariable(mw,w(k).name);end
sf=sfroot;ch=sf.find('-isa','Stateflow.EMChart');fp.charts=cell(0,2);
for k=1:numel(ch)
 if startsWith(char(ch(k).Path),[m '/'])
  fp.charts(end+1,:)={strrep(char(ch(k).Path),m,'$ROOT'),char(ch(k).Script)}; %#ok<AGROW>
 end
end
if ~isempty(fp.charts),fp.charts=sortrows(fp.charts,1);end
cs=getActiveConfigSet(m);p=get_param(cs,'ObjectParameters');names=sort(fieldnames(p));
fp.fullConfig=cell(0,2);
for k=1:numel(names)
 % Read-only/session properties are outside the saved configuration contract.
 if any(strcmp(p.(names{k}).Attributes,'read-only')),continue;end
 fp.fullConfig(end+1,:)={names{k},get_param(cs,names{k})}; %#ok<AGROW>
end
end
