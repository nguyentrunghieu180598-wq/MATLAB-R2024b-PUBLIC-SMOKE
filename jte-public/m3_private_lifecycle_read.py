"""Read two already verified M3 toy MAT files inside protected runner; no simulation."""
import json,os,sys
from pathlib import Path
import h5py,numpy as np
from JTE062_google_drive_synthetic import access_token,ensure_app_folder
from JTE101_io import one,download
from JTE063_streaming_drive import upload_verified
RUN="40798122691"
PREFIX="JTE063_VERIFIED_M3_LOGGER_"+RUN+"_"
MSG="M3_READ_EXISTING_TERMINAL_WITNESS_ONCE_20261029"
ROOT=Path("m3-private-readonly")
def decode_node(h,node,depth=0):
    if depth>5:raise RuntimeError("M3_HDF5_DEPTH")
    if isinstance(node,h5py.Group):
        return {k:decode_node(h,node[k],depth+1) for k in node if not k.startswith("#")}
    a=node[()]
    if hasattr(a,"dtype") and h5py.check_dtype(ref=a.dtype) is not None:
        vals=[decode_node(h,h[r],depth+1) if r else None for r in a.flat]
        return vals[0] if len(vals)==1 else vals
    if isinstance(a,np.ndarray):
        if node.attrs.get("MATLAB_class",b"") in (b"char","char"):
            return "".join(chr(int(x)) for x in a.flat if int(x)!=0)
        return a.item() if a.size==1 else a.tolist()
    return a.item() if isinstance(a,np.generic) else a
def main():
    e=json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    assert os.environ.get("GITHUB_REPOSITORY")=="nguyentrunghieu180598-wq/MATLAB-R2024b-PUBLIC-SMOKE"
    assert os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input"
    assert os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1"
    assert e["head_commit"]["message"]==MSG and e["head_commit"]["id"]==os.environ["GITHUB_SHA"]
    assert os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted"
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    token=access_token(*[os.environ[k] for k in keys]);folder=ensure_app_folder(token)
    ROOT.mkdir(mode=0o700,exist_ok=False)
    manifest=[]
    for role in ("PROBE_PARTIAL_LIFECYCLE","PROBE_PARTIAL_NATIVE_CLOCKS"):
        m=one(token,folder,PREFIX+role+".mat")
        manifest.append(download(token,m,ROOT/(role+".mat")))
    with h5py.File(ROOT/"PROBE_PARTIAL_LIFECYCLE.mat") as h:
        life=decode_node(h,h["lifecycle"])
        checkpointCount=len(h["checkpoints"]) if "checkpoints" in h else None
    with h5py.File(ROOT/"PROBE_PARTIAL_NATIVE_CLOCKS.mat") as h:
        clocks=decode_node(h,h["nativeClock"])
        last=decode_node(h,h["nativeLast"])
    def summarize(x):
        if x is None:return {"present":False}
        if not isinstance(x,list):x=[x]
        return {"present":True,"rows":len(x),"first":x[0] if x else None,"last":x[-1] if x else None}
    report={"sourceRun":RUN,"auditRun":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "inputSHA":manifest,"lifecycle":life,"checkpointCount":checkpointCount,
      "nativeClockSummary":[summarize(x) for x in clocks],
      "nativeLastPresent":[x is not None for x in last],
      "physicalRun":False,"G5Accepted":False}
    p=ROOT/"M3_TERMINAL_WITNESS_PRIVATE.json";p.write_text(json.dumps(report,indent=2,default=str))
    receipt=upload_verified(token,folder,p,schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
    (ROOT/"M3_TERMINAL_WITNESS_RECEIPT.json").write_text(json.dumps({"run":os.environ["GITHUB_RUN_ID"],"sourceRun":RUN,"output":receipt,"physicalRun":False},indent=2))
    upload_verified(token,folder,ROOT/"M3_TERMINAL_WITNESS_RECEIPT.json",schema="BTMS_M1_M2_STATIC_ONLY_NOT_G5")
    final=life.get("finalStepReturned")
    flag="TRUE" if final in (1,True,[1]) else "FALSE" if final in (0,False,[0]) else "UNAVAILABLE"
    print("M3_PRIVATE_WITNESS_READBACK_PASS finalstep="+flag+" physicalRun=0")
if __name__=="__main__":
    try:main()
    except Exception as e:
        print("M3_PRIVATE_WITNESS_BLOCKED code="+(str(e) if str(e).isupper() and "_" in str(e) else type(e).__name__))
        sys.exit(1)
