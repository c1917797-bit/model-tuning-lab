"""Software protocol fixtures only; no Torch, native load, or NPU execution."""
import ast
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("damp_cache_identity_adapter_test_v1", HERE/"adapter.py")
a = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = a
spec.loader.exec_module(a)
c = a.c

def view(offset=0, shape=(16, 4), strides=(4, 1), kind="gdn", layer="g", region="high"):
    return c.View(layer, region, kind, 0, 10000, 4096, offset, shape, strides, 4,
                  "torch.float32", "npu:0")

def request(blocks=((3,), (7,))):
    return NS(prompt_token_ids=[1, 2], prompt_is_token_ids=None, prompt_embeds=None,
              mm_features=[], block_ids=blocks, num_computed_tokens=0)

def scheduler(**overrides):
    data = dict(finished_req_ids=set(), scheduled_cached_reqs=NS(
        req_ids=[], new_block_ids=[], num_computed_tokens=[], resumed_req_ids=set()),
        scheduled_spec_decode_tokens={}, scheduled_new_reqs=[], num_scheduled_tokens={},
        new_block_ids_to_zero=None)
    data.update(overrides)
    return NS(**data)

def fixture_owner():
    o = object.__new__(a.Owner)
    o.retired = False
    o.groups = {0: (("g",), 1, 1, 1), 1: (("f",), 4, 16, 64)}
    o.layers = {"g": ("gdn", 0), "f": ("fa", 1)}
    o.views = {"g": (view(),), "f": (view(1024, (64, 8), (8, 1), "fa", "f", "K"),)}
    r = request()
    o.leases = {"g": NS(records={3: ("paused", id(r), 9)})}
    return o, NS(requests={"paused": r}), r

