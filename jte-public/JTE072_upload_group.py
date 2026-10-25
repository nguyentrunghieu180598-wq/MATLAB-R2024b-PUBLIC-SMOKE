"""JTE072 correlated triple-sensor bias, owner private Drive only."""
import os,json
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO,access_token,ensure_app_folder
from JTE063_streaming_drive import upload_verified
GROUPS=("early","mid","late")
TRIGGER="JTE072_AUTHORIZE_THREE_PREDECLARED_COSENSOR_GROUPS"
def guard(event,e,site):
    repo=event.get("repository") or {};head=event.get("head_commit") or {}
    if (site not in GROUPS or repo.get("private") is not False
        or repo.get("full_name")!=EXPECTED_REPO
        or e.get("GITHUB_REPOSITORY")!=EXPECTED_REPO
        or e.get("GITHUB_REF")!="refs/heads/main" or e.get("GITHUB_EVENT_NAME")!="push"
        or head.get("message")!=TRIGGER):
        raise PermissionError("JTE072_UNAUTHORIZED_GROUP")
def main():
    e=os.environ;site=e.get("JTE_GROUP","");eventfile=e.get("GITHUB_EVENT_PATH")
    if not eventfile or not Path(eventfile).is_file():raise PermissionError("JTE072_MISSING_EVENT")
    guard(json.loads(Path(eventfile).read_text()),e,site)
    mat=Path("jte072-private")/f"JTE072_GROUP_C1_{site}_ref293p15_2400_NATIVE.mat"
    if not mat.is_file() or mat.is_symlink() or mat.stat().st_size<1000:raise RuntimeError("JTE072_MAT_MISSING")
    keys=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(e.get(k) for k in keys):raise RuntimeError("JTE072_MISSING_OAUTH")
    token=access_token(*[e[k] for k in keys])
    folder=ensure_app_folder(token)
    data=upload_verified(token,folder,mat,schema="JTE072_GROUP3_RAW_UNREVIEWED")
    print("JTE072_GROUP_PRIVATE_DRIVE_READBACK_PASS group="+site+
        " bytes="+str(data["size_bytes"])+" sha256="+data["sha256"]+
        " accepted=false three_biasK=-2 referenceK=293.15")
if __name__=="__main__":main()
