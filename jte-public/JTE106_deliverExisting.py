"""Private delivery of an existing MATLAB result. No MAT load, oracle or simulation."""
import json,os,re
from pathlib import Path
from JTE101_io import one,download
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte106-delivery-private")
EXPECTED="2ccb7f79ac578f7a559769adadc7b718d4eb6cb44ffdd7d8dd31e0573feec38f"
def compact(x):
    if isinstance(x,dict):return {k:compact(v) for k,v in x.items()}
    if isinstance(x,list):
        if len(x)>32:return {"omittedArrayLength":len(x),"originalArrayRetainedInImmutableFullResults":True}
        return [compact(v) for v in x]
    return x
def main():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if (os.environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or
        os.environ.get("GITHUB_REF")!="refs/heads/codex/jte-tf-constant-input" or
        os.environ.get("GITHUB_EVENT_NAME")!="push" or os.environ.get("GITHUB_RUN_ATTEMPT")!="1" or
        (e.get("head_commit") or {}).get("message")!="JTE106_DELIVER_EXISTING_RESULT_ONLY" or
        (e.get("head_commit") or {}).get("id")!=os.environ.get("GITHUB_SHA")):
        raise RuntimeError("JTE106_DELIVERY_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    f=ensure_app_folder(t)
    ROOT.mkdir(mode=0o700,exist_ok=False)
    name="JTE106_40485742742_AUDIT_RESULTS.json"
    src=download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/name)
    if src["sha256"]!=EXPECTED:raise RuntimeError("JTE106_ORIGINAL_RESULTS_SHA_MISMATCH")
    a=json.loads((ROOT/name).read_text())
    if a["run"]!="40485742742" or a["commit"]!="ceeb8a5590f9361016ad4c69004ffdc9e9223c94":
        raise RuntimeError("JTE106_ORIGINAL_EXECUTION_MISMATCH")
    # Summarize pre-existing scalar decisions only. No scientific metric recomputation.
    classification=[]
    for c in a["cases"]:
        x=c["crossTrajectoryCore"];s=c["sameStateDecision"]
        classification.append({"opaqueId":c["opaqueId"],
          "SAME_STATE_NATIVE_MATLAB_DECISION_CONTRAST_PRESENT":s["nonzeroDecisionAtNativeRows"]>0,
          "CROSS_TRAJECTORY_RECORDED_CORE_CONTRAST_PRESENT":any(x.get(k,False) for k in
             ("anyExactCommonCoreContrast","anyDisjointTransitionBracket","anyNewRawLevel","sequenceDiffers")),
          "scope":"Stored native evidence only. Neither flag certifies accepted events or thermal causality."})
    out={"schema":"JTE106_NATIVE_CORE_AUDIT_NOT_G5","sourceExecutionRun":a["run"],"sourceCommit":a["commit"],
      "sourceResultsSHA256":EXPECTED,"deliveryRun":os.environ["GITHUB_RUN_ID"],"deliveryCommit":os.environ["GITHUB_SHA"],
      "deliveryOnly":True,"newMATLABExecution":False,"newOracleTests":False,"newSimulationRun":False,
      "largeArrayPolicy":"Arrays longer than32 omitted from digest only, immutable original JSON/MAT retained with SHA.",
      "separateDecisionEvidence":classification,"audit":compact(a)}
    p=ROOT/("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT_REVIEW_DIGEST.json")
    p.write_text(json.dumps(out,indent=2))
    receipt={"schema":"JTE106_NATIVE_CORE_AUDIT_NOT_G5","deliveryRun":os.environ["GITHUB_RUN_ID"],
      "sourceResultsSHA256":EXPECTED,"files":[{"name":p.name,**upload_verified(t,f,p,schema="JTE106_NATIVE_CORE_AUDIT_NOT_G5")}],
      "newMATLABExecution":False,"newSimulationRun":False}
    p=ROOT/("JTE106_"+os.environ["GITHUB_RUN_ID"]+"_AUDIT_REVIEW_RECEIPT.json")
    p.write_text(json.dumps(receipt,indent=2));upload_verified(t,f,p,schema="JTE106_NATIVE_CORE_AUDIT_NOT_G5")
    print("JTE106_EXISTING_RESULTS_DIGEST_PRIVATE_READBACK_PASS sourceRun=40485742742 matlabRerun=0 simulationRun=0 oracleTestsRepeated=0 rawValuesPublished=0")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE106_DELIVERY_FAILED"
        print("JTE106_DELIVERY_BLOCKED code="+c);raise SystemExit(1)
