"""M3 ONE infrastructure-only receipt publisher. No battery authorization."""
import os,json,sys,re,hashlib,urllib.request
from pathlib import Path
from JTE062_google_drive_synthetic import access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota
from sampled_actuator_review_io import ROOT
MSG="M3_REQUALIFY_TERMINAL_CLOCK_ONCE_20261029"
def main():
 e=json.load(open(os.environ["GITHUB_EVENT_PATH"]))
 assert os.environ.get("GITHUB_REPOSITORY")=="nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE" and (e.get("repository") or {}).get("private") is False
 assert os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and os.environ.get("GITHUB_EVENT_NAME")=="push"
 assert (e.get("head_commit") or {}).get("message")==MSG and (e.get("head_commit") or {}).get("id")==os.environ["GITHUB_SHA"]
 assert os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted"
 # Inspect mapping NAMES only; never read/print secret values for this check.
 workflow=Path(".github/workflows/m3-logger-probe.yml").read_text()
 maps=re.findall(r"^\s+(JTE_GOOGLE_[A-Z_]+): \$\{\{ secrets\.(JTE_GOOGLE_[A-Z_]+) \}\}",workflow,re.M)
 expected={"JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN"}
 assert len(maps)==6 and all(k==v for k,v in maps) and all(sum(k==v==name for k,v in maps)==2 for name in expected)
 t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")]);f=ensure_app_folder(t)
 run=os.environ["GITHUB_RUN_ID"];mode=sys.argv[1]
 if mode=="prepare":
  # Prior one-shot probe must be an executed, completed job before this NEW authorized one.
  url="https://api.github.com/repos/nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE/actions/runs/40748426658/jobs"
  request=urllib.request.Request(url,headers={"User-Agent":"M3-One-Probe-Guard"})
  with urllib.request.urlopen(request,timeout=20) as response:prior=json.load(response)
  jobs=prior.get("jobs",[]);assert len(jobs)==1 and jobs[0]["conclusion"]=="success"
  candidates=[s for s in jobs[0]["steps"] if s["name"]=="ONE tiny synthetic infrastructure trajectory"]
  assert len(candidates)==1 and candidates[0]["conclusion"]=="success","M3_PRIOR_PROBE_NOT_VERIFIED_STOP"
  ROOT.mkdir(mode=0o700,exist_ok=False)
  q=quota(t);assert q["availableBytes"]>3*1024**3
  names=["BTMS_M3_loggerProbe.m","BTMS_M3_completed.m","BTMS_M3_instrument.m","BTMS_M3_events.m"]
  gate={"run":run,"commit":os.environ["GITHUB_SHA"],"mappingNamesChecked":maps,"runtimeQuota":q,
   "candidateSHA256":{n:hashlib.sha256((Path("jte-public")/n).read_bytes()).hexdigest() for n in names},
   "fixedSourceCommits":["26a0152059c1659abdeba0b9599b0b3c5c9da699","12e22d5a482321b397d17423026cb609602f7caf","44816cab92c02e01eab9b92087b4a6122e2cd322"],
   "watchdogEvidenceReused":"40741741900","watchdogRerun":False,"physicalRun":False,"physicalApprovalConsumed":False}
  (ROOT/"PREPARE_GATE.json").write_text(json.dumps(gate,indent=2))
  print("M3_INFRA_SINK_READY mappingNames=PASS physicalRun=0")
 elif mode=="publish":
  # Preserve flags first and keep explicit receipts for zero-byte partial files.
  paths=sorted((p for p in ROOT.iterdir() if p.is_file()),key=lambda p:(p.suffix!=".json",p.name))
  rc={"run":run,"commit":os.environ["GITHUB_SHA"],"files":[],"emptyPartialFiles":[],"physicalRun":False,"G5Accepted":False}
  for p in paths:
   if p.stat().st_size==0:rc["emptyPartialFiles"].append(p.name);continue
   new=p.with_name("M3_LOGGER_"+run+"_"+p.name);p.rename(new)
   rc["files"].append({"name":new.name,**upload_verified(t,f,new,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")})
  r=ROOT/("M3_LOGGER_"+run+"_PRIVATE_RECEIPT.json");r.write_text(json.dumps(rc,indent=2))
  upload_verified(t,f,r,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
  print("M3_LOGGER_INFRA_PRIVATE_READBACK_PASS mappingNames=PASS physicalRun=0 G5_ACCEPTED=false")
 else:raise RuntimeError("MODE_DENIED")
if __name__=="__main__":
 try:main()
 except Exception as e:
  # No secret values or OAuth response bodies in logs.
  print("M3_INFRA_IO_UNQUALIFIED phase="+sys.argv[1]+" code="+(str(e) if re.fullmatch("[A-Z0-9_]+",str(e)) else type(e).__name__))
  raise SystemExit(1)
