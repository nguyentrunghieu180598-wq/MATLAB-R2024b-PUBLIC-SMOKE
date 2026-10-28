"""M1/M2 static source package: read ZIP/XML/SSC and prior compile receipts only."""
import json,os,re,sys,hashlib,zipfile,shutil,subprocess
from pathlib import Path
from xml.etree import ElementTree as E
import h5py,numpy as np
from sampled_actuator_review_io import ROOT,get,need
from JTE101_io import quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
SCHEMA="BTMS_M1_M2_STATIC_ONLY_NOT_G5";MSG="BTMS_M1_M2_PINNED_GRAPH_READONLY"
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
VENDOR="f98d21929a3a269dacd1ee38999cd9773760c6db"
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def context():
    e=json.load(open(os.environ["GITHUB_EVENT_PATH"]))
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")==MSG and (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","M1_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def prop(x):return {p.attrib.get("Name",""):p.text or "" for p in x.findall("./P")}
def parse_slx(file,label):
    before=sha(file);blocks=[];edges=[];systems=[];unresolved=[];visited=set()
    with zipfile.ZipFile(file) as z:
        docs={n:E.fromstring(z.read(n)) for n in z.namelist() if n.startswith("simulink/") and n.endswith(".xml")}
        need("simulink/blockdiagram.xml" in docs,"M1_BLOCKDIAGRAM_ABSENT")
        def resolve(s):
            if "Ref" not in s.attrib:return s,None
            ref=s.attrib["Ref"];candidate=[(n,d) for n,d in docs.items() if n.rsplit("/",1)[-1]==ref+".xml"]
            need(len(candidate)==1,"M1_SYSTEM_REF_UNRESOLVED")
            n,d=candidate[0]
            return (d if d.tag=="System" else d.find(".//System")),n
        def line(l,sys,src=None,name=""):
            pp=prop(l);src=pp.get("Src",src);name=pp.get("Name",name)
            if "Dst" in pp:edges.append({"system":sys,"src":src,"dst":pp["Dst"],"name":name,"parameters":pp})
            for c in l.findall("./Branch"):line(c,sys,src,name)
        def walk(s,path):
            s,doc=resolve(s);need(s is not None,"M1_SYSTEM_EMPTY")
            key=(path,doc)
            need(key not in visited,"M1_SYSTEM_CYCLE");visited.add(key)
            systems.append({"path":path,"file":doc,"parameters":prop(s)})
            for b in s.findall("./Block"):
                name=b.attrib.get("Name","");p=path+"/"+name;pp=prop(b);inst={}
                for v in b.findall("./InstanceData"):inst.update(prop(v))
                row={"path":p,"parent":path,"name":name,"SID":b.attrib.get("SID"),"type":b.attrib.get("BlockType"),"parameters":pp,"instance":inst}
                # Preserve nontrivial mask/port metadata, not guessed compiled attributes.
                row["portMetadata"]=[E.tostring(q,encoding="unicode") for q in b.findall("./PortCounts")+b.findall("./PortProperties")]
                mask=b.find("./Mask")
                if mask is not None:row["maskXML"]=E.tostring(mask,encoding="unicode")
                blocks.append(row)
                child=b.find("./System")
                if child is not None:walk(child,p)
            for l in s.findall("./Line"):line(l,path)
        root=docs["simulink/blockdiagram.xml"];m=root.find("./Model")
        if m is None:m=root.find(".//Model")
        need(m is not None,"M1_MODEL_ELEMENT_ABSENT")
        ss=m.find("./System")
        if ss is None:ss=m.find(".//System")
        need(ss is not None,"M1_MODEL_SYSTEM_ABSENT");walk(ss,"$ROOT")
        by={b["SID"]:b["path"] for b in blocks}
        for x in edges:
            for field in ("src","dst"):
                v=x[field]
                if not v:unresolved.append({"reason":"SOURCE_ABSENT","edge":x});continue
                sid=v.split("#",1)[0];x[field+"Path"]=by.get(sid,"UNRESOLVED_SID:"+sid)
        configs={n:E.tostring(d,encoding="unicode") for n,d in docs.items() if "configSet" in n}
    need(before==sha(file),"M1_SOURCE_BYTES_CHANGED")
    return {"label":label,"modelSHA":before,"blocks":blocks,"edges":edges,"systems":systems,"unresolved":unresolved,
      "configXML":configs,"scope":"STATIC_SAVED_XML_NO_MODEL_LOAD_NO_COMPILE_NO_SIM"}
