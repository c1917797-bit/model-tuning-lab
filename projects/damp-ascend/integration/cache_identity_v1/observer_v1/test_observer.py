"""Software fixtures, not native runner/metadata/NPU validation."""
import importlib.util
import inspect
from pathlib import Path
import sys
import types
import unittest

P = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("damp_observer_v1_tested", P/"observer.py")
m = importlib.util.module_from_spec(spec); sys.modules[spec.name] = m; spec.loader.exec_module(m)
cp = P.parent.parent/"continuous_metadata_v1/contract.py"
spec = importlib.util.spec_from_file_location("damp_observer_cont_tested", cp)
cont = importlib.util.module_from_spec(spec); sys.modules[spec.name] = cont; spec.loader.exec_module(cont)

class Tensor:
    def __init__(self, values, device="cpu", dtype="torch.int32", storage=1, pointer=1):
        self.values, self.device, self.dtype = values, device, dtype
        self.shape = (len(values), len(values[0])) if values and isinstance(values[0], list) else (len(values),)
        self.storage, self.pointer = storage, pointer
    def tolist(self): return self.values
    def cpu(self): raise AssertionError("no preview D2H")
    def untyped_storage(self): return types.SimpleNamespace(data_ptr=lambda:self.storage,nbytes=lambda:4096)
    def data_ptr(self): return self.pointer
    def nbytes(self): return 4096
    def stride(self): return (self.shape[1],1) if len(self.shape) == 2 else (1,)

