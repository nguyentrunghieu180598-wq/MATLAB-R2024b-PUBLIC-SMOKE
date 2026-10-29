"""JTE111 Step A only: existing G5 evidence inventory and conditional feasibility."""
from __future__ import annotations
import json,os,re,sys,time,shutil,hashlib,zipfile,xml.etree.ElementTree as ET,resource
from pathlib import Path
from datetime import datetime
import numpy as np
import h5py
from JTE101_io import one,download
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified,sha_file
from JTE102_metrics import read,num,vec,config,clean
from JTE111_G5_evidence_gate import blank,assess
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
SCHEMA="JTE111_PRIVATE_G5_EVIDENCE_NOT_ACCEPTANCE"
ROOT=Path("jte111-private");STAGE="CONTEXT"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE111_STEP_A_EXISTING_G5_EVIDENCE_ONLY" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"JTE111_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def fetch(t,f,name,expected=None,cert=None):
    need(bool(re.fullmatch(r"[A-Za-z0-9_.-]+",name)),"JTE111_ASSET_NAME_INVALID")
    name=name.removeprefix("JTE063_VERIFIED_")
    meta=download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/name)
    if expected:need(meta["sha256"]==expected,"JTE111_INPUT_HASH_LINK_MISMATCH")
    if cert is not None:
        need(name in cert and cert[name]["sha256"]==meta["sha256"] and
          cert[name]["size_bytes"]==meta["size"],"JTE111_RECEIPT_LINK_MISMATCH")
    return meta,ROOT/name
def jread(t,f,name,cert=None):
    m,p=fetch(t,f,name,cert=cert);return m,json.loads(p.read_text())
def stats(t):
    dt=np.diff(t);p=dt[dt>0]
    return {"recordedRows":int(len(t)),"duplicateAdjacentRows":int(np.count_nonzero(dt==0)),
      "minPositiveRecordedGap_s":float(p.min()),"maxRecordedGap_s":float(p.max()),
      "medianPositiveRecordedGap_s":float(np.median(p)),
      "meaning":"Logged native gaps only, NOT accepted/rejected solver-step sizes."}
def window(t,u,y,w,x=None,C=None):
    ix=np.flatnonzero((t>=w[0])&(t<=w[1]));need(len(ix)>1,"JTE111_WINDOW_NOT_COVERED")
    gap=y[ix]-u[ix];hit=np.abs(gap)>.005;first=np.flatnonzero(hit)
    k=int(ix[first[0]]) if len(first) else None
    q={"windowRequested_s":w,"nativeCoverage_s":[float(t[ix[0]]),float(t[ix[-1]])],
      "nativeGapStats":stats(t[ix]),"postfilterMinusCorePeakAbs":float(np.max(np.abs(gap))),
      "localizationFlag":bool(np.any(hit)),"localizationThresholdNormalized":.005,
      "thresholdIsAcceptance":False,"flaggedNativeTimes_s":t[ix][hit],
      "firstNativeBracket_s":[float(t[k-1]),float(t[k])] if k is not None and k>0 else None,
      "coreConstantAtRecordedPoints":bool(np.all(u[ix]==u[ix[0]])),
      "firstNativeOutputDelta":float(y[k]-y[k-1]) if k is not None and k>0 else None,
      "acceptedEventSemantics":"UNAVAILABLE",
      "interpretation":"Native adjacent-sample localization only; not a reset/ZC actor, certified event interval or physical excursion duration."}
    if x is not None:
        q["firstNativeStateDelta"]=float(x[k]-x[k-1]) if k is not None and k>0 else None
        q["savedStateOutputGain"]=C;q["stateOutputNativeResidualMax"]=float(np.max(np.abs(y[ix]-C*x[ix])))
    return q