class ContractTests(unittest.TestCase):
    def test_distinct_slots_can_overlap_cross_layer_bytes(self):
        left = view(offset=64).blocks((0,), "g:req", True)
        right = view(offset=0, kind="fa", layer="f").blocks((4,), "f:req", False)
        with self.assertRaises(c.Pending):
            c.check_spans(left+right)

    def test_distinct_storage_ids_still_address_alias(self):
        spans = (c.Span(100, 120, "a", True, "gdn"), c.Span(110, 130, "b", False, "fa"))
        with self.assertRaises(c.Pending):
            c.check_spans(spans)

    def test_read_read_overlap_allowed(self):
        self.assertTrue(c.check_spans((c.Span(100,120,"a",False,"fa"), c.Span(110,130,"b",False,"fa"))))

    def test_same_request_region_read_write_allowed(self):
        self.assertTrue(c.check_spans(view().blocks((1,), "g:high:r", False)+
                                     view().blocks((1,), "g:high:r", True)))

    def test_different_request_same_slot_rejected(self):
        with self.assertRaises(c.Pending):
            c.check_spans(view().blocks((1,), "g:high:r1", False)+
                          view().blocks((1,), "g:high:r2", True))

    def test_adjacent_byte_ranges_not_alias(self):
        self.assertTrue(c.check_spans((c.Span(100,120,"a",True,"gdn"), c.Span(120,140,"b",True,"fa"))))

    def test_stride_padding_used_not_dense_width(self):
        v = view(shape=(2,4),strides=(8,1))
        self.assertEqual([(s.begin,s.end) for s in v.blocks((0,1),"x",True)], [(10000,10016),(10032,10048)])

    def test_noncontiguous_inner_rejected(self):
        with self.assertRaises(c.Pending):
            view(shape=(2,2,2),strides=(4,1,2)).validate()

    def test_outer_stride_overlap_rejected(self):
        with self.assertRaises(c.Pending):
            view(shape=(2,4),strides=(2,1)).validate()

    def test_complete_storage_bound(self):
        with self.assertRaises(c.Pending):
            view(offset=4090).validate()

    def test_negative_dummy_block_rejected(self):
        with self.assertRaises(c.Pending):
            view().blocks((-1,), "x", True)

    def test_bool_block_rejected(self):
        with self.assertRaises(c.Pending):
            c.physical_to_logical((True,), 1)

    def test_exact_physical_logical_conversion(self):
        self.assertEqual(c.physical_to_logical((2,5),4), (8,9,10,11,20,21,22,23))

    def test_fa_read_write_and_slots_cross_block(self):
        self.assertEqual(c.fa_blocks((8,9,20),16,15,3), ((8,9),(8,9),(143,144,145)))

    def test_fa_short_table_rejected(self):
        with self.assertRaises(c.Pending):
            c.fa_blocks((8,),16,15,2)

    def test_zero_uses_physical_page_ratio(self):
        v = view(1024,(64,8),(8,1),"fa","f","K")
        spans = c.zero_spans(((v,11024),),128,(2,))
        self.assertEqual((spans[0].begin,spans[0].end), (11280,11408))

    def test_zero_alias_live_same_fa_rejected(self):
        v = view(1024,(64,8),(8,1),"fa","f","K")
        with self.assertRaises(c.Pending):
            c.check_spans(c.zero_spans(((v,11024),),128,(2,))+v.blocks((8,),"f:K:r",False))

    def test_zero_cannot_leave_raw_storage(self):
        v = view(1024,(64,8),(8,1),"fa","f","K")
        with self.assertRaises(c.Pending):
            c.zero_spans(((v,11024),),128,(40,))

    def test_pause_retains_gdn_and_fa_allocation(self):
        o, runner, _ = fixture_owner()
        spans = o._retained(runner, frozenset())
        self.assertEqual(len(spans), 5) # GDN plus all four logical FA blocks
        self.assertTrue(any(s.owner.endswith(":paused") and s.kind=="gdn" for s in spans))

    def test_exact_finish_releases_not_pause(self):
        o, runner, _ = fixture_owner()
        self.assertEqual(o._retained(runner, frozenset({"paused"})), [])

    def test_recycled_generation_rejected(self):
        o, runner, _ = fixture_owner()
        runner.requests["paused"] = request()
        with self.assertRaises(c.Pending):
            o._retained(runner, frozenset())

    def test_relocated_gdn_slot_rejected(self):
        o, runner, r = fixture_owner()
        r.block_ids = ((4,), (7,))
        with self.assertRaises(c.Pending):
            o._retained(runner, frozenset())

    def test_append_preserves_actual_native_identity(self):
        o, runner, r = fixture_owner()
        sched = scheduler(scheduled_cached_reqs=NS(req_ids=["paused"],new_block_ids=[((),(8,))],
                 num_computed_tokens=[9],resumed_req_ids=set()),num_scheduled_tokens={"paused":1})
        _, predicted = o._requests(runner,sched)
        self.assertEqual(predicted["paused"], (id(r), ((3,),(7,8)),9))
        self.assertEqual(r.block_ids, ((3,),(7,))) # observer did not mutate cache state

    def test_preemption_fail_before_native(self):
        o, runner, _ = fixture_owner()
        sched = scheduler(scheduled_cached_reqs=NS(req_ids=["paused"],new_block_ids=[None],
                 num_computed_tokens=[9],resumed_req_ids={"paused"}))
        with self.assertRaises(c.Pending):
            o._requests(runner,sched)

    def test_finished_external_id_can_be_new_generation(self):
        o, runner, _ = fixture_owner()
        new = request(((6,),(8,)));new.req_id="paused";new.num_computed_tokens=0
        finished,predicted=o._requests(runner,scheduler(finished_req_ids={"paused"},
                           scheduled_new_reqs=[new],num_scheduled_tokens={"paused":2}))
        self.assertEqual(finished,frozenset({"paused"}))
        self.assertIsNone(predicted["paused"][0])

    def test_prompt_masks(self):
        for mask in (None,[True,True]):
            r=request();r.prompt_is_token_ids=mask;c.prompt_only(r)
        for mask in ([True,False],[True],[1,True]):
            r=request();r.prompt_is_token_ids=mask
            with self.assertRaises(c.Pending): c.prompt_only(r)

    def test_multimodal_fail_closed(self):
        r=request();r.mm_features=[object()]
        with self.assertRaises(c.Pending):c.prompt_only(r)

