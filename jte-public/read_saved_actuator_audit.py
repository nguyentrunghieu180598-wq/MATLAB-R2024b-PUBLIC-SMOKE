"""Read-only decode of OUR saved static parameter diff. No model/solver execution."""
import json,os,sys
from pathlib import Path
import h5py,numpy as np
from sampled_actuator_review_io import get,need,ROOT,SCHEMA
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
def main():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="BTMS_READ_SAVED_STATIC_AUDIT" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"ACT_DIFF_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    folder=ensure_app_folder(t);ROOT.mkdir(mode=0o700,exist_ok=False)
    diff=get(t,folder,"ACTUATOR_REVIEW_40656346517_B0L_Ref_AUDIT_DIFF.mat","audit.mat")
    receipt=get(t,folder,"ACTUATOR_REVIEW_40656346517_PRIVATE_RECEIPT.json","receipt.json")
    rc=json.loads((ROOT/"receipt.json").read_text())
    linked=[x for x in rc["files"] if x["name"]==diff["name"].removeprefix("JTE063_VERIFIED_")]
    need(rc["run"]=="40656346517" and len(linked)==1 and linked[0]["sha256"]==diff["sha256"] and
      linked[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","ACT_DIFF_RECEIPT_LINK")
    with h5py.File(ROOT/"audit.mat","r") as f:
        cache={};active=set()
        def read(x):
            if x.name in cache:return cache[x.name]
            if x.name in active:return {"cycleReference":x.name}
            active.add(x.name)
            if isinstance(x,h5py.Group):
                out={k:read(v) for k,v in x.items() if not k.startswith("#")}
            else:
                a=x[()];kind=x.attrs.get("MATLAB_class",b"")
                if isinstance(kind,bytes):kind=kind.decode()
                if h5py.check_dtype(ref=x.dtype) is not None:
                    vals=np.asarray(a).T
                    if vals.size==0:out=[]
                    else:
                        out=[[read(f[r]) if r else None for r in row] for row in vals.reshape(vals.shape[0],-1)]
                        if vals.shape[0]==1:out=out[0]
                elif kind=="char":
                    vals=np.asarray(a).T
                    if vals.size==0:out=""
                    else:
                        rows=["".join(chr(int(v)) for v in row) for row in vals.reshape(vals.shape[0],-1)]
                        out=rows[0] if len(rows)==1 else rows
                else:
                    vals=np.asarray(a).T
                    if vals.size==1:out=vals.reshape(-1)[0].item()
                    else:out=vals.tolist()
            active.remove(x.name);cache[x.name]=out;return out
        data={k:read(f[k]) for k in ("before","after","initialDifference","solverRestored")}
    before={r[0]:r for r in data["before"]["blocks"]}
    after={r[0]:r for r in data["after"]["blocks"]}
    changes=[]
    for name in sorted(set(before)|set(after)):
        b=before.get(name);a=after.get(name)
        if b==a:continue
        row={"block":name,"beforeType":b[1] if b else None,"afterType":a[1] if a else None,"parameters":[]}
        if b and a and isinstance(b[2],list) and len(b[2])==2 and isinstance(a[2],list) and len(a[2])==2:
            pb=dict(zip(b[2][0],b[2][1]));pa=dict(zip(a[2][0],a[2][1]))
            for key in sorted(set(pb)|set(pa)):
                if pb.get(key)!=pa.get(key):row["parameters"].append({"key":key,"before":pb.get(key),"after":pa.get(key)})
        else:row.update({"before":b,"after":a})
        changes.append(row)
    report={"schema":SCHEMA,"scope":"READ_ONLY_SAVED_STATIC_DIFF_NO_COMPILE_NO_SIM","run":os.environ["GITHUB_RUN_ID"],
      "commit":os.environ["GITHUB_SHA"],"sourceRun":"40656346517","sourceDiff":diff,"sourceReceipt":receipt,
      "initialDifference":data["initialDifference"],"solverRestored":data["solverRestored"],
      "finalConfigEqual":data["before"]["config"]==data["after"]["config"],"changedBlocks":changes,
      "toyRun":False,"physicalRun":False}
    p=ROOT/("ACTUATOR_REVIEW_"+os.environ["GITHUB_RUN_ID"]+"_SAVED_AUDIT_DECODE.json")
    p.write_text(json.dumps(report,indent=2,ensure_ascii=True));proof=upload_verified(t,folder,p,schema=SCHEMA)
    q=ROOT/("ACTUATOR_REVIEW_"+os.environ["GITHUB_RUN_ID"]+"_DECODE_RECEIPT.json")
    q.write_text(json.dumps({"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[{"name":p.name,**proof}]}))
    upload_verified(t,folder,q,schema=SCHEMA)
    print("ACTUATOR_SAVED_AUDIT_READBACK_PASS compileRun=0 toyRun=0 physicalRun=0 parameterDiffPresent="+str(bool(changes)).lower())
if __name__=="__main__":
    try:main()
    except Exception:print("ACTUATOR_SAVED_AUDIT_UNQUALIFIED details=PRIVATE_INPUT_ONLY");sys.exit(1)
