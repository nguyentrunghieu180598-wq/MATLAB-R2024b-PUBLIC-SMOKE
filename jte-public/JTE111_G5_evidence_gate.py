"""JTE111 metadata-only G5 evidence gate. No MATLAB or study MAT.

This verifies presence, structure and source SHA of owner-provided evidence references.
Only an independent scientific review can decide G5; PASS flags alone cannot.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path

SOURCE_SHA="0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0"
GATES=(
"SOURCE_MODEL_LOCK","RUNTIME_LOCK","RAW_T312_CLOCK","ZERO_BIAS_IDENTITY",
"PAIR_INPUT_PARITY","ORIGINAL_WINDOW_1","ORIGINAL_WINDOW_2",
"ACCEPTED_EVENT_SEMANTICS","INDEPENDENT_NUMERICS_W1","INDEPENDENT_NUMERICS_W2",
"POSTFILTER_RELIABILITY","THERMAL_CONVERGENCE",
)
SHA=re.compile(r"^[a-f0-9]{64}$")
def blank():
    return {"schema":"JTE111_G5_EVIDENCE_V1","source_sha256":SOURCE_SHA,
            "gates":{k:{"status":"UNAVAILABLE","reason":"No qualified private evidence linked yet"} for k in GATES}}
def assess(record):
    if not isinstance(record,dict) or record.get("schema")!="JTE111_G5_EVIDENCE_V1":
        raise ValueError("wrong schema")
    if record.get("source_sha256")!=SOURCE_SHA:raise ValueError("wrong pinned model")
    g=record.get("gates")
    if not isinstance(g,dict) or set(g)!=set(GATES):raise ValueError("missing or extra gate")
    statuses={}
    for k in GATES:
        x=g[k]
        if not isinstance(x,dict) or x.get("status") not in ("PASS","FAIL","UNAVAILABLE"):
            raise ValueError("invalid status:"+k)
        if not isinstance(x.get("reason"),str) or not x["reason"].strip():
            raise ValueError("missing reason:"+k)
        if x["status"]=="PASS" and (
            not isinstance(x.get("evidence_reference"),str) or not x["evidence_reference"].strip() or
            not isinstance(x.get("evidence_sha256"),str) or not SHA.fullmatch(x["evidence_sha256"])):
            raise ValueError("PASS needs private evidence reference and SHA256:"+k)
        statuses[k]=x["status"]
    n={s:sum(v==s for v in statuses.values()) for s in ("PASS","FAIL","UNAVAILABLE")}
    return {"structural_result":"READY_FOR_INDEPENDENT_REVIEW" if n["PASS"]==len(GATES) else "G5_INCOMPLETE_OR_FAILED",
            "G5_SCIENTIFICALLY_ACCEPTED":False,"counts":n,"status_by_gate":statuses,
            "note":"Structural assertions only; independent verification of evidence/physics still mandatory."}
def test():
    a=blank()
    assert assess(a)["counts"]["UNAVAILABLE"]==12
    n=1
    for k in GATES:
        c=blank();c["gates"][k]["status"]="PASS"
        try:assess(c)
        except ValueError:n+=1
        else:raise AssertionError(k)
    c=blank()
    for k in GATES:
        c["gates"][k]={"status":"PASS","reason":"synthetic only","evidence_reference":"FAKE",
                       "evidence_sha256":"a"*64}
    out=assess(c)
    assert out["structural_result"]=="READY_FOR_INDEPENDENT_REVIEW";n+=1
    assert not out["G5_SCIENTIFICALLY_ACCEPTED"];n+=1
    c["gates"]["THERMAL_CONVERGENCE"]["status"]="FAIL"
    assert assess(c)["counts"]["FAIL"]==1;n+=1
    c=blank();c["source_sha256"]="b"*64
    try:assess(c)
    except ValueError:n+=1
    else:raise AssertionError("wrong SHA")
    print(f"JTE111_GATE_SYNTHETIC_PASS tests={n} MATLAB=NOT_RUN STUDY_DATA=NOT_USED G5_ACCEPTED=FALSE")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--self-test",action="store_true")
    g.add_argument("--blank-template",type=Path)
    g.add_argument("--check",type=Path)
    a=p.parse_args()
    if a.self_test:test()
    if a.blank_template:a.blank_template.write_text(json.dumps(blank(),indent=2)+"\n")
    if a.check:print(json.dumps(assess(json.loads(a.check.read_text())),indent=2))
