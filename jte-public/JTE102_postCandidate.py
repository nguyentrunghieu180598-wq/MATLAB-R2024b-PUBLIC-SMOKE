"""Postprocess existing failed-equivalent-realization test. NO MATLAB/simulation."""
import csv,json,os,sys,re
from pathlib import Path
import h5py,numpy as np
from JTE102_metrics import PIN,WINDOWS,read,num,vec,sha,clock,step_stats,repeated,load_case,comparison,event,clean,require
def main():
    root=Path("jte102-private");m=json.loads((root/"post_manifest.json").read_text())
    for item in m["files"]:require(sha(root/item["local"])==item["sha256"],"JTE102_POST_LOCAL_SHA")
    source=load_case(root/"ORIGINAL340.mat","ORIGINAL340",m)
    with h5py.File(root/"STATESPACE340.mat","r") as f:
        r="record/"
        require(read(f,r+"schema")=="JTE102_EQUIVALENT_REALIZATION_RAW_NOT_G5","JTE102_POST_SCHEMA")
        require(read(f,r+"run")=="40464385622" and read(f,r+"commit")=="2879f30d65c81ea0cc2b7b68deb677b2869cda6d","JTE102_POST_ORIGIN")
        require(read(f,r+"sourceSHA256")==PIN and sha(root/"STATESPACE340.slx")==read(f,r+"modelSHA256"),"JTE102_POST_MODEL")
        require(bool(read(f,r+"comparison/qualified")) and read(f,r+"comparison/candidate")=="EQUIVALENT_REALIZATION_DID_NOT_FIX","JTE102_POST_CANDIDATE")
        d={"t":vec(f,r+"observed/time"),"T":num(f,r+"observed/T"),"u":vec(f,r+"observed/core"),"y":vec(f,r+"observed/output"),
          "x":vec(f,r+"observed/state"),"actualInput":vec(f,r+"observed/input"),"q":vec(f,r+"observed/q")}
        clock(d["t"],340)
        for p in ("outputTime","trueTime","inputTime","qTime","stateTime"):
            require(np.array_equal(d["t"],vec(f,r+"observed/"+p)),"JTE102_POST_CLOCK")
        require(d["T"].shape==(len(d["t"]),312),"JTE102_POST_T312")
        require(np.array_equal(d["actualInput"],d["u"]) and np.all(d["u"]==.25),"JTE102_POST_INPUT")
        require(bool(read(f,r+"comparison/sourceLawNativeExact")),"JTE102_POST_ARCHIVED_MATLAB_LAW")
        numpyLawDiagnostic=bool(np.array_equal(d["u"],np.maximum(.25,d["q"]-np.mod(d["q"],.25))))
        initial=float(read(f,r+"prepared/X0"))
        require(initial==source["y"][0] and d["y"][0]==initial and d["x"][0]==initial and np.array_equal(d["T"][0],source["T"][0]),"JTE102_POST_INITIAL")
        nativeInfo={"nativeTimeStep":step_stats(d["t"]),"inputMinusCoreMaxAbs":float(np.abs(d["actualInput"]-d["u"]).max()),
          "sourceLawNativeExactArchivedMATLAB":True,"numpyModDiagnosticOnly":numpyLawDiagnostic,"crossRuntimeLawCaution":"NumPy mod is not the MATLAB/Simulink near-ULP oracle; actual MATLAB source-law test is authoritative.","initialX0DerivedFromSourceOutput":initial,"stateOutputMaxAbsResidual":float(np.abs(d["y"]-d["x"]).max()),
          "repeatState":repeated(d["t"],d["x"]),"repeatPostfilter":repeated(d["t"],d["y"]),"repeatTemperature":repeated(d["t"],d["T"]),
          "thermalEndpoint_K":d["T"][-1],"thermalPerChannelNativeMax_K":d["T"].max(axis=0),"thermalPerChannelNativeMin_K":d["T"].min(axis=0)}
    cp={field:comparison(source,d,field) for field in ("T","u","y")}
    cp["T_first"]=comparison(source,d,window=WINDOWS["FIRST"])
    cp["y_first"]=comparison(source,d,"y",WINDOWS["FIRST"])
    ix=np.searchsorted(d["t"],source["t"]);right=np.minimum(ix,len(d["t"])-1);left=np.maximum(ix-1,0)
    j=np.where(np.abs(d["t"][right]-source["t"])<np.abs(d["t"][left]-source["t"]),right,left)
    dt=d["t"][j]-source["t"];dv=d["T"][j]-source["T"]
    nearest={"perChannelMaxAbsContrast_K":np.max(np.abs(dv),axis=0),"maxTimeSeparation_s":float(np.max(np.abs(dt))),
      "sampleRMSE_K":float(np.sqrt(np.mean(dv**2))),"semantics":"Actual nearest native temperature samples only. Temporal mismatch included; not interpolation, error bound, causal thermal effect or convergence."}
    se=event(source["t"],source["y"],source["u"],source["T"],WINDOWS["FIRST"],source["x"],source["C"])
    ce=event(d["t"],d["y"],d["u"],d["T"],WINDOWS["FIRST"],d["x"],1.)
    require(ce["excursion"],"JTE102_POST_EXCURSION_NOT_REPRODUCED_IN_RAW")
    flags={"G5_PROVENANCE":"PASS_EXISTING_NATIVE_ASSETS","G5_THERMAL_NUMERICS":"OBSERVABLES_AUDITED_CONVERGENCE_UNPROVEN",
      "G5_ACTUATION_EVENT":"ACTUATION_EVENT_UNRESOLVED","REALIZATION_REMEDY":"FAIL_EXCURSION_SURVIVES",
      "candidateCanaryAndInitialProof":"PASS_ACTUAL_MATLAB","FIRST_STATE_SPACE_EXCURSION":"YES","SECOND_EVENT_STATE":"UNAVAILABLE_2400",
      "SECOND_EVENT_CANDIDATE":"NOT_COVERED","acceptedStepCertification":"UNAVAILABLE","physicalSimulationRun":False,"G5_ACCEPTED":False,
      "next":"Stop speculative filter/solver changes; authorized R2024b interactive Solver Profiler actor evidence or a principled alternate numerical reference is required."}
    report={"schema":"JTE102_PRIVATE_POST_CANDIDATE_V1","run":os.environ["GITHUB_RUN_ID"],"commit":os.environ["GITHUB_SHA"],
      "inputManifest":m,"sourceRun":"40449421507","actualCandidateRun":"40464385622","actualCandidateCommit":"2879f30d65c81ea0cc2b7b68deb677b2869cda6d",
      "flags":flags,"stateSpaceNativeInfo":nativeInfo,"firstEventSource":se,"firstEventStateSpace":ce,"nativeComparisons":cp,
      "nearestNativeTemperatureDiagnostic":nearest,"endpointPerChannelDifference_K":d["T"][-1]-source["T"][-1],
      "sourceStateCoordinateGain":source["C"],"stateComparisonSemantics":"Source canonical state scaled by archived calibrated Ctf; StateSpace state equals output. Jumps in saved states do not identify accepted-step/reset actor.",
      "causalityLimit":"Native core/input remain .25. Minor-stage input and reset actor remain unobserved. No physical causal claim or full-horizon convergence."}
    pre=root/("JTE102_"+os.environ["GITHUB_RUN_ID"]+"_POST")
    pre.with_name(pre.name+"_METRICS.json").write_text(json.dumps(clean(report),indent=2,allow_nan=False))
    pre.with_name(pre.name+"_FLAGS.json").write_text(json.dumps(flags,indent=2))
    with pre.with_name(pre.name+"_CHANNELS.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["channel_1based","source_endpoint_K","stateSpace_endpoint_K","signed_endpoint_difference_K","source_native_max_K","stateSpace_native_max_K","exact_common_native_max_abs_K","nearest_native_max_abs_contrast_K_includes_time_separation"])
        for k in range(312):w.writerow([k+1,source["T"][-1,k],d["T"][-1,k],d["T"][-1,k]-source["T"][-1,k],source["T"][:,k].max(),d["T"][:,k].max(),cp["T"]["perChannelMaxAbs"][k] if cp["T"]["perChannelMaxAbs"] is not None else "",nearest["perChannelMaxAbsContrast_K"][k]])
    print("JTE102_POST_RESULT REALIZATION_REMEDY=FAIL_EXCURSION_SURVIVES G5_PROVENANCE=PASS_EXISTING_NATIVE_ASSETS G5_THERMAL_NUMERICS=OBSERVABLES_AUDITED_CONVERGENCE_UNPROVEN G5_ACTUATION_EVENT=ACTUATION_EVENT_UNRESOLVED simulationRun=0 rawValuesPublished=0")
if __name__=="__main__":
    try:main()
    except Exception as e:
        c=str(e)
        if not re.fullmatch("[A-Z0-9_]+",c):c="JTE102_POST_ANALYSIS_FAILED"
        print("JTE102_POST_BLOCKED code="+c+" exceptionClass="+type(e).__name__);sys.exit(1)
