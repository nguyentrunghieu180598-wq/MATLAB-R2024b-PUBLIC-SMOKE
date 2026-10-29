"""Interpret saved M1 static evidence only. No MATLAB, compile, simulation or model edits."""
import os,json,hashlib,sys
from pathlib import Path
from xml.etree import ElementTree as E
import m1_m2_static as base
from sampled_actuator_review_io import ROOT,get,need
from JTE063_streaming_drive import upload_verified
base.MSG="BTMS_M1_M2_STATIC_CERTIFICATE_SID_SCOPE_FIX"
SCHEMA=base.SCHEMA
SOURCE="BTMS_M1M2_40692041954_"
def main(t,folder):
    ROOT.mkdir(mode=0o700,exist_ok=False)
    run=os.environ["GITHUB_RUN_ID"];prefix="BTMS_M1_CERT_"+run+"_";inputs=[];outputs=[]
    def asset(name,local,receipt=None):
        m=get(t,folder,name,local);inputs.append(m)
        if receipt is not None:
            rr=[q for q in receipt["files"] if q["name"]==name]
            need(len(rr)==1 and rr[0]["sha256"]==m["sha256"] and rr[0]["integrity"]=="FULL_REMOTE_READBACK_VERIFIED","M1_CERT_RECEIPT")
        return json.load(open(ROOT/local))
    def emit(suffix,data):
        p=ROOT/(prefix+suffix)
        p.write_text(data if isinstance(data,str) else json.dumps(data,indent=2))
        outputs.append({"name":p.name,**upload_verified(t,folder,p,schema=SCHEMA)})
    rc=asset(SOURCE+"PRIVATE_RECEIPT.json","receipt.json")
    need(rc["run"]=="40692041954" and rc["commit"]=="f3b34e7fb73945bfc0c6d0d9115c29190e17c208" and
      not rc["modelCompile"] and not rc["simulationRun"],"M1_CERT_SOURCE_RECEIPT")
    graphs={k:asset(SOURCE+k+"_GRAPH.json",k+"_graph.json",rc) for k in
      ("PINNED_VENDOR","B0L_Ref","B0L_Fine","C0_Ref","C0_Fine")}
    component=asset(SOURCE+"SOURCE_COMPONENT_AND_WORKSPACE.json","component.json",rc)
    resource=asset(SOURCE+"RESOURCE_INPUTS.json","resource.json",rc)
    need(component["vendorCommit"]==base.VENDOR and component["sourceSLXSHA"]==base.PIN and
      graphs["PINNED_VENDOR"]["modelSHA"]==base.PIN,"M1_CERT_VENDOR_PIN")
    def nets(g):
        result=[]
        for row in g["staticSupplement"]["connectionLines"]:
            if row["tag"]!="Line":continue
            x=E.fromstring(row["xml"])
            if x.attrib.get("LineType")!="Connection":continue
            # Conserving lines are undirected hyperedges. Nested DEST_DEST Src ports
            # are peers in the same net, not directed signal sources to discard.
            ports=sorted(set(p.text for p in x.iter("P") if p.attrib.get("Name") in ("Src","Dst")))
            need(len(ports)>=2,"M1_CERT_INCOMPLETE_PHYSICAL_NET")
            result.append({"document":row["file"],"ports":ports,"rawXML":row["xml"]})
        return result
    def edges(g):return {(e["src"],e["dst"]) for e in g["edges"]}
    def require_edges(es,rows):
        missing=[q for q in rows if tuple(q) not in es]
        need(not missing,"M1_CERT_SIGNAL_PATH:"+json.dumps(missing))
    def block(g,sid):
        q=[b for b in g["blocks"] if b["SID"]==str(sid)]
        need(len(q)==1,"M1_CERT_SID");return q[0]
    original=graphs["PINNED_VENDOR"];originalNets=nets(original)
    netKeys=lambda nn:sorted((n["document"],tuple(n["ports"])) for n in nn)
    electricalExpected=[
      {"135#rconn:2","12#lconn:1","158#lconn:1","1#rconn:1","317#lconn:1"},
      {"135#lconn:1","317#rconn:1","158#rconn:1"},
      {"317#lconn:2","254#rconn:1"}]
    fixedSignals=[
      ("268#out:1","253#in:1"),("253#out:1","255#in:1"),("255#out:1","269#in:1"),
      ("267#out:1","274#in:2"),("274#out:1","289#in:1"),
      ("230#out:1","283#in:1"),("284#out:1","275#in:1"),
      ("275#out:4","286#in:1"),("283#out:1","321#in:1"),("322#out:1","254#in:1"),
      ("275#out:1","294#in:1"),("275#out:2","294#in:2"),("294#out:1","288#in:1"),
      ("283#out:3","158#in:1"),("296#out:1","295#in:1"),("295#out:2","298#in:1"),
      ("275#out:3","285#in:1"),("283#out:2","239#in:1"),
      ("320#out:1","172#in:1"),("240#out:1","6#in:4")]
    ledger=[]
    for key,g in graphs.items():
        es=edges(g);nn=nets(g)
        need(netKeys(nn)==netKeys(originalNets),"M1_CERT_PHYSICAL_GRAPH_PARITY")
        need(all(any(set(n["ports"])==exp for n in nn if n["document"].endswith("system_root.xml")) for exp in electricalExpected),"M1_CERT_PUMP_ELECTRICAL_NET")
        require_edges(es,fixedSignals)
        actName="sensor dynamics 1" if key=="PINNED_VENDOR" else "Amended sampled actuator"
        actRows=[b for b in g["blocks"] if b["parent"]=="$ROOT/Battery Control" and b["name"]==actName]
        need(len(actRows)==1,"M1_CERT_ACTUATOR_PATH");act=actRows[0]["SID"]
        require_edges(es,[(act+"#out:1","267#in:1"),(act+"#out:1","274#in:3")])
        if key=="PINNED_VENDOR":require_edges(es,[("270#out:1","197#in:1")])
        else:
            holdRows=[b for b in g["blocks"] if b["parent"]=="$ROOT/Battery Control" and b["name"]=="Amended command sample hold"]
            need(len(holdRows)==1,"M1_CERT_HOLD_PATH");hold=holdRows[0]["SID"]
            require_edges(es,[("270#out:1",hold+"#in:1"),(hold+"#out:1",act+"#in:1")])
        for sid in (253,255,317,135,254,172):
            a=block(g,sid);b=block(original,sid)
            need(a["instance"]==b["instance"] and
              {k:v for k,v in a["parameters"].items() if k!="Position"}==
              {k:v for k,v in b["parameters"].items() if k!="Position"},"M1_CERT_RETAINED_COMPONENT")
        need(block(g,253)["parameters"]["Gain"]=="500" and
          block(g,255)["parameters"]["LowerLimit"]=="0" and block(g,255)["parameters"]["UpperLimit"]=="500" and
          block(g,254)["instance"]["Unit"]=="J/s" and block(g,172)["instance"]["Unit"]=="A","M1_CERT_POWER_UNITS")
        need(block(g,275)["parameters"]["OutputSignals"]=="FlwT,FlwR,Current,Pump Power","M1_CERT_BUS_LAYOUT")
        need(block(g,321)["parameters"]["GotoTag"]==block(g,322)["parameters"]["GotoTag"]=="pump","M1_CERT_PUMP_TAG")
        need(all(block(g,s)["parameters"]["GotoTag"]=="DC" for s in (239,240,320)),"M1_CERT_CURRENT_TAG")
        routes=[]
        for j,mid in enumerate((9,325,326,327,328,329,330,331),1):
            module=block(g,mid);inst=module["instance"]
            need(inst["LUTpointsFlowrate_b"]=="Flowrate_vec" and inst["LUTpointsFlowrate_b_unit"]=="kg/s" and
              inst["thermal_moduleBottom"]=="batteryModule.batteryThermalPortSelection.thermalLUT" and
              inst["modelComplexity"]=="batteryModule.batteryAbstractionLevel.grouped","M1_CERT_MODULE_LUT")
            need(inst==block(original,mid)["instance"],"M1_CERT_MODULE_PARAMETER_PARITY")
            out=[b for b in g["blocks"] if b["parent"].endswith("/Flow distribution to\ndifferent modules") and b["type"]=="Outport" and int(b["parameters"].get("Port","1"))==j]
            need(len(out)==1,"M1_CERT_FLOW_OUTPORT")
            gainEdge=[e for e in g["edges"] if e["dst"]==out[0]["SID"]+"#in:1"]
            need(len(gainEdge)==1,"M1_CERT_FLOW_GAIN_EDGE");gb=block(g,gainEdge[0]["src"].split("#")[0])
            need(gb["type"]=="Gain" and ("299#out:1",gb["SID"]+"#in:1") in es,"M1_CERT_FLOW_GAIN")
            goedge=[e for e in g["edges"] if e["src"]=="298#out:"+str(j)]
            need(len(goedge)==1,"M1_CERT_FLOW_TAG_EDGE");go=block(g,goedge[0]["dst"].split("#")[0])
            fr=[b for b in g["blocks"] if b["parent"]==go["parent"] and b["type"]=="From" and b["parameters"].get("GotoTag")==go["parameters"]["GotoTag"]]
            need(len(fr)==1,"M1_CERT_FLOW_FROM")
            converter=[b for b in g["blocks"] if b["name"]=="FlwR"+str(j) and b["parent"]==go["parent"]]
            need(len(converter)==1,"M1_CERT_FLOW_CONVERTER");cv=converter[0]
            require_edges(es,[(fr[0]["SID"]+"#out:1",cv["SID"]+"#in:1")])
            need(cv["instance"]["Unit"]=="1" and any({cv["SID"]+"#rconn:1",str(mid)+"#rconn:2"}.issubset(n["ports"]) for n in nn),"M1_CERT_FLOW_PHYSICAL_PORT")
            routes.append({"module":j,"gainBlock":gb["path"],"savedGainOverride":gb["parameters"].get("Gain"),
              "gainInterpretation":gb["parameters"].get("Gain","1 (documented Gain block default; no saved override)"),
              "tag":go["parameters"]["GotoTag"],"converter":cv["path"],"converterUnit":"1",
              "moduleFracPort":str(mid)+"#rconn:2","LUTParameter":"Flowrate_vec","LUTUnit":"kg/s"})
        cp=None
        if key!="PINNED_VENDOR":
            cp=asset(SOURCE+key+"_REUSED_COMPILE.json",key+"_compile.json",rc)
            need(cp["proof"]["amendedModelSHA"]==g["modelSHA"] and cp["unitsMetadataParity"] and
              cp["modelWorkspaceICParametersExact"] and cp["proof"]["outsideExactEndpointsConnectivityParity"],"M1_CERT_COMPILED_LINK")
            need(cp["amendedCompile"]["actuator"]["types"]["Outport"]==["double"] and
              cp["amendedCompile"]["actuator"]["widths"]["Outport"]==1 and
              cp["amendedCompile"]["trueVectorWidth"]==312,"M1_CERT_COMPILED_TYPES")
        ledger.append({"model":key,"modelSHA":g["modelSHA"],"actuator":block(g,act),"flowRoutes":routes,
          "physicalNets":nn,"physicalGraphSameAsPinnedSource":True,"pumpAndCoolingShareActuatorOutput":True,
          "priorCompiledUnitMetadataExplicit":cp["unitsExplicit"] if cp else None,
          "compiledActuator":cp["amendedCompile"]["actuator"] if cp else None})
    ssc=component["SSC"]
    mm=ssc["batteryMultiDimModel.ssc"]["text"];cc=ssc["batteryCellThermalLUTmodel.ssc"]["text"]
    need("frac_b= {1, '1'}" in mm and "connect(frac_b,coldPlateBottom_grouped(i).frac);" in mm and
      "Fvec=flowrate0" in mm and "frac*max(Fvec)" in cc and "'kg/s'" in cc,"M1_CERT_SSC_LOOKUP")
    explanations={
      "flow":"Normalized post-actuator fraction is maldistributed per module; physical lookup coordinate is frac*max(Fvec) in kg/s. This is not evidence of a conserved hydraulic network or measured pump flow.",
      "power":"The same post-actuator output drives 500*FlwR saturated to [0,500] and a J/s Simulink-PS converter. Power dynamic load is connected across the two battery terminal nets. This is a source modeling assumption, not measured pump power/efficiency.",
      "current":"The Scope label Battery current is DC filtered demand routed through controlled current source; it is not an independent current-sensor measurement of total battery current including pump branch.",
      "causality":"A fault-induced actuator change affects both cooling lookup and electrically connected auxiliary demand. No temperature/energy/operating-quadrant magnitude is established by static topology.",
      "clock":"Amended sample hold/discrete actuator replaces continuous 1ms dynamics upstream of BOTH paths, with declared 10/5ms output holds. Toy pass does not validate physical adequacy or waveform equivalence.",
      "units":"Saved compile receipts have blank actuator/T312 signal unit labels; parity is not explicit compiled SI-unit proof. Converter and SSC units support static flow/power interpretation. FlwT converter remains source Unit=1 whereas delT_b is K; retained ambiguity is not silently fixed.",
      "parserCorrection":"Initial directed edge extraction omitted nested conserving Src peers in DEST_DEST branches. Original raw graphs/failed run retained; corrected undirected physical hypernets preserve every Src/Dst and match all five models."
    }
    cert={"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],"sourceCollectionRun":"40692041954",
      "M1_STATIC_COOLING_PATH":"PASS","M1_STATIC_PUMP_ELECTRICAL_PATH":"PASS","M1_FOUR_AMENDED_PATH_PARITY":"PASS",
      "M1_COMPILED_EXPLICIT_SI_METADATA":"UNAVAILABLE","M1_PHYSICAL_OR_THERMAL_VALIDATION":"UNQUALIFIED",
      "graphs":ledger,"sourceComponentSHA":{k:v["sha256"] for k,v in ssc.items()},"explanation":explanations,
      "workspace":component["workspace"],"newMATLAB":False,"newCompile":False,"newSimulation":False,"G5Accepted":False}
    emit("PATH_CERTIFICATE.json",cert)
    emit("M2_RESOURCE_SCREEN.json",{"rawEvidence":resource,"decision":"NO_GO_MINIMAL_LOGGER_RUNTIME_AND_FREE_HEADROOM_UNQUALIFIED",
      "boundedPhaseWriter":"PROPOSAL_ONLY_NOT_IMPLEMENTED","acceptedPhysicalCheckpoint":"UNQUALIFIED",
      "completeSolvedInitialOperatingPoint":"UNQUALIFIED","newLicenseOrMinuteEntitlementCheck":"NOT_PERFORMED_NO_MATLAB_REQUEST",
      "nativeRowUpperBound":"UNAVAILABLE; Ts schedule is not an upper bound on solver/native rows",
      "storageRule":"One T312 sample plus own timestamp is 2504 bytes payload; each scalar with own timestamp is 16 bytes. Object/HDF5/cache/engine overhead and peak RAM are not included.",
      "oldResourceScreenWarning":"Historical linear wall-time screens are not predictions/bounds for amended Simscape execution",
      "full2400Go":False,"one340Authorized":False})
    emit("PRIVATE_HANDOFF.md",HANDOFF)
    emit("INPUT_MANIFEST.json",{"inputs":inputs,"priorGraphRun":"40691093123","supplementRun":"40692041954",
      "newSimulation":False,"G5Accepted":False})
    p=ROOT/(prefix+"PRIVATE_RECEIPT.json");p.write_text(json.dumps({"schema":SCHEMA,"run":run,"commit":os.environ["GITHUB_SHA"],
      "files":outputs,"newMATLAB":False,"newCompile":False,"newSimulation":False,"G5Accepted":False},indent=2))
    upload_verified(t,folder,p,schema=SCHEMA)
    print("BTMS_M1_STATIC_PATHS_PASS allFiveModels=1 pumpCoolingCommonOutput=1 privateSHAReadback=PASS M2=NO_GO_UNQUALIFIED noMATLAB=1 noSimulation=1 G5_ACCEPTED=false")
