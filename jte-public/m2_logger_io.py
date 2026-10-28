"""M2 logger construction/compile only. No trajectory or standalone access retest."""
import os,json,sys,hashlib,shutil,zipfile,re
from pathlib import Path
from xml.etree import ElementTree as E
from sampled_actuator_review_io import ROOT,get,need
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
from JTE101_io import quota
MSG="BTMS_M2_TOFILE_METADATA_SCALAR_FIX";SCHEMA="BTMS_M1_M2_STATIC_ONLY_NOT_G5"
PIN="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
def context():
 e=json.load(open(os.environ["GITHUB_EVENT_PATH"]))
 need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
  os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
  (e.get("head_commit")or{}).get("id")==os.environ["GITHUB_SHA"] and (e.get("head_commit")or{}).get("message")==MSG and
  (e.get("repository")or{}).get("private") is False and os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","M2_CONTEXT")
 t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
 return t,ensure_app_folder(t)
def resources(t):
 mem={}
 for x in Path("/proc/meminfo").read_text().splitlines():
  k,v=x.split(":",1)
  if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
 return {"RAM":mem,"diskFree_bytes":shutil.disk_usage(".").free,"Drive":quota(t),"CPU":os.cpu_count(),
  "runner":"standard_public_github_hosted","paidService":False,"scope":"Current host metadata, not physical trajectory peak"}