def main(t,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];prefix="BTMS_M1M2_"+run+"_";inputs=[];outputs=[]
    def asset(name,local,rc=None):
        m=get(t,folder,name,local);inputs.append(m)
        if rc is not None:
            a=[v for v in rc["files"] if v["name"]==name]
            need(len(a)==1 and a[0]["sha256"]==m["sha256"] and a[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","M1_RECEIPT_LINK")
        return m
    def emit(suffix,data):
        p=ROOT/(prefix+suffix);p.write_text(json.dumps(data,indent=2,ensure_ascii=True))
        outputs.append({"name":p.name,**upload_verified(t,folder,p,schema=SCHEMA)})
    p="ACTUATOR_REVIEW_40659584085_"
    asset(p+"PRIVATE_RECEIPT.json","compile_receipt.json");rc=json.load(open(ROOT/"compile_receipt.json"))
    need(rc["run"]=="40659584085" and rc["commit"]=="5ebb693c5109fe79c0b32374613637f4beecccd5","M1_COMPILE_SOURCE")
    asset(p+"INPUT_MANIFEST.json","old_input_manifest.json",rc)
    old=json.load(open(ROOT/"old_input_manifest.json"))
    workspace=asset("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")
    ww=[x for x in old["files"] if x["local"]=="source_workspace.mat"]
    need(len(ww)==1 and ww[0]["sha256"]==workspace["sha256"],"M1_WORKSPACE_LINK")
    cases=[]
    for case in ("B0L","C0"):
        for role in ("Ref","Fine"):
            key=case+"_"+role
            a=asset(p+key+"_PROOF.json",key+"_proof.json",rc);q=json.load(open(ROOT/(key+"_proof.json")))
            model=asset(p+key+"_MODEL.slx",key+".slx",rc)
            need(model["sha256"]==q["proof"]["amendedModelSHA"] and q["proof"]["physicalParameterParity"] and
              q["proof"]["sourceWireNamesPreserved"] and q["modelWorkspaceICParametersExact"],"M1_PRIOR_STATIC_PARITY")
            cases.append({"label":key,"local":key+".slx","proof":q,"model":model})
    rprefix="ACTUATOR_REVIEW_40661029261_"
    asset(rprefix+"CONSOLIDATED_RECEIPT.json","cost_receipt.json");cr=json.load(open(ROOT/"cost_receipt.json"))
    need(cr["run"]=="40661029261" and cr["commit"]=="f4182fc6d20ce11371c9414f34b0e30b7670b6fc","M1_COST_SOURCE")
    asset(rprefix+"RESOURCE_SCREEN.json","old_resource.json",cr)
    vendor=Path("vendor-pack")
    rev=subprocess.check_output(["git","-C",str(vendor),"rev-parse","HEAD"],text=True).strip()
    source=vendor/"Models/Battery_Pack_Thermal_Management.slx"
    need(rev==VENDOR and sha(source)==PIN,"M1_VENDOR_PIN")
    print("BTMS_M1_M2_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" mode=STATIC_NO_MATLAB noCompile=1 noSimulation=1",flush=True)
    base=parse_slx(source,"PINNED_VENDOR")
    emit("PINNED_VENDOR_GRAPH.json",base)
    graphMeta=[]
    for c in cases:
        g=parse_slx(ROOT/c["local"],c["label"])
        need(g["modelSHA"]==c["model"]["sha256"],"M1_AMENDED_GRAPH_SHA")
        emit(c["label"]+"_GRAPH.json",g)
        emit(c["label"]+"_REUSED_COMPILE.json",c["proof"])
        graphMeta.append({"label":c["label"],"modelSHA":g["modelSHA"],"blocks":len(g["blocks"]),"edges":len(g["edges"]),"unresolved":g["unresolved"]})
    vals={}
    with h5py.File(ROOT/"source_workspace.mat","r") as f:
        for k in ("ambient","coolantTemp","initialPackSOC","Flowrate_vec"):
            x=f["workspaceSnapshot/"+k];need(x.dtype.kind=="f","M1_WORKSPACE_NUMERIC_TYPE");a=x[()]
            need(np.isfinite(a).all(),"M1_WORKSPACE_NONFINITE");vals[k]=a.T.tolist()
    ssc={}
    for name in ("batteryMultiDimModel.ssc","batteryCellHeatConvection.ssc","batteryCellThermalLUTmodel.ssc","bottomCoolantPlate.ssc"):
        p=vendor/"Libraries/+batteryModule"/name
        ssc[name]={"sha256":sha(p),"text":p.read_text()}
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    resource={"currentHost":{"RAM":mem,"diskFree_bytes":shutil.disk_usage(".").free,"CPU":os.cpu_count(),"Drive":quota(t)},
      "historic":json.load(open(ROOT/"old_resource.json")),"sourceRun":"40661029261",
      "loggingRuntimeQualified":False,"newSimulation":False,"full2400Go":False}
    emit("SOURCE_COMPONENT_AND_WORKSPACE.json",{"vendorCommit":VENDOR,"sourceSLXSHA":PIN,"workspace":vals,"SSC":ssc})
    emit("RESOURCE_INPUTS.json",resource)
    emit("INDEX.json",{"run":run,"commit":os.environ["GITHUB_SHA"],"inputs":inputs,"graphs":graphMeta,"vendor":{"blocks":len(base["blocks"]),"edges":len(base["edges"]),"unresolved":base["unresolved"]},
      "scope":"Static evidence collection only; path/unit interpretation and M2 review required","sourceCompiledReceiptsReused":True,
      "MATLABRun":False,"modelCompile":False,"simulationRun":False,"G5Accepted":False})
    p=ROOT/(prefix+"PRIVATE_RECEIPT.json")
    p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":outputs,"modelCompile":False,"simulationRun":False,"G5Accepted":False},indent=2))
    upload_verified(t,folder,p,schema=SCHEMA)
    print("BTMS_M1_M2_STATIC_PRIVATE_READBACK_PASS interpretedPathCertificate=PENDING noCompile=1 noSimulation=1 G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context();main(t,f)
    except Exception as e:
        # Fail closed; retain diagnostic privately when possible.
        if ROOT.is_dir():
            try:
                p=ROOT/("BTMS_M1M2_"+os.environ["GITHUB_RUN_ID"]+"_FAILURE.json")
                p.write_text(json.dumps({"exception":type(e).__name__,"message":str(e),"newSimulation":False}))
                upload_verified(t,f,p,schema=SCHEMA)
            except Exception:pass
        print("BTMS_M1_M2_STATIC_UNQUALIFIED details=OWNER_PRIVATE_ONLY");sys.exit(1)
