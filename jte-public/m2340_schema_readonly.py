"""Targeted read-only inspection of ALREADY-SAVED M2 logger schema. No MATLAB."""
import os,json,sys,zipfile
from pathlib import Path
from xml.etree import ElementTree as E
import numpy as np,h5py
import m2340_io as ctx
from sampled_actuator_review_io import ROOT,get,need
from JTE063_streaming_drive import upload_verified
ctx.parent.MSG="BTMS_M2_340_INSPECT_SAVED_SINK_SCHEMA"
SCHEMA=ctx.SCHEMA
def main(t,f):
 ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"];pre="BTMS_M2340_SCHEMA_"+run+"_";inputs=[];out=[]
 def emit(suffix,d):
  p=ROOT/(pre+suffix);p.write_text(json.dumps(d,indent=2));out.append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
 def asset(name,local,rc=None):
  a=get(t,f,name,local);inputs.append(a)
  if rc:
   z=[x for x in rc["files"] if x["name"]==name];need(len(z)==1 and z[0]["sha256"]==a["sha256"],"M2340_SCHEMA_RECEIPT")
  return a
 result={"scope":"READ_ONLY_SAVED_SCHEMA_NO_MATLAB_NO_MODEL_CREATION","run":run,"commit":os.environ["GITHUB_SHA"],"noCompile":True,"physicalRun":False}
 try:
  p="BTMS_M2_40701917441_"
  asset(p+"PRIVATE_RECEIPT.json","rc.json");rc=json.load(open(ROOT/"rc.json"))
  need(rc["run"]=="40701917441" and rc["commit"]=="75afa01be55339d20ce5831830a0cacdb0c5d3f4","M2340_SCHEMA_SOURCE")
  asset(p+"B0L_Ref_LOGGER.slx","source.slx",rc);asset(p+"B0L_Ref_PROOF.mat","proof.mat",rc)
  xmlrows=[]
  with zipfile.ZipFile(ROOT/"source.slx") as z:
   for n in z.namelist():
    if not n.startswith("simulink/") or not n.endswith(".xml"):continue
    d=E.fromstring(z.read(n))
    for b in d.iter("Block"):
     if b.attrib.get("BlockType")=="ToFile":
      pp={v.attrib["Name"]:v.text or "" for v in b.findall("./P")}
      xmlrows.append({"SID":b.attrib.get("SID"),"name":b.attrib.get("Name"),"parameterNames":list(pp),
       "fileKeys":[k for k in pp if k.casefold()=="filename"]})
  matrows=[]
  with h5py.File(ROOT/"proof.mat","r") as fmat:
   def char(ref):
    o=fmat[ref];cl=o.attrs.get("MATLAB_class",b"")
    need(cl==b"char","M2340_SCHEMA_EXPECTED_CHAR")
    return np.asarray(o,dtype="<u2").tobytes().decode("utf-16-le")
   rows=np.asarray(fmat["b/blocks"])
   if rows.shape[0]!=3:rows=rows.T
   need(rows.shape[0]==3,"M2340_SCHEMA_BLOCK_SHAPE")
   for col in rows.T:
    if char(col[1])!="ToFile":continue
    params=np.asarray(fmat[col[2]]).ravel(order="F")
    names=[char(x) for x in np.asarray(fmat[params[0]]).ravel(order="F")]
    matrows.append({"path":char(col[0]),"dialogParameterNames":names,"fileKeys":[k for k in names if k.casefold()=="filename"]})
  need(len(xmlrows)==4 and len(matrows)==4,"M2340_SCHEMA_FOUR")
  result.update({"sourceXML":xmlrows,"actualSavedMATLABDialogMetadata":matrows,"schemaVerified":True})
  tests=[]
  def key(pp):
   z=[x for x in pp if x.casefold()=="filename"]
   if len(z)!=1:raise ValueError("MISSING_OR_AMBIGUOUS_FILENAME")
   return z[0]
  for pp,ok in [({"Filename":"x"},True),({"FileName":"x"},True),({},False),({"Filename":"x","FileName":"y"},False)]:
   try:key(pp);got=True
   except ValueError:got=False
   tests.append(got==ok)
  result["softwareSchemaTests"]={"count":len(tests),"allPass":all(tests),"syntheticOnly":True}
 except Exception as e:
  result["failure"]={"type":type(e).__name__,"message":str(e)}
 emit("FINDINGS.json",result);emit("INPUT_MANIFEST.json",{"inputs":inputs,"noCompile":True,"physicalRun":False})
 p=ROOT/(pre+"PRIVATE_RECEIPT.json");p.write_text(json.dumps({"run":run,"commit":os.environ["GITHUB_SHA"],"files":out,"noMATLAB":True,"physicalRun":False},indent=2))
 upload_verified(t,f,p,schema=SCHEMA)
 print("BTMS_M2340_SAVED_SCHEMA_INSPECTION_COMPLETE noMATLAB=1 physicalRun=0 privateReadback=PASS")
 need(result.get("schemaVerified") is True and "failure" not in result,"M2340_SCHEMA_NOT_VERIFIED")
if __name__=="__main__":
 try:t,f=ctx.parent.context();main(t,f)
 except Exception:print("BTMS_M2340_SCHEMA_UNQUALIFIED details=OWNER_PRIVATE_ONLY");sys.exit(1)
