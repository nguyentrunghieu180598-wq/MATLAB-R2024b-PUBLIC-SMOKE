"""W108-01: read-only fixed-state critical-bias endpoint from existing native MAT."""
from __future__ import annotations
import json,os,re,sys,math
from pathlib import Path
import h5py
import numpy as np
from JTE101_io import one,download
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified,sha_file
ROOT=Path("jte108-private")
SCHEMA="JTE108_PRIVATE_CRITICAL_BIAS_NOT_G5"
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
R106="40485742742";C106="ceeb8a5590f9361016ad4c69004ffdc9e9223c94"
R107="40524182276";C107="551e870ea41057e61e0cd053be4888afbb8d2fbe"
P106="JTE106_"+R106+"_AUDIT_";P107="JTE107_"+R107+"_"
STAGE="CONTEXT"
def need(ok,code):
    if not ok:raise RuntimeError(code)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE108_ONE_READONLY_CRITICAL_BIAS_AUDIT" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"JTE108_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,cert=None,expected=None):
    need(bool(re.fullmatch(r"[A-Za-z0-9_.-]+",name)),"JTE108_ASSET_NAME_INVALID")
    remote=name if name.startswith("JTE063_VERIFIED_") else "JTE063_VERIFIED_"+name
    local=name.removeprefix("JTE063_VERIFIED_")
    meta=download(t,one(t,f,remote),ROOT/local)
    if cert is not None:
        need(local in cert and meta["sha256"]==cert[local]["sha256"] and meta["size"]==cert[local]["size_bytes"],
          "JTE108_RECEIPT_HASH_LINK_MISMATCH")
    if expected is not None:need(meta["sha256"]==expected,"JTE108_PRIOR_ARCHIVE_HASH_MISMATCH")
    return meta,ROOT/local
def readjson(t,f,name,cert=None):
    m,p=get(t,f,name,cert);return m,json.loads(p.read_text())
def deref(f,x):
    for _ in range(8):
        if isinstance(x,h5py.Dataset) and h5py.check_dtype(ref=x.dtype) is not None:
            a=x[()];need(a.size==1,"JTE108_NONSCALAR_STRUCT_REFERENCE")
            ref=a.reshape(-1)[0];need(bool(ref),"JTE108_EMPTY_STRUCT_REFERENCE")
            x=f[ref]
        else:return x
    raise RuntimeError("JTE108_REFERENCE_DEPTH")
def node(f,path):
    x=f
    for key in path.split("/"):
        x=deref(f,x);need(isinstance(x,h5py.Group) and key in x,"JTE108_HDF5_FIELD_UNAVAILABLE")
        x=x[key]
    return deref(f,x)
def numeric(f,path):
    x=node(f,path)
    need(isinstance(x,h5py.Dataset) and x.dtype.kind=="f" and x.dtype.itemsize==8,"JTE108_HDF5_DOUBLE_REQUIRED")
    a=x[()];need(np.all(np.isfinite(a)),"JTE108_NONFINITE_NATIVE_VALUES")
    return a
def scalar(f,path):
    a=numeric(f,path);need(a.size==1,"JTE108_SCALAR_REQUIRED");return float(a.reshape(-1)[0])
def textfield(f,path):
    x=node(f,path)
    need(isinstance(x,h5py.Dataset) and x.dtype.kind in "ui","JTE108_HDF5_CHAR_REQUIRED")
    return "".join(chr(int(v)) for v in x[()].reshape(-1) if int(v))
def presence(mask,t):
    ix=np.flatnonzero(mask)
    if not len(ix):return {"recordedRows":0,"nativeRowPresenceRuns":[]}
    parts=np.split(ix,np.flatnonzero(np.diff(ix)>1)+1)
    return {"recordedRows":int(len(ix)),"nativeRowPresenceRuns":[
      {"firstRow1":int(g[0]+1),"lastRow1":int(g[-1]+1),
       "firstRecordedTime_s":float(t[g[0]]),"lastRecordedTime_s":float(t[g[-1]])} for g in parts]}
