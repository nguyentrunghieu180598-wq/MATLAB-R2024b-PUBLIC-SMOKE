"""Software-only guard qualification; synthetic child, no MATLAB battery."""
import os,json,sys,tempfile,time,subprocess,signal
from pathlib import Path
from unittest.mock import patch
import BTMS_M3_oneShotWatchdog as w
from JTE062_google_drive_synthetic import access_token,ensure_app_folder
from JTE101_io import quota
from JTE063_streaming_drive import upload_verified
from sampled_actuator_review_io import ROOT
def main():
 ROOT.mkdir(mode=0o700,exist_ok=False);checks=[]
 def check(name,condition):checks.append({"name":name,"pass":bool(condition)});assert condition,name
 good={"hostAvailable":8*w.GiB,"cgroupAvailable":8*w.GiB}
 check("caps_nominal",w.violation(good,8*w.GiB,8*w.GiB,[0]*4,0) is None)
 for name,m,d,q,sz,t in [
  ("host",dict(good,hostAvailable=w.GiB),8*w.GiB,8*w.GiB,[0]*4,0),
  ("cgroup",dict(good,cgroupAvailable=w.GiB),8*w.GiB,8*w.GiB,[0]*4,0),
  ("disk",good,w.GiB,8*w.GiB,[0]*4,0),("drive",good,8*w.GiB,w.GiB,[0]*4,0),
  ("one_file",good,8*w.GiB,8*w.GiB,[w.GiB+1,0,0,0],0),
  ("total",good,8*w.GiB,8*w.GiB,[w.GiB]*3+[0],0),
  ("wall",good,8*w.GiB,8*w.GiB,[0]*4,1200)]:
  check("stop_"+name,w.violation(m,d,q,sz,t) is not None)
 with tempfile.TemporaryDirectory(dir=ROOT) as td:
  p=Path(td);(p/"cg/service").mkdir(parents=True)
  (p/"self").write_text("0::/service\n");(p/"mem").write_text("MemAvailable: 8388608 kB\n")
  for d,limit,current in [(p/"cg","10737418240","1073741824"),(p/"cg/service","max","1073741824")]:
   (d/"memory.max").write_text(limit);(d/"memory.current").write_text(current)
  mm=w.memory(str(p/"self"),str(p/"cg"),str(p/"mem"))
  check("own_cgroup_resolved",mm["cgroupPath"]==str(p/"cg/service"))
  check("ancestor_limit_respected",mm["cgroupAvailable"]==9*w.GiB)
  model=p/"model.fixture";model.write_text("SYNTHETIC_GUARD_FIXTURE_NOT_SLX");native=p/"native";native.mkdir(mode=0o700)
  m={"model":{"path":str(model),"sha256":w.sha(model)},"nativeDir":str(native),
   "nativeFiles":[str(native/(str(k)+".mat")) for k in range(4)],"authorization":{"scope":w.SCOPE,
   "directHumanWorkConsent":True,"authorizedRun":os.environ["GITHUB_RUN_ID"],"preparedRun":"40735694599",
   "preparedModelSHA":w.sha(model),"exactlyOneInitialize":True,"allowRetry":False}}
  with patch.dict(os.environ,{"BTMS_M3_OWNER_APPROVAL":""}):
   try:w.authorize(m);ok=False
   except RuntimeError as e:ok=str(e)=="OWNER_APPROVAL_REQUIRED"
   check("approval_absent_blocks",ok)
  with patch.dict(os.environ,{"BTMS_M3_OWNER_APPROVAL":w.APPROVAL}):
   w.authorize(m);check("bound_scope_gate",True)
   m["authorization"]["allowRetry"]=True
   try:w.authorize(m);ok=False
   except RuntimeError:ok=True
   check("retry_denied",ok);m["authorization"]["allowRetry"]=False
   (native/"0.mat").write_text("existing")
   try:w.authorize(m);ok=False
   except RuntimeError:ok=True
   check("overwrite_denied",ok)
  # Tiny real process tree ignores INT/TERM; force-kill fallback must stop both.
  pidfile=p/"child.json"
  child="import signal,time;signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN);time.sleep(30)"
  parent="import signal,subprocess,sys,json,time;signal.signal(signal.SIGINT,signal.SIG_IGN);signal.signal(signal.SIGTERM,signal.SIG_IGN);q=subprocess.Popen([sys.executable,'-c',"+repr(child)+"]);open(sys.argv[1],'w').write(json.dumps({'pid':q.pid}));time.sleep(30)"
  cleanenv={k:v for k,v in os.environ.items() if not k.startswith("JTE_GOOGLE_")}
  proc=subprocess.Popen([sys.executable,"-c",parent,str(pidfile)],start_new_session=True,env=cleanenv)
  try:
   for _ in range(100):
    if pidfile.exists():break
    time.sleep(.03)
   assert pidfile.exists();kid=json.loads(pidfile.read_text())["pid"];start=w.proc_start(proc.pid)
   w.terminate_tree(proc.pid,"wrong-identity",grace=.1);check("recycled_identity_not_signaled",proc.poll() is None)
   w.terminate_tree(proc.pid,start,grace=.3);proc.wait(timeout=2)
   def alive(pid):
    try:s=Path(f"/proc/{pid}/stat").read_text();return s[s.rfind(")")+2:].split()[0]!="Z"
    except FileNotFoundError:return False
   check("real_child_stopped",not alive(proc.pid));check("descendant_stopped",not alive(kid))
  finally:
   if proc.poll() is None:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
 actual=w.memory();check("genuine_host_cgroup_read",actual["hostAvailable"]>0 and actual["cgroupPath"])
 token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
 q=quota(token);check("genuine_drive_quota_read",q["availableBytes"]>0);folder=ensure_app_folder(token)
 run=os.environ["GITHUB_RUN_ID"];p=ROOT/("M3_GUARDS_"+run+"_RESULT.json")
 data={"run":run,"commit":os.environ["GITHUB_SHA"],"checks":checks,"allPass":all(c["pass"] for c in checks),
  "actualHost":actual,"actualDrive":q,"syntheticProcessOnly":True,"MATLABRun":False,"physicalRun":False,
  "physicalApprovalConsumed":False,"sourceWatcher":"Chat e172ff4 reviewed; Work fixes own/ancestor cgroup,live Drive,PID identity/tree and bounded async quota."}
 p.write_text(json.dumps(data,indent=2))
 rc=upload_verified(token,folder,p,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
 receipt=ROOT/("M3_GUARDS_"+run+"_PRIVATE_RECEIPT.json");receipt.write_text(json.dumps({"run":run,"commit":os.environ["GITHUB_SHA"],"files":[{"name":p.name,**rc}],"physicalRun":False},indent=2));upload_verified(token,folder,receipt,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
 print("M3_GUARDS_QUALIFIED checks="+str(len(checks))+" tinySyntheticChild=1 noMATLAB=1 physicalRun=0 privateReadback=PASS")
if __name__=="__main__":main()
