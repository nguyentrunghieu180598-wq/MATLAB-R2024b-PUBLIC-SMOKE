"""JTE103 protected cloud transport. Reuse accepted access; no ACL/preflight."""
import json,os,re,sys
from pathlib import Path
from JTE101_io import one,query,download,quota
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
ROOT=Path("jte103-private");SCHEMA="JTE103_PROFILER_PATH_NOT_G5"
MESSAGES={"JTE103_PROFILER_CAPABILITY_AND_READONLY_G6_AUDIT","JTE103_ONE_SOURCE_PROFILER340"}
def context():
    e=json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    if (os.environ.get("GITHUB_REPOSITORY")!=EXPECTED_REPO or (e.get("repository") or {}).get("full_name")!=EXPECTED_REPO or
        os.environ.get("GITHUB_REF")!="refs/heads/codex/jte-tf-constant-input" or os.environ.get("GITHUB_EVENT_NAME")!="push" or
        (e.get("head_commit") or {}).get("message") not in MESSAGES or
        (e.get("head_commit") or {}).get("id")!=os.environ.get("GITHUB_SHA") or os.environ.get("GITHUB_RUN_ATTEMPT")!="1"):
        raise RuntimeError("JTE103_CONTEXT_DENIED")
    token=access_token(*[os.environ[k] for k in ("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")])
    return token,ensure_app_folder(token)
