classdef JTE092BlockCapture < handle
% Read-only source-internal execution listener. Evaluations are NOT accepted steps.
properties
 Paths; Handles={}; Rows=zeros(100000,4); N=0; Counts=zeros(1,3);
 Overflow=false; Window=[330 338]; InputOutputReadable=true;
end
methods
 function o=JTE092BlockCapture(paths,window)
   o.Paths=paths;o.Window=window;
 end
 function attach(o)
  for k=1:numel(o.Paths)
   assert(~strcmp(get_param(o.Paths{k},'BlockType'),'SubSystem'),'JTE092:VirtualBlock');
   idx=k;
   o.Handles{end+1}=add_exec_event_listener(o.Paths{k},'PostOutputs',@(r,e)o.take(r,idx));
  end
 end
 function take(o,r,idx)
  o.Counts(idx)=o.Counts(idx)+1;
  t=double(r.CurrentTime);
  if t<o.Window(1)||t>o.Window(2),return;end
  if o.N>=size(o.Rows,1),o.Overflow=true;return;end
  try
   x=double(r.InputPort(1).Data);
   y=double(r.OutputPort(1).Data);
   if ~isscalar(x)||~isscalar(y)||~isfinite(x)||~isfinite(y)
    o.InputOutputReadable=false;return;
   end
  catch
   o.InputOutputReadable=false;return;
  end
  o.N=o.N+1;o.Rows(o.N,:)=[t idx x y];
 end
 function a=data(o)
  a=o.Rows(1:o.N,:);
 end
 function detach(o)
  o.Handles={};
 end
end
end
