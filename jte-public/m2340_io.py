"""ONE B0L10ms 340s derivative STATIC compile only; private receipt transport."""
import os,json,sys,re,hashlib,shutil,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
import m2_logger_io as parent
from sampled_actuator_review_io import ROOT,get,need
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota
parent.MSG="BTMS_M2_340_INCLUDE_COMMENTED_AUDIT"
SCHEMA=parent.SCHEMA;SRC="BTMS_M2_40701917441_"
def host(t):
 ram={}
 for row in Path("/proc/meminfo").read_text().splitlines():
  k,v=row.split(":",1)
  if k in ("MemTotal","MemAvailable"):ram[k+"_bytes"]=int(v.split()[0])*1024
 lines=Path("/proc/self/cgroup").read_text().splitlines();base=Path("/sys/fs/cgroup");dirs=[]
 for x in lines:
  q=x.split(":",2)
  if len(q)==3 and q[0]=="0":dirs.append(base/q[2].lstrip("/"))
 dirs += [base]
 cg={"status":"UNAVAILABLE","procSelfCgroup":lines}
 for d in dirs:
  if (d/"memory.current").is_file() and (d/"memory.max").is_file():
   fields={}
   for name in ("memory.max","memory.current","memory.peak","memory.high","memory.swap.max"):
    p=d/name
    if p.is_file():fields[name]=p.read_text().strip()
   cg={"status":"AVAILABLE_V2","path":str(d),"values":fields,"procSelfCgroup":lines};break
 if cg["status"]=="UNAVAILABLE":
  d=base/"memory"
  if (d/"memory.limit_in_bytes").is_file():
   cg={"status":"AVAILABLE_V1","path":str(d),"values":{"memory.max":(d/"memory.limit_in_bytes").read_text().strip(),
    "memory.current":(d/"memory.usage_in_bytes").read_text().strip()},"procSelfCgroup":lines}
 limit=ram["MemTotal_bytes"];head=ram["MemAvailable_bytes"]
 if cg["status"]!="UNAVAILABLE":
  v=cg["values"];raw=v["memory.max"];used=int(v["memory.current"])
  if raw!="max":limit=min(limit,int(raw));head=min(head,max(0,limit-used))
 return {"RAM":ram,"cgroup":cg,"effectiveLimit_bytes":limit,"effectiveAvailable_bytes":head,
  "diskFree_bytes":shutil.disk_usage(".").free,"Drive":quota(t),"CPU":os.cpu_count(),
  "standardIncludedPublicRunner":True,"paidService":False,"actualPhysicalPeakKnown":False}
