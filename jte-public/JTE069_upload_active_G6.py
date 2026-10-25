"""JTE069 private research upload, active reference 293.15K, −2 K single sensor."""
import os,json
from pathlib import Path
from JTE062_google_drive_synthetic import EXPECTED_REPO, access_token, ensure_app_folder
from JTE063_streaming_drive import upload_verified
POSITIONS=("hot","middle","cold")
TRIGGER="JTE069_AUTHORIZE_ACTIVE_REFERENCE_THREE_MINUS2K_CASES"
def guard(event,e,site):
    r=event.get("repository") or {}; c=event.get("head_commit") or {}
    if (site not in POSITIONS or r.get("full_name")!=EXPECTED_REPO
        or r.get("private") is not False or e.get("GITHUB_REPOSITORY")!=EXPECTED_REPO
        or e.get("GITHUB_REF")!="refs/heads/main" or
        e.get("GITHUB_EVENT_NAME")!="push" or c.get("message")!=TRIGGER):
        raise PermissionError("JTE069_NOT_AUTHORIZED")
def main():
    e=os.environ;site=e.get("JTE_POSITION","")
    ev=e.get("GITHUB_EVENT_PATH")
    if not ev or not Path(ev).is_file():raise PermissionError("JTE069_NO_EVENT")
    guard(json.loads(Path(ev).read_text()),e,site)
    p=Path("jte069-private")/f"JTE069_ACTIVE_C1_{site}_ref293p15_2400_NATIVE.mat"
    if not p.is_file() or p.is_symlink() or p.stat().st_size<1000:raise ValueError("JTE069_NO_NATIVE_MAT")
    names=("JTE_GOOGLE_CLIENT_ID","JTE_GOOGLE_CLIENT_SECRET","JTE_GOOGLE_REFRESH_TOKEN")
    if not all(e.get(n) for n in names):raise RuntimeError("JTE069_MISSING_SECRET")
    token=access_token(*[e[n] for n in names])
    folder=ensure_app_folder(token)
    res=upload_verified(token,folder,p,schema="JTE069_ACTIVE_G6_RAW_UNREVIEWED")
    print("JTE069_ACTIVE_G6_PRIVATE_DRIVE_READBACK_PASS site="+site+
        " bytes="+str(res["size_bytes"])+" sha256="+res["sha256"]+
        " accepted=false referenceK=293.15 single_sensor_biasK=-2")
if __name__=="__main__":main()
