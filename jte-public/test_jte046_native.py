"""Synthetic numerical fixtures only. Attested receipt mocks are NOT GCM authentication."""
import csv, hashlib, json, math, tempfile, unittest
from pathlib import Path
from jte046_native_compare import Trace,compare,controller,threshold_brackets,audit,EvidenceError,SOURCE_SHA,PUBLIC_SHA,ARCHIVES

def scalar(t,v,mode='linear',convention='UNVERIFIED'):
    return Trace(t,[[x] for x in v],mode,convention)
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class NativeTests(unittest.TestCase):
    def test_linear_integral_exact(self):
        z=compare(scalar([0,1],[0,1]),scalar([0,1],[0,0]))
        self.assertAlmostEqual(z['RMSEtime_max_channel'],1/math.sqrt(3))
    def test_terminal_zoh_jump_no_false_area(self):
        z=compare(scalar([0,1],[0,1],'zoh'),scalar([0,1],[0,0],'zoh'))
        self.assertEqual(z['maxAbs'],1);self.assertEqual(z['RMSEtime_max_channel'],0)
    def test_shifted_two_sided_steps(self):
        a=scalar([0,1,1,2],[0,0,1,1],'zoh','first_pre_last_post')
        b=scalar([0,1.25,1.25,2],[0,0,1,1],'zoh','first_pre_last_post')
        r=compare(a,b)
        self.assertAlmostEqual(r['RMSEtime_max_channel'],math.sqrt(.25/2))
        self.assertEqual(r['observed_event_time_deltas_s'],[-.25])
        self.assertEqual(a.source_times,(0.,1.,1.,2.))
        self.assertEqual(a.source_rows,((0.,),(0.,),(1.,),(1.,)))
    def test_linear_jump_does_not_smear(self):
        a=scalar([0,1,1,2],[0,0,1,1],'linear','first_pre_last_post')
        z=compare(a,scalar([0,2],[0,0]))
        self.assertAlmostEqual(z['RMSEtime_max_channel'],math.sqrt(.5))
    def test_ambiguous_duplicate_rejected(self):
        with self.assertRaises(EvidenceError):scalar([0,1,1,2],[0,0,1,1])
    def test_more_than_two_sides_rejected(self):
        with self.assertRaises(EvidenceError):scalar([0,1,1,1,2],[0,0,1,2,2],'linear','first_pre_last_post')
    def test_zoh_pre_side_checked(self):
        with self.assertRaises(EvidenceError):scalar([0,1,1,2],[0,.1,1,1],'zoh','first_pre_last_post')
    def test_unsorted_rejected(self):
        with self.assertRaises(EvidenceError):scalar([0,2,1],[0,1,2])
    def test_nonfinite_rejected(self):
        with self.assertRaises(EvidenceError):scalar([0,1],[0,float('nan')])
    def test_horizon_mismatch_no_extrapolation(self):
        with self.assertRaises(EvidenceError):compare(scalar([0,1],[0,0]),scalar([0,2],[0,0]))
    def test_channel_mismatch(self):
        with self.assertRaises(EvidenceError):compare(Trace([0,1],[[0,1],[1,2]],'linear'),scalar([0,1],[0,1]))
    def test_multichannel_rmse(self):
        z=compare(Trace([0,2],[[1,2],[1,2]],'linear'),Trace([0,2],[[0,0],[0,0]],'linear'))
        self.assertEqual(z['RMSEtime_by_channel'],[1.,2.])
    def test_unmatched_events_not_arbitrarily_paired(self):
        z=compare(scalar([0,1,2],[0,1,1],'zoh'),scalar([0,1,2],[0,2,2],'zoh'))
        self.assertIsNone(z['observed_event_time_deltas_s'])
    def test_threshold_law(self):
        for a in (280.,300.,320.):
            for d,u in [(-1,.25),(2.5,.25),(5-1e-8,.25),(5,.5),(5+1e-8,.5),
                        (7.5-1e-8,.5),(7.5,.75),(7.5+1e-8,.75),(20,.75)]:
                self.assertEqual(controller(a+d,a),u)
    def test_negative_two_kelvin_windows(self):
        for x,drop in [(4.9,0),(5,-.25),(6.9,-.25),(7,0),(7.49,0),(7.5,-.25),(9.49,-.25),(9.5,0)]:
            self.assertEqual(controller(300+x-2,300)-controller(300+x,300),drop)
    def test_threshold_times_are_estimates(self):
        z=threshold_brackets(scalar([0,20],[300,310]),300)
        self.assertEqual([x['estimated_time_s'] for x in z],[10.,15.])
        self.assertTrue(all('NOT_SOLVER_ROOT' in x['time_kind'] for x in z))
    def test_threshold_jump_is_not_an_interpolated_root(self):
        t=scalar([0,1,1,2],[300,304,308,310],'linear','first_pre_last_post')
        z=threshold_brackets(t,300)
        self.assertEqual([v['logged_time_s'] for v in z],[1.,1.])
        self.assertTrue(all(v['estimated_time_s'] is None and 'NOT_INTERPOLATED_ROOT' in v['time_kind'] for v in z))
    def test_csv_event_rows_retained(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'trace.csv';p.write_text('time_s,value_1\n0,0\n1,0\n1,1\n2,1\n')
            t=Trace.from_csv(p,'zoh','first_pre_last_post')
            self.assertEqual(len(t.source_times),4)
    def test_template_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();(root/'manifest.json').write_text('{"scope":"TEMPLATE_NOT_EVIDENCE"}')
            with self.assertRaises(EvidenceError):audit(root,Path(d)/'out.json')

class PipelineTests(unittest.TestCase):
    def fixture(self,root):
        # These files/mock receipts exist only to test validators; no actual MAT/GCM.
        cases={}
        for key in ARCHIVES:
            mat=root/(key+'_SYNTHETIC_NOT_MAT.mat');mat.write_bytes(b'SYNTHETIC VALIDATOR FIXTURE, NOT MATLAB DATA')
            receipt=root/(key+'_MOCK_receipt.json')
            receipt.write_text(json.dumps({'rsaOaepAesGcmAuthenticated':True,'artifactSHA256':ARCHIVES[key],
               'publicKeySHA256':PUBLIC_SHA,'members':{mat.name:{'sha256':digest(mat)}}}))
            signals={}
            values={'jteTmaxTrue':[300,300,300,300],'jteUcore':[.25,.25,.25,.25]}
            if key.startswith('C0'):values['jteTmaxMeas']=[300,300,300,300]
            for name,vals in values.items():
                p=root/(key+'_'+name+'.csv')
                with p.open('w',newline='') as f:
                    w=csv.writer(f);w.writerow(['time_s','value_1']);w.writerows(zip([0,1,1,2400],vals))
                signals[name]={'file':p.name,'sha256':digest(p),'sampling':'zoh' if name=='jteUcore' else 'linear','duplicate_convention':'first_pre_last_post'}
            cases[key]={'temperature_unit_verified':'K','ambient_actual_K':300.,
                'solver_profile':key.rsplit('_',1)[1],'load_sha256':'a'*64,'initial_state_sha256':'b'*64,'model_sha256':'c'*64,
                'gcm_receipt_file':receipt.name,'gcm_receipt_sha256':digest(receipt),'source_mat_file':mat.name,'source_mat_sha256':digest(mat),
                'source_mat_member':mat.name,'signals':signals,'data_time_source':'raw_event_time','root_event_coverage_verified':False}
        m={'scope':'AUTHENTICATED_MATLAB_STUDY','source_sha256':SOURCE_SHA,'horizon_s':2400,
           'matched_conditions_verified':True,'solver_profiles':{
             'original':dict(Solver='ode23t',SolverType='Variable-step',RelTol='1e-3',AbsTol='auto',MaxStep='auto'),
             'fine':dict(Solver='ode23t',SolverType='Variable-step',RelTol='5e-4',AbsTol='auto',MaxStep='auto')},'cases':cases}
        (root/'manifest.json').write_text(json.dumps(m));return m
    def test_mock_end_to_end_never_accepts_science(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();self.fixture(root)
            out=Path(d)/'SYNTHETIC_ONLY.json';r=audit(root,out)
            self.assertFalse(r['G5_PASS'])
            self.assertEqual(r['results']['paired_original']['jteTmaxTrue']['maxAbs'],0)
            self.assertTrue(any('ROOT_EVENT' in x for x in r['blockers']))
            self.assertTrue(any('G6_BLOCKED' in x for x in r['blockers']))
    def test_tampered_csv_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();m=self.fixture(root)
            p=root/m['cases']['B0L_original']['signals']['jteTmaxTrue']['file'];p.write_text('tampered')
            out=Path(d)/'bad.json'
            with self.assertRaises(EvidenceError):audit(root,out)
            self.assertFalse(out.exists())
    def test_compact_skips_command_events(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();m=self.fixture(root)
            for c in m['cases'].values():c['data_time_source']='already_interpolated_1s'
            (root/'manifest.json').write_text(json.dumps(m))
            r=audit(root,Path(d)/'SYNTHETIC_COMPACT.json')
            self.assertFalse(r['G5_PASS'])
            self.assertNotIn('jteUcore',r['results']['paired_original'])
            self.assertTrue(any('ONE_SECOND' in x for x in r['blockers']))

    def test_c0_full_zero_bias_vector_is_compared(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();m=self.fixture(root)
            for key in ('C0_original','C0_fine'):
                for name in ('jteTtrue','jteTmeas'):
                    f=root/(key+'_'+name+'.csv')
                    f.write_text('time_s,value_1,value_2\n' +
                        ''.join(f'{t},300,299\n' for t in (0,1,1,2400)))
                    m['cases'][key]['signals'][name]={
                      'file':f.name,'sha256':digest(f),
                      'sampling':'linear','duplicate_convention':'first_pre_last_post'}
            (root/'manifest.json').write_text(json.dumps(m))
            z=audit(root,Path(d)/'review.json')
            self.assertFalse(z['G5_PASS'])
            self.assertEqual(set(z['zero_bias_full_vectors']),{'C0_original','C0_fine'})
            self.assertEqual(z['zero_bias_full_vectors']['C0_original']['maxAbs'],0)
            self.assertFalse(any('ZERO_BIAS_FULL_VECTOR_NOT_AVAILABLE' in b for b in z['blockers']))

    def test_c0_sensor_mismatch_flagged_even_if_max_agrees(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)/'input';root.mkdir();m=self.fixture(root)
            for name,values in [('jteTtrue',(300,299)),('jteTmeas',(300,297))]:
                f=root/('C0_original_'+name+'.csv')
                f.write_text('time_s,value_1,value_2\n' +
                    ''.join(f'{t},{values[0]},{values[1]}\n' for t in (0,1,1,2400)))
                m['cases']['C0_original']['signals'][name]={
                  'file':f.name,'sha256':digest(f),
                  'sampling':'linear','duplicate_convention':'first_pre_last_post'}
            (root/'manifest.json').write_text(json.dumps(m))
            z=audit(root,Path(d)/'review.json')
            self.assertEqual(z['zero_bias_max']['C0_original']['maxAbs'],0)
            self.assertEqual(z['zero_bias_full_vectors']['C0_original']['maxAbs'],2)
            self.assertIn('C0_original:ZERO_BIAS_FULL_VECTOR_NONZERO_REVIEW',z['blockers'])
            self.assertIn('C0_fine:ZERO_BIAS_FULL_VECTOR_NOT_AVAILABLE',z['blockers'])
            self.assertFalse(z['G5_PASS'])

if __name__=='__main__':
    unittest.main(verbosity=2)