def brief_prior_case(c):
    return {k:c[k] for k in ("source","injection","selection","sameFrame","selector","sameStateDecision","flags")}
def read_evidence(path):
    keys=("time_s","mxTrue","mxMeas","uSameTrue","uSameFault","observedLoss","oracleLoss","channels")
    with h5py.File(path,"r") as f:
        return {k:numeric(f,k).reshape(-1) for k in keys}
def raw_AB(path,c,d):
    t=d["time_s"];n=len(t)
    with h5py.File(path,"r") as f:
        need(textfield(f,"record/schema") in ("JTE067_C1_NATIVE_V1","JTE072_GROUP3_C1_NATIVE_V1"),
          "JTE108_NATIVE_SCHEMA_INVALID")
        need(textfield(f,"record/sourceSHA256")==PIN and
          textfield(f,"record/generatedModelSHA256")==c["source"]["generatedModelSHA"] and
          textfield(f,"record/load/SHA256")==c["source"]["loadSHA"] and
          textfield(f,"record/caseName")==c["source"]["caseName"] and
          textfield(f,"record/profile")==c["source"]["profile"] and
          "24.2.0.3361896" in textfield(f,"record/matlabVersion") and
          textfield(f,"record/units/temperature")=="K" and textfield(f,"record/units/time")=="s",
          "JTE108_NATIVE_SOURCE_FRAME_INVALID")
        ref=scalar(f,"record/ambient/valueK")
        need(ref==c["source"]["controllerReferenceK"] and ref in (300,293.15),"JTE108_NATIVE_REFERENCE_MISMATCH")
        need(scalar(f,"record/injection/biasK")==-2,"JTE108_NATIVE_BIAS_NOT_LOCKED")
        group=c["selection"]["fixedGroupsSeparateDesign"]
        key="channels_1based" if group else "channel_1based"
        ch=numeric(f,"record/injection/"+key).reshape(-1)
        need(np.array_equal(ch,np.asarray(c["injection"]["channels_1based"]).reshape(-1)) and
          np.array_equal(ch,d["channels"]) and np.all(ch==np.floor(ch)) and
          len(np.unique(ch))==len(ch) and len(ch)>0 and len(ch)<312 and np.all((ch>=1)&(ch<=312)),
          "JTE108_NATIVE_GROUP_MEMBERSHIP_MISMATCH")
        ti=numeric(f,"record/signalData/jteTtrue/time_s").reshape(-1)
        need(np.array_equal(t,ti) and t[0]==0 and t[-1]==2400 and np.all(np.diff(t)>=0),
          "JTE108_NATIVE_CLOCK_MISMATCH")
        x=node(f,"record/signalData/jteTtrue/values")
        need(isinstance(x,h5py.Dataset) and x.dtype.kind=="f" and x.dtype.itemsize==8 and x.shape in ((312,n),(n,312)),
          "JTE108_NATIVE_T312_SHAPE")
        channels=ch.astype(np.int64)-1
        keep=np.ones(312,dtype=bool);keep[channels]=False
        A=np.empty(n);B=np.empty(n)
        # Chunk full vectors; no 1s interpolation, time sorting or channel re-selection.
        for left in range(0,n,4096):
            right=min(n,left+4096)
            v=x[:,left:right].T if x.shape==(312,n) else x[left:right,:]
            need(np.all(np.isfinite(v)),"JTE108_NONFINITE_T312")
            A[left:right]=np.max(v[:,channels],axis=1)
            B[left:right]=np.max(v[:,keep],axis=1)
    return A,B,ref,ch
