function q=BTMS_M3_completed(s,processed)
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
assert(s.Time>=processed,'M3:Clock','Next top-of-step regressed.');
q=struct('processedPriorTop',processed,'nextTop',s.Time,'signalTimes',times,...
 'core',v{1},'held',v{2},'y',v{3},'T312',v{4},'phases',{events},...
 'clockScope','Completed major only. Discrete phase times are their own latest tick; nextTop is not a processed sample.');
end
function [t,v,n]=tail(ts)
n=numel(ts.Time);assert(n>0,'M3:Empty','No logged native sample.');t=ts.Time(end);a=ts.Data;
if n==1,a=reshape(a,1,[]);elseif ts.IsTimeFirst,a=reshape(a,n,[]);
else,a=reshape(permute(a,[ndims(a),1:ndims(a)-1]),n,[]);end
v=a(end,:);assert(isfinite(t)&&all(isfinite(v)),'M3:Finite','Nonfinite logged checkpoint.');
end
