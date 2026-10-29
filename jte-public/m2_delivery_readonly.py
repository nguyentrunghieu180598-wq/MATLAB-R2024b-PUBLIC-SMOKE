"""Final M2 engineering delivery: consume completed static proofs only."""
import os,json,sys,re,shutil
from pathlib import Path
import m2_logger_io as io
from sampled_actuator_review_io import ROOT,get,need
from JTE063_streaming_drive import upload_verified
io.MSG="BTMS_M2_FINAL_READONLY_DELIVERY"
SCHEMA=io.SCHEMA;SRC="BTMS_M2_40701917441_"
def main(t,f):
 ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];pre="BTMS_M2DELIVERY_"+run+"_";inputs=[];outputs=[]
 def asset(name,local,rc=None):
  m=get(t,f,name,local);inputs.append(m)
  if rc is not None:
   a=[x for x in rc["files"] if x["name"]==name]
   need(len(a)==1 and a[0]["sha256"]==m["sha256"] and a[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","M2_DELIVERY_LINK")
  return json.load(open(ROOT/local))
 def emit(suffix,data):
  p=ROOT/(pre+suffix);p.write_text(data if isinstance(data,str) else json.dumps(data,indent=2))
  outputs.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
 rc=asset(SRC+"PRIVATE_RECEIPT.json","receipt.json")
 need(rc["run"]=="40701917441" and rc["commit"]=="75afa01be55339d20ce5831830a0cacdb0c5d3f4" and not rc["physicalRun"],"M2_DELIVERY_SOURCE")
 flags=asset(SRC+"FLAGS.json","flags.json",rc);xml=asset(SRC+"XML_PARITY.json","xml.json",rc)
 resource=asset(SRC+"CURRENT_RESOURCES.json","resources.json",rc);manifest=asset(SRC+"INPUT_MANIFEST.json","manifest.json",rc)
 need(flags["staticCompileAll"] and flags["loggerCandidate"]=="M2_STATIC_LOGGER_CANDIDATE_READY" and
  flags["decision"]=="NO_GO_IC_CLOCK_OR_RESOURCE" and xml["allFour"] and len(flags["caseProofs"])==4,"M2_DELIVERY_STATIC")
 def memory(r):
  s="\n".join(r.get("procStatus",[]))
  return {k+"_bytes":int(m.group(1))*1024 for k in ("VmHWM","VmRSS","VmPeak","VmSize")
   if (m:=re.search(r"(?m)^"+k+r":\s*(\d+)\s*kB",s))}
 table=[]
 for case in ("B0L_Ref","B0L_Fine","C0_Ref","C0_Fine"):
  p=asset(SRC+case+"_PROOF.json",case+".json",rc)
  need(p["trueT312CompiledWidthVerified"] and p["fullRetainedParametersConfigGraphParity"] and
   p["newStreamingTaps"]==4 and p["staticCompileOnly"],"M2_DELIVERY_PROOF")
  taps=p["tapCompiled"];need(len(taps)==4 and all(x["sourceRateContainsLoggerRate"] for x in taps),"M2_DELIVERY_RATES")
  inv=p["existingLogging"];n=len(inv["toWorkspace"])//2
  names=[x["VariableName"] for x in inv["toWorkspace"][n:]]
  raw=inv["config"];c=len(raw)//2;config=dict(zip(raw[:c],raw[c:]))
  table.append({"case":case,"period_s":p["period_s"],"staticGraphAndCompile":"PASS",
   "taps":taps,"legacyToWorkspaceCount":n,"legacyVariableNames":names,
   "retainedModelLoggingConfig":config,"scopeLogging":inv["scopes"],
   "globalSDI":"UNAVAILABLE_NOT_CHANGED","sourceTwoPathProofReused":p["sourceTwoPathProofReused"],
   "staticProcess":memory(p["processAfterCompile"]),"compileOnlyWall_s":p["compileWall_s"],
   "sourceModelSHA":p["sourceSHA256"],"loggerModelSHA":p["instrumentedModelSHA256"],
   "savedStopTime":p["stopTimePreserved"],"shortHorizonRunCapApplied":p["shortHorizonRunCapApplied"]})
 rows=[]
 for Ts,N in ((.01,34001),(.005,68001)):
  rows.append({"horizon_s":340,"Ts_s":Ts,"scheduledHitsOnly":N,
   "T312_values_payload_bytes":N*312*8,"T312_time_payload_bytes":N*8,
   "T312_values_plus_time_bytes":N*313*8,
   "notAnUpperBound":True,"actualNativeRowCount":"NOT_OBSERVED_NO_PLANT",
   "otherRoleClockStorage":"16*(N_core+N_sampled+N_y) bytes; no common-clock assumption",
   "HDF5AndWorkspaceCopies":"NOT_INCLUDED; native extra hits, duplicates and metadata increase storage",
   "peakPhysicalRAMMeasured":False})
 envelope={"actualCurrentResource":resource,"preSetupResource":manifest["resource"],"schedulePayloadScreens":rows,
  "actualMATLABRuntime":flags["runtime"],"actualAllFourStaticWall_s":flags["totalWall_s"],
  "staticMATLABProcessAtEnd":memory(flags["processAtEnd"]),
  "caveat":"Static process HWM and current host availability are actual evidence, not 340s trajectory peak/runtime estimates.",
  "full2400BudgetRequiredFor340":False,"future340RuntimeAndPeak":"UNMEASURED",
  "finalDecision":"NO_GO_IC_CLOCK_OR_RESOURCE"}
 emit("STATIC_TABLE_AND_LOGGING_INVENTORY.json",{"cases":table,"XML":xml,"noPlant":True})
 emit("RESOURCE_ENVELOPE_340.json",envelope)
 emit("QUALIFICATION.json",{"decision":"NO_GO_IC_CLOCK_OR_RESOURCE","loggerStaticCandidate":"M2_STATIC_LOGGER_CANDIDATE_READY",
  "staticCompileRun":"40701917441","staticCompileCommit":rc["commit"],"caseCount":4,"graphAndConfigParityAll":True,
  "toFileCanaryRun":False,"reasonNoExtraCanary":"Documented APIs and actual sink rates/type/width compile checks are qualified. Generic file toy would not establish this plant's solved IC or process peak; no repeat of8/8 actuator toy.",
  "completePhysicalIC":"UNQUALIFIED","actualFileClocksAndAcceptedMajor":"UNQUALIFIED_NO_PHYSICAL_RUN",
  "memoryReduction":"UNPROVEN_LEGACY_LOGGERS_RETAINED","physicalRunAuthorized":False,
  "originalG5":"REJECTED_FOR_THERMAL_INFERENCE","amendedPhysicalG5":"UNQUALIFIED","G5Accepted":False})
 emit("OPERATIONS_PROPOSAL_ONLY.md",Path("actuator-amendment/M2_340_OPERATIONS_PROPOSAL.md").read_text())
 emit("INTERNAL_HANDOFF.md",Path("actuator-amendment/M2_STATIC_LOGGER_DELIVERY.md").read_text())
 emit("INPUT_MANIFEST.json",{"inputs":inputs,"scope":"READ_ONLY_FINAL_ENGINEERING_DELIVERY","noMATLAB":True,"noPhysicalRun":True})
 p=ROOT/(pre+"PRIVATE_RECEIPT.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
  "files":outputs,"MATLABRun":False,"physicalRun":False,"G5Accepted":False},indent=2));upload_verified(t,f,p,schema=SCHEMA)
 print("BTMS_M2_DELIVERY_PRIVATE_READBACK_PASS staticCompileCases=4 final=NO_GO_IC_CLOCK_OR_RESOURCE noMATLAB=1 physicalRun=0 G5_ACCEPTED=false")
if __name__=="__main__":
 try:
  t,f=io.context();main(t,f)
 except Exception:
  print("BTMS_M2_DELIVERY_UNQUALIFIED noPhysicalRun=1");sys.exit(1)
