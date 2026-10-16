"""Runtime integration controls without importing Torch or allocating an NPU."""
import sys,types,unittest
from unittest.mock import patch
from independent_runtime_adapter import freeze_native_runner
from independent_runner_context import CURRENT_PROMPT_TOKENS
from independent_compact_activation import snapshot_install_route

class Runner:pass
class Array:
    def __init__(self,rows):self.rows=rows
    def __getitem__(self,key):return Array(self.rows[key])
    def tolist(self):return self.rows
class NoIter:
    def __len__(self):return 32768
    def __iter__(self):raise AssertionError("completed decode prompt copied")
class Tests(unittest.TestCase):
    def runner(self,tokens,computed,scheduled):
        r=Runner();ids=tuple("r"+str(i) for i in range(len(tokens)))
        r.input_batch=types.SimpleNamespace(req_ids=ids,num_computed_tokens_cpu=computed)
        r.requests={rid:types.SimpleNamespace(prompt_token_ids=t,mm_features=[]) for rid,t in zip(ids,tokens)}
        boundaries=[0]
        for x in scheduled:boundaries.append(boundaries[-1]+x)
        r.query_start_loc=types.SimpleNamespace(cpu=Array(boundaries))
        return r
    def freeze(self,r,scheduled,flag=False):
        m=types.ModuleType("vllm.distributed")
        m.get_tp_group=lambda:types.SimpleNamespace(world_size=4,rank_in_group=2)
        with patch.dict(sys.modules,{"vllm.distributed":m}):
            return freeze_native_runner(r,(None,scheduled),{},prefill_prompt_snapshot=flag)
    def test_default_original(self):
        r=self.runner([[1,2,3]],[4],[1]);rows=self.freeze(r,[1])
        self.assertEqual(CURRENT_PROMPT_TOKENS.get()["r0"],(1,2,3))
        self.assertEqual((rows[0].rank,rows[0].computed_tokens),(2,4))
    def test_complete_decode_no_iteration(self):
        r=self.runner([NoIter()],[32768],[1]);self.freeze(r,[1],True)
        self.assertIsNone(CURRENT_PROMPT_TOKENS.get()["r0"])
    def test_mixed_preserves_prefill(self):
        r=self.runner([NoIter(),[4,5,6]],[32769,1],[1,2])
        rows=self.freeze(r,[1,2],True)
        self.assertEqual(dict(CURRENT_PROMPT_TOKENS.get()),{"r0":None,"r1":(4,5,6)})
        self.assertEqual([(x.token_start,x.token_end) for x in rows],[(0,1),(1,3)])
    def test_last_prompt_token_retained(self):
        r=self.runner([[4,5,6]],[2],[1]);self.freeze(r,[1],True)
        self.assertEqual(CURRENT_PROMPT_TOKENS.get()["r0"],(4,5,6))
    def test_multitoken_retained(self):
        r=self.runner([[4,5,6]],[3],[2]);self.freeze(r,[2],True)
        self.assertEqual(CURRENT_PROMPT_TOKENS.get()["r0"],(4,5,6))
    def test_step_identity_unchanged(self):
        r=self.runner([[4,5,6]],[3],[1])
        a=self.freeze(r,[1],True);b=self.freeze(r,[1],False)
        self.assertEqual(b[0].step,a[0].step+1)
        self.assertEqual(CURRENT_PROMPT_TOKENS.get()["r0"],(4,5,6))
    def test_bad_switch(self):
        r=self.runner([[1]],[1],[1])
        for value in (1,0,"true",None):
            with self.assertRaises(ValueError):self.freeze(r,[1],value)
    def test_route_default_and_copy(self):
        original={"x":3};out,flag=snapshot_install_route(original)
        self.assertFalse(flag);self.assertEqual(out,original);self.assertIsNot(out,original)
    def test_route_enabled_consumed(self):
        original={"prefill_prompt_snapshot":True,"x":3}
        out,flag=snapshot_install_route(original)
        self.assertTrue(flag);self.assertEqual(out,{"x":3});self.assertIn("prefill_prompt_snapshot",original)
    def test_route_invalid(self):
        for value in (1,0,"true",None):
            with self.assertRaises(ValueError):snapshot_install_route({"prefill_prompt_snapshot":value})
    def test_installed_runner_receives_switch_and_owned_stop(self):
        from independent_compact_runtime_snapshot import activate_compact_runner
        package=types.ModuleType("vllm_ascend");package.__path__=[]
        ops=types.ModuleType("vllm_ascend.ops");package.ops=ops
        worker=types.ModuleType("vllm_ascend.worker");worker.__path__=[]
        model=types.ModuleType("vllm_ascend.worker.model_runner_v1")
        model.NPUModelRunner=Runner
        modules={"vllm_ascend":package,"vllm_ascend.ops":ops,
                 "vllm_ascend.worker":worker,"vllm_ascend.worker.model_runner_v1":model}
        captured={};stops=[]
        def install(cls,freeze,**kwargs):
            captured["freeze"]=freeze
            self.assertTrue(kwargs["enabled"])
            return lambda:stops.append("owned")
        with patch.dict(sys.modules,modules),patch("independent_runner_context.install_runner_context",install):
            stop=activate_compact_runner(enabled=True,prefill_prompt_snapshot=True)
        r=self.runner([NoIter()],[32768],[1])
        group=types.ModuleType("vllm.distributed")
        group.get_tp_group=lambda:types.SimpleNamespace(world_size=4,rank_in_group=2)
        with patch.dict(sys.modules,{"vllm.distributed":group}):
            captured["freeze"](r,(None,[1]),{})
        self.assertIsNone(CURRENT_PROMPT_TOKENS.get()["r0"])
        stop();self.assertEqual(stops,["owned"])
    def test_disabled_runner_import_free(self):
        from independent_compact_runtime_snapshot import activate_compact_runner
        activate_compact_runner(enabled=False,prefill_prompt_snapshot=True)()
if __name__=="__main__":unittest.main()
