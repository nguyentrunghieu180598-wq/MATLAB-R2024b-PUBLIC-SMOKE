"""W107-01: classify existing stored native arrays, no oracle/simulation rerun."""
from __future__ import annotations
import json,os,re,sys
from pathlib import Path
import h5py
import numpy as np
from JTE101_io import one,download
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte107-private")
SCHEMA="JTE107_PRIVATE_MECHANISM_LEDGER_NOT_G5"
SOURCE_RUN="40485742742"
SOURCE_COMMIT="ceeb8a5590f9361016ad4c69004ffdc9e9223c94"
PREFIX="JTE106_"+SOURCE_RUN+"_AUDIT_"
def require(ok,code):
    if not ok:raise RuntimeError(code)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    require(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE107_SELECTOR_BOUNDARY_FLAG_COMPLETION" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"JTE107_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,cert=None):
    require(bool(re.fullmatch(r"[A-Za-z0-9_.-]+",name)),"JTE107_ASSET_NAME_INVALID")
    meta=download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/name)
    if cert is not None:
        require(name in cert and meta["sha256"]==cert[name]["sha256"] and meta["size"]==cert[name]["size_bytes"],
          "JTE107_SOURCE_RECEIPT_ASSET_MISMATCH")
    return meta,ROOT/name
def runs(mask,t):
    """Native row-presence runs only; endpoints are not event bounds or durations."""
    ix=np.flatnonzero(mask)
    if not len(ix):return {"countRecordedRows":0,"nativePresenceRuns":[]}
    cuts=np.flatnonzero(np.diff(ix)>1)+1
    chunks=np.split(ix,cuts)
    return {"countRecordedRows":int(len(ix)),"nativePresenceRuns":[
      {"firstRow1":int(g[0]+1),"lastRow1":int(g[-1]+1),
       "firstRecordedTime_s":float(t[g[0]]),"lastRecordedTime_s":float(t[g[-1]])} for g in chunks]}
def ulp_near(x,b):
    # Eight double spacings at the actual input scale; a conservative localization flag.
    # This NEVER changes raw u, L, or a D category.
    scale=np.maximum(np.abs(x),abs(b))
    tol=8*np.spacing(np.maximum(1.0,scale))
    return np.abs(x-b)<=tol
