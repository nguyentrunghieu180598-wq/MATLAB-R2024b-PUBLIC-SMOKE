function ci_jte_ambient_upstream_trace()
% Structural-only source tracing; no numerical study values or private data.
root=pwd;addpath(fullfile(root,'jte-public'));
p=openProject(fullfile(root,'vendor-pack','batteryExamplesProjectSetup.prj'));
pguard=onCleanup(@()quietCloseProject(p)); %#ok<NASGU>
pair=JTE2026build(fullfile(root,'vendor-pack'),fullfile(root,'ambient-source-audit'));
cases={pair.baseline,pair.study};
for k=1:numel(cases)
    [~,model]=fileparts(cases{k});
    load_system(cases{k});
    fprintf('AUDIT_MODEL %s\n',model);
    ctrl=[model '/Battery Control'];
    f=get_param([ctrl '/FlwR_calc'],'PortHandles');
    ambientLine=get_param(f.Inport(2),'Line');
    sourcePort=get_param(ambientLine,'SrcPortHandle');
    sourceBlock=get_param(sourcePort,'Parent');
    fprintf('AMBIENT_CONTROL_SOURCE_REL=%s TYPE=%s\n',stripModel(sourceBlock,model),get_param(sourceBlock,'BlockType'));
    if strcmp(get_param(sourceBlock,'BlockType'),'Inport')
        portN=str2double(get_param(sourceBlock,'Port'));
        boundary=get_param(ctrl,'PortHandles');
        assert(portN>=1 && portN<=numel(boundary.Inport),'Invalid Ambient boundary port');
        outerLine=get_param(boundary.Inport(portN),'Line');
        assert(outerLine~=-1,'Upstream Ambient boundary disconnected');
        priorPort=get_param(outerLine,'SrcPortHandle');
        assert(priorPort~=-1,'Upstream Ambient physical port missing');
        priorBlock=get_param(priorPort,'Parent');
        fprintf('AMBIENT_UPSTREAM_REL=%s TYPE=%s\n',stripModel(priorBlock,model),get_param(priorBlock,'BlockType'));
        step=0;
        seen={};
        while step<8
            typ=get_param(priorBlock,'BlockType');
            if strcmp(typ,'Constant')
                fprintf('AMBIENT_UPSTREAM_CONSTANT_FOUND SampleTime=%s\n',get_param(priorBlock,'SampleTime'));
                break;
            end
            if ~strcmp(typ,'Inport'),break;end
            % For an Inport of a nested subsystem, trace the parent boundary.
            parent=get_param(priorBlock,'Parent');
            if strcmp(parent,model), break;end
            pp=get_param(parent,'PortHandles');
            nn=str2double(get_param(priorBlock,'Port'));
            assert(nn>=1 && nn<=numel(pp.Inport),'Invalid upstream port number');
            ln=get_param(pp.Inport(nn),'Line');
            if ln==-1,break;end
            ph=get_param(ln,'SrcPortHandle');if ph==-1,break;end
            prev=get_param(ph,'Parent');
            if any(strcmp(seen,prev)),break;end
            seen{end+1}=prev; %#ok<AGROW>
            priorBlock=prev;step=step+1;
            fprintf('AMBIENT_FURTHER_UPSTREAM_REL=%s TYPE=%s\n',stripModel(priorBlock,model),get_param(priorBlock,'BlockType'));
        end
    end
    close_system(model,0);
end
fprintf('AMBIENT_UPSTREAM_TRACE_COMPLETE_NO_TEMPERATURE_VALUES\n');
end
function rel=stripModel(path,model)
rel=char(path);
if strncmp(rel,[model '/'],numel(model)+1),rel=rel(numel(model)+2:end);end
end
function quietCloseProject(p)
try,close(p);catch,end
end