def audit_case(rawpath,evpath,c,old,law,stem):
    d=read_evidence(evpath);t=d["time_s"];n=len(t)
    need(all(len(d[k])==n for k in d if k!="channels"),"JTE108_EVIDENCE_LENGTH")
    A,B,ref,ch=raw_AB(rawpath,c,d)
    mx=np.maximum(A,B);m2=np.maximum(A-2,B);m3=np.maximum(A-3,B)
    need(np.array_equal(mx,d["mxTrue"]) and np.array_equal(m2,d["mxMeas"]),
      "JTE108_T312_EVIDENCE_MAX_LINK_MISMATCH")
    theta=np.asarray([ref+5,ref+7.5],dtype=np.float64)
    eligible=(B[:,None]<theta[None,:])&(theta[None,:]<=A[:,None])
    distance=A[:,None]-theta[None,:]
    critical=np.min(np.where(eligible,distance,np.inf),axis=1)
    finite=np.isfinite(critical)
    strict2=eligible&(2>distance);strict3=eligible&(3>distance)
    cross2=(m2[:,None]<theta[None,:])&(theta[None,:]<=mx[:,None])
    cross3=(m3[:,None]<theta[None,:])&(theta[None,:]<=mx[:,None])
    theoremMismatch=np.any(strict2!=cross2,axis=1)|np.any(strict3!=cross3,axis=1)
    count2=np.sum(strict2,axis=1);count3=np.sum(strict3,axis=1)
    pred2=count2>0;pred3=count3>0
    ut=d["uSameTrue"];uf=d["uSameFault"]
    native2=ut!=uf
    predictedFault2=ut-law["step"]*count2
    mismatch2=(pred2!=native2)|(predictedFault2!=uf)|theoremMismatch
    # A three-K oracle is reused only at exactly the SAME input Max and frame.
    sameTrue3=m3==d["mxTrue"];sameFault3=m3==d["mxMeas"]
    covered3=sameTrue3|sameFault3
    knownU3=np.full(n,np.nan);knownU3[sameTrue3]=ut[sameTrue3];knownU3[sameFault3]=uf[sameFault3]
    conflicting3=sameTrue3&sameFault3&(ut!=uf)
    predictedFault3=ut-law["step"]*count3
    mismatch3=covered3&(predictedFault3!=knownU3)
    # Localize eligibility and strict bias/threshold boundaries at the inherited K budget.
    budget=float(c["source"]["sourceNativeFpBudget_K"])
    boundaryReasons={}
    for name,arr in (("A",A),("B",B),("FAULT_MAX_2",m2),("FAULT_MAX_3",m3)):
        for j,th in enumerate(theta):
            boundaryReasons[name+"_NEAR_THETA_"+str(j+1)]=np.abs(arr-th)<=budget
    boundary=np.logical_or.reduce(list(boundaryReasons.values()))
    unresolved=boundary|mismatch2|mismatch3|conflicting3|theoremMismatch
    # Cross-check accepted JTE107 labels; do not execute its classification tests.
    expectedD=int(old["mechanismCategories"]["D_RAW_NATIVE_CORE_CHANGE"]["rawStoredCategory"]["countRecordedRows"])
    need(int(np.count_nonzero(native2))==expectedD,"JTE108_JTE107_NATIVE_D_LINK_MISMATCH")
    for tag,mask in (("A_SELECTOR_MASKING",d["observedLoss"]==0),
      ("B_FLOOR_MASKING",(d["observedLoss"]>0)&(ut==uf)&(ut==law["step"])),
      ("C_QUANTIZER_MASKING",(d["observedLoss"]>0)&(ut==uf)&(ut>law["step"]))):
        need(int(np.count_nonzero(mask))==old["mechanismCategories"][tag]["rawStoredCategory"]["countRecordedRows"],
          "JTE108_JTE107_MECHANISM_COUNT_LINK_MISMATCH")
    design="JTE072_FIXED_GROUP" if c["selection"]["fixedGroupsSeparateDesign"] else "JTE067_SINGLE_SITE"
    flags={"opaqueId":c["opaqueId"],"CRITICAL_BIAS_FINITE_PRESENT":bool(np.any(finite)),
      "ALL_STORED_STATES_INFINITE":bool(np.all(~finite)),
      "DELTA_2_PREDICTION_MATCHES_NATIVE_MATLAB":bool(np.all(~mismatch2)),
      "DELTA_3_PROSPECTIVE_SWITCH_POSSIBLE":bool(np.any(pred3)),
      "SOURCE_FRAME_K":ref,"CASE_DESIGN":design,"NEAR_THRESHOLD_UNRESOLVED":bool(np.any(unresolved))}
    out=ROOT/(stem+"_"+c["opaqueId"]+"_MARGIN_ROWS.npz")
    np.savez_compressed(out,time_s=t,A_K=A,B_K=B,theta_K=theta,channels_1based=ch,
      deltaCritical_K=critical,eligibleThresholds=eligible,delta2PredictedStepCount=count2,delta3PredictedStepCount=count3,
      uTrue_native=ut,uFault2_native=uf,delta2Mismatch=mismatch2,nearThreshold=boundary,
      unresolved=unresolved,delta3OracleInputCovered=covered3,uFault3_archivedLookup=knownU3,
      delta3CoveredMismatch=mismatch3)
    size,sha,_=sha_file(out)
    allInfinite=not np.any(finite)
    report={"opaqueId":c["opaqueId"],"flags":flags,"prior":brief_prior_case(c),
      "rawDatasetHorizon_s":[float(t[0]),float(t[-1])],"nativeRecordedRows":n,
      "finiteCriticalBias":{"minimum_K":float(np.min(critical[finite])) if not allInfinite else None,
        "maximum_K":float(np.max(critical[finite])) if not allInfinite else None,
        "finite":presence(finite,t),"infinite":presence(~finite,t),
        "semantics":"Finite values are strict-transition infima. Infinity is fixed-state ideal impossibility on THIS S only, not dynamic/continuous-time safety."},
      "perThresholdEligible":{"theta1":presence(eligible[:,0],t),"theta2":presence(eligible[:,1],t)},
      "delta2":{"predicted":presence(pred2,t),"nativeStored":presence(native2,t),
        "mismatch":presence(mismatch2,t),"floatTheoremFormMismatch":presence(theoremMismatch,t),
        "maxStepCountPredicted":int(np.max(count2)),"rawStoredCommandsNotRounded":True},
      "delta3":{"predicted":presence(pred3,t),"resolvedPotential":presence(pred3&~unresolved,t),
        "archivedNativeInputCovered":presence(covered3,t),"uncovered":presence(~covered3,t),
        "coveredMismatch":presence(mismatch3,t),"conflictingArchivedLookup":presence(conflicting3,t),
        "nativeLookupAuthority":"Exact identical Max input to stored uSameTrue/uSameFault, same source/frame; not a new MATLAB evaluation.",
        "fullNativeValidationAvailable":bool(np.all(covered3)&np.all(~mismatch3)&np.all(~conflicting3)),
        "maxStepCountPredicted":int(np.max(count3)),"dynamicC1Outcome":"NOT_SIMULATED_NOT_CLAIMED"},
      "boundaryAmbiguity":{"budget_K":budget,"rule":"Within inherited eight-ULP native-K operation budget of A/B/faulted Max and either actual reference threshold; no rounding or mismatch suppression.",
        "nearThreshold":presence(boundary,t),"unresolved":presence(unresolved,t),
        "reasons":{k:presence(v,t) for k,v in boundaryReasons.items()},
        "inheritedJTE107SelectorAmbiguity":old["numericThresholdAmbiguous"],
        "inheritedSelectorFlagIsNotAutomaticallyCriticalBoundaryUncertainty":True},
      "rowEvidence":{"name":out.name,"size_bytes":size,"sha256":sha},
      "selectionDeviation":old["selection"],
      "caseDesignEstimandStratum":design,
      "timeSemantics":"Native row presence only; endpoints are recorded timestamps, not accepted-event bounds or exposure durations.",
      "G5_NUMERICAL_ACCEPTED":False,"G6_TEMPERATURE_CLAIM_AUTHORIZED":False}
    return flags,report,out
