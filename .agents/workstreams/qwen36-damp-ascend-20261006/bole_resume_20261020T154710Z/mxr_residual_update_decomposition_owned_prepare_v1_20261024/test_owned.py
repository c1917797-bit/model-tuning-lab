"""Stdlib, SYNTHETIC contracts only; no Torch or real numeric calculation."""
import copy,hashlib,importlib.util,json,subprocess,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
OWNER_PARENT={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_actual_inverse_rounding_owned_prepare_v2_20261024/owner.py","bytes":6611,"sha256":"3253a92717c6b368bb63b99bccc64b2d760e5ddc5665c0e96f61823276d07300"}
GUEST_PARENT={"path":"/opt/host/vnf/austinov/model-tuning-lab/.agents/workstreams/qwen36-damp-ascend-20261006/bole_resume_20261020T154710Z/mxr_actual_inverse_rounding_owned_prepare_v2_20261024/guest_entry.py","bytes":3583,"sha256":"cfdb1d0abef0228321f417cd9f5ce49d86bbca9b429df269e52ee7ea6d3bb19e"}
OWNER_EDITS=[["Actual retained-A cast diagnostic","Actual residual/update decomposition"],["/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_ACTUAL_INVERSE_ROUNDING_CPU_20261024_V2","/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_RESIDUAL_UPDATE_DECOMPOSITION_CPU_20261024_V1"],["mxr-actual-inverse-rounding-CPU-20261024-v2","mxr-residual-update-decomposition-CPU-20261024-v1"],["mxr.MAIN-actual-inverse-rounding-owned-CPU-review/v1","mxr.MAIN-residual-update-decomposition-owned-CPU-review/v1"],["ACTUAL_CAST.json","DECOMPOSITION.json"],["MAIN_MXR_ACTUAL_CAST_","MAIN_MXR_RESIDUAL_UPDATE_"],["mxr.actual-inverse-rounding-two-CPU-children/v1","mxr.residual-update-decomposition-two-CPU-children/v1"],["mxr.actual-inverse-rounding-owned-CPU/v1","mxr.residual-update-decomposition-owned-CPU/v1"],["ACTUAL_INVERSE_ROUNDING_CPU_DIAGNOSTIC","ACTUAL_RESIDUAL_UPDATE_CPU_DIAGNOSTIC"],["    for r in [A.DIRECT]:O.checked(r)","    original_source_inputs=O.source_inputs\n    inputs=[*inputs,*A.RAW_REFS,A.CONSUMED]\n    need(len(inputs)==21 and len({r['path']for r in inputs})==21,'original17 plus explicit3raw and CONSUMED control Ref')\n    for r in [A.DIRECT,*A.RAW_REFS,A.CONSUMED]:O.checked(r)\n    def source_inputs():\n        H,old_inputs=original_source_inputs()\n        need(old_inputs==inputs[:17],'unchanged original seventeen mount inputs')\n        return H,inputs\n    O.source_inputs=source_inputs"]]
GUEST_EDITS=[["/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_ACTUAL_INVERSE_ROUNDING_CPU_20261024_V2","/opt/host/vnf/austinov/run-mxr-event-single6-owned-main-MXR_RESIDUAL_UPDATE_DECOMPOSITION_CPU_20261024_V1"],["ACTUAL_CAST.json","DECOMPOSITION.json"],["MAIN_MXR_ACTUAL_CAST_","MAIN_MXR_RESIDUAL_UPDATE_"],["Original software then actual same-A cast comparison","Original software then residual/update decomposition"]]
def load(n):
    s=importlib.util.spec_from_file_location('_decomposition_'+n,HERE/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def checked(r):
    b=Path(r['path']).read_bytes();assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];return b.decode()
class Controls(unittest.TestCase):
    def test_full_source_inverse_and_original_lifecycle(self):
        for name,parent,edits in [('owner.py',OWNER_PARENT,OWNER_EDITS),('guest_entry.py',GUEST_PARENT,GUEST_EDITS)]:
            s=(HERE/name).read_text()
            for before,after in reversed(edits):self.assertIn(after,s);s=s.replace(after,before)
            self.assertEqual(s,checked(parent))
        M=load('owner');O=M.configured();body,pairs,old=O.derive_cpu(O.checked(O.PARENT_HOST).read_bytes())
        for a,b in reversed(pairs):body=body.replace(b,a,1)
        self.assertEqual(body,old);self.assertEqual(M.execution_decision(O),'approve')
        m=O.review_contract();self.assertEqual(len(m['readonly_inputs']),21);self.assertEqual(m['readonly_inputs'][17:20],load('analysis').RAW_REFS)
        self.assertEqual(m['readonly_inputs'][20],load('analysis').CONSUMED)
        H,inputs=O.source_inputs();self.assertEqual(inputs,m['readonly_inputs'])
        old_checked=O.checked
        try:
            for dec,ok in [('approve',True),('APPROVED',False)]:
                synthetic=copy.deepcopy(m);synthetic['decision']=dec
                O.checked=lambda _:types.SimpleNamespace(read_bytes=lambda:json.dumps(synthetic).encode())
                if ok:O.require_review({'synthetic':True})
                else:
                    with self.assertRaises(ValueError):O.require_review({'synthetic':True})
        finally:O.checked=old_checked
    def test_default_off_missing_review_and_plan(self):
        for args,ok in [([],True),(['--execute'],False),(['--plan'],True)]:
            p=subprocess.run([sys.executable,'-I','-B',str(HERE/'owner.py'),*args],capture_output=True,text=True,timeout=20)
            self.assertEqual(p.returncode==0,ok,p.stderr)
            if args==['--plan']:
                q=json.loads(p.stdout);self.assertEqual(q['required_execution_decision'],'approve');self.assertFalse(q['execution_ready'])
    def test_actual_producer_labels_and_conditional_decision(self):
        A=load('analysis')
        raw=dict(schema='mxr.actual-three-tile-rounding-raw/v1',arm='saved_candidate',variant='precast',chunk=0,head=0,source=A.NPU_SOURCE,variant_ref=A.VARIANT,full_saved_B_bitwise=True,qualification=False,native_precast='unknown')
        A.validate_labels(raw,0,0)
        for k,v in [('schema','bad'),('arm','native'),('variant','other'),('chunk',False),('head',True),('source',{}),('full_saved_B_bitwise',False)]:
            q=copy.deepcopy(raw);q[k]=v
            with self.assertRaises(ValueError):A.validate_labels(q,0,0)
        rows=[dict(sameA_B_mismatches={k:1 for k in A.ROUTES})for _ in range(3)]
        self.assertEqual(A.counts(rows)['next_action'],'NO_THREE_TILE_EVIDENCE_TO_PREFER_COMPENSATED_RESIDUAL')
        rows[0]['sameA_B_mismatches']['Xb_direct_RNE_B']=0
        self.assertEqual(A.counts(rows)['next_action'],'CONSIDER_BOUNDED_COMPENSATED_RESIDUAL_DIAGNOSTIC')
        self.assertIn('inverse_recomputed',Path(HERE/'analysis.py').read_text())
if __name__=='__main__':unittest.main()