def fetch(t,f):
 ROOT.mkdir(mode=0o700,exist_ok=False);inputs=[]
 def asset(name,local,rc=None):
  a=get(t,f,name,local);inputs.append(a)
  if rc is not None:
   x=[q for q in rc["files"] if q["name"]==name]
   need(len(x)==1 and x[0]["sha256"]==a["sha256"] and x[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","M2340_RECEIPT")
  return a
 asset(SRC+"PRIVATE_RECEIPT.json","old_receipt.json");rc=json.load(open(ROOT/"old_receipt.json"))
 need(rc["run"]=="40701917441" and rc["commit"]=="75afa01be55339d20ce5831830a0cacdb0c5d3f4" and not rc["physicalRun"],"M2340_PROVENANCE")
 src=asset(SRC+"B0L_Ref_LOGGER.slx","M2340Source.slx",rc)
 asset(SRC+"B0L_Ref_PROOF.json","old_proof.json",rc);q=json.load(open(ROOT/"old_proof.json"))
 need(q["instrumentedModelSHA256"]==src["sha256"] and q["period_s"]==.01 and
  q["trueT312CompiledWidthVerified"] and q["fullRetainedParametersConfigGraphParity"],"M2340_SOURCE")
 asset(SRC+"B0L_Ref_PROOF.mat","old_proof.mat",rc)
 asset(SRC+"INPUT_MANIFEST.json","old_manifest.json",rc)
 old=json.load(open(ROOT/"old_manifest.json"))
 w=asset("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")
 rr=[z for z in old["inputs"] if z["local"]=="source_workspace.mat"]
 need(len(rr)==1 and rr[0]["sha256"]==w["sha256"],"M2340_WORKSPACE")
 r=host(t);resourceOK=(r["cgroup"]["status"]!="UNAVAILABLE" and r["effectiveAvailable_bytes"]>8*1024**3 and
  r["diskFree_bytes"]>10*1024**3 and r["Drive"]["availableBytes"]>int(2.5*1024**3))
 out=ROOT/"private340";out.mkdir(mode=0o700,exist_ok=False)
 m={"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"inputs":inputs,"sourceModel":src,
  "privateDir":str(out.resolve()),"resource":r,"staticCompileResourceScreen":resourceOK,
  "physicalRunAuthorized":False,"scope":"ONE_STATIC_B0L10MS_DERIVATIVE_NO_TIME_ADVANCEMENT"}
 (ROOT/"m2340_manifest.json").write_text(json.dumps(m,indent=2))
 print("BTMS_M2_340_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+" oneStaticDerivative=1 physicalRun=0")
 need(resourceOK,"M2340_RESOURCE_STATIC_SCREEN")
def prop(e):return {p.attrib["Name"]:p.text or "" for p in e.findall("./P")}
def canonical(e):
 return (e.tag,tuple(sorted(e.attrib.items())),(e.text or "").strip(),tuple(canonical(c) for c in e))
def saved(file,stop):
 with zipfile.ZipFile(file) as z:
  docs={n:E.fromstring(z.read(n)) for n in z.namelist() if n.startswith("simulink/") and n.endswith(".xml")}
  config={}
  for n,d in docs.items():
   if "configSet" not in n:continue
   for p in d.iter("P"):
    if p.attrib.get("Name")=="StopTime":
     need(p.text==stop,"M2340_SAVED_STOP");p.text="ALLOWED_SOURCE_2400_TARGET_340"
   config[n]=canonical(d)
  nets=[];commented={};files={}
  for n,d in docs.items():
   for l in d.iter("Line"):
    if l.attrib.get("LineType")=="Connection":
     nets.append((n,tuple(sorted(set(p.text for p in l.iter("P") if p.attrib.get("Name") in ("Src","Dst"))))))
   for b in d.iter("Block"):
    sid=b.attrib.get("SID");pp=prop(b)
    if sid:
     commented[sid]=pp.get("Commented","off")
     if b.attrib.get("BlockType")=="ToFile":
      kk=[k for k in pp if k.casefold()=="filename"]
      need(len(kk)==1 and isinstance(pp[kk[0]],str) and pp[kk[0]],"M2340_SAVED_FILENAME")
      files[sid]=pp[kk[0]]
  return {"config":config,"nets":sorted(nets),"commented":commented,"fileTargets":files}
def publish(t,f):
 run=os.environ["GITHUB_RUN_ID"];pre="BTMS_M2340_"+run+"_";outs=[];uploaded=set()
 def stash():
  for p in sorted(ROOT.glob(pre+"*")):
   if p.is_file() and p.name not in uploaded and not p.name.endswith("PRIVATE_RECEIPT.json"):
    outs.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)});uploaded.add(p.name)
 result={"status":"M2_340_STATIC_GRAPH_REJECTED","staticCompilePass":False,"physicalRun":False,"G5Accepted":False}
 flags=ROOT/(pre+"FLAGS.json")
 if flags.is_file():result=json.load(open(flags))
 # Preserve raw MATLAB evidence BEFORE attempting interpretation. An audit bug
 # must never prevent publication of existing console/flags/model/proof files.
 target=ROOT/"M2340Prepared.slx"
 if target.is_file() and not (ROOT/(pre+"MODEL.slx")).exists():
  shutil.copyfile(target,ROOT/(pre+"MODEL_UNQUALIFIED.slx"))
 stash()
 xml={"available":False,"onlyAllowedConfigDelta":False,"sameCompletePhysicalNets":False}
 resource={"status":"UNAVAILABLE"}
 try:
  m=json.load(open(ROOT/"m2340_manifest.json"));src=ROOT/"M2340Source.slx";dst=ROOT/(pre+"MODEL.slx")
  need(hashlib.sha256(src.read_bytes()).hexdigest()==m["sourceModel"]["sha256"],"M2340_SOURCE_BYTES_CHANGED")
  if dst.is_file():
   a=saved(src,"2400");b=saved(dst,"340")
   changes=[{"SID":sid,"source":v,"target":b["commented"].get(sid)} for sid,v in a["commented"].items() if b["commented"].get(sid)!=v]
   targets=list(b["fileTargets"].values());parentDir=Path(m["privateDir"]).resolve()
   pathsOK=(len(targets)==4 and len(set(targets))==4 and
    all(isinstance(p,str) and p and Path(p).resolve().parent==parentDir for p in targets))
   xml={"available":True,"onlyAllowedConfigDelta":a["config"]==b["config"],"sameCompletePhysicalNets":a["nets"]==b["nets"],
    "allSameBlockSIDs":a["commented"].keys()==b["commented"].keys(),"commentChanges":changes,
    "changedFileTargets":len([sid for sid,v in a["fileTargets"].items() if b["fileTargets"].get(sid)!=v]),
    "allFileTargetsPrivateAndDistinct":pathsOK,
    "allFileTargetsAbsent":pathsOK and all(not Path(p).exists() for p in targets)}
   good=(xml["onlyAllowedConfigDelta"] and xml["sameCompletePhysicalNets"] and xml["allSameBlockSIDs"] and
    len(changes)==3 and all(c["source"]=="off" and c["target"]=="on" for c in changes) and
    xml["changedFileTargets"]==4 and xml["allFileTargetsAbsent"])
   if not good:result["status"]="M2_340_STATIC_GRAPH_REJECTED";result["staticCompilePass"]=False
  else:result["status"]="M2_340_STATIC_GRAPH_REJECTED";result["staticCompilePass"]=False
  resource=host(t)
  readyResource=(resource["cgroup"]["status"]!="UNAVAILABLE" and resource["effectiveAvailable_bytes"]>2*1024**3 and
   resource["diskFree_bytes"]>4*1024**3 and resource["Drive"]["availableBytes"]>int(2.5*1024**3))
  if not readyResource and result.get("staticCompilePass"):result["status"]="M2_340_NO_GO_RESOURCE_OR_IC"
 except Exception as e:
  result["status"]="M2_340_STATIC_GRAPH_REJECTED";result["staticCompilePass"]=False
  result["publicationAuditFailure"]={"type":type(e).__name__,"message":str(e)}
  m=json.load(open(ROOT/"m2340_manifest.json")) if (ROOT/"m2340_manifest.json").is_file() else {}
 (ROOT/(pre+"XML_PARITY.json")).write_text(json.dumps(xml,indent=2))
 (ROOT/(pre+"HOST_AND_STOP_POLICY.json")).write_text(json.dumps({"currentHost":resource,
  "beforeSetup":m.get("resource"),"staticHostScreenPass":m.get("staticCompileResourceScreen"),
  "runtimeMemoryPeak":"UNMEASURED_UNTIL_OWNER_APPROVED_OBSERVATION",
  "RAMReserve_bytes":2*1024**3,"diskReserve_bytes":2*1024**3,
  "maxOneFile_bytes":1024**3,"maxTotalNativeFiles_bytes":2*1024**3,
  "DriveDeliveryReserve_bytes":512*1024**2,"trajectoryWallCap_s":1200,"deliveryReserve_s":300,
  "onLimit":"Request pause/stop, preserve partial; incomplete UNQUALIFIED, no sample deletion/retry",
  "watchdog":"External live cgroup/process + disk/file growth; must be active before any approved initialize; NOT STARTED IN_STATIC_JOB",
  "futureOwnerApprovalRequired":True,"full2400HistoryBudgetRequired":False},indent=2))
 (ROOT/(pre+"FINAL_QUALIFICATION.json")).write_text(json.dumps(result,indent=2))
 if (ROOT/"m2340_manifest.json").is_file():shutil.copyfile(ROOT/"m2340_manifest.json",ROOT/(pre+"INPUT_MANIFEST.json"))
 for file in ("actuator-amendment/M2_340_WITNESS_AND_STOP_PLAN.md",):
  shutil.copyfile(file,ROOT/(pre+Path(file).name))
 stash()
 p=ROOT/(pre+"PRIVATE_RECEIPT.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
  "files":outs,"physicalRun":False,"G5Accepted":False},indent=2));upload_verified(t,f,p,schema=SCHEMA)
 print("BTMS_M2_340_PRIVATE_READBACK_PASS status="+result["status"]+" physicalRun=0 G5_ACCEPTED=false")
 need(result.get("staticCompilePass") is True and result["status"]=="M2_340_PREPARED_STATIC_PASS_OWNER_PHYSICAL_APPROVAL_NEEDED","M2340_NOT_PREPARED")
if __name__=="__main__":
 try:
  t,f=parent.context()
  if sys.argv[1]=="fetch":fetch(t,f)
  elif sys.argv[1]=="publish":publish(t,f)
  else:raise RuntimeError("M2340_MODE")
 except Exception:
  print("BTMS_M2_340_UNQUALIFIED details=OWNER_PRIVATE_ONLY physicalRun=0");sys.exit(1)
