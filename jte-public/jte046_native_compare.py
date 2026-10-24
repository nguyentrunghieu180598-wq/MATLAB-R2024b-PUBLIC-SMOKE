"""Native trace comparison. No decryption, simulation, or automatic scientific PASS."""
from __future__ import annotations
import argparse, bisect, csv, hashlib, json, math
from pathlib import Path

SOURCE_SHA='0a61b958173e55f9a5683d8f91fc82dc00078d6a948b66c23883b370bbc4abc0'
PUBLIC_SHA='697b4f3b15cdd9ae1e450955329f72d6b759ec025ed4a8f7dbe71c4febbbdeae'
ARCHIVES={
 'B0L_original':'9327ada78d02b70a64abfd522427f77a53009b4bb176f6617d34c7bcd763f1e2',
 'C0_original':'305b5c51e94a2ef3e4fafdf118e01c0f0e2da4020b1e10b34921cc6769ac3443',
 'B0L_fine':'0ceeabdadcbd948e87b4c3682bd17d7d596412740992ceab02db076b126da612',
 'C0_fine':'de65624da32694f1fef0473c149ae11e85b52554746edde540a11e5db16e8d01'}
class EvidenceError(ValueError): pass
def need(ok,msg):
    if not ok: raise EvidenceError(msg)
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk)
    return h.hexdigest()
def private_file(root,name):
    need(isinstance(name,str),'FILE_PATH_REQUIRED')
    p=(root/name).resolve()
    need(p.is_relative_to(root) and p.is_file(),'FILE_OUTSIDE_OR_MISSING')
    return p

class Trace:
    def __init__(self,t,rows,mode,duplicate_convention='UNVERIFIED'):
        need(mode in ('linear','zoh'),'SAMPLING_MODE_UNVERIFIED')
        self.source_times=tuple(float(x) for x in t)
        self.source_rows=tuple(tuple(float(v) for v in row) for row in rows)
        need(len(t)>=2 and len(t)==len(rows),'TRACE_SHAPE')
        width=len(self.source_rows[0]);need(width>0,'EMPTY_CHANNELS')
        need(all(len(r)==width and all(math.isfinite(v) for v in r) for r in self.source_rows),'NONFINITE_OR_RAGGED')
        need(all(math.isfinite(v) for v in self.source_times),'NONFINITE_TIME')
        need(all(b>=a for a,b in zip(self.source_times,self.source_times[1:])),'TIME_NOT_ORDERED')
        self.mode=mode;self.width=width;self.times=[];self.left=[];self.right=[]
        i=0
        while i<len(t):
            j=i+1
            while j<len(t) and self.source_times[j]==self.source_times[i]:j+=1
            need(j-i<=2,'MORE_THAN_TWO_EVENT_SIDES')
            if j-i==2:
                need(duplicate_convention=='first_pre_last_post','DUPLICATE_CONVENTION_UNVERIFIED')
                pre=self.source_rows[i]
                if mode=='zoh' and self.right: need(pre==self.right[-1],'ZOH_PRE_EVENT_NOT_PREVIOUS_HOLD')
            else:
                pre=self.right[-1] if mode=='zoh' and self.right else self.source_rows[i]
            self.times.append(self.source_times[i]);self.left.append(pre);self.right.append(self.source_rows[j-1]);i=j
        need(len(self.times)>=2 and self.times[-1]>self.times[0],'EMPTY_HORIZON')
    @classmethod
    def from_csv(cls,path,mode,convention='UNVERIFIED'):
        with Path(path).open(newline='',encoding='utf-8-sig') as f:
            reader=csv.reader(f);head=next(reader,[])
            need(len(head)>=2 and head==['time_s']+[f'value_{i}' for i in range(1,len(head))],'CSV_SCHEMA')
            data=list(reader)
        need(all(len(r)==len(head) for r in data),'CSV_ROW_WIDTH')
        return cls([float(r[0]) for r in data],[[float(x) for x in r[1:]] for r in data],mode,convention)
    def at(self,t,side='right'):
        need(self.times[0]<=t<=self.times[-1],'NO_EXTRAPOLATION')
        j=bisect.bisect_left(self.times,t)
        if j<len(self.times) and self.times[j]==t:return self.left[j] if side=='left' else self.right[j]
        i=j-1
        if self.mode=='zoh':return self.right[i]
        f=(t-self.times[i])/(self.times[j]-self.times[i])
        return tuple(a+(b-a)*f for a,b in zip(self.right[i],self.left[j]))
    def events(self):
        need(self.mode=='zoh','EVENTS_REQUIRE_VERIFIED_HOLD')
        return [{'time_s':t,'before':self.left[i],'after':self.right[i]}
                for i,t in enumerate(self.times) if i and self.left[i]!=self.right[i]]

