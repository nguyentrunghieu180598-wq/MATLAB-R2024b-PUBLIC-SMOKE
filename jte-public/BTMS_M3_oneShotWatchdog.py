#!/usr/bin/env python3
"""M3 external monitor. No MATLAB launch, retry or G5 acceptance.
Reviewed derivative of Chat e172ff4; production requires direct-owner consent
bound to the exact protected run + prepared model receipt. Secrets stay here.
"""
import os,json,time,signal,re,hashlib,sys
from pathlib import Path
from JTE101_io import quota
from JTE062_google_drive_synthetic import access_token
GiB=1024**3
APPROVAL="APPROVE_SINGLE_B0L10MS_0_TO_340"
SCOPE="M3_B0L10MS_340_OWNER_20261029_40735694599"
REPO="nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"
def need(v,m):
 if not v:raise RuntimeError(m)
def atomic(p,d):
 p=Path(p);tmp=p.with_suffix(p.suffix+".partial")
 with tmp.open("w") as f:json.dump(d,f,indent=2);f.flush();os.fsync(f.fileno())
 os.replace(tmp,p)
def sha(p):
 h=hashlib.sha256()
 with open(p,"rb") as f:
  for x in iter(lambda:f.read(1024**2),b""):h.update(x)
 return h.hexdigest()
def proc_start(pid):
 # stat comm may contain spaces/parentheses; fields after last ')' start at3.
 s=Path(f"/proc/{pid}/stat").read_text();return s[s.rfind(")")+2:].split()[19]
def proc_rss(pid):
 s=Path(f"/proc/{pid}/status").read_text();m=re.search(r"(?m)^VmRSS:\s*(\d+)\s*kB",s)
 need(m is not None,"PROCESS_RSS_UNAVAILABLE");return int(m.group(1))*1024
def descendants(root):
 pairs={}
 for p in Path("/proc").iterdir():
  if not p.name.isdecimal():continue
  try:
   s=(p/"stat").read_text();a=s[s.rfind(")")+2:].split();pairs[int(p.name)]=int(a[1])
  except (FileNotFoundError,ProcessLookupError,PermissionError,IndexError):pass
 seen={root}
 while True:
  old=len(seen);seen|={pid for pid,pp in pairs.items() if pp in seen}
  if len(seen)==old:return sorted(seen,reverse=True)
def terminate_tree(pid,start,grace=5):
 # Never signal the job/uploader/watchdog parent or a recycled PID.
 if pid==os.getpid() or pid<=1:raise RuntimeError("UNSAFE_TARGET_PID")
 try:
  if proc_start(pid)!=start:return
 except FileNotFoundError:return
 tracked={}
 for p in descendants(pid):
  try:tracked[p]=proc_start(p)
  except (FileNotFoundError,ProcessLookupError):pass
 for sig,seconds in ((signal.SIGINT,grace),(signal.SIGTERM,grace),(signal.SIGKILL,1)):
  for p,identity in list(tracked.items()):
   try:
    if proc_start(p)==identity:os.kill(p,sig)
   except (FileNotFoundError,ProcessLookupError,PermissionError):pass
  limit=time.monotonic()+seconds
  while time.monotonic()<limit:
   alive=[]
   for p,identity in tracked.items():
    try:
     st=Path(f"/proc/{p}/stat").read_text();parts=st[st.rfind(")")+2:].split()
     if parts[0]!="Z" and proc_start(p)==identity:alive.append(p)
    except (FileNotFoundError,ProcessLookupError):pass
   if not alive:return
   time.sleep(.1)
def memory(cgroup_file="/proc/self/cgroup",cgroot="/sys/fs/cgroup",meminfo="/proc/meminfo"):
 text=Path(meminfo).read_text();m=re.search(r"(?m)^MemAvailable:\s*(\d+)\s*kB",text)
 need(m is not None,"HOST_AVAILABLE_RAM_UNAVAILABLE");available=int(m.group(1))*1024
 root=Path(cgroot);own=None
 for line in Path(cgroup_file).read_text().splitlines():
  q=line.split(":",2)
  if len(q)==3 and q[0]=="0":own=root/q[2].lstrip("/");break
 need(own is not None and (own/"memory.max").is_file() and (own/"memory.current").is_file(),"OWN_CGROUP_V2_UNAVAILABLE")
 d=own;observed=[];free=[]
 while True:
  if (d/"memory.max").is_file() and (d/"memory.current").is_file():
   cap=(d/"memory.max").read_text().strip();used=int((d/"memory.current").read_text())
   observed.append({"path":str(d),"max":cap,"current":used})
   if cap!="max":free.append(int(cap)-used)
  if d==root:break
  need(root in d.parents,"CGROUP_PATH_ESCAPE");d=d.parent
 cgfree=min(free) if free else None
 found=own;cap=observed[0]["max"];used=observed[0]["current"]
 return {"hostAvailable":available,"cgroupAvailable":cgfree,"cgroupPath":str(found),"cgroupCurrent":used,"cgroupMax":cap}
def violation(mem,diskfree,drivefree,sizes,elapsed,wall=1200):
 if mem["hostAvailable"]<2*GiB:return "HOST_RAM_RESERVE"
 if mem["cgroupAvailable"] is not None and mem["cgroupAvailable"]<2*GiB:return "CGROUP_RAM_RESERVE"
 if diskfree<2*GiB:return "SCRATCH_DISK_RESERVE"
 if drivefree<2*GiB+GiB//2:return "DRIVE_DELIVERY_RESERVE"
 if any(x>GiB for x in sizes):return "NATIVE_SINGLE_FILE_CAP"
 if sum(sizes)>2*GiB:return "NATIVE_TOTAL_FILE_CAP"
 if elapsed>=wall:return "WALL_CEILING"
 return None