HANDOFF="""# Internal M1/M2 engineering handoff, not official research report
M1 path verification reuses full SHA/readback graphs and actual earlier MATLAB compile receipts; no model load/compile or trajectory in this job.
Cooling is normalized per-module input to a mass-flow-indexed thermal lookup. No sum-to-one/total hydraulic mass conservation is claimed.
Pump is an assumed linear 500W-full-scale auxiliary demand from the same actuator, with real electrical two-node connectivity. Static connectivity alone does not determine delivered power, operating quadrant, total current or thermal effect.
The source Scope Battery current is a demand signal, not a separate measured total battery current. Future electrical accounting must use actual battery/branch voltage/current or documented physical logged variables, not Scope labels.
Four amended models retain both branches; their sampled dynamics jointly affect both. They remain a method amendment, not an equivalent source continuous waveform.
Blank compiled units remain UNAVAILABLE as explicit metadata; source converter/SSC contracts are separately traced. FlwT's source Unit=1 versus component K remains disclosed.

## M2 proposed bounded logger (NO new run authorization)
For a future separately approved single B0L 0-340s diagnostic, retain source physics/load/reference/IC/solver and exactly the already-frozen actuator method. This design does not certify physical initial-state parity.
R2024b classic batch sim(SimulationInput), normal mode, fast restart off, Dataset signal logging with LoggingToFile/on to MAT is the documented disk route.
Do not use Simulation object/Simulation Stepper with LoggingToFile in R2024b: that support came in R2025a; R2024b excludes Stepper/fast restart from persistent storage.
Disable duplicate legacy ToWorkspace full-vector/all-state histories and Scope/SDI duplication only on a fresh instrumentation copy after explicit review of the logging-only diff. Do not alter signal paths, plant parameters or native samples. LoggingToFile does not magically redirect legacy Timeseries ToWorkspace buffers.
Select a single Ttrue312 Dataset stream; measured Tmax/Tmin; raw core; held input; actuator state/output; modeled pump demand; actual pack/aux current and voltage if traceable without changing physics. Preserve each role's own original clock and duplicate rows; decimation1, no row truncation/interpolation/zero-crossing sample deletion.
Retain discrete output/preupdate/postupdate phase evidence using a bounded append writer at actual declared events; this records block event ordering, not accepted continuous solver-state provenance. The writer is a proposal and has not been implemented/benchmarked.
Global all-state histories off. Saving a final operating point conflicts with persistent final-state Dataset settings; do not declare complete solved t0 physical state or restart equivalence from model workspace equality. A documented compatible initial/accepted checkpoint mechanism and memory qualification remain missing.
Payload budget is 2504 bytes per T312 row including its timestamp, plus16 bytes per scalar row on its own clock. Scheduled Ts counts are a lower bound for observation cardinality, not an upper bound on solver samples. Engine factorization, logging cache/SDI, HDF5/object overhead, phase writer and peak memory remain unmeasured for the new minimal logger.
Real host/Drive/historical benchmark evidence is in the companion resource file. Historical linear runtime estimates must not be promoted to measured amended runtime. No guaranteed free-time entitlement or new-method peak RAM/abort/sink qualification is established here.
Decision: NO_GO_MINIMAL_LOGGER_RUNTIME_AND_FREE_HEADROOM_UNQUALIFIED. Full2400s is also NO-GO. No toy or plant was started.

## M3 / scientific hold
Keep only the already saved highest-computed-RMS340s segment as a proposal. FromFile interpolation and polarity, cell SOC/voltage/current/thermal-LUT domains and physical IC/load legitimacy still need qualification. No file or trajectory is generated, no favorable channel reselection, no guaranteed activation, no switch to293.15K as a physical load.
Original G5 remains rejected/unqualified for thermal claims; amended G5 unqualified. Chat/owner independent scientific acceptance is required. JTE058, confidentiality and no-merge/no-payment holds remain.

Primary documentation:
https://www.mathworks.com/help/releases/R2024b/simulink/ug/log-data-to-persistent-storage-1.html
https://www.mathworks.com/help/simulink/gui/logdatatofile.html (Version history: R2025a Simulation objects)
https://www.mathworks.com/help/releases/R2024b/simulink/slref/gain.html (default Gain1; saved source Gain1/Gain2 do not override it)
"""
if __name__=="__main__":
    try:
        t,f=base.context()
        print("BTMS_M1_CERT_RECEIVED executor=GITHUB_HOSTED_ACTIONS run="+os.environ["GITHUB_RUN_ID"]+" mode=READ_ONLY_INTERPRETATION_NO_MATLAB",flush=True)
        main(t,f)
    except Exception as e:
        if ROOT.is_dir():
            try:
                p=ROOT/("BTMS_M1_CERT_"+os.environ["GITHUB_RUN_ID"]+"_FAILURE.json")
                p.write_text(json.dumps({"exception":type(e).__name__,"message":str(e),"simulationRun":False}))
                upload_verified(t,f,p,schema=SCHEMA)
            except Exception:pass
        print("BTMS_M1_CERT_UNQUALIFIED details=OWNER_PRIVATE_ONLY noSimulation=1");sys.exit(1)
