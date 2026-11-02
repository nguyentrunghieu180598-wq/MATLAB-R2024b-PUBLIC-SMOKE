function WK08_entry()
% Keep MATLAB diagnostics private, including on failure. No retry.
root=fullfile(pwd,'actuator-review-private');
try
 pid=feature('getpid'); % process identity only
 f=fopen(fullfile(root,'WK08_PID.json'),'w');assert(f>=0);
 fprintf(f,'%s',jsonencode(struct('pid',pid)));fclose(f);
 t=tic;
 while ~isfile(fullfile(root,'WK08_WATCH_ACK.json')) && toc(t)<15,pause(.1);end
 assert(isfile(fullfile(root,'WK08_WATCH_ACK.json')) && ...
  ~isfile(fullfile(root,'WK08_WATCH_STOP.json')),'WK08:Watchdog','No healthy watchdog.');
 console=evalc('WK08_run(root,fullfile(pwd,''vendor-pack''),340);');
 assert(~isfile(fullfile(root,'WK08_WATCH_STOP.json')),'WK08:Watchdog','Resource stop.');
 save(fullfile(root,'WK08_CONSOLE.mat'),'console','-v7.3');
 f=fopen(fullfile(root,'WK08_DONE.json'),'w');fprintf(f,'{}');fclose(f);
catch err
 diagnostic=getReport(err,'extended','hyperlinks','off');
 save(fullfile(root,'WK08_FAILURE.mat'),'diagnostic','-v7.3');
 error('WK08:Unqualified','R1 stopped. Review private diagnostic; no retry authorized.');
end
end