def classify(path,c,law):
    fields=("time_s","mxTrue","mxMeas","observedLoss","oracleLoss","uSameTrue","uSameFault",
      "qTrue","qFault","recordedCore","recordedPostfilter","sameStateDelta","channels")
    with h5py.File(path,"r") as f:
        require(all(k in f and isinstance(f[k],h5py.Dataset) for k in fields),"JTE107_EVIDENCE_DATASET_MISSING")
        d={}
        for k in fields:
            x=f[k][()]
            require(x.dtype.kind=="f" and x.dtype.itemsize==8 and np.all(np.isfinite(x)),
              "JTE107_EVIDENCE_NUMERIC_TYPE_INVALID")
            d[k]=x.reshape(-1)
    t=d["time_s"];n=len(t)
    require(n>1 and all(len(d[k])==n for k in fields if k!="channels") and
      t[0]==0 and t[-1]==2400 and np.all(np.diff(t)>=0),"JTE107_NATIVE_CLOCK_INVALID")
    L=d["observedLoss"];ut=d["uSameTrue"];uf=d["uSameFault"]
    require(np.all(L>=0) and np.all(ut>=law["step"]) and np.all(uf>=law["step"]),
      "JTE107_STORED_VALUE_OUTSIDE_QUALIFIED_SCOPE")
    require(np.array_equal(d["recordedCore"],uf),"JTE107_STORED_NATIVE_CORE_LINK_MISMATCH")
    ch=d["channels"]
    require(np.all(ch==np.floor(ch)) and np.all((ch>=1)&(ch<=312)) and
      np.array_equal(ch,np.asarray(c["injection"]["channels_1based"]).reshape(-1)),
      "JTE107_CHANNEL_LINK_MISMATCH")
    # Exact comparisons on stored MATLAB double arrays. No source-law recomputation.
    D=ut!=uf
    A=(L==0)&~D
    B=(L>0)&~D&(ut==law["step"])
    C=(L>0)&~D&(ut>law["step"])
    require(np.all(A.astype(int)+B.astype(int)+C.astype(int)+D.astype(int)==1),
      "JTE107_CLASSIFICATION_NOT_EXHAUSTIVE")
    ref=c["source"]["controllerReferenceK"]
    # Effective output-level thresholds of this verified controller are ref+5/ref+7.5.
    # q=.25 is also included as a conservative floor/quantizer interface marker,
    # although it is NOT a discontinuity of u=max(.25,q-mod(q,.25)).
    reasons={"SELECTOR_SMALL_POSITIVE_LOSS_WITHIN_PRIOR_NATIVE_K_BUDGET":
      (L>0)&(L<=c["source"]["sourceNativeFpBudget_K"])}
    for label,arr in (("TRUE",d["mxTrue"]),("MEAS",d["mxMeas"])):
        for delta in (5.0,7.5):
            reasons[label+"_T_REF_PLUS_"+str(delta)]=ulp_near(arr,ref+delta)
    for label,arr in (("TRUE",d["qTrue"]),("FAULT",d["qFault"])):
        for bound in (law["step"],2*law["step"],3*law["step"]):
            reasons[label+"_Q_BOUNDARY_"+str(bound)]=ulp_near(arr,bound)
    ambiguous=np.logical_or.reduce(list(reasons.values()))
    cats={"A_SELECTOR_MASKING":A,"B_FLOOR_MASKING":B,"C_QUANTIZER_MASKING":C,"D_RAW_NATIVE_CORE_CHANGE":D}
    counts={key:{"rawStoredCategory":runs(mask,t),
                "excludingThresholdAmbiguous":runs(mask&~ambiguous,t),
                "thresholdAmbiguousSubset":runs(mask&ambiguous,t)} for key,mask in cats.items()}
    design="JTE072_FIXED_GROUP" if c["selection"]["fixedGroupsSeparateDesign"] else "JTE067_SINGLE_SITE"
    require((design=="JTE072_FIXED_GROUP" and len(ch)>1) or (design=="JTE067_SINGLE_SITE" and len(ch)==1),
      "JTE107_CASE_DESIGN_CHANNEL_COUNT_MISMATCH")
    flags={"opaqueId":c["opaqueId"],"SOURCE_REF_K":ref,"CASE_DESIGN":design,
      "ANY_SELECTOR_LOSS":bool(np.any(L>0)),"ANY_FLOOR_MASKING":bool(np.any(B)),
      "ANY_QUANTIZER_MASKING":bool(np.any(C)),"ANY_IDEAL_OR_NATIVE_CORE_CHANGE":bool(np.any(D)),
      "NUMERIC_THRESHOLD_AMBIGUITY":bool(np.any(ambiguous)),
      "G6_PROTOCOL_DEVIATION_PRESENT":c["flags"]["G6_PROTOCOL_DEVIATION_PRESENT"],
      "JTE042_SINGLE_SITE_RANK_APPLICABLE":design=="JTE067_SINGLE_SITE",
      "A_PRESENT_NATIVE":bool(np.any(A)),"B_PRESENT_NATIVE":bool(np.any(B)),
      "C_PRESENT_NATIVE":bool(np.any(C)),"D_PRESENT_NATIVE":bool(np.any(D)),
      "G5_NUMERICAL_ACCEPTED":False,"G6_TEMPERATURE_CLAIM_AUTHORIZED":False}
    # No ideal Decimal oracle is evaluated: the requested combined flag is supplied by
    # actual STORED MATLAB-native u arrays only. D is retained even when ambiguous.
    details={"opaqueId":c["opaqueId"],"flags":flags,"nativeRecordedRows":n,
      "duplicateTimeRows":int(np.count_nonzero(np.diff(t)==0)),
      "source":c["source"],"injection":c["injection"],"selection":c["selection"],
      "sameFrame":c["sameFrame"],"priorSelector":c["selector"],
      "priorNativeSourceLaw":c["sameStateDecision"],"priorCrossTrajectory":c["crossTrajectoryCore"],
      "mechanismCategories":counts,"numericThresholdAmbiguous":runs(ambiguous,t),
      "selectorSmallPositiveLossBudget_K":c["source"]["sourceNativeFpBudget_K"],
      "ambiguityReasons":{k:runs(v,t) for k,v in reasons.items()},
      "rawDWithinAmbiguity":runs(D&ambiguous,t),
      "caseDesignEstimandStratum":design,
      "JTE042SingleSiteProtocolReproduction":False if design=="JTE067_SINGLE_SITE" else "NOT_APPLICABLE_SEPARATE_FIXED_GROUP_DESIGN",
      "nativeVsAccepted":"Recorded row presence only, not accepted solver steps, dwell times or independent observations.",
      "coreChangeFlagAuthority":"Stored MATLAB-native uSameTrue/uSameFault exact inequality; no new ideal/Python/Decimal source-law oracle.",
      "fullClockCrossTrajectoryIdentity":c["crossTrajectoryCore"]["fullRecordedCoreBitwiseIdentity"]}
    # Avoid carrying bulky redundant common-point tables into this mechanism ledger.
    details["priorCrossTrajectory"]={k:v for k,v in c["crossTrajectoryCore"].items() if k!="commonPointContrasts"}
    return flags,details