def put_json(p,x):p.write_text(json.dumps(x,indent=2))
def fetch_cap(t,folder,reuse_g6=False):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    m={"schema":SCHEMA,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"missing":[],"priorProfiles":[],"unqualifiedProfileCandidates":[],"quota":quota(t)}
    def add(name,local,kind,ref=None,mandatory=False):
        rows=query(t,folder,"name = 'JTE063_VERIFIED_"+name+"'")
        spec={"name":name,"local":local,"kind":kind,"controllerReferenceK":ref}
        if len(rows)!=1:
            if mandatory:raise RuntimeError("JTE103_REQUIRED_REFERENCE_NOT_UNIQUE")
            m["missing"].append({**spec,"status":"ABSENT" if not rows else "AMBIGUOUS"});return
        item=download(t,rows[0],ROOT/local);item.update({"kind":kind,"controllerReferenceK":ref});m["files"].append(item)
    if reuse_g6:
        meta=one(t,folder,"JTE063_VERIFIED_JTE103_40473995420_CAPABILITY_G6_LEDGER.json")
        v=download(t,meta,ROOT/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_CAPABILITY_G6_INHERITED_LEDGER.json"))
        g=json.loads((ROOT/v["local"]).read_text())
        if g.get("status")!="PASS_READONLY_LEDGER_COMPLETE" or g.get("run")!="40473995420":raise RuntimeError("JTE103_G6_REUSE_NOT_QUALIFIED")
        m["reusedG6AuditRun"]="40473995420";m["reusedG6Audit"]=v
    else:
        add("JTE065_C0_original_2400_NATIVE.mat","C0_300_original.mat","C0",300,True)
        add("JTE065_C0_fine_2400_NATIVE.mat","C0_300_fine.mat","C0",300)
        add("JTE068_ACTIVE_C0_AMBIENT293p15_2400_NATIVE.mat","C0_293p15_original.mat","C0",293.15)
        for site in ("hot","middle","cold"):
            add("JTE067_C1_"+site+"_original_2400_NATIVE.mat","JTE067_"+site+".mat","C1_SINGLE",300)
            add("JTE069_ACTIVE_C1_"+site+"_ref293p15_2400_NATIVE.mat","JTE069_"+site+".mat","C1_SINGLE",293.15)
        for site in ("early","mid","late"):
            add("JTE072_GROUP_C1_"+site+"_ref293p15_2400_NATIVE.mat","JTE072_"+site+".mat","C1_GROUP",293.15)
    candidates=query(t,folder,"name contains 'JTE085' or name contains 'PROFILER' or name contains 'PROFILE_SESSION' or name contains 'solverprofiler'")
    candidates=[x for x in candidates if x["name"].lower().endswith(".mat")]
    for i,meta in enumerate(candidates):
        p=meta.get("appProperties",{})
        if p.get("state")=="VERIFIED" and re.fullmatch("[a-f0-9]{64}",p.get("sha256","")):
            if len(m["priorProfiles"])>=3:raise RuntimeError("JTE103_PRIOR_PROFILE_AMBIGUOUS_REQUIRES_METADATA_REVIEW")
            item=download(t,meta,ROOT/("prior_profile_"+str(i)+".mat"));m["priorProfiles"].append(item)
        else:m["unqualifiedProfileCandidates"].append({"name":meta["name"],"status":"NO_VERIFIED_SHA_DO_NOT_LOAD"})
    put_json(ROOT/"cap_manifest.json",m)
    ack={"schema":"JTE103_WORK_CLOUD_RECEIPT","ack":"JTE103_RECEIVED","executor":"GITHUB_HOSTED_ACTIONS",
      "taskIdKind":"GITHUB_ACTIONS_WORKFLOW_RUN_NOT_CODEX_REMOTE_TASK","run":os.environ["GITHUB_RUN_ID"],"jobName":os.environ["GITHUB_JOB"],
      "runnerOS":os.environ.get("RUNNER_OS"),"runnerName":os.environ.get("RUNNER_NAME"),"commit":os.environ["GITHUB_SHA"],
      "remoteCodexTaskId":"NOT_ASSIGNED_NOT_INVENTED","LAST_ACCEPTED_RUN":"40465657897","personalPCSimulation":False,
      "coordination":"No JTE103 in recent remote-task metadata or active repository runs observed before dispatch; no new remote chat/task created."}
    put_json(ROOT/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_CAPABILITY_WORK_CLOUD_RECEIPT.json"),ack)
    print("JTE103_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+" LAST_ACCEPTED_RUN=40465657897 oldSimulationsRerun=0")
def publish(t,folder,phase):
    files=sorted(ROOT.glob("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_"+phase+"*"))
    if not files:raise RuntimeError("JTE103_OUTPUT_ABSENT")
    r={"schema":SCHEMA,"phase":phase,"run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],"files":[],"G5_ACCEPTED":False}
    for p in files:r["files"].append({"name":p.name,**upload_verified(t,folder,p,schema=SCHEMA)})
    p=ROOT/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_"+phase+"_RECEIPT.json");put_json(p,r);upload_verified(t,folder,p,schema=SCHEMA)
    print("JTE103_PRIVATE_READBACK_PASS phase="+phase+" rawValuesPublished=0 G5_ACCEPTED=false")
def readback_canary(t,folder):
    flags=json.loads((ROOT/("JTE103_"+os.environ["GITHUB_RUN_ID"]+"_CAPABILITY_FLAGS.json")).read_text())
    local=flags.get("retentionFile","")
    if not local:
        print("JTE103_SESSION_READBACK_UNAVAILABLE captureAbsent=1 noSourceProfileAuthorized=1");return
    item=one(t,folder,"JTE063_VERIFIED_"+local)
    d=download(t,item,ROOT/"downloaded_profile_session.mat");put_json(ROOT/"readback_manifest.json",d)
    print("JTE103_PROFILE_SESSION_CLOUD_DOWNLOAD_SHA_PASS sessionFieldsNotDecoded=1")
def main():
    t,f=context();mode=sys.argv[1]
    if mode=="fetch-cap":fetch_cap(t,f)
    elif mode=="fetch-cap-api":fetch_cap(t,f,True)
    elif mode=="publish-cap":publish(t,f,"CAPABILITY")
    elif mode=="readback-canary":readback_canary(t,f)
    elif mode=="publish-readback":publish(t,f,"READBACK")
    else:raise RuntimeError("JTE103_MODE_DENIED")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE103_PRIVATE_IO_FAILED"
        print("JTE103_BLOCKED code="+c);sys.exit(1)
