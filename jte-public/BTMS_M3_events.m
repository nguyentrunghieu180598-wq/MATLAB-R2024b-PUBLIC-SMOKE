function varargout=BTMS_M3_events(action,varargin)
% Stream raw block execution phases; these are NOT completed-major proof.
persistent path fid listeners seq last
switch action
 case 'init'
  path=varargin{1};assert(~isfile(varargin{2}),'M3:EventFile','Phase file already exists.');fid=fopen(varargin{2},'w');
  assert(fid>=0,'M3:EventFile','Fresh private phase file required.');
  fprintf(fid,'seq,time,phase,state,input,output,readable\n');listeners={};seq=0;last=cell(1,3);
 case 'start'
  phases={'PostOutputs','PreUpdate','PostUpdate'};
  for k=1:3
   listeners{end+1}=add_exec_event_listener(path,phases{k},@(r,e)capture(r,e,k)); %#ok<AGROW>
  end
 case 'get'
  varargout{1}=last;
 case 'close'
  listeners={};if ~isempty(fid)&&fid>=0,fclose(fid);end;fid=-1;
 otherwise,error('M3:EventAction','Unsupported action.');
end
 function capture(r,~,phase)
  x=NaN;u=NaN;y=NaN;ok=false;v=[];
  try
   for k=1:r.NumDworks
    d=r.Dwork(k);
    if d.UsedAsDiscState||strcmp(char(d.Usage),'DState')
     a=d.Data;if isa(a,'double')&&isscalar(a)&&isreal(a)&&isfinite(a),v(end+1)=a;end %#ok<AGROW>
    end
   end
   ok=numel(v)==1;if ok,x=v;end
   y=r.OutputPort(1).Data;
   if phase~=1,u=r.InputPort(1).Data;end
  catch,ok=false;
  end
  seq=seq+1;t=r.CurrentTime;
  fprintf(fid,'%d,%.17g,%d,%.17g,%.17g,%.17g,%d\n',seq,t,phase,x,u,y,ok);
  last{phase}=struct('sequence',seq,'time',t,'phase',phase,'state',x,'input',u,'output',y,'readable',ok);
 end
end