def main():
    t,f=context()
    ROOT.mkdir(mode=0o700,exist_ok=False)
    print("JTE107_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+
      " job="+os.environ["GITHUB_JOB"]+" matlabRun=0 simulationRun=0 syntheticTestsRepeated=0")
    receiptmeta,p=get(t,f,PREFIX+"RECEIPT.json")
    receipt=json.loads(p.read_text())
    require(receipt["run"]==SOURCE_RUN and receipt["commit"]==SOURCE_COMMIT and
      all(z["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" for z in receipt["files"]),
      "JTE107_SOURCE_EXECUTION_RECEIPT_INVALID")
    cert={z["name"]:z for z in receipt["files"]}
    resultmeta,p=get(t,f,PREFIX+"RESULTS.json",cert)
    a=json.loads(p.read_text())
    require(a["run"]==SOURCE_RUN and a["commit"]==SOURCE_COMMIT and len(a["cases"])==9 and
      not a["manifest"]["missing"] and not a["manifest"]["unqualifiedCandidates"],
      "JTE107_SOURCE_AUDIT_SCOPE_INVALID")
    lawmeta,p=get(t,f,PREFIX+"SOURCE_LAW.json",cert)
    law=json.loads(p.read_text())
    require(law["verified"] and law["gain"]==.1 and law["step"]==.25 and law["lower"]==.001 and law["upper"]==.95,
      "JTE107_QUALIFIED_SOURCE_LAW_UNAVAILABLE")
    references={}
    for r in a["references"]:
        label=r["label"];references[label]=r
    for profile in ("original","fine"):
        r=references["C0_"+profile+".mat"]
        require(r["B0L_C0_NATIVE_VECTOR_EQUIVALENCE"]=="PASS" and r["B0L_C0_fullClockAndT312Exact"] and
          r["B0L_C0_qualification"]["match"],"JTE107_PRIOR_B0L_C0_CERTIFICATE_UNQUALIFIED")
    active=references["ACTIVE_C0_original.mat"]
    require(active["frame"]==293.15 and active["sourceMATLABCoreMatch"] and
      active["B0L_C0_NATIVE_VECTOR_EQUIVALENCE"]=="NOT_AVAILABLE_FOR_THIS_FRAME_PROFILE",
      "JTE107_ACTIVE_REFERENCE_CERTIFICATE_INVALID")
    flags=[];cases=[];inputs=[receiptmeta,resultmeta,lawmeta]
    for c in a["cases"]:
        fl=c["flags"]
        require(all(fl[k] for k in ("DATA_QUALIFICATION","SAME_FRAME_MATCH","SELECTOR_ORACLE_PASS",
           "NEGATIVE_BIAS_ONLY","SOURCE_MATLAB_ORACLE_MATCH_AT_ARCHIVED_SAMPLES")) and
          not fl["G5_NUMERICAL_ACCEPTED"] and not fl["G6_TEMPERATURE_CLAIM_AUTHORIZED"],
          "JTE107_SOURCE_CASE_NOT_QUALIFIED")
        name=Path(c["evidenceFile"]["name"]).name
        meta,p=get(t,f,name,cert);inputs.append(meta)
        require(meta["sha256"]==c["evidenceFile"]["SHA256"],"JTE107_CASE_EVIDENCE_HASH_LINK_MISMATCH")
        flag,detail=classify(p,c,law);detail["inputEvidence"]=meta
        flags.append(flag);cases.append(detail)
        print("JTE107_CASE_METADATA "+json.dumps(flag,separators=(",",":")))
    anyD=any(z["ANY_IDEAL_OR_NATIVE_CORE_CHANGE"] for z in flags)
    decision="RECORDED_D_PRESENT_CHAT_REVIEW_ONLY_NO_EXPERIMENT_AUTHORIZED" if anyD else "NO_NEW_PHYSICAL_RUN"
    dictionary={"A":"L==0 and stored u_true==u_fault: selector masking.",
      "B":"L>0 and stored u_true==u_fault==.25: floor masking.",
      "C":"L>0 and stored u_true==u_fault>.25: quantizer masking.",
      "D":"Exact raw inequality of STORED MATLAB source-native u_true/u_fault. Takes precedence, never rounded or removed.",
      "ambiguous":"Separate overlay also includes 0<L<=the prior JTE106 temperature-operation8ULP budget (near selector L=0). Existing source-control flags remain: within8 double spacings of Tref+5/Tref+7.5 or stored saturated q=.25/.5/.75, at max(1,abs(value),abs(boundary)) scale. q=.25 is a conservative interface marker, not an output jump.",
      "counts":"Raw native recorded rows, no time fractions/durations/statistical replicate interpretation. Counts excluding ambiguity are also reported; raw D always remains visible.",
      "presenceRuns":"Contiguous row-index runs with first/last recorded timestamps, not accepted-event brackets or durations.",
      "idealOrNativeFlag":"Uses stored native MATLAB outputs ONLY; ideal/static tests were not repeated.",
      "uncertainty":"Threshold proximity flag is numerical localization, not certified roundoff error bound or physical significance.",
      "protocol":"Single sites and fixed groups remain separate; no re-selection or legacy relabeling.",
      "thermal":"No causal temperature/actuation/convergence claim."}
    ledger={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "executor":"GITHUB_HOSTED_ACTIONS","job":os.environ["GITHUB_JOB"],
      "sourceRun":SOURCE_RUN,"sourceCommit":SOURCE_COMMIT,
      "numericAmbiguityCoverageCompletion":{"initialRun":"40523566508","reason":"Initial mechanism ledger localized control thresholds but did not separately flag selector small-positive-loss rows. Raw A/B/C/D definitions and data remain unchanged; initial ledger retained."},
      "inputs":inputs,"cases":cases,"publicMetadata":flags,
      "sourceReferenceAudit":{"mode":"REUSE_SHA_VERIFIED_JTE106_CERTIFICATES_NO_T312_OR_MATLAB_RERUN",
        "source300OriginalAndFine":"B0L_C0_FULL_NATIVE_CLOCK_T312_EXACT_CERTIFICATES_PASS",
        "active293p15":"C0_REFERENCE_QUALIFIED_WITHIN_FRAME; NO_ARCHIVED_B0L_COUNTERPART_FABRICATED",
        "references":list(references.values())},
      "dataDictionary":dictionary,
      "scientificGates":{"validatedSameStateSelectorMasking":True,
        "nativeSourceLawControllerResponseNull":not anyD,
        "acceptedBiasCausedActuatorEvent":"UNPROVEN","causalTrueTemperatureOrSolverResolvedThermalChange":"UNPROVEN",
        "G5_PROVENANCE":"PASS_REUSED","G5_ACTUATION_EVENT":"UNPROVEN","G5_THERMAL_CONVERGENCE":"UNPROVEN"},
      "decision":decision,"newExperimentAuthorized":False,"newMATLABExecution":False,
      "syntheticTestsRepeated":False,"newSimulationRun":False,"stopAfterThisExplanation":True}
    stem="JTE107_"+os.environ["GITHUB_RUN_ID"]
    p=ROOT/(stem+"_PRIVATE_MECHANISM_LEDGER.json")
    p.write_text(json.dumps(ledger,indent=2))
    outputs=[{"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)}]
    # Permitted Boolean/category metadata only; full counts, IDs, filenames, hashes stay private.
    metaout={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "cases":flags,"decision":decision,"G5_NUMERICAL_ACCEPTED":False,"G6_TEMPERATURE_CLAIM_AUTHORIZED":False}
    p=ROOT/(stem+"_METADATA_FLAGS.json");p.write_text(json.dumps(metaout,indent=2))
    outputs.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(stem+"_PRIVATE_READBACK_RECEIPT.json")
    p.write_text(json.dumps({"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "sourceRun":SOURCE_RUN,"inputReceipt":receiptmeta,"files":outputs,"newSimulationRun":False},indent=2))
    upload_verified(t,f,p,schema=SCHEMA)
    print("JTE107_PRIVATE_LEDGER_SHA_READBACK_PASS decision="+decision+
      " matlabRun=0 simulationRun=0 syntheticTestsRepeated=0 G5_NUMERICAL_ACCEPTED=false G6_TEMPERATURE_CLAIM_AUTHORIZED=false")
if __name__=="__main__":
    try:main()
    except Exception as exc:
        code=str(exc)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE107_PRIVATE_MECHANISM_FAILED"
        print("JTE107_BLOCKED code="+code);sys.exit(1)