class SeamTests(unittest.TestCase):
    def test_update_order_and_native_return_unchanged(self):
        calls=[];runner=object();sched=object();result=object()
        owner=NS(before_update=lambda r,s:calls.append(("before",r,s)),
                 after_update=lambda r,s:calls.append(("after",r,s)),retire=lambda:calls.append(("retired",)))
        def native(r,s):calls.append(("native-zero",r,s));return result
        self.assertIs(a.wrap_update(native,lambda r:owner)(runner,sched),result)
        self.assertEqual([x[0] for x in calls],["before","native-zero","after"])
        self.assertTrue(all(x[1:] == (runner,sched) for x in calls))

    def test_pending_never_calls_native_writer(self):
        calls=[]
        def pending(r,s):raise c.Pending("missing actual source-bound receipt")
        owner=NS(before_update=pending,retire=lambda:calls.append("retired"))
        with self.assertRaises(c.Pending):
            a.wrap_update(lambda r,s:calls.append("native"),lambda r:owner)(object(),object())
        self.assertEqual(calls,["retired"])

    def test_default_off_does_not_inspect_or_modify_classes(self):
        cls=type("Empty",(),{})
        self.assertFalse(a.install_runner_update(cls,lambda r:None))
        self.assertFalse(a.install_zeroer_init(cls,lambda r:None))
        self.assertNotIn("_update_states",cls.__dict__)

    def test_unowned_native_call_preserved(self):
        token=object()
        self.assertIs(a.wrap_update(lambda r,s:token,lambda r:None)(object(),object()),token)

    def test_zeroer_iterable_consumed_once_native_return_kept(self):
        calls=[];token=object();z=object();groups=[object(),object()]
        owner=NS(before_zeroer_init=lambda *args:calls.append(("before",args)),
                 after_zeroer_init=lambda:calls.append(("after",)),retire=lambda:calls.append(("retired",)))
        def native(*args):calls.append(("native",args));return token
        wrapped=a.wrap_zeroer_init(native,lambda x:owner)
        self.assertIs(wrapped(z,iter(groups),[[16]],"auto",set(),{}),token)
        self.assertEqual([x[0] for x in calls],["before","native","after"])
        self.assertEqual(calls[1][1][1],tuple(groups))

    def test_partial_core_never_commits(self):
        owner=NS(retired=False,retire=lambda:None)
        token=a.AdmittedTurn(owner,object(),{"g":object()},
                             {"g":NS(metadata_id=id(owner))})
        with self.assertRaises(c.Pending):token.writer_started("g")

    def test_complete_layer_protocol_no_success_claim(self):
        native=object();turn=object();retired=[]
        owner=NS(retired=False,retire=lambda:retired.append(True))
        admitted=a.AdmittedTurn(owner,object(),{"g":turn},{"g":NS(metadata_id=id(native))})
        self.assertIs(admitted.require_layer("g",native),turn)
        admitted.before_writer("g",turn,native);admitted.writer_started("g");admitted.layer_succeeded("g")
        with self.assertRaises(c.Pending):admitted.layer_succeeded("g")
        self.assertFalse(admitted.ready);self.assertFalse(admitted.npu_executed)
        self.assertFalse(admitted.performance_measurement_admitted)
        admitted.retire("g","test exception",retry_allowed=False)
        self.assertEqual(retired,[True])

    def test_no_cache_content_or_torch_load(self):
        tree=ast.parse((HERE/"adapter.py").read_text())
        imports=[n for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom))]
        self.assertFalse(any("torch" in ast.unparse(n) for n in imports))
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
        self.assertFalse(any(n.func.attr in ("cpu","clone","tolist","copy_","deepcopy") for n in calls))

if __name__=="__main__":
    unittest.main()