def conditional_proposal(c,r):
    # No execution. Immutable membership, first feasible opaque ID in frozen manifest order.
    n=r["nativeRecordedRows"];elapsed=c["source"].get("archivedElapsedWall_s")
    referenceSteps=math.ceil(2400/(.001/10))
    proxy=None if not elapsed else float(elapsed)*referenceSteps/n
    return {"status":"ONE_PROPOSAL_ONLY_REQUIRES_SUBSEQUENT_INDEPENDENT_SCIENTIFIC_SIGNOFF",
      "screeningRuleDeclaredBeforeAudit":"First feasible archived case in immutable opaque-ID order; no S/rank/ref/load change and no thermal outcome selection.",
      "caseBinding":{"opaqueId":c["opaqueId"],"channels":c["injection"]["channels_1based"],
        "source":c["source"],"selection":c["selection"],"sameFrame":c["sameFrame"]},
      "protocol":"Retain immutable original design. JTE042 Level-B minus3K is prospective by owner statement; fixed-group results remain a separate design and need an explicit independent amendment, never relabeled JTE042 single-site.",
      "pair":"One confirmatory baseline/C1-minus3K pair from identical complete source initialization, load and controller reference. No group/channel reselection or restart from temperatures alone. Same full source physical model and unit contract.",
      "oracleGate":"Before physical approval require original MATLAB source-native arithmetic at all new Max inputs not covered by exact archived lookup; ambiguous ideal comparisons never count as verified native steps.",
      "primaryNumerics":"Original archived solver/configuration retained as the source-reproduction pair, not accepted for1ms-filter convergence.",
      "independentNumericalReferencePlan":"One predeclared independent implicit stiff ode15s reference pair, full initialization and same load; MaxStep<=tau/10=0.0001s, original tolerances initially held to separate method/step effects. No automatic sweeps. This is a resource-heavy proposal, not a demonstrated remedy.",
      "filterReference":"Use certified accepted core-event times and exact piecewise-constant filter solution y=u+(y0-u)*exp(-dt/.001) as an independent output consistency check. Callback coincidences are not accepted-event certificates.",
      "prospectiveAcceptance":"Require exact source/load/IC/injection/unit parity, source-native core consistency and certified event order. Bound filtered-output uncertainty by event-time uncertainty and analytic1ms-filter response plus arithmetic. For each prespecified full312 thermal endpoint inK, require effect direction stable between primary/reference and absolute paired contrast larger than baseline+fault numerical-discrepancy and clock-uncertainty envelope. No p-values or arbitrary post-hoc tolerances.",
      "resources":{"referenceMinimumStepsPerTrajectory":referenceSteps,"archivedWall_s":elapsed,
        "roughReferenceWallProxy_s":proxy,"proxyCaveat":"Planning only: cost scales using recorded row count, not accepted solver steps; no certified runtime or free-budget availability.",
        "trajectoryPlan":"Primary pair plus one independent numerical-reference pair, never blind iterations.","spendAuthorized":False},
      "stop":"No run until science and free-resource feasibility are accepted. Stop if reference cannot resolve1ms actuation, initialization/event semantics are unqualified, resource allowance insufficient, or contrast is below uncertainty. No paid service or larger bias/reference/load change."}