def authorize(m):
 need(os.environ.get("BTMS_M3_OWNER_APPROVAL")==APPROVAL,"OWNER_APPROVAL_REQUIRED")
 need(os.environ.get("GITHUB_REPOSITORY")==REPO and os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
  os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","RUN_CONTEXT")
 a=m["authorization"]
 need(a["scope"]==SCOPE and a["directHumanWorkConsent"] is True and a["authorizedRun"]==os.environ["GITHUB_RUN_ID"] and
  a["preparedRun"]=="40735694599" and a["preparedModelSHA"]==m["model"]["sha256"] and a["exactlyOneInitialize"] and not a["allowRetry"],"AUTHORIZATION_BINDING")
 model=Path(m["model"]["path"]);need(sha(model)==m["model"]["sha256"],"APPROVED_MODEL_SHA")
 folder=Path(m["nativeDir"]).resolve(strict=True);need(folder.stat().st_mode&0o077==0,"PRIVATE_MODE")
 files=[Path(x).resolve() for x in m["nativeFiles"]]
 need(len(files)==len(set(files))==4 and all(p.parent==folder and not p.exists() for p in files),"FRESH_FOUR_NATIVE_TARGETS")
 return folder,files
def monitor(manifest):
 import shutil
 m=json.load(open(manifest));folder,files=authorize(m);base=Path(manifest).parent
 token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
 drive=quota(token)["availableBytes"];lastQuota=time.monotonic();startup=time.monotonic()
 mem=memory();issue=violation(mem,shutil.disk_usage(base).free,drive,[0]*4,0)
 need(issue is None,"WATCHDOG_PREFLIGHT_"+str(issue))
 atomic(base/"watch_ready.json",{"pid":os.getpid(),"start":proc_start(os.getpid()),"run":os.environ["GITHUB_RUN_ID"],"scope":SCOPE,"liveDriveVerified":True})
 pid=None;identity=None;physicalStart=None;peak=0;largest=0;reason="WAITING_FOR_MATLAB"
 import threading,queue
 refresh=None;refreshStart=None;updates=queue.Queue()
 def quota_worker():
  try:updates.put((True,quota(token)["availableBytes"]))
  except Exception as e:updates.put((False,type(e).__name__))
 try:
  while True:
   now=time.monotonic()
   if (base/"driver_pid.json").exists() and pid is None:
    q=json.load(open(base/"driver_pid.json"));pid=int(q["pid"]);identity=proc_start(pid)
    cmd=Path(f"/proc/{pid}/cmdline").read_bytes()
    need(b"MATLAB" in cmd or b"matlab" in cmd,"TARGET_NOT_MATLAB")
    need(Path(f"/proc/{pid}/cgroup").read_text()==Path("/proc/self/cgroup").read_text(),"MATLAB_CGROUP_DIFFERS")
    atomic(base/"watch_ack.json",{"pid":pid,"start":identity,"watchdogPID":os.getpid(),"healthy":True})
   if (base/"initialize_entered.json").exists() and physicalStart is None:physicalStart=now
   if (base/"driver_done.json").exists():
    q=json.load(open(base/"driver_done.json"));reason="DRIVER_FINISHED_REQUIRES_DATA_AUDIT";break
   if pid is not None:
    try:
     need(proc_start(pid)==identity,"TARGET_IDENTITY_CHANGED");peak=max(peak,proc_rss(pid))
    except FileNotFoundError:reason="UNQUALIFIED_MATLAB_EXITED_WITHOUT_DONE";break
   if refresh is None and now-lastQuota>=45:
    refresh=threading.Thread(target=quota_worker,daemon=True);refreshStart=now;refresh.start()
   if refresh is not None:
    if not updates.empty():
     ok,value=updates.get();need(ok,"LIVE_DRIVE_REFRESH_FAILED");drive=value;lastQuota=now;refresh=None
    elif now-refreshStart>10:raise RuntimeError("LIVE_DRIVE_REFRESH_TIMEOUT")
   mem=memory();sizes=[p.stat().st_size if p.exists() else 0 for p in files];largest=max(largest,sum(sizes))
   elapsed=0 if physicalStart is None else now-physicalStart
   issue=violation(mem,shutil.disk_usage(base).free,drive,sizes,now-startup,wall=1185)
   if physicalStart is None and now-startup>300:issue="PREINITIALIZE_WALL_CEILING"
   atomic(base/"watch_heartbeat.json",{"unix":time.time(),"healthy":issue is None,"elapsedPhysical_s":elapsed,"nativeBytes":sum(sizes)})
   if issue:
    reason="UNQUALIFIED_"+issue;atomic(base/"STOP_REQUEST.json",{"reason":reason,"unix":time.time()})
    if pid is not None:terminate_tree(pid,identity)
    break
   time.sleep(.5)
 except Exception as e:
  reason="UNQUALIFIED_WATCHDOG_EXCEPTION_"+type(e).__name__
  atomic(base/"STOP_REQUEST.json",{"reason":reason,"message":str(e)})
  if pid is not None:terminate_tree(pid,identity)
 finally:
  atomic(base/"watchdog_receipt.json",{"status":reason,"actualMaxObservedMATLABRSS_bytes":peak,
   "maxObservedNativeBytes":largest,"liveDriveLastVerifiedBytes":drive,"scope":SCOPE,
   "physicalInitializeObserved":physicalStart is not None,"automaticRetry":False,"G5Accepted":False})
 return 0 if reason=="DRIVER_FINISHED_REQUIRES_DATA_AUDIT" else 5
if __name__=="__main__":
 try:sys.exit(monitor(sys.argv[1]))
 except Exception as e:
  print("M3_WATCHDOG_FAIL_CLOSED="+type(e).__name__+" G5_ACCEPTED=false");sys.exit(4)
