"""W112-A: necessary LTI physical envelope on five authentic archived native streams."""
from __future__ import annotations
import json,os,re,sys,zipfile,xml.etree.ElementTree as ET,shutil
from pathlib import Path
import h5py,numpy as np
from JTE101_io import one,download
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified,sha_file
from JTE102_metrics import read,vec,clean
ROOT=Path("jte112-private");SCHEMA="JTE112_CONDITIONAL_PHYSICAL_ENVELOPE_NOT_G5"
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
R111="40620218579";C111="f501b58134179ff742d8caaa31f471cfa2a85012"
STAGE="CONTEXT"
def need(x,c):
    if not x:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE112_ONE_PRIVATE_ENVELOPE_AUDIT" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA"),"JTE112_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,expected=None,cert=None):
    name=name.removeprefix("JTE063_VERIFIED_")
    need(bool(re.fullmatch(r"[A-Za-z0-9_.-]+",name)),"JTE112_FILENAME_INVALID")
    meta=download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/name)
    if expected:need(meta["sha256"]==expected,"JTE112_OLD_HASH_LINK_MISMATCH")
    if cert is not None:
        need(name in cert and cert[name]["sha256"]==meta["sha256"] and cert[name]["size_bytes"]==meta["size"],
          "JTE112_RECEIPT_LINK_MISMATCH")
    return meta,ROOT/name
def jread(t,f,name,cert=None):
    m,p=get(t,f,name,cert=cert);return m,json.loads(p.read_text())
def props(block):
    return {p.attrib.get("Name"):p.text for p in block.findall("P")}
def structural_graph(model):
    docs={}
    with zipfile.ZipFile(model) as z:
        for name in z.namelist():
            if name.startswith("simulink/") and name.endswith(".xml"):
                try:docs[name]=ET.fromstring(z.read(name))
                except ET.ParseError:continue
    tf=[(n,b) for n,r in docs.items() for b in r.iter("Block")
      if b.attrib.get("SID")=="197" and b.attrib.get("BlockType")=="TransferFcn"]
    need(len(tf)==1,"JTE112_TF_STATIC_NOT_UNIQUE")
    doc,block=tf[0];p=props(block)
    # Omitted Numerator is not guessed as a compiled default; accepted JTE101/106
    # source public get_param assertions separately verified [1]/[1e-3 1].
    need(p.get("Denominator")=="[1e-3 1]","JTE112_TF_DENOMINATOR_CHANGED")
    resetKinds={"EnablePort","TriggerPort","ResetPort","ActionPort","ReinitializeFunction","ResettableSubsystem","ResettableSubSystem"}
    chain=[];seen=set();complete=False
    for _ in range(12):
        if doc in seen:break
        seen.add(doc);root=docs[doc]
        direct=root.findall("Block") if root.tag=="System" else []
        resetPorts=[{"name":b.attrib.get("Name"),"type":b.attrib.get("BlockType")} for b in direct if b.attrib.get("BlockType") in resetKinds]
        key=Path(doc).stem
        owners=[(n,b) for n,r in docs.items() for b in r.iter("Block") for sy in b.findall("System")
          if Path(sy.attrib.get("Ref","")).stem==key]
        item={"systemXML":doc,"resetEnableTriggerActionPorts":resetPorts}
        if len(owners)==1:
            parent,owner=owners[0];item["owner"]={"name":owner.attrib.get("Name"),
              "type":owner.attrib.get("BlockType"),"SID":owner.attrib.get("SID"),
              "resetRelatedLiteralParameters":{k:v for k,v in props(owner).items() if any(x in k.lower() for x in ("reset","stateswhen","initialize"))}}
            chain.append(item);doc=parent
        else:
            item["ownerCount"]=len(owners);chain.append(item)
            complete=(len(owners)==0 and key in ("system_root","blockdiagram"))
            break
    writers=[{"xml":n,"name":b.attrib.get("Name"),"type":b.attrib.get("BlockType")}
      for n,r in docs.items() for b in r.iter("Block") if b.attrib.get("BlockType") in ("StateWriter","StateWriterBlock","ReinitializeFunction")]
    explicitReset=any(c["resetEnableTriggerActionPorts"] for c in chain)
    for c in chain:
        vals=c.get("owner",{}).get("resetRelatedLiteralParameters",{})
        explicitReset=explicitReset or any(str(v).lower() in ("reset","on") for v in vals.values())
    tfReset=[{k:v} for k,v in p.items() if "reset" in k.lower() and str(v).lower() not in ("none","off","")]
    supported=complete and not explicitReset and not tfReset and not writers
    return {"TFblock":{"name":block.attrib.get("Name"),"SID":"197","type":"TransferFcn","literalParameters":p},
      "ancestorTrace":chain,"ancestorTraceComplete":complete,"explicitResetSupportFound":bool(explicitReset or tfReset),
      "stateWriterCandidates":writers,"TF_RESET_FREE_ASSUMPTION_SUPPORTED":bool(supported),
      "scope":"Structural support for no explicit physical reset; NOT proof of no numerical solver reinitialization, state mutation, callback/minor-stage effects or all-time execution."}