class Contract(unittest.TestCase):
    def turn(self):
        return cont.plan((cont.Row("d",2,1,9,5,99),cont.Row("p",6,4,3,12,101)),
                         (0,1,5),10)
    def test_cpu_does_not_read_device(self):
        with self.assertRaises(m.Pending): m.cpu_list(Tensor([1],"npu:0"))
    def test_cpu_dtype(self):
        with self.assertRaises(m.Pending): m.cpu_list(Tensor([1],dtype="torch.int64"),"torch.int32")
    def test_slots_kernel_rule_with_block_split(self):
        self.assertEqual(m.derived_fa_slots(((6,4),(1,1)),(0,4,5),((20,21,22),(7,)),4),
                         [21*4+2,21*4+3,22*4,22*4+1,7*4+1])
    def test_slots_reject_missing_alloc(self):
        with self.assertRaises(m.Pending): m.derived_fa_slots(((5,1),),(0,1),((4,),),4)
    def test_slots_reject_bad_boundary(self):
        with self.assertRaises(m.Pending): m.derived_fa_slots(((1,1),),(0,2),((4,),),4)
    def test_bool_index_reject(self):
        with self.assertRaises(m.Pending): m.derived_fa_slots(((1,1),),(0,1),((True,),),4)
    def test_gdn_mixed_mirror(self):
        mirror=m.gdn_mirror(self.turn(),[[2],[6]])
        self.assertEqual(mirror["provenance"],"derived_not_device_observed")
        self.assertEqual(mirror["decode_actual_seq_lengths"],[0,1])
        self.assertEqual(mirror["prefill_starts"],[0,4])
        self.assertEqual(mirror["conv_has_initial"],[True,True])
        self.assertTrue(cont.verify_native(self.turn(),mirror))
    def test_gdn_no_cumulative_decode(self):
        rows=(cont.Row("a",2,1,9,5,99),cont.Row("b",3,1,10,6,100))
        mirror=m.gdn_mirror(cont.plan(rows,(0,1,2),10),[[2],[3]])
        self.assertEqual(mirror["decode_actual_seq_lengths"],[0,1,1])
        self.assertNotIn("conv_has_initial",mirror)
    def test_gdn_fresh_and_continuation(self):
        turn=cont.plan((cont.Row("c",2,1,3,4,99),cont.Row("fresh",4,1,0,5,100)),(0,1,2),8)
        mirror=m.gdn_mirror(turn,[[2],[4]])
        self.assertEqual(mirror["num_decodes"],1)
        self.assertEqual(mirror["conv_has_initial"],[True,False])
        self.assertEqual(mirror["prefill_has_initial"],[False])
    def test_descriptor_host_only(self):
        a=Tensor([1],"npu:0",storage=9,pointer=9)
        d=m.descriptor(a)
        self.assertEqual(d["object_id"],id(a))
    def test_storage_mismatch_reject(self):
        a,b=Tensor([1],"npu:0",storage=9),Tensor([1],"npu:0",storage=10)
        with self.assertRaises(m.Pending): m.same_storage(a,b)
    def test_fa_actual_seq_result_is_cpu_not_assumed_npu(self):
        seq=Tensor([12],device="cpu")
        common=types.SimpleNamespace(seq_lens=Tensor([12],device="npu:0"))
        md=types.SimpleNamespace(seq_lens=seq,query_start_loc=Tensor([0,1],device="npu:0"),
                                 slot_mapping=Tensor([3],device="npu:0"))
        event=m.Event("fa",1,("f",),md,common,{"request_ids":["x"]},{})
        old=m.read_metadata
        observed=[]
        def fixture(tensor):
            self.assertEqual(tensor.device,"npu:0");observed.append(tensor);return tensor.values
        m.read_metadata=fixture
        try: value=m.device_values(event)
        finally:m.read_metadata=old
        self.assertEqual(value["seq_lens"],[12]);self.assertIn(common.seq_lens,observed)
        self.assertNotIn(seq,observed)
    def test_exact_compare_reject_missing_field(self):
        with self.assertRaises(m.Pending): m.compare_values({"provenance":"derived_not_device_observed","x":[1]},{})
    def test_exact_compare_pass_no_success_selfclaim(self):
        self.assertTrue(m.compare_values({"provenance":"derived_not_device_observed","x":[1]},{"x":[1]}))
    def test_checked_default_reject_before_device_read(self):
        p=object.__new__(m.Producer)
        with self.assertRaises(m.Pending): p.checked_admission(None)
    def test_checked_mismatch_retains_diagnostic_values(self):
        p=object.__new__(m.Producer);ticket=object();retired=[]
        p.owner=types.SimpleNamespace(ticket=ticket,retire=lambda:retired.append(True))
        event=m.Event("fa",1,("f",),object(),None,{"provenance":"derived_not_device_observed","x":[1]}, {})
        p.preview=m.Preview(7,8,ticket,{},(event,),{},{});p.last_comparison=None;p.last_failure=None
        old=m.device_values;m.device_values=lambda e:{"x":[2]}
        try:
            with self.assertRaises(m.Pending):p.checked_admission(p.preview,mode="checked-diagnostic")
        finally:m.device_values=old
        self.assertEqual(p.last_failure["comparison"]["actual"],{"x":[2]})
        self.assertEqual(p.last_failure["status"],"failed");self.assertEqual(retired,[True])
        self.assertFalse(p.last_failure["ready"])
    def test_formal_always_pending(self):
        p=object.__new__(m.Producer)
        with self.assertRaises(m.Pending): p.pending_formal()
    def test_preview_not_ready(self):
        p=m.Preview(1,2,None,{},(),{}, {})
        self.assertFalse(p.ready);self.assertFalse(p.npu_executed)
        self.assertFalse(p.performance_measurement_admitted)
    def test_install_default_off_does_not_touch_classes(self):
        class C: pass
        self.assertFalse(m.install(C,C,C,C,lambda _:None,lambda _:None))
        self.assertEqual(C.__dict__.get("build"),None)
    def test_commit_original_exact_args_result(self):
        calls=[];sentinel=object();table=object()
        def native(t,n): calls.append((t,n));return sentinel
        result=m.wrap_commit(native,lambda _:None)(table,3)
        self.assertIs(result,sentinel);self.assertEqual(calls,[(table,3)])
    def test_commit_observe_precedes_native(self):
        events=[];table=object();sentinel=object()
        p=types.SimpleNamespace(observe_commit=lambda t,n:events.append(("cpu",t,n)),owner=types.SimpleNamespace(retire=lambda:events.append("retire")))
        def native(t,n): events.append(("native",t,n));return sentinel
        self.assertIs(m.wrap_commit(native,lambda _:p)(table,2),sentinel)
        self.assertEqual([e[0] for e in events],["cpu","native"])
    def test_commit_failure_retires_no_retry(self):
        events=[]
        p=types.SimpleNamespace(observe_commit=lambda *a:None,owner=types.SimpleNamespace(retire=lambda:events.append("retire")))
        def native(t,n):events.append("native");raise RuntimeError("original failed")
        with self.assertRaises(RuntimeError):m.wrap_commit(native,lambda _:p)(object(),2)
        self.assertEqual(events,["native","retire"])
    def test_builder_original_exact_defaults_result(self):
        calls=[];sentinel=object();builder=object();common=object()
        def native(self,common_prefix_len,common_attn_metadata,fast_build=False):
            calls.append((self,common_prefix_len,common_attn_metadata,fast_build));return sentinel
        wrapped=m.wrap_builder(native,"fa")
        self.assertIs(wrapped(builder,0,common,fast_build=False),sentinel)
        self.assertEqual(calls,[(builder,0,common,False)])
    def test_builder_actual_one_call_group_not_fake64(self):
        events=[];sentinel=object();builder=object();common=object()
        p=types.SimpleNamespace(input=lambda *a: events.append("input") or "prepared",
                                output=lambda *a: events.append(("output",a[2])))
        def native(self,common_prefix_len,common_attn_metadata,fast_build=False):
            events.append("native");return sentinel
        token=m._ACTIVE.set(p)
        try: result=m.wrap_builder(native,"fa")(builder,0,common)
        finally: m._ACTIVE.reset(token)
        self.assertIs(result,sentinel);self.assertEqual(events,["input","native",("output",sentinel)])
    def test_runner_original_result_unchanged_no_observer(self):
        runner=object();sentinel=object();calls=[]
        def native(self,num_tokens): calls.append((self,num_tokens));return sentinel
        self.assertIs(m.wrap_runner(native,lambda _:None)(runner,5),sentinel)
        self.assertEqual(calls,[(runner,5)])
    def finish_fixture(self):
        p=object.__new__(m.Producer)
        g=tuple("g"+str(i) for i in range(48));f=tuple("f"+str(i) for i in range(16))
        gmd,fmd=object(),object()
        p.owner=types.SimpleNamespace(layers={**{n:("gdn",0) for n in g},**{n:("fa",1) for n in f}})
        p.events=[m.Event("gdn",1,g,gmd,None,{},{}),m.Event("fa",2,f,fmd,None,{}, {})]
        p.turns={n:None for n in g};p.active=True;p.serial=1;p.runner=object();p.ticket=object()
        return p,{**{n:gmd for n in g},**{n:fmd for n in f}}
    def test_finish_actual_group_mapping_not64events(self):
        p,mapping=self.finish_fixture();preview=p.finish((mapping,None))
        self.assertEqual(len(preview.events),2);self.assertEqual(len(preview.by_layer),64)
        self.assertEqual(p.commits,{})
        self.assertFalse(preview.ready)
    def test_finish_missing_actual_group_rejects(self):
        p,mapping=self.finish_fixture();p.events.pop()
        with self.assertRaises(m.Pending):p.finish((mapping,None))
    def test_finish_foreign_md_alias_rejects(self):
        p,mapping=self.finish_fixture();mapping["g0"]=object()
        with self.assertRaises(m.Pending):p.finish((mapping,None))
    def test_finish_list_ubatch_rejects(self):
        p,mapping=self.finish_fixture()
        with self.assertRaises(m.Pending):p.finish(([mapping],None))
    def test_source_no_torch_and_only_diagnostic_d2h(self):
        text=(P/"observer.py").read_text()
        self.assertNotIn("import torch",text)
        self.assertEqual(text.count(".detach().cpu()"),1)
        self.assertNotIn(".clone()",text)
    def test_snapshot_manifest_no_pass_claim(self):
        import json
        source=json.loads((P/"SOURCE_MANIFEST.json").read_text())
        self.assertEqual(source["status"],"source-prepared-not-runner-observed")
        self.assertFalse(source["npu_executed"])
        self.assertFalse(source["serve_ready"])
if __name__=="__main__": unittest.main()
