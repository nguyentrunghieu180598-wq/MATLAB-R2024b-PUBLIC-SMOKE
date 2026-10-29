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
% The only accepted physical/solver output time is the prior top captured
% BEFORE step(s), corroborated by this step's bounded native signal and
% phase logs. After the terminal step there is NO next major step. Some
% R2024bU10 runs expose empty Simulation.Time after termination; this is
% not itself a numerical clock regression and must never be used as a
% synthetic accepted-major timestamp.
returnedTime=s.Time;status=char(s.Status);
returnedTimeAvailable=isnumeric(returnedTime)&&isreal(returnedTime)&&...
 isscalar(returnedTime)&&isfinite(returnedTime);
terminalInactiveObserved=false;
if finalstep
 assert(isfinite(expectedStop)&&processed==expectedStop,...
  'M3:TerminalHorizon','Actual finalstep must process exactly the frozen stop horizon.');
 assert(any(strcmp(status,{'paused','inactive'})),...
  'M3:TerminalLifecycle','Terminal lifecycle is neither paused nor inactive.');
 terminalInactiveObserved=strcmp(status,'inactive');
 if terminalInactiveObserved
  % R2024b documentation ordinarily describes a paused normal-mode
  % final step. If an observed runtime is already inactive, require the
  % true finalstep flag, exact processed horizon, bounded signals above,
  % readable phase state above and no reported simulation error. Complete
  % ToFile native clocks are checked independently by the caller.
  assert(isempty(o.ErrorMessage),...
   'M3:TerminalError','Inactive terminal has a simulation error; not qualified.');
 elseif returnedTimeAvailable
  assert(returnedTime>=processed,...
   'M3:TerminalClock','Available paused terminal time regressed.');
 end
 % Neither empty nor finite returned terminal Time establishes another hit.
 nextTop=[];nextTopAvailable=false;
else
 % Before terminal completion the next top-of-step MUST remain available
 % and nonregressing. No relaxation of this original active-step gate.
 assert(returnedTimeAvailable,'M3:Clock','Active returned time unavailable.');
 assert(strcmp(status,'paused')&&returnedTime>=processed,...
  'M3:Clock','Active next top-of-step regressed or is not paused.');
 nextTop=returnedTime;nextTopAvailable=true;
end
q=struct('processedPriorTop',processed,'nextTop',nextTop,...
 'nextTopAvailable',nextTopAvailable,'returnedSimulationTime',returnedTime,...
 'returnedTimeAvailable',returnedTimeAvailable,...
 'terminalInactiveObserved',terminalInactiveObserved,...
 'simulationStatus',status,'finalStepReturned',finalstep,'signalTimes',times,...
 'core',v{1},'held',v{2},'y',v{3},'T312',v{4},'phases',{events},...
 'clockScope','Completed step clocks come from processedPriorTop and independently logged signal/phase times. Terminal returned Time cannot be a next major. Inactive terminal requires finalstep, exact horizon, no simulation error and independent ToFile checks. This does not prove hidden physical t0.');
end
function [t,v,n]=tail(ts)
n=numel(ts.Time);assert(n>0,'M3:Empty','No logged native sample.');t=ts.Time(end);a=ts.Data;
if n==1,a=reshape(a,1,[]);elseif ts.IsTimeFirst,a=reshape(a,n,[]);
else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),n,[]);end
v=a(end,:);assert(isfinite(t)&&all(isfinite(v)),'M3:Finite','Nonfinite logged checkpoint.');
end
