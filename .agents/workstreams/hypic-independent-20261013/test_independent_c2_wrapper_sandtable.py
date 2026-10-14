"""Execute actual C2 wrapper with explicit CPU ABI doubles, not NPU proof.

Only external source verification/NPU/backend imports are mocked in this test.
Production verifier and enabled runtime are unchanged.
"""
import sys,unittest
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
from contextlib import ExitStack
import torch
from independent_compact_c2_hook import install_compact_c2
from independent_compact_model_hook import CURRENT_COMPACT_MODEL,CompactModelSelection
from independent_runner_context import CURRENT_REQUEST_SLICES
from independent_mixed_query_plan import NativeQueryPlan
from independent_cache_map import CacheSlice
from test_independent_c2_metadata import metadata

class C2WrapperTests(unittest.TestCase):
    def run_case(self,bad_lease=False):
        calls=[];events=[]
        class Backend:
            num_kv_heads=1;head_size=256
            def forward(self,layer,q,k,v,cache,meta,out=None,*args):
                calls.append((meta.slot_mapping.tolist(),meta.seq_lens_list))
                out.copy_(q+meta.seq_lens_list[0])
                return out
        original=Backend.forward
        module=ModuleType('vllm_ascend.attention.attention_v1')
        module.AscendAttentionBackendImpl=Backend
        module.AscendAttentionState=SimpleNamespace(PrefillCacheHit='paged')
        def forbidden(*args,**kw):raise AssertionError('native branch acquired public material')
        stage=SimpleNamespace(compact_kv_store=SimpleNamespace(acquire_private=forbidden))
        plans=(NativeQueryPlan('d',0,3,0,3,1,'decode'),
               NativeQueryPlan('p',0,3,1,0,6,'cold-material'))
        caches=(CacheSlice('d',0,3,0,0,8,(1,),(11,)),
                CacheSlice('p',0,3,0,1,8,(2,),tuple(range(16,22))))
        leases=(('d',0,(11,)),('p',0,() if bad_lease else tuple(range(16,22))))
        selected=CompactModelSelection(plans,(0,6),False,caches,
                                       ((0,('layer',)),),leases)
        native=metadata();native.num_decodes=1;native.num_decode_tokens=1;native.num_prefills=1
        native.block_tables=torch.tensor([[1],[2]],dtype=torch.int32)
        q=torch.arange(7*256).reshape(7,256).float();out=torch.full_like(q,-1)
        model_token=CURRENT_COMPACT_MODEL.set(selected)
        req_token=CURRENT_REQUEST_SLICES.set(('fixture',))
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.dict(sys.modules,{module.__name__:module}))
                stack.enter_context(patch('independent_compact_c2_hook.inspect.getfile',return_value=__file__))
                stack.enter_context(patch('independent_compact_c2_hook.Path.read_bytes',return_value=b'cpu-source-double'))
                stack.enter_context(patch('independent_compact_c2_hook.hashlib.sha256',
                    return_value=SimpleNamespace(hexdigest=lambda:'80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390')))
                stack.enter_context(patch.object(torch,'npu',SimpleNamespace(synchronize=lambda:None),create=True))
                stop=install_compact_c2(stage,enabled=True,emit=events.append)
                try:
                    fn=lambda:Backend().forward(SimpleNamespace(layer_name='layer'),q,q,q,
                        (torch.empty(1),torch.empty(1)),native,out)
                    if bad_lease:
                        with self.assertRaises(ValueError):fn()
                        self.assertEqual(calls,[])
                        self.assertTrue((out==-1).all())
                    else:
                        fn()
                        self.assertEqual(calls,[([11],[4]),(list(range(16,22)),[6])])
                        self.assertTrue(torch.equal(out[:1],q[:1]+4))
                        self.assertTrue(torch.equal(out[1:],q[1:]+6))
                        self.assertEqual([e['event'] for e in events],
                                         ['mixed_native_c2_completed']*2)
                        self.assertTrue(all(e['skipped_body_queries']==0 for e in events))
                    self.assertEqual(native.num_decodes,1)
                finally:stop()
                self.assertIs(Backend.forward,original)
        finally:
            CURRENT_REQUEST_SLICES.reset(req_token)
            CURRENT_COMPACT_MODEL.reset(model_token)
    def test_actual_wrapper_native_paths_do_not_acquire_public_material(self):
        self.run_case()
    def test_late_bad_lease_prevents_all_backend_calls(self):
        self.run_case(True)

if __name__=='__main__':unittest.main()