def compare(a,b):
    need(a.mode==b.mode and a.width==b.width,'COMPARISON_SCHEMA')
    need(a.times[0]==b.times[0] and a.times[-1]==b.times[-1],'HORIZON_MISMATCH')
    # Breakpoint union is only an integration grid. Original event rows are retained.
    grid=sorted(set(a.times+b.times));width=a.width
    maxima=[0.]*width;areas=[[] for _ in range(width)]
    def delta(t,side):return [x-y for x,y in zip(a.at(t,side),b.at(t,side))]
    for t in grid:
        for side in ('left','right'):
            for k,x in enumerate(delta(t,side)):maxima[k]=max(maxima[k],abs(x))
    for t0,t1 in zip(grid,grid[1:]):
        x=delta(t0,'right');y=delta(t1,'left');dt=t1-t0
        for k in range(width):
            e=dt*x[k]*x[k] if a.mode=='zoh' else dt*(x[k]*x[k]+x[k]*y[k]+y[k]*y[k])/3
            areas[k].append(e)
    rmse=[math.sqrt(max(0,math.fsum(e)/(grid[-1]-grid[0]))) for e in areas]
    out={'maxAbs_by_channel':maxima,'RMSEtime_by_channel':rmse,'maxAbs':max(maxima),
         'RMSEtime_max_channel':max(rmse),'mode':a.mode,'breakpoints':len(grid),
         'interpretation':'Exact for the stated piecewise representation, not exact continuous plant solution'}
    if a.mode=='zoh':
        ea,eb=a.events(),b.events()
        same=[(x['before'],x['after']) for x in ea]==[(x['before'],x['after']) for x in eb]
        out['observed_event_counts']=[len(ea),len(eb)]
        out['event_sequence_status']='MATCHED_OBSERVED_SEQUENCE' if same else 'UNMATCHED_OBSERVED_SEQUENCE'
        out['observed_event_time_deltas_s']=[x['time_s']-y['time_s'] for x,y in zip(ea,eb)] if same else None
    return out

def controller(tmax,ambient):
    q=min(.95,max(.001,.1*(tmax-ambient)))
    return max(.25,q-q%.25)

def threshold_brackets(trace,ambient):
    """Linear-reconstruction estimates; never label these as original solver roots."""
    need(trace.mode=='linear' and trace.width==1,'THRESHOLD_TRACE_SCHEMA')
    out=[]
    for i in range(len(trace.times)-1):
        t0,t1=trace.times[i:i+2]
        a=trace.right[i][0]-ambient;b=trace.left[i+1][0]-ambient
        for theta in (5.,7.5):
            if (a<theta<=b) or (b<theta<=a):
                out.append({'threshold_K':theta,'bracket_s':[t0,t1],
                            'estimated_time_s':t0+(theta-a)*(t1-t0)/(b-a),
                            'direction':'up' if b>a else 'down',
                            'time_kind':'LINEAR_RECONSTRUCTION_ESTIMATE_NOT_SOLVER_ROOT'})
    return out

