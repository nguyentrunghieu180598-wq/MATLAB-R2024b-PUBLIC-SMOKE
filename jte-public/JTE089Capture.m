classdef JTE089Capture < handle
% Read-only documented execution listeners; rows are solver evaluations, NOT
% accepted time steps. Rejected iterations may go backward in time.
properties
 TF; Core; Handles={}; Rows=zeros(200000,6); N=0;
 Counts=zeros(1,4); InputChanged=false(1,4);
 StateReadable=true; DerivativeReadable=true; Overflow=false;
 Window=[330 338];
end
methods
 function o=JTE089Capture(tf,core,window)
  o.TF=tf;o.Core=core;o.Window=window;
 end
 function attach(o)
  o.Handles{end+1}=add_exec_event_listener(o.TF,'PreOutputs',@(r,e)o.take(r,2));
  o.Handles{end+1}=add_exec_event_listener(o.TF,'PostOutputs',@(r,e)o.take(r,3));
  o.Handles{end+1}=add_exec_event_listener(o.TF,'PostDerivatives',@(r,e)o.take(r,4));
  if ~isempty(o.Core)
   o.Handles{end+1}=add_exec_event_listener(o.Core,'PostOutputs',@(r,e)o.take(r,1));
  end
 end
 function take(o,r,tag)
  o.Counts(tag)=o.Counts(tag)+1;
  t=double(r.CurrentTime);u=NaN;y=NaN;x=NaN;dx=NaN;
  if tag==1
   u=double(r.OutputPort(1).Data);
  else
   u=double(r.InputPort(1).Data);
   if tag==3,y=double(r.OutputPort(1).Data);end
   try
    z=r.ContStates;
    if isobject(z),z=z.Data;end
    x=double(z);
    if ~isscalar(x),x=NaN;o.StateReadable=false;end
   catch
    o.StateReadable=false;
   end
   if tag==4
    try
     z=r.Derivatives;if isobject(z),z=z.Data;end
     dx=double(z);
     if ~isscalar(dx),dx=NaN;o.DerivativeReadable=false;end
    catch
     o.DerivativeReadable=false;
    end
   end
  end
  o.InputChanged(tag)=o.InputChanged(tag)||any(abs(u-0.25)>1e-12);
  if t<o.Window(1)||t>o.Window(2),return;end
  if o.N>=size(o.Rows,1),o.Overflow=true;return;end
  o.N=o.N+1;o.Rows(o.N,:)=[t tag u y x dx];
 end
 function rows=data(o)
  rows=o.Rows(1:o.N,:);
 end
 function detach(o)
  o.Handles={};
 end
end
end
