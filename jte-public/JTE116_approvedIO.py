"""Owner-approved ONE guard025 trajectory. Private transport and runtime intent."""
import base64,hashlib,json,os,re,shutil,subprocess,sys,time
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte116-one-private")
SCHEMA="JTE116_OWNER_APPROVED_ONE_GUARD025_NOT_G5"
INTENT="JTE116_GUARD025_B0L340_OWNER_APPROVED_ONE_INTENT.json"
def need(v,c):
    if not v:raise RuntimeError(c)
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    need(os.environ.get("GITHUB_REPOSITORY")==EXPECTED_REPO and
      (e.get("repository") or {}).get("full_name")==EXPECTED_REPO and
      (e.get("repository") or {}).get("private") is False and
      os.environ.get("GITHUB_REF")=="refs/heads/codex/jte-tf-constant-input" and
      os.environ.get("GITHUB_EVENT_NAME")=="push" and os.environ.get("GITHUB_RUN_ATTEMPT")=="1" and
      (e.get("head_commit") or {}).get("message")=="JTE116_OWNER_APPROVED_ONE_GUARD025_340" and
      (e.get("head_commit") or {}).get("id")==os.environ.get("GITHUB_SHA") and
      os.environ.get("RUNNER_ENVIRONMENT")=="github-hosted","JTE116ONE_CONTEXT_DENIED")
    t=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return t,ensure_app_folder(t)
def get(t,f,name,local):
    return download(t,one(t,f,"JTE063_VERIFIED_"+name),ROOT/local)
