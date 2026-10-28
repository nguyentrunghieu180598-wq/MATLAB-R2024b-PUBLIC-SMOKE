"""Infrastructure-only receipt publisher; no battery initialization."""
import os,json,sys
from pathlib import Path
from JTE062_google_drive_synthetic import access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota
from sampled_actuator_review_io import ROOT
def main():
 t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")]);f=ensure_app_folder(t)
 run=os.environ["GITHUB_RUN_ID"];mode=sys.argv[1]
 if mode=="prepare":
  ROOT.mkdir(mode=0o700,exist_ok=False)
  q=quota(t);assert q["availableBytes"]>3*1024**3
  print("M3_INFRA_SINK_READY physicalRun=0")
 elif mode=="publish":
  paths=sorted(p for p in ROOT.iterdir() if p.is_file())
  rc={"run":run,"commit":os.environ["GITHUB_SHA"],"files":[],"physicalRun":False,"G5Accepted":False}
  for p in paths:
   new=p.with_name("M3_LOGGER_"+run+"_"+p.name);p.rename(new)
   rc["files"].append({"name":new.name,**upload_verified(t,f,new,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")})
  r=ROOT/("M3_LOGGER_"+run+"_PRIVATE_RECEIPT.json");r.write_text(json.dumps(rc,indent=2))
  upload_verified(t,f,r,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
  print("M3_LOGGER_INFRA_PRIVATE_READBACK_PASS physicalRun=0")
 else:raise RuntimeError("MODE_DENIED")
if __name__=="__main__":main()