def raw_stream(path,label):
    with h5py.File(path,"r") as f:
        need(read(f,"record/sourceSHA256")==PIN,"JTE112_SOURCE_PIN")
        if label=="ORIGINAL340":
            need(read(f,"record/schema")=="JTE101_TF_340_RAW_NOT_G5" and
              read(f,"record/role")=="ORIGINAL340" and read(f,"record/run")=="40449421507","JTE112_JTE101_ORIGIN")
            t=vec(f,"record/observed/outputTime");y=vec(f,"record/observed/output")
            u=vec(f,"record/observed/core");tu=vec(f,"record/observed/coreTime")
            tx=vec(f,"record/observed/stateTime");x=vec(f,"record/observed/state")
            ti=vec(f,"record/observed/inputTime");ui=vec(f,"record/observed/input")
            actual={"actualInputPresent":True,"inputClockExact":np.array_equal(t,ti),
              "inputEqualsCoreAtSavedPoints":bool(np.array_equal(ui,u) and np.array_equal(ti,tu)),
              "inputSavedMinimum":float(ui.min()),"inputSavedMaximum":float(ui.max()),
              "statePresent":True,"stateClockExact":bool(np.array_equal(t,tx)),
              "stateInitial":float(x[0]),"stateOutputGain":float(read(f,"record/calibration/C"))}
            source={"modelSHA256":read(f,"record/modelSHA256"),"schema":read(f,"record/schema")}
            horizon=340
        else:
            need(read(f,"record/schema")=="JTE056_NATIVE_V1" and read(f,"record/caseName")==label and
              "24.2.0.3361896" in read(f,"record/matlabVersion"),"JTE112_JTE065_ORIGIN")
            t=vec(f,"record/signalData/jteFlwR/time_s");y=vec(f,"record/signalData/jteFlwR/values")
            u=vec(f,"record/signalData/jteUcore/values");tu=vec(f,"record/signalData/jteUcore/time_s")
            actual={"actualInputPresent":False,"statePresent":False,
              "reason":"JTE065 schema lacks independent actual TF input and continuous TF state. Saved core rows cannot certify all-time/minor-stage input."}
            source={"modelSHA256":read(f,"record/generatedModelSHA256"),"schema":read(f,"record/schema")}
            horizon=2400
        need(t[0]==0 and t[-1]==horizon and len(t)==len(y) and np.all(np.diff(t)>=0),
          "JTE112_NATIVE_POSTFILTER_CLOCK_INVALID")
        actual["corePostClockExact"]=bool(np.array_equal(t,tu))
        actual["coreSavedMinimum"]=float(u.min());actual["coreSavedMaximum"]=float(u.max())
        return t,y,actual,source
