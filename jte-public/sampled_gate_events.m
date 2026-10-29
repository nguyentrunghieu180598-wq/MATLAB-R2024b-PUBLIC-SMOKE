function varargout=sampled_gate_events(action,varargin)
% Public runtime listeners. Raw callbacks are NOT plant accepted-step evidence.
persistent specs trace listeners seq
switch action
 case 'init'
  specs=varargin{1};trace=cell(0,1);listeners={};seq=0;
 case 'start'
  for j=1:numel(specs)
   for p={'PostOutputs','PreUpdate','PostUpdate'}
    phase=p{1};
    listeners{end+1}=add_exec_event_listener(specs(j).path,phase,@(r,e)capture(r,e,j,phase)); %#ok<AGROW>
   end
  end
 case 'get'
  varargout{1}=trace;
 case 'clear'
  listeners={};specs=[];trace={};seq=0;
 otherwise,error('Gate:EventAction','Unknown event action.');
end
 function capture(r,~,j,phase)
  seq=seq+1;x=[];which=[];usage={};readable=true;why='';
  try
   for w=1:r.NumDworks
    dw=r.Dwork(w);usage{end+1}=char(dw.Usage); %#ok<AGROW>
    if dw.UsedAsDiscState||strcmp(char(dw.Usage),'DState')
     a=dw.Data;
     if isa(a,'double')&&isreal(a)&&isscalar(a)&&isfinite(a),x(end+1)=a;which(end+1)=w;end %#ok<AGROW>
    end
   end
   readable=numel(x)==1;
   if ~readable,why='ACTUAL_SCALAR_DSTATE_NOT_UNAMBIGUOUS';end
  catch err,readable=false;why=err.identifier;
  end
  y=r.OutputPort(1).Data;u=[];
  if ~strcmp(phase,'PostOutputs'),u=r.InputPort(1).Data;end
  trace{end+1}=struct('sequence',seq,'branch',j,'phase',phase,'time_s',r.CurrentTime,...
   'actualDState',x,'dworkIndices',which,'dworkUsage',{usage},'actualStateReadable',readable,'reason',why,...
   'heldInput',u,'output',y,'NumDworks',r.NumDworks,'NumDworkDiscStates',r.NumDworkDiscStates); %#ok<AGROW>
 end
end