def raw2400(path,label):
    with h5py.File(path,"r") as f:
        p="record/"
        need(read(f,p+"schema")=="JTE056_NATIVE_V1" and read(f,p+"caseName")==label,"JTE111_RAW_SCHEMA")
        version=read(f,p+"matlabVersion")
        need("24.2.0.3361896" in version and read(f,p+"sourceSHA256")==PIN and
          read(f,p+"units/temperature")=="K" and read(f,p+"units/time")=="s","JTE111_SOURCE_RUNTIME_UNITS")
        t=vec(f,p+"signalData/jteTtrue/time_s");T=num(f,p+"signalData/jteTtrue/values")
        u=vec(f,p+"signalData/jteUcore/values");y=vec(f,p+"signalData/jteFlwR/values")
        need(T.shape==(len(t),312) and t[0]==0 and t[-1]==2400 and np.all(np.diff(t)>=0) and
          np.array_equal(t,vec(f,p+"signalData/jteUcore/time_s")) and
          np.array_equal(t,vec(f,p+"signalData/jteFlwR/time_s")),"JTE111_RAW_CLOCK")
        zero=None
        if label.startswith("C0"):
            need(np.array_equal(t,vec(f,p+"signalData/jteTmeas/time_s")),"JTE111_ZERO_CLOCK")
            zero=np.array_equal(T,num(f,p+"signalData/jteTmeas/values"))
            need(zero,"JTE111_ZERO_BIAS_VECTOR_FAILURE")
        r={"label":label,"sourceSHA256":PIN,"version":version,"solver":read(f,p+"solver"),
          "loadSHA256":read(f,p+"load/SHA256"),"ambientReferenceK":float(read(f,p+"ambient/valueK")),
          "native":stats(t),"nativeT312Shape":T.shape,"zeroBiasIdentity":zero,
          "first":window(t,u,y,[330.,338.]),"second":window(t,u,y,[2000.,2400.]),
          "actualTFInput":"UNAVAILABLE_IN_JTE065_NATIVE_SCHEMA_CORE_IS_NOT_ACTUAL_INPUT_CERTIFICATE",
          "TFstate":"UNAVAILABLE_IN_JTE065_NATIVE_SCHEMA",
          "acceptedStepCertification":"UNAVAILABLE"}
        return r,t,T
def slx_ic(path):
    found=[]
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if not n.startswith("simulink/") or not n.endswith(".xml"):continue
            try:root=ET.fromstring(z.read(n))
            except ET.ParseError:continue
            for block in root.iter("Block"):
                if block.attrib.get("SID")=="197":
                    found.append({"xmlMember":n,"blockName":block.attrib.get("Name"),
                      "blockType":block.attrib.get("BlockType"),"parameters":{
                       p.attrib.get("Name"):p.text for p in block.findall("P")
                       if p.attrib.get("Name") in ("Numerator","Denominator","InitialCondition","InitialStates")}})
    return {"staticEntries":found,"scope":"Read-only literal SLX metadata, no compiled/resolved default inference."}
def original340(path,model,prior):
    with h5py.File(path,"r") as f:
        p="record/"
        need(read(f,p+"schema")=="JTE101_TF_340_RAW_NOT_G5" and read(f,p+"role")=="ORIGINAL340" and
          read(f,p+"run")=="40449421507" and read(f,p+"sourceSHA256")==PIN,"JTE111_JTE101_ORIGIN")
        need(sha_file(model)[1]==read(f,p+"modelSHA256"),"JTE111_JTE101_MODEL_BYTES")
        t=vec(f,p+"observed/outputTime");y=vec(f,p+"observed/output");u=vec(f,p+"observed/core")
        x=vec(f,p+"observed/state");a=vec(f,p+"observed/input")
        T=num(f,p+"observed/trueTemperature")
        for n in ("coreTime","stateTime","inputTime","trueTime"):
            need(np.array_equal(t,vec(f,p+"observed/"+n)),"JTE111_JTE101_NATIVE_CLOCK")
        need(t[0]==0 and t[-1]==340 and np.all(np.diff(t)>=0) and
          T.shape==(len(t),312) and len(x)==len(t) and len(a)==len(t),"JTE111_JTE101_DIM")
        C=float(read(f,p+"calibration/C"))
        cfg=config(f,p+"prepared/beforeGraph/config")
        # TimingInfo is public SimulationMetadata, but serialized objects may not be Python-readable.
        # Use prior validated export if present; do not interpret undocumented object internals.
        r={"sourceSHA256":PIN,"modelSHA256":read(f,p+"modelSHA256"),"solver":cfg,
          "loadSHA256":read(f,p+"prepared/loadSHA256"),"native":stats(t),"nativeT312Shape":T.shape,
          "actualInputEqualsCoreNative":bool(np.array_equal(a,u)),"actualInputConstantNative":bool(np.all(a==.25)),
          "savedTFStateInitial":float(x[0]),"savedTFOutputInitial":float(y[0]),"savedStateOutputGain":C,
          "stateOutputNativeResidualMax":float(np.max(np.abs(y-C*x))),
          "savedDeclarationAcceptedStepCertification":read(f,p+"acceptedStepCertification"),
          "nativeAcceptedStepCertification":read(f,p+"observed/acceptedStepCertification"),
          "declaredTFICFromSLX":slx_ic(model),"first":window(t,u,y,[330.,338.],x,C),
          "second":"NOT_COVERED_340",
          "runtimeEvidence":"JTE101_stageB R2024bU10 assertion and accepted actual40449421507 execution; JTE101 raw wrapper does not expose a separate version string.",
          "priorValidatedMetadata":prior["cases"]["ORIGINAL340"]["metadata"]}
        return r