def presence(mask,t):
    ix=np.flatnonzero(mask)
    if not len(ix):return {"recordedRows":0,"firstRecordedTime_s":None,"lastRecordedTime_s":None,"nativeRowRuns":[]}
    parts=np.split(ix,np.flatnonzero(np.diff(ix)>1)+1)
    return {"recordedRows":int(len(ix)),"firstRecordedTime_s":float(t[ix[0]]),"lastRecordedTime_s":float(t[ix[-1]]),
      "nativeRowRuns":[{"firstRow1":int(g[0]+1),"lastRow1":int(g[-1]+1),
        "firstRecordedTime_s":float(t[g[0]]),"lastRecordedTime_s":float(t[g[-1]])} for g in parts]}
def envelope_case(path,label,opaque,law,graph,stem,scope):
    t,y,actual,source=raw_stream(path,label);y0=float(y[0])
    y0ok=bool(np.all(y[t==0]==y0))
    alpha=-np.expm1(-t/.001)
    lower=y0+(.25-y0)*alpha;upper=y0+(.75-y0)*alpha
    need(np.all(lower<=upper),"JTE112_INTERVAL_INVALID")
    scale=np.maximum.reduce((np.ones(len(t)),np.abs(y),np.abs(lower),np.abs(upper),np.full(len(t),abs(y0))))
    margin=32*np.spacing(scale)
    lowExcess=np.maximum(lower-y,0);highExcess=np.maximum(y-upper,0);excess=np.maximum(lowExcess,highExcess)
    rawOutside=(y<lower)|(y>upper)
    flagged=(y<lower-margin)|(y>upper+margin)
    bounded=bool(law["verified"] and law["gain"]==.1 and law["lower"]==.001 and law["upper"]==.95 and law["step"]==.25)
    reset=graph["TF_RESET_FREE_ASSUMPTION_SUPPORTED"]
    public={"opaqueId":opaque,"SOURCE_BOUNDED_INPUT_VERIFIED":bounded,
      "TF_RESET_FREE_ASSUMPTION_SUPPORTED":reset,"INITIAL_Y0_NATIVE_VERIFIED":y0ok,
      "OUTSIDE_ANALYTIC_ENVELOPE_EXISTS":bool(np.any(flagged)),
      "INSIDE_ENVELOPE_ONLY_NOT_G5_PASS":bool(np.all(~flagged)),
      "CONCLUSION_CONDITIONAL":True,"ACCEPTED_STEP_CERTIFIED":False,"G5_SCIENTIFICALLY_ACCEPTED":False}
    report={"opaqueId":opaque,"archiveRole":label,"source":source,"flags":public,
      "SOURCE_BOUNDED_INPUT_SCOPE":"Verified original static connected Gain/Saturation/Mod/floor composition for finite consistent real inputs; not a certificate of each runtime/minor-stage evaluation. "+scope,
      "TF_RESET_FREE_SCOPE":graph["scope"],
      "INITIAL_Y0_NATIVE_VERIFIED":y0ok,"y0_native":y0,"sameTimeZeroRows":int(np.count_nonzero(t==0)),
      "MAX_EXCESS_COMMAND_NORMALIZED":float(excess.max()),
      "FIRST_RECORDED_EXCESS_TIME":float(t[np.flatnonzero(flagged)[0]]) if np.any(flagged) else None,
      "maxExcessAboveLocalizationMargin":float(np.max(np.maximum(excess-margin,0))),
      "strictOutside":presence(rawOutside,t),"outsideWith32ULP":presence(flagged,t),
      "nativeRows":len(t),"adjacentDuplicateRows":int(np.count_nonzero(np.diff(t)==0)),
      "nativeActualInputAndState":actual,
      "class":"CONDITIONAL_NATIVE_POINT_INCONSISTENT_WITH_EXACT_RESET_FREE_BOUNDED_INPUT_RESPONSE" if np.any(flagged) else "INSIDE_ANALYTIC_INTERVAL_ONLY_NOT_G5_PASS",
      "assumptions":"Authentic source first-order LTI, finite bounded input for all real time, actual y0, no separate physical state reset. Static support does not prove all-time numerical execution or accepted-step membership.",
      "interpretation":"An outside recorded value is not an exact physical solution under these hypotheses, or a hypothesis/logging semantics fails. No actor attribution or unconditional scientific FAIL; absence never certifies G5.",
      "windows":{}}
    for name,w in (("FIRST",[330.,338.]),("SECOND",[2000.,2400.])):
        ix=np.flatnonzero((t>=w[0])&(t<=w[1]))
        if not len(ix):report["windows"][name]={"status":"NOT_COVERED_340" if label=="ORIGINAL340" else "UNAVAILABLE"};continue
        hit=flagged[ix];r=presence(hit,t[ix]);first=np.flatnonzero(hit)
        k=int(ix[first[0]]) if len(first) else None
        r.update({"status":"NATIVE_ONLY_CONDITIONAL","windowRequested_s":w,
          "MAX_EXCESS_COMMAND_NORMALIZED":float(excess[ix].max()),"upperExcessPeak":float(highExcess[ix].max()),
          "lowerExcessPeak":float(lowExcess[ix].max()),
          "firstNativeAdjacentBracket_s":[float(t[k-1]),float(t[k])] if k is not None and k>0 else None,
          "bracketIsAcceptedEventBound":False})
        report["windows"][name]=r
    out=ROOT/(stem+"_"+opaque+"_ENVELOPE_ROWS.npz")
    np.savez_compressed(out,time_s=t,postfilter=y,lower=lower,upper=upper,margin32ULP=margin,
      lowerExcess=lowExcess,upperExcess=highExcess,rawOutside=rawOutside,outsideWithMargin=flagged,y0=np.asarray(y0))
    size,sha,_=sha_file(out);report["rowEvidence"]={"name":out.name,"size_bytes":size,"sha256":sha}
    return public,report,out