def main():
    global STAGE
    token,folder=context();ROOT.mkdir(mode=0o700,exist_ok=False)
    run=os.environ["GITHUB_RUN_ID"];stem="JTE108_"+run
    print("JTE108_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" job="+os.environ["GITHUB_JOB"]+
      " matlabRun=0 simulationRun=0 previousAuditsRerun=0 syntheticTestsRepeated=0",flush=True)
    inputs=[];outputs=[];STAGE="READ_CERTIFICATES"
    meta,rc=readjson(token,folder,P106+"RECEIPT.json");inputs.append(meta)
    need(rc["run"]==R106 and rc["commit"]==C106 and all(z["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" for z in rc["files"]),
      "JTE108_JTE106_CERTIFICATE_INVALID")
    cert={z["name"]:z for z in rc["files"]}
    meta,a=readjson(token,folder,P106+"RESULTS.json",cert);inputs.append(meta)
    need(a["run"]==R106 and a["commit"]==C106 and len(a["cases"])==9 and
      not a["manifest"]["missing"] and not a["manifest"]["unqualifiedCandidates"],"JTE108_JTE106_SCOPE_INVALID")
    meta,law=readjson(token,folder,P106+"SOURCE_LAW.json",cert);inputs.append(meta)
    need(law["verified"] and law["gain"]==.1 and law["step"]==.25 and law["lower"]==.001 and law["upper"]==.95,
      "JTE108_SOURCE_LAW_CERTIFICATE_INVALID")
    meta,r107=readjson(token,folder,P107+"PRIVATE_READBACK_RECEIPT.json");inputs.append(meta)
    need(r107["run"]==R107 and r107["commit"]==C107 and all(z["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" for z in r107["files"]),
      "JTE108_JTE107_CERTIFICATE_INVALID")
    cert107={z["name"]:z for z in r107["files"]}
    meta,old=readjson(token,folder,P107+"PRIVATE_MECHANISM_LEDGER.json",cert107);inputs.append(meta)
    oldcases={c["opaqueId"]:c for c in old["cases"]}
    need(old["run"]==R107 and old["commit"]==C107 and len(oldcases)==9,"JTE108_JTE107_SCOPE_INVALID")
    reports=[];flags=[];raws={}
    for c in sorted(a["cases"],key=lambda z:z["opaqueId"]):
        STAGE=c["opaqueId"]
        need(all(c["flags"][k] for k in ("DATA_QUALIFICATION","SAME_FRAME_MATCH","SELECTOR_ORACLE_PASS",
          "NEGATIVE_BIAS_ONLY","SOURCE_MATLAB_ORACLE_MATCH_AT_ARCHIVED_SAMPLES")),"JTE108_PRIOR_CASE_UNQUALIFIED")
        name=Path(c["evidenceFile"]["name"]).name
        meta,ev=get(token,folder,name,cert,expected=c["evidenceFile"]["SHA256"]);inputs.append(meta)
        meta,raw=get(token,folder,c["archive"]["name"],expected=c["archive"]["sha256"]);inputs.append(meta)
        flag,report,rowpath=audit_case(raw,ev,c,oldcases[c["opaqueId"]],law,stem)
        report["inputNativeArchive"]=meta;reports.append(report);flags.append(flag);raws[c["opaqueId"]]=c
        outputs.append({"name":rowpath.name,**upload_verified(token,folder,rowpath,schema=SCHEMA)})
        raw.unlink();ev.unlink();rowpath.unlink()
        print("JTE108_CASE_METADATA "+json.dumps(flag,separators=(",",":")),flush=True)
    STAGE="DELIVER_LEDGER"
    allQualified=all(f["DELTA_2_PREDICTION_MATCHES_NATIVE_MATLAB"] and not f["NEAR_THRESHOLD_UNRESOLVED"] for f in flags)
    possible=next((r for r in reports if r["delta3"]["resolvedPotential"]["recordedRows"]>0),None)
    if not allQualified:decision="HOLD_BOUNDARY_OR_NATIVE_MISMATCH_NO_PHYSICAL_RUN"
    elif possible is not None:decision="GO_PROPOSAL_ONLY_MINUS3_SAME_STATE_FEASIBLE"
    else:decision="NO_GO_MINUS3_UNDER_ARCHIVED_STATES_NO_NEW_PHYSICAL_RUN"
    proposal=conditional_proposal(raws[possible["opaqueId"]],possible) if possible is not None and allQualified else {
      "status":"NO_CONFIRMATORY_PHYSICAL_RUN_PROPOSED",
      "reason":"No qualified same-state minus3 feasibility, or unresolved boundary/native evidence. No larger fault/new group/load/reference."}
    refs=[{k:r[k] for k in ("label","frame","profile","B0L_C0_NATIVE_VECTOR_EQUIVALENCE","B0L_C0_fullClockAndT312Exact") if k in r} for r in a["references"]]
    ledger={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"executor":"GITHUB_HOSTED_ACTIONS",
      "job":os.environ["GITHUB_JOB"],"sourceJTE106Run":R106,"sourceJTE107Run":R107,
      "inputs":inputs,"cases":reports,"publicMetadata":flags,"decision":decision,"conditionalProposal":proposal,
      "referenceAudit":{"certificatesReused":refs,"activeB0L":"NOT_AVAILABLE_NOT_FABRICATED",
        "hiddenSimscapeIC":"NOT_CERTIFIED; same-frame prior declaration/T0 scope only"},
      "dataDictionary":{"A_B":"Maxima inK of exactly archived faulted subset and its nonempty complement, same physical native row.",
        "critical":"min(A-theta) for B<theta<=A, infinity if no eligible threshold. Finite extrema reported only over finite entries. Infimum requires STRICT delta>critical.",
        "idealVsNative":"The theorem uses ideal threshold geometry at source reference+5/+7.5K. Saved original MATLAB doubles are authority for2K;3K native oracle reused only at EXACT input equality to saved true/fault Max.",
        "rowsNPZ":"Full per-row A/B/critical/eligibility/predictions/native-match/ambiguity arrays. +inf is IEEE infinity; NaN in3K lookup marks missing archived oracle, never a fabricated value.",
        "boundary":"Eight-ULP native-K operation budget localizes control eligibility/input boundaries, plus mismatches. Prior selector small-loss ambiguity retained separately, not conflated with critical-boundary uncertainty.",
        "counts":"Native recorded-row presence, never elapsed time fractions, statistical replicates or p-values.",
        "scope":"Fixed-state subset robustness endpoint only, not continuous-time safety, accepted actuator event, cooling performance or true-temperature causality.",
        "protocol":"Inherited ranking/tie deviations retained; single-site300, single-site293.15 and fixed-group293.15 remain separate strata."},
      "G5_NUMERICAL_ACCEPTED":False,"G5_ACTUATION_EVENT":"UNPROVEN","G5_THERMAL_CONVERGENCE":"UNPROVEN",
      "G6_TEMPERATURE_CLAIM_AUTHORIZED":False,"newPhysicalRunAuthorized":False,"newMATLABExecution":False,
      "syntheticTestsRepeated":False,"previousAuditRerun":False,"stopAfterThisAudit":True}
    p=ROOT/(stem+"_PRIVATE_MARGIN_LEDGER.json");p.write_text(json.dumps(ledger,indent=2,allow_nan=False))
    outputs.append({"name":p.name,**upload_verified(token,folder,p,schema=SCHEMA)})
    p=ROOT/(stem+"_METADATA_FLAGS.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
      "cases":flags,"decision":decision,"newPhysicalRunAuthorized":False},indent=2))
    outputs.append({"name":p.name,**upload_verified(token,folder,p,schema=SCHEMA)})
    p=ROOT/(stem+"_PRIVATE_READBACK_RECEIPT.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,
      "commit":os.environ["GITHUB_SHA"],"files":outputs,"newSimulationRun":False},indent=2))
    upload_verified(token,folder,p,schema=SCHEMA)
    print("JTE108_PRIVATE_MARGIN_SHA_READBACK_PASS decision="+decision+
      " matlabRun=0 simulationRun=0 previousAuditsRerun=0 G5_NUMERICAL_ACCEPTED=false G6_TEMPERATURE_CLAIM_AUTHORIZED=false",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        code=str(exc)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE108_READONLY_AUDIT_FAILED_"+type(exc).__name__.upper()
        # Private parser/transport evidence; do not print archive paths, keys or data.
        if ROOT.is_dir():
            try:
                p=ROOT/("JTE108_"+os.environ.get("GITHUB_RUN_ID","UNKNOWN")+"_PRIVATE_FAILURE.json")
                p.write_text(json.dumps({"schema":SCHEMA,"stage":STAGE,"code":code,"exceptionClass":type(exc).__name__,
                  "matlabRun":False,"simulationRun":False}))
                t,f=context();upload_verified(t,f,p,schema=SCHEMA)
            except Exception:pass
        print("JTE108_BLOCKED stage="+STAGE+" code="+code,flush=True);sys.exit(1)
