"""Five explicit stdlib qualification controls. Synthetic fixtures are never NPU evidence."""
import ast
import copy
import json
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import sourceio as C
import fastpath_numeric_consumer as N
import fastpath_numeric_observer as O
import qualification_source_validate as V
import qualification_state_probe as SP

class QualificationControls(unittest.TestCase):
    def manifest(self):
        return C.obj(C.ref(Path(__file__).parent/'SOURCE_BOUND.json'))

    def test_explicit_default_OFF_and_scope_rejection(self):
        import os
        from unittest.mock import patch
        with patch.dict(os.environ,{},clear=True):
            self.assertIsNone(O.install(None,None,None,{},0,snapshot=None,sink=None))
            with self.assertRaises(ValueError):
                O.install(None,None,None,{'fastpath_numeric_qualification':{}},0,snapshot=None,sink=None)
        m=self.manifest();self.assertTrue(V.qualification_shape(m))
        for key in ('fastpath_numeric_qualification','performance_profile','performance_client_contract'):
            bad=copy.deepcopy(m)
            if key=='performance_profile':bad[key]['scope']['output_tokens']=1024
            else:bad[key]['output_tokens']=1024
            with self.assertRaises(ValueError):V.qualification_shape(bad)

    def test_selected_conv_rejects_other_legal_tail(self):
        class Exact:
            @staticmethod
            def equal(t,a,b,s):
                if a!=b:raise ValueError(s)
        tails=[['root'],['left'],['right']]
        for terminal in range(3):
            N.selected_conv_write(None,Exact,{'after':tails[terminal]},{'actual_conv_tail':tails},terminal)
            for other in set(range(3))-{terminal}:
                with self.assertRaises(ValueError):
                    N.selected_conv_write(None,Exact,{'after':tails[other]},{'actual_conv_tail':tails},terminal)

    def test_state_adapter_real_shape_positive_and_negative(self):
        # This control tests the receipt ABI only. The fixture's booleans are
        # explicit synthetic data and are not persisted as actual qualification.
        import short_state_digest as D
        from unittest.mock import patch
        sr={'fixture':'software-not-NPU'};m=self.manifest()
        digest=dict(dtype='torch.float32',shape=[1],bytes=4,sha256='a'*64,finite=True)
        rows=[dict(layer=i,kind=k,after=dict(digest),
                   **({'before':dict(digest)}if k in('state','conv')else{}))
              for i,k in sorted(D.DESTINATIONS)]
        def run(mutation=None):
            owner=NS(request='fixture',generation=1,version=0,length=131)
            pub=dict(owner=owner,cache_published=True,actual_applied=[],
                diagnostic_readback_performed=False,processed_nodes=(0,),emitted_tokens=(7,),next_length=132)
            proposal=dict(owner=owner,published=False,processed_nodes=(0,))
            report=dict(source=sr,rank=0,generation=1,ordinal=0,frame_checks_passed=True,
                        full128_actual_state_writes_verified=True,selected_write_digests=copy.deepcopy(rows))
            if mutation=='missing':report['selected_write_digests'].pop()
            if mutation=='stale':report['ordinal']=1
            if mutation=='array':pub['actual_applied']=[object()]
            probe=SP.Probe.__new__(SP.Probe);probe.C=NS(
                need=V.need,ref=C.ref,checked=lambda r:True,obj=lambda r:report)
            probe.m=m;probe.source=sr;probe.rank=0;probe.failed=False;probe.active='fixture'
            probe.generation=1;probe.last_version=-1;probe.last_publication=None
            probe.profile=dict(D.DECLARATION,observation='OFF');probe.frames=set();events=[]
            probe.emit=lambda *a:events.append(a)
            bridge=NS(collect_observation_only=False,fastpath_numeric_observer=NS(
                current=None,receipts=[{'fixture-report':'not-actual'}]))
            frame=NS(owner=owner,proposal=proposal,publication=pub,tokens=(1,2,3))
            probe.capture(bridge,frame,dict(req_ids=['fixture'],sampled_token_ids=[[7]]))
            return probe,events
        probe,events=run();self.assertEqual(len(events),1);self.assertEqual(len(events[0][3]['rows']),128)
        for mutation in ('missing','stale','array'):
            with self.assertRaises(ValueError):run(mutation)

    def test_wrong_or_missing_authority_never_admits(self):
        m=self.manifest();bad=copy.deepcopy(m);bad['qualification_authority_ref']=None
        with self.assertRaisesRegex(ValueError,'unbound'):V.execution_window(bad,clock=False,require_phase=False)
        for schema in ('bole.MAIN-reviewed-fastpath-performance-execution-authority/v1','old-fixed-window'):
            with self.assertRaises(ValueError):
                V.authority_shape(dict(schema=schema,approved=True,start_epoch=0,cutoff_epoch=999999,
                                       scope=V.SCOPE,MAIN_review_ref={'fixture':'not-actual'}))
        self.assertIn('actual fastpath NPU numerical admission adapter remains unbound',
            V.read_ref(m['qualification_parent_preparation_readset']['followup_source_validate.py']).decode())

    def test_CPU_full_digest_exact_original_formula(self):
        m=self.manifest();text=V.read_ref(m['files']['short_state_digest.py']).decode()
        node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)and n.name=='tensor_digest')
        original=ast.get_source_segment(text,node);derived=N.cpu_digest_source(original)
        self.assertEqual(derived.replace("value.device.type == 'cpu'","value.device.type == 'npu'"),original)
        self.assertIn('hashlib.sha256(raw).hexdigest()',derived)
        with self.assertRaises(ValueError):N.cpu_digest_source(original.replace("'npu'","'cuda'"))

if __name__=='__main__':unittest.main()