def source_runtime(prior):
    # Recorded original run timing, if its accepted export includes it. Never substitute CI total.
    found={}
    for k,c in prior.get("cases",{}).items():
        for n,v in c.get("metadata",{}).items():
            if any(s in n.lower() for s in ("elapsed","wall","executiontime","timing")):found[k+"."+n]=v
    return found
def public_resources():
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key,value=line.split(":",1)
        if key in ("MemTotal","MemAvailable"):mem[key+"_bytes"]=int(value.split()[0])*1024
    disk=shutil.disk_usage(".")
    return {"logicalCPUs":os.cpu_count(),"affinityCPUs":len(os.sched_getaffinity(0)),
      "RAM":mem,"diskFree_bytes":disk.free,"diskTotal_bytes":disk.total,
      "thisPythonProcessPeakRSS_bytes":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
      "runtimeQuotaRemaining":"UNAVAILABLE_NO_BILLING_OR_FUTURE_ALLOCATION_READ",
      "MATLABLicenseAvailability":"Previously successfulR2024bU10 action only; not checked or reserved for a new run",
      "personalPCUsedForScientificCompute":False}
def main():
    global STAGE
    tok,folder=context();ROOT.mkdir(mode=0o700,exist_ok=False)
    run=os.environ["GITHUB_RUN_ID"];stem="JTE111_"+run
    print("JTE111_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" job="+os.environ["GITHUB_JOB"]+
      " step=A matlabRun=0 simulationRun=0 syntheticTestsRepeated=0",flush=True)
    inputs=[];start=time.monotonic()
    STAGE="REUSE_PRIVATE_CERTIFICATES"
    meta,old=jread(tok,folder,"JTE102_40462103051_METRICS.json");inputs.append(meta)
    meta,oldrc=jread(tok,folder,"JTE102_40462103051_RECEIPT.json");inputs.append(meta)
    ent=next(z for z in oldrc["files"] if z["name"]=="JTE102_40462103051_METRICS.json")
    need(ent["sha256"]==inputs[0]["sha256"] and ent["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","JTE111_JTE102_RECEIPT")
    meta,d103=jread(tok,folder,"JTE103_40477302616_DELIVERY_AUDIT.json");inputs.append(meta)
    meta,rc103=jread(tok,folder,"JTE103_40477302616_DELIVERY_RECEIPT.json");inputs.append(meta)
    ent=next(z for z in rc103["files"] if z["name"]=="JTE103_40477302616_DELIVERY_AUDIT.json")
    need(ent["sha256"]==inputs[-2]["sha256"] and ent["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","JTE111_JTE103_RECEIPT")
    meta,rc106=jread(tok,folder,"JTE106_40485742742_AUDIT_RECEIPT.json");inputs.append(meta)
    cert={z["name"]:z for z in rc106["files"]}
    meta,a106=jread(tok,folder,"JTE106_40485742742_AUDIT_RESULTS.json",cert);inputs.append(meta)
    oldmanifest=old["inputManifest"]["files"]
    def linked(name):
        items=[z for z in oldmanifest if z["name"]=="JTE063_VERIFIED_"+name]
        need(len(items)==1,"JTE111_OLD_RAW_LINK_NOT_UNIQUE");return items[0]["sha256"]
    reports=[];zeroProof={};solvers={}
    for prof in ("original","fine"):
        STAGE="RAW_"+prof.upper()
        pair=[]
        for case in ("B0L","C0"):
            label=case+"_"+prof;name="JTE065_"+label+"_2400_NATIVE.mat"
            meta,path=fetch(tok,folder,name,expected=linked(name));inputs.append(meta)
            r,t,T=raw2400(path,label);r["input"]=meta;pair.append((r,t,T));solvers[label]=r["solver"]
            path.unlink()
        identical=np.array_equal(pair[0][1],pair[1][1]) and np.array_equal(pair[0][2],pair[1][2])
        need(identical,"JTE111_ZERO_BIAS_B0L_C0_FAILURE")
        zeroProof[prof]={"nativeClockAndFullT312Exact":identical,"C0MeasuredEqualsTrue":pair[1][0]["zeroBiasIdentity"]}
        reports.extend([pair[0][0],pair[1][0]]);del pair
    STAGE="RAW_ORIGINAL340"
    name="JTE101_40449421507_ORIGINAL340_RAW.mat";meta,path=fetch(tok,folder,name,expected=linked(name));inputs.append(meta)
    name="JTE101_40449421507_ORIGINAL340_MODEL.slx";mm,model=fetch(tok,folder,name,expected=linked(name));inputs.append(mm)
    short=original340(path,model,old);path.unlink()
    need(len({r["loadSHA256"] for r in reports} | {short["loadSHA256"]})==1,"JTE111_LOAD_PARITY_FAILURE")
    resources=public_resources();resources["auditElapsedBeforeDelivery_s"]=time.monotonic()-start
    # Preserve all source settings; only ONE unexecuted candidate is specified.
    candidate=dict(short["solver"]);candidate.update({"Solver":"ode23tb","MaxStep":"0.005","StartTime":"0","StopTime":"340"})
    sourceCfg=short["solver"]
    timing=source_runtime(old)
    markerPath=Path("jte111/ARCHIVED_EXECUTION_MARKERS.json")
    marker=json.loads(markerPath.read_text())
    elapsed=(datetime.fromisoformat(marker["original340End"].replace("Z","+00:00"))-datetime.fromisoformat(marker["original340Start"].replace("Z","+00:00"))).total_seconds()
    need(elapsed>0,"JTE111_SOURCE_WALL_MARKER_INVALID")
    timing["archivedGithubLogSimulationWallBracket_s"]=elapsed
    timing["sourceRun"]="40449421507";timing["sourceJob"]=122008391751
    timing["meaning"]="Public log markers bracket sim(input); not CPU time or an accepted-step cost certificate."
    markersSHA=hashlib.sha256(markerPath.read_bytes()).hexdigest()
    proposal={"status":"CONDITIONAL_NOT_AUTHORIZED_NOT_READY_TO_RUN",
      "purpose":"Independent first-window baseline numerical reliability; not thermal efficacy, actuator causality or full2400 G5 closure.",
      "existingComparator":"Reuse source original34040449421507, no old case rerun",
      "sourceConfig":sourceCfg,"candidateConfig":candidate,
      "configChangesFromSavedDeclaration":{k:{"source":sourceCfg.get(k),"candidate":v} for k,v in candidate.items() if sourceCfg.get(k)!=v},
      "methodBasis":"One stiff TR-BDF2 ode23tb option per official MathWorks solver docs, not already failed ode15s or equivalent filter replacement. Stability is not an accuracy/repair guarantee.",
      "officialSource":"https://www.mathworks.com/help/simulink/gui/solver.html",
      "maxStepBasis":"0.005s reduces the source maximum tenfold;5*tau is a prospective discriminator for a stiff method, NOT a convergence claim.0.0001s is not imposed as a universal rule. No further sweep authorized.",
      "wiringIC":"Same archived original physical/controller/TF paths, t0=0 with complete source initialization/workspace; no330s temperature-only restart, StateSpace/quantizer/PID substitution.",
      "measurementPrerequisite":"Need publicR2024b-supported accepted-step/event/state-commit semantics or an independently justified event-time uncertainty bound. Native/callback rows and profiler global counts do not satisfy it; no GUI hunt requested.",
      "acceptanceLockedBeforeAnyFutureRun":{"sourceParity":"Exact source/load/declaredIC and full initialization qualification, actual input/core/state/output/T312 channels and units.",
        "firstWindow":"330–338s plus negative control330–334s, retain every native row and state jump. Localization.005 is NOT a scientific acceptance tolerance.",
        "filter":"Exact-ZOH canary may be applied only after held-input/no-reset/event-time semantics certified. Otherwise no analytic-reference PASS.",
        "thermal":"Need a prospectively justified K error/clock envelope for fullT312. No RMSE on arbitrary union/interpolated jump grid; no tolerance converted directly from RelTol.",
        "thresholdReadiness":"UNAVAILABLE_NO_INDEPENDENT_PHYSICAL_OR_NUMERICAL_ERROR_BUDGET_YET"},
      "workload":{"sourceNative340":short["native"],"sourceRecordedTimingExports":timing,
        "candidateHorizonOverMaxStepNominalMinimum":68000,
        "sourceNativeGapMaximum_s":short["native"]["maxRecordedGap_s"],
        "RAM_T312_oneLoggedMatrix_nominal_bytes":68001*312*8,
        "RAMModelSolverPeak":"UNAVAILABLE_NO_SOURCE_PEAK_MEMORY_CAPTURE",
        "wallPlanningProxy_s":elapsed*max(68000,short["native"]["recordedRows"])/short["native"]["recordedRows"],
        "CPUWallEstimate":"Rough archive-based planning proxy from original simulation wall bracket and native recorded-row density; not a runtime bound, accepted-step count, CPU-time estimate or implicit-solver cost certificate.",
        "storage":"New raw size depends on complete state logging; archived original340 size is retained in input manifest; no fabricated compression factor.",
        "observedAuditRunner":resources,"freeFutureRuntime":"UNAVAILABLE_NO_FREE_ALLOCATION_RESERVATION",
        "additionalSpendAuthorized":False},
      "stop":"Do not run before independent scientific/resource/measurement/threshold signoff. If a single approved candidate retains unexplained first excursion or cannot qualify clocks, stop, do not sweep. Second event is out of340s scope; no full2400 run approved."}
    if timing:
        proposal["workload"]["archivedTimingPublicProvenance"]={"file":str(markerPath),"sha256":markersSHA,"sourceRun":"40449421507","sourceJob":122008391751}
    STAGE="BUILD_PRIVATE_EVIDENCE"
    findings={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"inputs":inputs,
      "raw2400":reports,"zeroBiasProof":zeroProof,"original340":short,
      "declaredParityReused":[r.get("B0L_C0_qualification",{}) for r in a106["references"] if r.get("B0L_C0_fullClockAndT312Exact")],
      "priorSolverProfileDeltas":old.get("solverProfileDeltas"),"priorIndependentComparisonLimits":{
       "solverComparison":{k:{a:v for a,v in z.items() if a in ("clockExact","matchedRows","status","semantics","maxAbs")}
         for k,z in old["comparisons"].items() if k.startswith("solver_")},
       "note":"Same ode23t and MaxStep.05, RelTol-only change, sparse exact native matches do not establish independent numerical convergence."},
      "priorJTE103":{"actualSourceRun":d103["actualSourceRun"],"eventActor":d103["EXACT_RESET_OR_ZC_ACTOR_PROVEN"],
        "secondScope":d103["SECOND_EVENT_SCOPE"],"privateReadback":d103["privateReadback"],
        "nativeTFStateCaptured":d103.get("nativeTFStateCaptured"),"APIEventAccess":d103["PUBLIC_API_EVENT_BLOCK_ACCESS"]},
      "G5_CANARY_SYNTHETIC":{"status":"CHAT_REPORTED_SYNTHETIC_ONLY_NOT_REEXECUTED",
        "reviewedPR":56,"reviewedHead":"6379bdc90f464b3adabd3182e8e85011b3f004bc",
        "canaryRole":"Reviewed conditional LTI math/clock checks, not source solver reproduction or first-impulse causal proof."},
      "G5_REFERENCE_FEASIBLE":{"status":"BLOCKED_MEASUREMENT_THRESHOLDS_AND_FUTURE_RESOURCE_QUALIFICATION",
        "reason":"Archive input/state accessible; accepted events, numericalK/command error budget, future runtime/license and full-plant memory not certified. No new simulation authorized."},
      "G5_REFERENCE_PLAN":proposal,"JTE109":"NO_VERIFIABLE_PR_OR_RUN_IN_READ_REPOSITORY_SNAPSHOT_NOT_REPEATED",
      "resources":resources,"simulationRun":False,"MATLABRun":False,"syntheticTestsRepeated":False}
    p=ROOT/(stem+"_PRIVATE_FINDINGS.json");p.write_text(json.dumps(clean(findings),indent=2,allow_nan=False))
    _,findsha,_=sha_file(p)
    record=blank()
    def gate(k,status,reason,anchor):
        record["gates"][k]={"status":status,"reason":reason,
          "evidence_reference":p.name+"#"+anchor,"evidence_sha256":findsha}
    gate("SOURCE_MODEL_LOCK","PASS","All four verified native source pins and original340/model byte hash linked to accepted archives; no source mutation.","raw2400/original340")
    gate("RUNTIME_LOCK","PASS","Four native records expose R2024bU10; original340 has accepted actual execution with explicit version assertion. No new MATLAB execution.","raw2400/original340/runtimeEvidence")
    gate("RAW_T312_CLOCK","PASS","Actual native finiteNx312, horizon, nondecreasing duplicate-preserving clocks and input/state clock alignments verified.","raw2400/original340")
    gate("ZERO_BIAS_IDENTITY","PASS","C0 measured=true and full B0L/C0 native clock/T312 identity for original/fine verified from saved records.","zeroBiasProof")
    gate("PAIR_INPUT_PARITY","UNAVAILABLE","Load/source/declared solver/parameter/T0 matches are available; complete hidden Simscape initial-state equivalence is not certified. Do not widen declared parity into a full state proof.","declaredParityReused")
    gate("ORIGINAL_WINDOW_1","PASS","Original/fine native first window localized; actual original340 TF input/state/output available. PASS means recorded coverage only, not accepted-event or causal proof.","raw2400/first/original340/first")
    gate("ORIGINAL_WINDOW_2","PASS","Actual original/fine2400 native second window localized. ActualTFinput/continuousTFstate are absent in2400 schema; separate acceptance gates stay unavailable.","raw2400/second")
    gate("ACCEPTED_EVENT_SEMANTICS","UNAVAILABLE","No independently certified accepted/rejected event-state commit trace. Callback/native rows, coincident timestamps and profiler global counts do not establish it.","original340/priorJTE103")
    gate("INDEPENDENT_NUMERICS_W1","UNAVAILABLE","No qualified independent numerical reference with accepted event/clock and a priori error budget. RelTol-only fine and prior failed realization are insufficient.","priorIndependentComparisonLimits")
    gate("INDEPENDENT_NUMERICS_W2","UNAVAILABLE","No independent accepted second-window numerical reference;340s does not cover it.","priorIndependentComparisonLimits")
    gate("POSTFILTER_RELIABILITY","UNAVAILABLE","Native state/output discontinuities persist with no certified event provenance or numerical remedy. Localization is not physical actuator reliability.","raw2400/original340")
    gate("THERMAL_CONVERGENCE","UNAVAILABLE","No prospectively qualified independent fullT312 convergence/error envelope. Zero-bias identity is a different gate.","priorIndependentComparisonLimits")
    record["producer"]={"run":run,"commit":os.environ["GITHUB_SHA"],"privateOnly":True,"newPhysicalRunAuthorized":False}
    out=assess(record)
    p2=ROOT/(stem+"_G5_EVIDENCE.json");p2.write_text(json.dumps(record,indent=2))
    p3=ROOT/(stem+"_GATE_ASSESSMENT.json");p3.write_text(json.dumps(out,indent=2))
    outputs=[]
    for v in (p,p2,p3):outputs.append({"name":v.name,**upload_verified(tok,folder,v,schema=SCHEMA)})
    rc=ROOT/(stem+"_PRIVATE_READBACK_RECEIPT.json")
    rc.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":outputs,
      "G5_SCIENTIFICALLY_ACCEPTED":False,"simulationRun":False},indent=2))
    upload_verified(tok,folder,rc,schema=SCHEMA)
    print("JTE111_STEP_A_PRIVATE_READBACK_PASS structural_result="+out["structural_result"]+
      " status_by_gate="+json.dumps(out["status_by_gate"],separators=(",",":"))+
      " G5_SCIENTIFICALLY_ACCEPTED=false simulationRun=0 MATLABRun=0 syntheticTestsRepeated=0",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        c=str(exc)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE111_PRIVATE_AUDIT_FAILED_"+type(exc).__name__.upper()
        if ROOT.is_dir():
            try:
                p=ROOT/("JTE111_"+os.environ.get("GITHUB_RUN_ID","UNKNOWN")+"_PRIVATE_FAILURE.json")
                p.write_text(json.dumps({"schema":SCHEMA,"stage":STAGE,"code":c,"exceptionClass":type(exc).__name__}))
                t,f=context();upload_verified(t,f,p,schema=SCHEMA)
            except Exception:pass
        print("JTE111_BLOCKED stage="+STAGE+" code="+c,flush=True);sys.exit(1)