def audit(folder,output):
    root=Path(folder).resolve();m=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
    need(m.get('scope')=='AUTHENTICATED_MATLAB_STUDY','TEMPLATE_OR_SYNTHETIC_NOT_STUDY')
    need(m.get('source_sha256')==SOURCE_SHA and m.get('horizon_s')==2400,'SOURCE_OR_HORIZON')
    need(m.get('matched_conditions_verified') is True,'MATCHED_INPUTS_IC_REQUIRED')
    need(set(m.get('cases',{}))==set(ARCHIVES),'FOUR_CASES_REQUIRED')
    profiles=m.get('solver_profiles',{})
    need(set(profiles)=={'original','fine'} and profiles['original']!=profiles['fine'],'TWO_SOLVER_PROFILES_REQUIRED')
    for p in profiles.values():
        need(all(p.get(k) is not None for k in ('Solver','SolverType','RelTol','AbsTol','MaxStep')),'SOLVER_PROFILE_INCOMPLETE')
    traces={};blockers=['INDEPENDENT_SCIENTIFIC_REVIEW_AND_ACCEPTANCE_LIMITS_REQUIRED']
    amb=[];loads=[];ics=[];lineage={}
    for key,item in m['cases'].items():
        need(item.get('temperature_unit_verified')=='K','TEMPERATURE_UNIT_REQUIRED')
        a=item.get('ambient_actual_K');need(type(a) in (int,float) and math.isfinite(a),'AMBIENT_SCALAR_REQUIRED');amb.append(a)
        need(item.get('solver_profile')==key.rsplit('_',1)[1],'SOLVER_CASE_PROFILE_MISMATCH')
        for v in ('load_sha256','initial_state_sha256','model_sha256'):
            h=item.get(v);need(isinstance(h,str) and len(h)==64 and all(c in '0123456789abcdef' for c in h),'PROVENANCE_HASH_REQUIRED')
        loads.append(item['load_sha256']);ics.append(item['initial_state_sha256'])
        rp=private_file(root,item.get('gcm_receipt_file'));need(sha(rp)==item.get('gcm_receipt_sha256'),'RECEIPT_FILE_HASH')
        r=json.loads(rp.read_text(encoding='utf-8-sig'))
        need(r.get('rsaOaepAesGcmAuthenticated') is True and r.get('artifactSHA256')==ARCHIVES[key]
             and r.get('publicKeySHA256')==PUBLIC_SHA,'AUTHENTICATED_RECEIPT_REQUIRED')
        mat=private_file(root,item.get('source_mat_file'));mh=sha(mat)
        need(mh==item.get('source_mat_sha256')==r.get('members',{}).get(item.get('source_mat_member'),{}).get('sha256'),'MAT_RECEIPT_CHAIN')
        lineage[key]={'archive_sha256':r['artifactSHA256'],'receipt_sha256':sha(rp),'MAT_sha256':mh,'model_sha256':item['model_sha256']}
        signals=item.get('signals',{});need('jteTmaxTrue' in signals,'TRUE_MAX_MISSING')
        if key.startswith('C0'):need('jteTmaxMeas' in signals,'ZERO_BIAS_MEASURED_MAX_MISSING')
        traces[key]={}
        for name,info in signals.items():
            p=private_file(root,info.get('file'));need(sha(p)==info.get('sha256'),'SIGNAL_CSV_HASH')
            mode=info.get('sampling')
            if mode not in ('linear','zoh'):
                blockers.append(key+':'+name+':SAMPLING_NOT_VERIFIED');continue
            if name=='jteUcore' and (item.get('data_time_source')!='raw_event_time' or mode!='zoh'):
                blockers.append(key+':CORE_NATIVE_EVENT_SEMANTICS_REQUIRED');continue
            x=Trace.from_csv(p,mode,info.get('duplicate_convention','UNVERIFIED'))
            need(x.times[0]==0 and x.times[-1]==2400,'SIGNAL_FULL_HORIZON_REQUIRED')
            traces[key][name]=x
            lineage[key].setdefault('CSV_sha256',{})[name]=sha(p)
        if item.get('data_time_source')!='raw_event_time':blockers.append(key+':ONE_SECOND_INTERPOLATED_OR_UNVERIFIED')
        if item.get('root_event_coverage_verified') is not True:blockers.append(key+':ROOT_EVENT_COVERAGE_UNVERIFIED')
        if 'jteTtrue' not in signals:blockers.append(key+':FULL_SENSOR_VECTOR_NOT_EXPORTED_G6_BLOCKED')
    need(max(amb)-min(amb)<=1e-9 and len(set(loads))==1 and len(set(ics))==1,'INPUT_IC_AMBIENT_MISMATCH')
    results={}
    pairs=[('paired_original','B0L_original','C0_original'),('paired_fine','B0L_fine','C0_fine'),
           ('solver_B0L','B0L_original','B0L_fine'),('solver_C0','C0_original','C0_fine')]
    for label,ka,kb in pairs:
        results[label]={name:compare(traces[ka][name],traces[kb][name])
                        for name in traces[ka].keys() & traces[kb].keys()}
    zero={key:compare(v['jteTmaxTrue'],v['jteTmaxMeas']) for key,v in traces.items() if key.startswith('C0')}
    conformance={};thresholds={}
    for key,v in traces.items():
        temp=v.get('jteTmaxMeas' if key.startswith('C0') else 'jteTmaxTrue')
        core=v.get('jteUcore');a=m['cases'][key]['ambient_actual_K']
        if temp and temp.mode=='linear' and temp.width==1:
            thresholds[key]=threshold_brackets(temp,a)
        if core and temp and core.times==temp.times and core.width==temp.width==1:
            conformance[key]={'right_side_pointwise_maxAbs':max(abs(core.right[i][0]-controller(temp.right[i][0],a)) for i in range(len(core.times))),
                              'scope':'Recorded right-side states only; not event completeness'}
        elif core:
            blockers.append(key+':CORE_AND_TMAX_CLOCK_NOT_IDENTICAL_NO_SILENT_RESAMPLING')
    result={'status':'NUMERIC_EVIDENCE_REVIEW_REQUIRED','G5_PASS':False,'scope':m['scope'],
            'results':results,'zero_bias_max':zero,'core_conformance':conformance,'threshold_brackets_estimated':thresholds,'lineage':lineage,'solver_profiles':profiles,'blockers':sorted(set(blockers)),
            'auth_caution':'Receipt validation is a provenance check, not decryption/GCM performed by this program'}
    out=Path(output).resolve();need(not out.exists() and not out.is_relative_to(root),'OUTPUT_MUST_BE_NEW_OUTSIDE_INPUT')
    with out.open('x',encoding='utf-8') as f:json.dump(result,f,indent=2,allow_nan=False)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    try:
        audit(a.input,a.output)
        print('PRIVATE NUMERIC REVIEW SAVED; G5 NOT AUTO-ACCEPTED')
    except (EvidenceError,ValueError,OSError,KeyError,TypeError):
        print('BLOCKED_INPUT_EVIDENCE: no scientific acceptance')
        raise SystemExit(2) from None