def fetch(t,f):
 ROOT.mkdir(mode=0o700,exist_ok=False);got=[]
 def asset(name,local,rc=None):
  a=get(t,f,name,local);got.append(a)
  if rc is not None:
   rr=[q for q in rc["files"] if q["name"]==name]
   need(len(rr)==1 and rr[0]["sha256"]==a["sha256"] and rr[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","M2_INPUT_RECEIPT")
  return a
 pre="ACTUATOR_REVIEW_40659584085_"
 asset(pre+"PRIVATE_RECEIPT.json","source_receipt.json");rc=json.load(open(ROOT/"source_receipt.json"))
 need(rc["run"]=="40659584085" and rc["commit"]=="5ebb693c5109fe79c0b32374613637f4beecccd5","M2_PRIOR_COMPILE")
 asset(pre+"INPUT_MANIFEST.json","old_manifest.json",rc)
 old=json.load(open(ROOT/"old_manifest.json"));w=asset("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")
 rr=[x for x in old["files"] if x["local"]=="source_workspace.mat"]
 need(len(rr)==1 and rr[0]["sha256"]==w["sha256"],"M2_WORKSPACE_LINK")
 cases=[]
 for case in ("B0L","C0"):
  for role in ("Ref","Fine"):
   key=case+"_"+role
   model=asset(pre+key+"_MODEL.slx",key+".slx",rc)
   asset(pre+key+"_PROOF.json",key+"_proof.json",rc)
   q=json.load(open(ROOT/(key+"_proof.json")))
   need(model["sha256"]==q["proof"]["amendedModelSHA"] and q["proof"]["physicalParameterParity"] and
    q["modelWorkspaceICParametersExact"],"M2_AMENDED_SOURCE")
   logDir=ROOT/"logs"/key;logDir.mkdir(mode=0o700,parents=True,exist_ok=False)
   cases.append({"key":key,"source":key+".slx","sourceSHA":model["sha256"],"priorProof":key+"_proof.json","privateDir":str(logDir.resolve())})
 asset("BTMS_M1M2_40692041954_RESOURCE_INPUTS.json","prior_resources.json")
 asset("BTMS_M1_CERT_40693084138_PRIVATE_RECEIPT.json","m1_receipt.json")
 mc=json.load(open(ROOT/"m1_receipt.json"))
 need(mc["run"]=="40693084138" and mc["commit"]=="f39d580d1d6c98556977ba5e619e6929e5e311ea","M2_M1_RECEIPT")
 asset("BTMS_M1_CERT_40693084138_PATH_CERTIFICATE.json","m1_paths.json",mc)
 m=json.load(open(ROOT/"m1_paths.json"));need(m["M1_STATIC_PUMP_ELECTRICAL_PATH"]=="PASS" and m["M1_FOUR_AMENDED_PATH_PARITY"]=="PASS","M2_M1_PATHS")
 r=resources(t)
 need(r["RAM"]["MemAvailable_bytes"]>4*1024**3 and r["diskFree_bytes"]>10*1024**3 and r["Drive"]["availableBytes"]>512*1024**2,"M2_STATIC_COMPILE_RESOURCE")
 manifest={"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"inputs":got,"cases":cases,"resource":r,
  "vendorSLXSHA":PIN,"scope":"CONSTRUCTION_AND_COMPILE_ONLY","physicalRunAuthorized":False,"G5Accepted":False}
 (ROOT/"m2_manifest.json").write_text(json.dumps(manifest,indent=2))
 print("BTMS_M2_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+" scope=LOGGER_STATIC_COMPILE_ONLY noPhysicalRun=1")
def canonical(x):
 return (x.tag,tuple(sorted(x.attrib.items())),(x.text or "").strip(),tuple(canonical(c) for c in x))
def zip_audit(file):
 with zipfile.ZipFile(file) as z:
  docs={n:E.fromstring(z.read(n)) for n in z.namelist() if n.startswith("simulink/") and n.endswith(".xml")}
  config={n:canonical(d) for n,d in docs.items() if "configSet" in n}
  nets=[]
  for n,d in docs.items():
   for l in d.iter("Line"):
    if l.attrib.get("LineType")=="Connection":
     ports=sorted(set(p.text for p in l.iter("P") if p.attrib.get("Name") in ("Src","Dst")))
     nets.append((n,tuple(ports)))
  marked=[]
  for n,d in docs.items():
   for port in d.iter("Port"):
    pp={p.attrib.get("Name"):p.text for p in port.findall("./P")}
    if pp.get("DataLogging")=="on":marked.append({"document":n,"attributes":port.attrib,"properties":pp})
  return {"config":config,"physicalNets":sorted(nets),"explicitDataLoggingPorts":marked}
def publish(t,f):
 run=os.environ["GITHUB_RUN_ID"];prefix="BTMS_M2_"+run+"_"
 # Always preserve actual MATLAB files first, including failure/console diagnostics.
 result={"decision":"NO_GO_STATIC_LOGGER_GRAPH","runtimeEvidence":"MATLAB_FLAGS_UNAVAILABLE","physicalRun":False,"G5Accepted":False}
 summary=ROOT/(prefix+"FLAGS.json")
 if summary.is_file():result=json.load(open(summary))
 pairs=[]
 for c in json.load(open(ROOT/"m2_manifest.json"))["cases"]:
  key=c["key"];src=ROOT/c["source"];dst=ROOT/(prefix+key+"_LOGGER.slx")
  need(hashlib.sha256(src.read_bytes()).hexdigest()==c["sourceSHA"],"M2_SOURCE_MUTATED")
  if dst.is_file():
   a=zip_audit(src);b=zip_audit(dst)
   ok=a["physicalNets"]==b["physicalNets"] and a["config"]==b["config"]
   pairs.append({"case":key,"fullConfigXMLParity":a["config"]==b["config"],"completePhysicalNetsParity":a["physicalNets"]==b["physicalNets"],
    "sourcePortLoggingMarks":a["explicitDataLoggingPorts"],"clonePortLoggingMarks":b["explicitDataLoggingPorts"]})
   if not ok:result["decision"]="NO_GO_STATIC_LOGGER_GRAPH"
 (ROOT/(prefix+"XML_PARITY.json")).write_text(json.dumps({"caseChecks":pairs,"allFour":len(pairs)==4 and all(x["fullConfigXMLParity"] and x["completePhysicalNetsParity"] for x in pairs),"physicalRun":False},indent=2))
 (ROOT/(prefix+"FINAL_QUALIFICATION.json")).write_text(json.dumps({"matlab":result,
  "finalDecision":result["decision"],"completePhysicalIC":"UNQUALIFIED","acceptedMajorClock":"UNQUALIFIED",
  "physicalRuntimePeakRAM":"UNMEASURED","full2400RequiredFor340Preflight":False,"legacyLoggingRemoval":"PROPOSAL_ONLY_NO_CHANGES",
  "sourceReceiptReused":True,"G5Accepted":False},indent=2))
 (ROOT/(prefix+"CURRENT_RESOURCES.json")).write_text(json.dumps(resources(t),indent=2))
 shutil.copyfile(ROOT/"m2_manifest.json",ROOT/(prefix+"INPUT_MANIFEST.json"))
 out=[]
 for p in sorted(ROOT.glob(prefix+"*")):
  if p.is_file():out.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
 receipt={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":out,"physicalRun":False,"G5Accepted":False}
 p=ROOT/(prefix+"PRIVATE_RECEIPT.json");p.write_text(json.dumps(receipt,indent=2));upload_verified(t,f,p,schema=SCHEMA)
 print("BTMS_M2_PRIVATE_READBACK_PASS decision="+str(result.get("decision"))+" physicalRun=0 G5_ACCEPTED=false")
 need(result.get("staticCompileAll") is True and len(pairs)==4 and all(x["fullConfigXMLParity"] and x["completePhysicalNetsParity"] for x in pairs),"M2_STATIC_QUALIFICATION_NOT_PASS")
if __name__=="__main__":
 try:
  t,f=context()
  if sys.argv[1]=="fetch":fetch(t,f)
  elif sys.argv[1]=="publish":publish(t,f)
  else:raise RuntimeError("M2_MODE")
 except Exception:
  print("BTMS_M2_UNQUALIFIED details=OWNER_PRIVATE_ONLY noPhysicalRun=1");sys.exit(1)