def main():
    global STAGE
    tok,folder=context();ROOT.mkdir(mode=0o700,exist_ok=False)
    run=os.environ["GITHUB_RUN_ID"];stem="JTE112_"+run;inputs=[];outputs=[]
    print("JTE112_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" job="+os.environ["GITHUB_JOB"]+
      " MATLABRun=0 simulationRun=0 syntheticTestsRepeated=0",flush=True)
    STAGE="LINK_JTE111"
    meta,rc=jread(tok,folder,"JTE111_"+R111+"_PRIVATE_READBACK_RECEIPT.json");inputs.append(meta)
    need(rc["run"]==R111 and rc["commit"]==C111 and all(z["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" for z in rc["files"]),
      "JTE112_JTE111_RECEIPT")
    cert={z["name"]:z for z in rc["files"]}
    meta,a=jread(tok,folder,"JTE111_"+R111+"_PRIVATE_FINDINGS.json",cert);inputs.append(meta)
    need(a["run"]==R111 and a["commit"]==C111,"JTE112_JTE111_ORIGIN")
    def expected(name):
        v=[i for i in a["inputs"] if i["name"]=="JTE063_VERIFIED_"+name]
        need(len(v)==1,"JTE112_RAW_NOT_IN_PRIOR_MANIFEST");return v[0]["sha256"]
    meta,rc106=jread(tok,folder,"JTE106_40485742742_AUDIT_RECEIPT.json");inputs.append(meta)
    need(rc106["run"]=="40485742742" and rc106["commit"]=="ceeb8a5590f9361016ad4c69004ffdc9e9223c94" and
      all(z["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" for z in rc106["files"]),"JTE112_JTE106_RECEIPT")
    cert106={z["name"]:z for z in rc106["files"]}
    meta,law=jread(tok,folder,"JTE106_40485742742_AUDIT_SOURCE_LAW.json",cert106);inputs.append(meta)
    need(law["verified"],"JTE112_SOURCE_GRAPH_NOT_VERIFIED")
    modelName="JTE101_40449421507_ORIGINAL340_MODEL.slx"
    meta,model=get(tok,folder,modelName,expected=expected(modelName));inputs.append(meta)
    need(meta["sha256"]==law["sourceModelSHA"] and meta["sha256"]==a["original340"]["modelSHA256"],
      "JTE112_SOURCE_GRAPH_MODEL_HASH")
    STAGE="STRUCTURAL_SOURCE_GRAPH"
    graph=structural_graph(model)
    need(graph["TFblock"]["name"]=="sensor dynamics 1","JTE112_SOURCE_TF_PATH")
    # The physical/source reset-free hypothesis remains conditional even if structure supports it.
    graph["runtimeCallbacksPriorDeclaration"]={k:v for k,v in a["original340"]["solver"].items() if k.endswith("Fcn")}
    graph["sourceLawEvidence"]=law
    graph["TFTransferShapeProvenance"]="Accepted JTE101_stageB verifyTF get_param assertions of numerator[1],denominator[1e-3 1],SID197 on this exact model byte hash; no new MATLAB run."
    graph["remainingUncertified"]="Numerical state commits/reinitializations, solver/reset event actor, all-time input stage coherence and accepted-step semantics."
    reports=[];flags=[]
    cases=[(c+"_"+p,"JTE065_"+c+"_"+p+"_2400_NATIVE.mat") for c,p in
      (("B0L","original"),("C0","original"),("B0L","fine"),("C0","fine"))]
    cases.append(("ORIGINAL340","JTE101_40449421507_ORIGINAL340_RAW.mat"))
    for i,(label,name) in enumerate(cases,1):
        opaque="G5_ARCHIVE_"+str(i).zfill(3);STAGE=opaque
        meta,path=get(tok,folder,name,expected=expected(name));inputs.append(meta)
        scope="Exact archived original340 model bytes." if label=="ORIGINAL340" else "Inherited JTE111 source-pin/builder provenance; per-derivative JTE065 SLX bytes are not independently re-opened."
        flag,report,rows=envelope_case(path,label,opaque,law,graph,stem,scope)
        report["inputArchive"]=meta;flags.append(flag);reports.append(report)
        outputs.append({"name":rows.name,**upload_verified(tok,folder,rows,schema=SCHEMA)})
        path.unlink();rows.unlink()
        print("JTE112_CASE_METADATA "+json.dumps(flag,separators=(",",":")),flush=True)
    STAGE="PRIVATE_LEDGER"
    motivated=any(r["windows"]["FIRST"].get("recordedRows",0)>0 for r in reports)
    plan={"status":"CONDITIONAL_COST_REVIEW_ONLY_NO_BENCHMARK_OR_RUN" if motivated else "NO_CANDIDATE_MOTIVATED_BY_FIRST_WINDOW",
      "purpose":"If independent review accepts conditional envelope findings as a discriminating first-window baseline reliability question, reuse ONE unexecuted JTE111 ode23tb candidate. This is not a G6 or thermal-efficacy run.",
      "originalComparator":"Existing original340 source, preserve authentic TF/controller/plant and complete source initialization fromt0=0; never restart fromT312 at330s.",
      "archivedComparativeEnvelope":{r["opaqueId"]:r["windows"]["FIRST"] for r in reports},
      "JTE111UnexecutedPlan":a["G5_REFERENCE_PLAN"] if motivated else None,
      "resourceQualification":"Native-density/wall-marker forecast and audit CPU/RAM/disk are planning proxies. Full-model peak memory, future free action quota and new license reservation remain UNAVAILABLE. No paid resource authorization.",
      "measurementScope":"Envelope needs bounded-input/no-physical-reset, not certified transition times. The status of each point as accepted numerical solution remains separate.32ULP margin is NOT a candidate solver accuracy tolerance or thermalK budget.",
      "stop":"No automatic execution. A retained unexplained excursion or missing source/IC/measurement/resource qualification stops this single candidate, not a solver sweep. Second event remains outside340."}
    ledger={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"executor":"GITHUB_HOSTED_ACTIONS",
      "job":os.environ["GITHUB_JOB"],"inputs":inputs,"sourceGraphAudit":graph,"cases":reports,"publicMetadata":flags,
      "dataDictionary":{"envelope":"y0+(.25-y0)*(1-exp(-t/.001)) <= y <= y0+(.75-y0)*(1-exp(-t/.001)); computed with -expm1 for startup stability.",
        "y0":"Actual first stored postfilter value at exactt0=0 for EACH archive; duplicate zero timestamps must agree for the native verification flag.",
        "32ULP":"Localization only:32*spacing(max(1,abs(y0),abs(y),abs(L),abs(U))) per row; normalized command, notK, plant uncertainty or a solver acceptance tolerance.",
        "excess":"max(L-y,y-U,0) raw, plus separate32ULP-outside flag. Original postfilter values never overwritten/clipped.",
        "sourceBoundFlag":"Static connected original source law supports .25to.75 for all finite coherent real evaluations; does NOT claim every runtime/minor stage was observed. Graph coverage scopes remain explicit perfile.",
        "resetFlag":"Static ancestor/reset-port/write-path support only. Not runtime certification; source bounded-input/no-physical-reset conclusions remain conditional.",
        "insideFlag":"INSIDE_ENVELOPE_ONLY_NOT_G5_PASS=true iff no32ULP outside records. False does not itself mark scientificG5 failure.",
        "clock":"Every original row retained, no interpolation/dedup, no sample counts as durations/replicates. NPZ stores all inputs/bounds/margins/excess/masks.",
        "accepted":"Accepted transition times are not needed for this necessary bound. Native/callback points still are not certified accepted physical solutions.",
        "privacy":"All scalar excess and timing values private; public Boolean metadata only."},
      "conditionalCandidateCostReview":plan,
      "JTE109":"NO_VERIFIABLE_TASK_NAMED_PR_IN_LATEST_INSPECTED_REPOSITORY_SNAPSHOT; NOT_REPEATED_OR_INFERRED_FROM_OTHER_THREADS",
      "loadScope":"Existing293.15K changed controller reference only, not battery current/heating load. No second load designed or run.",
      "newPhysicalRunAuthorized":False,"MATLABRun":False,"simulationRun":False,"syntheticTestsRepeated":False,
      "G5_SCIENTIFICALLY_ACCEPTED":False,"G5_ACTUATION_EVENT":"UNPROVEN","G5_THERMAL_CONVERGENCE":"UNPROVEN",
      "decision":"CONDITIONAL_NATIVE_ENVELOPE_FLAGS_FOR_INDEPENDENT_REVIEW_NO_G5_PASS","stopAfterThisAudit":True}
    p=ROOT/(stem+"_PRIVATE_ENVELOPE_LEDGER.json");p.write_text(json.dumps(clean(ledger),indent=2,allow_nan=False))
    outputs.append({"name":p.name,**upload_verified(tok,folder,p,schema=SCHEMA)})
    p=ROOT/(stem+"_METADATA_FLAGS.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
      "cases":flags,"G5_SCIENTIFICALLY_ACCEPTED":False},indent=2))
    outputs.append({"name":p.name,**upload_verified(tok,folder,p,schema=SCHEMA)})
    p=ROOT/(stem+"_PRIVATE_READBACK_RECEIPT.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,
      "commit":os.environ["GITHUB_SHA"],"files":outputs,"MATLABRun":False,"simulationRun":False},indent=2))
    upload_verified(tok,folder,p,schema=SCHEMA)
    print("JTE112_PRIVATE_ENVELOPE_SHA_READBACK_PASS conclusion=CONDITIONAL_NATIVE_ENVELOPE_REVIEW G5_SCIENTIFICALLY_ACCEPTED=false MATLABRun=0 simulationRun=0 syntheticTestsRepeated=0",flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        code=str(exc)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE112_PRIVATE_ENVELOPE_FAILED_"+type(exc).__name__.upper()
        if ROOT.is_dir():
            try:
                p=ROOT/("JTE112_"+os.environ.get("GITHUB_RUN_ID","UNKNOWN")+"_PRIVATE_FAILURE.json")
                p.write_text(json.dumps({"schema":SCHEMA,"stage":STAGE,"code":code,"exceptionClass":type(exc).__name__}))
                t,f=context();upload_verified(t,f,p,schema=SCHEMA)
            except Exception:pass
        print("JTE112_BLOCKED stage="+STAGE+" code="+code,flush=True);sys.exit(1)
