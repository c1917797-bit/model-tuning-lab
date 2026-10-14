"""Draft C2 hot wrapper CPU sandtable; official backend/source are doubles."""
import sys
import unittest
from contextlib import ExitStack,contextmanager
from types import ModuleType,SimpleNamespace
from unittest.mock import patch
import torch
from experimental_c2_layer_barrier import install_compact_c2
from independent_compact_model_hook import CURRENT_COMPACT_MODEL,CompactModelSelection
from independent_runner_context import CURRENT_REQUEST_SLICES
from independent_request_map import RequestSlice
from independent_cache_map import CacheSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_hybrid_material import MaterialIdentity
from test_independent_c2_metadata import metadata

class HotBarrier(unittest.TestCase):
    def run_case(self,bad=False):
        calls=[];events=[];syncs=[];lease=[False]
        class Backend:
            num_kv_heads=1;head_size=256
            def forward(self,layer,q,k,v,cache,meta,out=None,*args):
                calls.append((meta.slot_mapping.tolist(),meta.seq_lens_list))
                out.copy_(q+meta.seq_lens_list[0]);return out
        original=Backend.forward
        module=ModuleType("vllm_ascend.attention.attention_v1")
        module.AscendAttentionBackendImpl=Backend
        module.AscendAttentionState=SimpleNamespace(PrefillCacheHit="paged")
        data={"keys":torch.ones(5,1,256),"values":torch.full((5,1,256),2.),
              "positions":torch.arange(3,8)}
        if bad:data["keys"][0,0,0]=float("nan")
        @contextmanager
        def acquire(key):
            lease[0]=True
            try:yield 1,data
            finally:lease[0]=False
        stage=SimpleNamespace(identity=lambda layer,rank:MaterialIdentity("m","c",layer,rank,"a"*64,8,3),
            compact_kv_store=SimpleNamespace(acquire_private=acquire))
        req=RequestSlice("r",0,4,0,12,0,0,12)
        plan=plan_c2_queries(req,SegmentSelection(2,10,False,"x"),seam_tokens=3,public_length=8)
        slots=tuple(range(12));cache=CacheSlice("r",0,4,0,0,4,(0,1,2),slots)
        selected=CompactModelSelection((plan,),(0,11),False,(cache,),((0,("layer",)),),(("r",0,slots),))
        native=metadata();native.num_prefills=1
        native.block_tables=torch.tensor([[0,1,2]],dtype=torch.int32)
        q=torch.arange(7*256).reshape(7,256).float();out=torch.full_like(q,-1)
        kv=(torch.zeros(3,4,1,256),torch.zeros(3,4,1,256))
        token=CURRENT_COMPACT_MODEL.set(selected);request_token=CURRENT_REQUEST_SLICES.set(("fixture",))
        def emit(event):
            self.assertTrue(lease[0]);self.assertEqual(syncs,["complete"]);events.append(event)
        try:
            with ExitStack() as stack:
                stack.enter_context(patch.dict(sys.modules,{module.__name__:module}))
                stack.enter_context(patch("experimental_c2_layer_barrier.inspect.getfile",return_value=__file__))
                stack.enter_context(patch("experimental_c2_layer_barrier.Path.read_bytes",return_value=b"source-double"))
                stack.enter_context(patch("experimental_c2_layer_barrier.hashlib.sha256",
                    return_value=SimpleNamespace(hexdigest=lambda:"80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390")))
                stack.enter_context(patch.object(torch,"npu",SimpleNamespace(synchronize=lambda:syncs.append("complete")),create=True))
                stop=install_compact_c2(stage,enabled=True,emit=emit)
                try:
                    run=lambda:Backend().forward(SimpleNamespace(layer_name="layer"),q,q,q,kv,native,out)
                    if bad:
                        with self.assertRaises(ValueError):run()
                        self.assertEqual(calls,[]);self.assertEqual(events,[])
                        self.assertEqual(syncs,[]);self.assertTrue((kv[1]==0).all())
                    else:
                        run();self.assertEqual(calls,[(list(range(5)),[5]),([10,11],[12])])
                        self.assertTrue(torch.equal(out[:5],q[:5]+5))
                        self.assertTrue(torch.equal(out[5:],q[5:]+12))
                        self.assertTrue((kv[1].reshape(12,1,256)[5:10]==2).all())
                        self.assertEqual(len(events),1)
                        self.assertEqual(events[0]["skipped_body_queries"],5)
                        self.assertEqual(syncs,["complete"])
                finally:stop()
                self.assertIs(Backend.forward,original)
        finally:
            CURRENT_REQUEST_SLICES.reset(request_token);CURRENT_COMPACT_MODEL.reset(token)
        self.assertFalse(lease[0])
    def test_hot_kv_seam_suffix_before_single_receipt_barrier(self):self.run_case()
    def test_nonfinite_hot_material_rejected_before_backend(self):self.run_case(True)

if __name__=="__main__":unittest.main()
