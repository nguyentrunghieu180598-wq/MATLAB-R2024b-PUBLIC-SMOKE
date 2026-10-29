function q=BTMS_M3_completed(s,processed,finalstep,expectedStop)
% Terminal handling is a source-reviewed proposal, NOT yet MATLAB-qualified.
if nargin<3,finalstep=false;end
if nargin<4,expectedStop=NaN;end
assert(islogical(finalstep)&&isscalar(finalstep),'M3:TerminalFlag','Actual step return required.');
% processed MUST be captured from s.Time BEFORE step(s).
o=s.SimulationOutput;logs=o.get('m3Signals');names={'m3Core','m3Held','m3Y','m3T312'};
v=cell(1,4);times=zeros(1,4);lengths=zeros(1,4);
for k=1:4
 e=logs.getElement(names{k});[times(k),v{k},lengths(k)]=tail(e.Values);
end
assert(all(lengths<=2),'M3:Tail','Unbounded signal history.');
assert(times(1)==processed&&times(4)==processed&&times(2)==times(3)&&times(2)<=processed,...
 'M3:Clock','Continuous/discrete role clocks not qualified.');
assert(numel(v{4})==312&&all(cellfun(@numel,v(1:3))==1),'M3:Width','Wrong native widths.');
events=BTMS_M3_events('get');
assert(all(cellfun(@(x)~isempty(x)&&x.readable,events)),'M3:State','Actual phase states unreadable.');
assert(events{1}.time==times(3)&&events{1}.output==v{3}&&events{1}.state==v{3},...
 'M3:Phase','Output is not actual C=1,D=0 pre-update state at its own tick.');
returnedTime=s.Time;status=char(s.Status);
assert(isscalar(returnedTime)&&isfinite(returnedTime),'M3:Clock','Returned simulation time unavailable.');
if finalstep
 assert(isfinite(expectedStop)&&processed==expectedStop&&...
  any(strcmp(status,{'paused','inactive'})),...
  'M3:TerminalClock','Terminal return, processed horizon and lifecycle must agree.');
 % There is no next processed major after the horizon. Preserve raw lifecycle
 % time for diagnosis; never reinterpret it as another accepted sample.
 nextTop=[];nextTopAvailable=false;
else
 assert(strcmp(status,'paused')&&returnedTime>=processed,...
  'M3:Clock','Active next top-of-step regressed or is not paused.');
 nextTop=returnedTime;nextTopAvailable=true;
end
q=struct('processedPriorTop',processed,'nextTop',nextTop,...
 'nextTopAvailable',nextTopAvailable,'returnedSimulationTime',returnedTime,...
 'simulationStatus',status,'finalStepReturned',finalstep,'signalTimes',times,...
 'core',v{1},'held',v{2},'y',v{3},'T312',v{4},'phases',{events},...
 'clockScope','Signal/phase clocks must match the processed prior top. Discrete times retain their latest tick. No nextTop is asserted after finalStep; raw lifecycle time is preserved. Not hidden physical t0 proof.');
end
function [t,v,n]=tail(ts)
n=numel(ts.Time);assert(n>0,'M3:Empty','No logged native sample.');t=ts.Time(end);a=ts.Data;
if n==1,a=reshape(a,1,[]);elseif ts.IsTimeFirst,a=reshape(a,n,[]);
else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),n,[]);end
v=a(end,:);assert(isfinite(t)&&all(isfinite(v)),'M3:Finite','Nonfinite logged checkpoint.');
end
