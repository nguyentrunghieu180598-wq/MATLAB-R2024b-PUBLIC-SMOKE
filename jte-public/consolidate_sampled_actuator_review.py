"""Consolidate verified STATIC compile proofs; no MATLAB, model load or simulation."""
import hashlib,json,math,os,sys
from pathlib import Path
import h5py
from sampled_actuator_review_io import ROOT,SCHEMA,get,need
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
SOURCE_RUN="40659584085"
SOURCE_COMMIT="5ebb693c5109fe79c0b32374613637f4beecccd5"
MESSAGE="BTMS_CONSOLIDATE_SAVED_STATIC_PROOFS"
def main():
    ev=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (ev.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (ev.get("head_commit") or {}).get("message")==MESSAGE and
      (ev.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","STATIC_FINAL_CONTEXT_DENIED")
    token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    folder=ensure_app_folder(token);ROOT.mkdir(mode=0o700,exist_ok=False)
    prefix="ACTUATOR_REVIEW_"+SOURCE_RUN+"_"
    rcmeta=get(token,folder,prefix+"PRIVATE_RECEIPT.json","receipt.json")
    rc=json.loads((ROOT/"receipt.json").read_text())
    need(rc["run"]==SOURCE_RUN and rc["commit"]==SOURCE_COMMIT and not rc["physicalSimulation"] and not rc["toySimulation"],"STATIC_FINAL_SOURCE_SCOPE")
    inputs=[]
    def archived(suffix,local):
        m=get(token,folder,prefix+suffix,local);name=m["name"].removeprefix("JTE063_VERIFIED_")
        rows=[x for x in rc["files"] if x["name"]==name]
        need(len(rows)==1 and rows[0]["sha256"]==m["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","STATIC_FINAL_RECEIPT_LINK")
        inputs.append(m);return json.loads((ROOT/local).read_text())
    summary=archived("SUMMARY.json","summary.json")
    need(summary["failure"]["stage"]=="RESOURCE_SCREEN" and summary["failure"]["identifier"]=="MATLAB:heterogeneousStrucAssignment" and
      summary["flags"]["DECISION"]=="STATIC_REVIEW_UNQUALIFIED","STATIC_FINAL_EXPECTED_RESOURCE_SOFTWARE_FAILURE")
    manifest=archived("INPUT_MANIFEST.json","manifest.json")
    need(manifest["run"]==SOURCE_RUN and manifest["commit"]==SOURCE_COMMIT and not manifest["physicalSimulationAuthorized"],"STATIC_FINAL_MANIFEST")
    proofs=[];units_same=True;units_explicit=True
    for case in ("B0L","C0"):
        for role,Ts in (("Ref",.01),("Fine",.005)):
            q=archived(case+"_"+role+"_PROOF.json",case+"_"+role+".json");p=q["proof"]
            need(q["caseSource"]==case and q["role"]==role and p["Ts_s"]==Ts and p["tau_s"]==.001 and p["C"]==1 and p["D"]==0,"STATIC_FINAL_METHOD")
            keys=("physicalParameterParity","retainedControllerParameterParity","retainedInitializationParameterParity",
              "outsideExactEndpointsConnectivityParity","localEdgesExact","sourceWireNamesPreserved")
            need(all(p[k] is True for k in keys) and not p["originalSolverPolicyRestoredAfterEditorAutoChange"] and
              q["biasMechanismPreserved"] is True and q["modelWorkspaceICParametersExact"] is True and
              not p["physicalSimulation"] and not p["toySimulation"] and not q["G5Accepted"],"STATIC_FINAL_PARITY")
            need(q["amendedCompile"]["actuator"]["sampleTime"]==[Ts,0] and q["amendedCompile"]["hold"]["sampleTime"]==[Ts,0] and
              q["amendedCompile"]["trueVectorWidth"]==312 and q["controllerCompiledRateSame"] is True,"STATIC_FINAL_COMPILE_CLOCK")
            units_same=units_same and q["unitsMetadataParity"];units_explicit=units_explicit and q["unitsExplicit"]
            model_name=prefix+case+"_"+role+"_MODEL.slx";models=[x for x in rc["files"] if x["name"]==model_name]
            need(len(models)==1 and models[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" and models[0]["sha256"]==p["amendedModelSHA"],"STATIC_FINAL_MODEL_RECEIPT")
            proofs.append(q)
    # Reuse negative study only for measured cost, never thermal truth.
    nm=get(token,folder,"JTE116ONE_40645118578_PLANT_RAW.mat","negative.mat")
    prior=[x for x in manifest["files"] if x["local"]=="negative_raw.mat"]
    need(len(prior)==1 and prior[0]["sha256"]==nm["sha256"],"STATIC_FINAL_RESOURCE_SOURCE")
    benchmark={"sourceRun":"40645118578","scope":"Rejected-source saved execution cost only, not amended runtime prediction or thermal truth"}
    try:
        with h5py.File(ROOT/"negative.mat","r") as f:
            benchmark["elapsedWall_s"]=float(f["r/elapsedWall_s"][()].reshape(-1)[0])
            benchmark["savedStateWidth"]=int(f["r/resourcePreflight/savedStateWidth"][()].reshape(-1)[0])
            benchmark["nativeRows"]=math.prod(f["r/observed/time"].shape)
        need(benchmark["elapsedWall_s"]>0 and benchmark["savedStateWidth"]>0 and benchmark["nativeRows"]>0,"STATIC_FINAL_COST_METADATA")
        benchmark["availability"]="AVAILABLE"
    except Exception:
        benchmark={"sourceRun":"40645118578","availability":"UNAVAILABLE_HDF5_COST_LAYOUT","scope":"No runtime/memory extrapolation inferred"}
    scenarios=[]
    for horizon in (340,2400):
        for Ts in (.01,.005):
            rows=math.ceil(horizon/Ts)+1
            z={"horizon_s":horizon,"Ts_s":Ts,"minimumScheduledRows":rows,"T312_singleCopy_bytes":rows*312*8,
              "runtimeIsMeasuredForAmendedModel":False}
            if benchmark["availability"]=="AVAILABLE":
                z["legacyThreeCopyLogging_bytes"]=3*rows*8*(benchmark["savedStateWidth"]+2*312+32)
                z["oldRuntimeLinearScreen_s"]=benchmark["elapsedWall_s"]*rows/benchmark["nativeRows"]
            scenarios.append(z)
    resource={"scope":"COST_SCREEN_ONLY_NOT_FULL_THERMAL_QUALIFICATION","sourceCompileResource":manifest["resource"],
      "benchmark":benchmark,"scenarios":scenarios,"currentFullStateLoggerFullThermalStatus":"NO_GO_UNQUALIFIED",
      "essentialSignalBoundedStatePlan":"PROPOSED_NOT_IMPLEMENTED_NOT_QUALIFIED",
      "limits":"Sampling changes model/grid. Screening is not a benchmark, error bound, future performance guarantee or spending authorization."}
    flags={"DECISION":"STATIC_COMPILE_REVIEW_READY" if units_same and units_explicit else "STATIC_COMPILE_REVIEW_WITH_UNIT_LIMITATIONS",
      "PER_CASE_STATIC_COMPILE_PROOFS_VERIFIED":True,"COMPILE_ALL":True,"PHYSICAL_GRAPH_PARITY":True,
      "CONTROLLER_BIAS_PRESERVED":True,"IC_PARAMETERS_PRESERVED":True,"ARCHIVED_Y0_USED":True,
      "UNIT_METADATA_PARITY":units_same,"UNIT_METADATA_EXPLICIT":units_explicit,"OWNER_METHOD_APPROVAL":False,
      "TOY_RUN":False,"PHYSICAL_RUN":False,"G5_ACCEPTED":False,"SOURCE_G5_FINAL_THERMAL_REJECTED":True}
    report={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"execution":"PYTHON_READ_ONLY_CONSOLIDATION",
      "sourceCompileRun":SOURCE_RUN,"sourceCompileCommit":SOURCE_COMMIT,"sourceGlobalSummary":summary,"sourceReceipt":rcmeta,"inputs":inputs,
      "flags":flags,"proofs":proofs,"resourceScreen":resource,
      "history":"The original resource-helper UNQUALIFIED record is immutable. Four per-model MATLAB static/compile proofs completed before that helper failed. This consolidation executes no MATLAB and repeats no compile.",
      "limitations":["Source actuator unit metadata blank: equality is not independent physical unit certification.",
        "Only parameter/workspace IC parity; solved physical IC unproven.","No amended trajectory, recurrence-clock toy, thermal convergence or scientific G5.",
        "10/5ms method and persistent-decision latency budget await owner/scientific approval."]}
    run=os.environ["GITHUB_RUN_ID"];base="ACTUATOR_REVIEW_"+run+"_"
    files=[]
    for suffix,data in (("CONSOLIDATED_REVIEW.json",report),("RESOURCE_SCREEN.json",resource),("FLAGS.json",flags)):
        p=ROOT/(base+suffix);p.write_text(json.dumps(data,indent=2,ensure_ascii=True))
        files.append({"name":p.name,**upload_verified(token,folder,p,schema=SCHEMA)})
    receipt={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"sourceCompileRun":SOURCE_RUN,
      "files":files,"physicalSimulation":False,"toySimulation":False,"G5Accepted":False}
    p=ROOT/(base+"CONSOLIDATED_RECEIPT.json");p.write_text(json.dumps(receipt,indent=2));upload_verified(token,folder,p,schema=SCHEMA)
    print("STATIC_COMPILE_CONSOLIDATION_READBACK_PASS sourceRun="+SOURCE_RUN+" compileRepeated=0 toyRun=0 physicalRun=0 UNIT_METADATA_PARITY="+str(units_same).lower()+" UNIT_METADATA_EXPLICIT="+str(units_explicit).lower()+" G5_ACCEPTED=false")
if __name__=="__main__":
    try:main()
    except Exception:print("STATIC_COMPILE_CONSOLIDATION_UNQUALIFIED details=OWNER_PRIVATE_ONLY");sys.exit(1)