def fetch(t,f):
    ROOT.mkdir(mode=0o700,exist_ok=False);run=os.environ["GITHUB_RUN_ID"]
    need(not query(t,f,"name = 'JTE063_VERIFIED_"+INTENT+"'"),"JTE116ONE_PRIOR_PLANT_INTENT_NO_REPEAT")
    probe=ROOT/("JTE116ONE_"+run+"_SINK_PROBE.json")
    probe.write_text(json.dumps({"schema":SCHEMA,"run":run,"phase":"PRIVATE_SINK_BEFORE_TOY","physicalSimulation":False}))
    upload_verified(t,f,probe,schema=SCHEMA)
    pairs=[
      ("JTE116_40635052627_PRIVATE_RECEIPT.json","static_receipt.json"),
      ("JTE116_40635052627_FLAGS.json","static_flags.json"),
      ("JTE116_40635052627_STATIC_PROOF.json","static_proof.json"),
      ("JTE116_40635052627_PREPARED.mat","prepared.mat"),
      ("JTE116_40635052627_GUARDED_MODEL.slx","JTE116Guarded.slx"),
      ("JTE111_40620218579_PRIVATE_FINDINGS.json","j111_findings.json"),
      ("JTE111_40620218579_PRIVATE_READBACK_RECEIPT.json","j111_receipt.json"),
      ("JTE101_40449421507_ORIGINAL340_RAW.mat","original_raw.mat"),
      ("JTE101_40449421507_ORIGINAL340_MODEL.slx","JTE101Original.slx"),
      ("JTE101_40449421507_PREPARE_WORKSPACE.mat","source_workspace.mat")]
    got={local:get(t,f,name,local) for name,local in pairs}
    rc=json.loads((ROOT/"static_receipt.json").read_text())
    need(rc["run"]=="40635052627" and rc["commit"]=="26069fa77e5f2089ab0d103538eb271901521361","JTE116ONE_STATIC_RECEIPT_CONTEXT")
    for local in ("static_flags.json","static_proof.json","prepared.mat","JTE116Guarded.slx"):
        a=got[local];rows=[x for x in rc["files"] if x["name"]==a["name"].removeprefix("JTE063_VERIFIED_")]
        need(len(rows)==1 and rows[0]["sha256"]==a["sha256"] and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","JTE116ONE_STATIC_SHA_LINK")
    rc=json.loads((ROOT/"j111_receipt.json").read_text());a=got["j111_findings.json"]
    rows=[x for x in rc["files"] if x["name"]==a["name"].removeprefix("JTE063_VERIFIED_")]
    need(len(rows)==1 and rows[0]["sha256"]==a["sha256"],"JTE116ONE_REFERENCE_RECEIPT_LINK")
    old=json.loads((ROOT/"j111_findings.json").read_text())
    for local in ("original_raw.mat","JTE101Original.slx","source_workspace.mat"):
        a=got[local];rows=[x for x in old["inputs"] if x["name"]==a["name"]]
        if rows:need(len(rows)==1 and rows[0]["sha256"]==a["sha256"],"JTE116ONE_OLD_SOURCE_HASH_LINK")
    mem={}
    for line in Path("/proc/meminfo").read_text().splitlines():
        k,v=line.split(":",1)
        if k in ("MemTotal","MemAvailable"):mem[k+"_bytes"]=int(v.split()[0])*1024
    disk=shutil.disk_usage(".");q=quota(t)
    need(mem["MemAvailable_bytes"]>4*1024**3 and disk.free>5*1024**3 and q["availableBytes"]>1024**3,
      "JTE116ONE_FREE_RESOURCE_UNQUALIFIED")
    approval="Owner directly approved exactly ONE JTE116 guarded025 B0L 0-340s original ode23t trajectory in current Work chat; reuse saved JTE101, no retry/solver change/payment. Follow PR61 comment6461303109 completed-major logging."
    m={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"files":list(got.values()),
      "ownerAuthorization":{"exactlyOne":True,"source":"Direct human message in the active Work conversation","scope":approval,
        "scopeSHA256":hashlib.sha256(approval.encode()).hexdigest(),"scientificComment":"6461303109"},
      "resource":{"RAM":mem,"CPU":os.cpu_count(),"diskFree_bytes":disk.free,"drive":q,"paidServices":False,
        "repositoryPublicVerifiedFromGithubEvent":True,"runner":"ubuntu-latest_standard_github_hosted",
        "preflightUnixEpoch":time.time(),"jobLimit_s":2400,"oneTrajectoryWallLimit_s":1200,
        "policySources":["https://docs.github.com/en/actions/concepts/billing-and-usage","https://github.com/matlab-actions/setup-matlab"]}}
    (ROOT/"manifest.json").write_text(json.dumps(m,indent=2))
    (ROOT/("JTE116ONE_"+run+"_INPUT_MANIFEST.json")).write_text(json.dumps(m,indent=2))
    print("JTE116ONE_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+run+" ownerAuthorization=ONE privateInputSHA=PASS originalRerun=0")
def publish(t,f,phase):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE116ONE_"+run+"_"+phase
    flag=ROOT/(prefix+"_FLAGS.json")
    if not flag.exists():
        flag.write_text(json.dumps({"DECISION":"UNQUALIFIED_LOGGING_OR_RESOURCE","LOGGER_QUALIFIED":False,
          "PHYSICAL_ATTEMPT_ENTERED":"UNAVAILABLE","G5_ACCEPTED":False,
          "stepOutcome":os.environ.get("JTE116ONE_STEP_OUTCOME")}))
    paths=sorted(ROOT.glob(prefix+"_*"))
    if phase=="TOY":paths.append(ROOT/("JTE116ONE_"+run+"_INPUT_MANIFEST.json"))
    rc={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"phase":phase,"files":[],"G5_ACCEPTED":False}
    for p in paths:
        need(not query(t,f,"name = 'JTE063_VERIFIED_"+p.name+"'"),"JTE116ONE_DUPLICATE_OUTPUT_DENIED")
        rc["files"].append({"name":p.name,**upload_verified(t,f,p,schema=SCHEMA)})
    p=ROOT/(prefix+"_RECEIPT.json");p.write_text(json.dumps(rc,indent=2));upload_verified(t,f,p,schema=SCHEMA)
    print("JTE116ONE_PRIVATE_FULL_SHA_READBACK_PASS phase="+phase+" G5_ACCEPTED=false rawPublic=0")
def signed_intent(payload):
    need(shutil.which("openssl") is not None,"JTE116ONE_RUNTIME_SIGNER_UNAVAILABLE")
    key=ROOT/"ephemeral_intent_private.pem";pub=ROOT/"ephemeral_intent_public.pem"
    data=ROOT/"ephemeral_intent_payload.json";sig=ROOT/"ephemeral_intent_signature.bin"
    def cmd(args):
        r=subprocess.run(["openssl",*args],capture_output=True)
        need(r.returncode==0,"JTE116ONE_RUNTIME_INTENT_SIGNATURE_FAILED")
    try:
        cmd(["genpkey","-algorithm","ED25519","-out",str(key)]);os.chmod(key,0o600)
        cmd(["pkey","-in",str(key),"-pubout","-out",str(pub)])
        canonical=json.dumps(payload,sort_keys=True,separators=(",",":")).encode();data.write_bytes(canonical)
        cmd(["pkeyutl","-sign","-rawin","-inkey",str(key),"-in",str(data),"-out",str(sig)])
        cmd(["pkeyutl","-verify","-rawin","-pubin","-inkey",str(pub),"-in",str(data),"-sigfile",str(sig)])
        return {"payload":payload,"payloadSHA256":hashlib.sha256(canonical).hexdigest(),"algorithm":"Ed25519",
          "signatureBase64":base64.b64encode(sig.read_bytes()).decode(),"publicKeyPEM":pub.read_text(),
          "signerScope":"Ephemeral runtime integrity signature, NOT an owner PKI signature. Authorization comes from the direct human Work message.",
          "privateKeyRetainedAfterSigning":False}
    finally:
        for p in (key,pub,data,sig):p.unlink(missing_ok=True)
def gate(t,f):
    run=os.environ["GITHUB_RUN_ID"];prefix="JTE116ONE_"+run+"_TOY"
    flag=json.loads((ROOT/(prefix+"_FLAGS.json")).read_text())
    rcmeta=get(t,f,prefix+"_RECEIPT.json","toy_receipt_readback.json")
    rc=json.loads((ROOT/"toy_receipt_readback.json").read_text())
    need(rc["run"]==run and rc["commit"]==os.environ["GITHUB_SHA"],"JTE116ONE_TOY_RUN_CONTEXT")
    allowed=flag.get("LOGGER_QUALIFIED") is True
    if allowed:
        for suffix in ("_FLAGS.json","_RAW.mat","_SUMMARY.json"):
            p=ROOT/(prefix+suffix);rows=[x for x in rc["files"] if x["name"]==p.name]
            need(len(rows)==1 and rows[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED" and
              hashlib.sha256(p.read_bytes()).hexdigest()==rows[0]["sha256"],"JTE116ONE_TOY_SHA_NOT_DELIVERED")
        need(not query(t,f,"name = 'JTE063_VERIFIED_"+INTENT+"'"),"JTE116ONE_PLANT_ALREADY_RESERVED_NO_REPEAT")
        m=json.loads((ROOT/"manifest.json").read_text())
        payload={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"ownerAuthorization":m["ownerAuthorization"],
          "phase":"ONE_APPROVED_INITIALIZATION_TRAJECTORY_NO_RETRY","guard":"025","case":"B0L","start":0,"stop":340,
          "solver":"original_ode23t","comparator":"archived_JTE101_40449421507","toyReceipt":rcmeta,
          "inputHashes":{x["local"]:x["sha256"] for x in m["files"]},"repeatAuthorized":False,"G5_ACCEPTED":False}
        p=ROOT/INTENT;p.write_text(json.dumps(signed_intent(payload),indent=2));upload_verified(t,f,p,schema=SCHEMA)
    with open(os.environ["GITHUB_OUTPUT"],"a") as out:out.write("may_run="+str(allowed).lower()+"\n")
    print("JTE116ONE_GATE "+("ONE_SIGNED_INTENT_RESERVED" if allowed else "UNQUALIFIED_LOGGING_OR_RESOURCE")+" retryAuthorized=0 G5_ACCEPTED=false")
if __name__=="__main__":
    try:
        t,f=context();mode=sys.argv[1]
        if mode=="fetch":fetch(t,f)
        elif mode=="publish-toy":publish(t,f,"TOY")
        elif mode=="gate":gate(t,f)
        elif mode=="publish-plant":publish(t,f,"PLANT")
        else:raise RuntimeError("JTE116ONE_MODE_DENIED")
    except Exception as e:
        code=str(e)
        if not re.fullmatch("[A-Z0-9_]+",code):code="JTE116ONE_PRIVATE_IO_UNQUALIFIED"
        print("JTE116ONE_UNQUALIFIED_LOGGING_OR_RESOURCE code="+code+" G5_ACCEPTED=false");sys.exit(1)
