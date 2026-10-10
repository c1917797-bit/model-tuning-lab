"""Source-only guards and exact actual attention closure with fake transport.
No model loading, torch, native kernel, device, or remote execution.
"""
import argparse
import ast
import copy
import hashlib
import importlib.util
import inspect
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent
DEPS = None


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


I = load("_actual_timing_installer", ROOT / "installer.py")


class Array:
    def __init__(self, values):
        self.values = list(values)
    def __getitem__(self, item):
        return Array(self.values[item]) if isinstance(item, slice) else self.values[item]
    def tolist(self):
        return list(self.values)


class Tensor:
    def __init__(self, shape=(2,), values=(0, 1), dtype="int32", device="npu",
                 base=4096, offset=0, trace=None):
        self.shape, self.values = tuple(shape), tuple(values)
        self.dtype = dtype
        self.device = types.SimpleNamespace(type=device)
        self.base, self.offset = base, offset
        self.trace = [] if trace is None else trace
    @property
    def ndim(self):
        return len(self.shape)
    def stride(self):
        return (1,) if self.ndim == 1 else (self.shape[-1], 1)
    def is_contiguous(self):
        return True
    def untyped_storage(self):
        return types.SimpleNamespace(data_ptr=lambda: self.base, nbytes=lambda: 4096)
    def data_ptr(self):
        return self.base + 4 * self.offset
    def storage_offset(self):
        return self.offset
    def __getitem__(self, item):
        result = copy.copy(self)
        result.values = self.values[item]
        result.shape = (len(result.values),)
        return result
    def pin_memory(self):
        return self
    def to(self, device, *, non_blocking=False):
        kind = device if isinstance(device, str) else device.type
        self.trace.append(("observer_d2h",) if kind == "cpu" else ("native_h2d",))
        return Tensor(self.shape, self.values, self.dtype, kind, self.base + 65536, self.offset, self.trace)
    def tolist(self):
        if self.device.type != "cpu":
            raise AssertionError("implicit device read")
        return list(self.values)
    def reshape(self, *shape):
        result = copy.copy(self)
        result.shape = tuple(shape)
        return result
    def contiguous(self):
        return self


TORCH = types.SimpleNamespace(int32="int32", npu=types.SimpleNamespace(is_current_stream_capturing=lambda: False))


def partition_fixture(trace=None):
    cpu = Tensor(device="cpu", trace=trace)
    gpu = Tensor(trace=trace)
    runner = types.SimpleNamespace(query_start_loc=types.SimpleNamespace(cpu=cpu, gpu=gpu, np=Array((0, 1))))
    layer = Tensor(base=65536, trace=trace)
    meta = types.SimpleNamespace(causal=True, num_actual_tokens=1, query_start_loc=layer, actual_seq_lengths_q=[1])
    frame = {"epoch": 1, "req_ids": ["fixture"], "total_tokens": 1, "query_start_loc": [0, 1]}
    return runner, meta, frame


def descriptor(tensor):
    return {"shape": list(tensor.shape), "base": tensor.base, "offset": tensor.offset, "dtype": tensor.dtype,
            "logical_bytes": 8}


def proof(meta, frame):
    return {"epoch": frame["epoch"], "meta": meta, "query": meta.query_start_loc,
            "starts": list(frame["query_start_loc"]), "query_descriptor": descriptor(meta.query_start_loc)}


def layout_fixture():
    objects, layers, contexts = {}, {}, {}
    for index in range(64):
        name = "model.layers.%d.attn" % index
        tensors = (Tensor(base=(index * 2 + 1) * 4096), Tensor(base=(index * 2 + 2) * 4096))
        objects[name] = types.SimpleNamespace(kv_cache=tensors)
        kind = "FA" if index % 4 == 3 else "GDN"
        layers[name] = {"kind": kind, "views": [descriptor(t) for t in tensors]}
        if kind == "FA":
            fields=("key_codes","key_scales","key_minima","value_codes","value_scales",
                    "value_minima","key_residual","value_residual","shifts")
            pool={field:Tensor(base=1024*(index+1)+32*j) for j,field in enumerate(fields)}
            pool.update(allocated_bytes=72,dense_shadow_bytes=0)
            contexts[name] = {"arena": types.SimpleNamespace(pool=pool,pool_bytes=72)}
    runner = types.SimpleNamespace(speculative_config=None,
                                   compilation_config=types.SimpleNamespace(static_forward_context=objects))
    return runner, {"layers": layers}, contexts, types.SimpleNamespace(scalar_tensor=descriptor)


def extract_factory(name="attention_factory"):
    tree = ast.parse((ROOT / "installer.py").read_text(encoding="utf-8"))
    install = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "install")
    factory = next(node for node in install.body if isinstance(node, ast.FunctionDef) and node.name == name)
    return compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])), str(ROOT / "installer.py"), "exec")


def update_fixture(boundary=False, changed_layout=False):
    trace = []
    scheduler_type = type("SchedulerOutput", (), {"__module__": "vllm.v1.core.sched.output"})
    scheduler = scheduler_type()
    scheduler.scheduled_new_reqs = []
    scheduler.finished_req_ids = ["fixture"] if boundary else []
    scheduler.scheduled_spec_decode_tokens = {}
    scheduler.preempted_req_ids = []
    scheduler.scheduled_cached_reqs = types.SimpleNamespace(resumed_req_ids=[], req_ids=[] if boundary else ["fixture"])
    ident = {"pid": 1}
    runner = types.SimpleNamespace(requests={"fixture": object()}, input_batch=types.SimpleNamespace(req_ids=["fixture"]))
    deferred = lambda: None
    def original(supplied):
        trace.append(("native_update", supplied is scheduler))
        if boundary:
            runner.requests.clear()
            runner.input_batch.req_ids.clear()
        return deferred
    def forbidden(name):
        def call(*args):
            raise AssertionError("steady token observer: " + name)
        return call
    def observer(name, value=None):
        def call(*args):
            trace.append((name,))
            return value
        return call
    contexts = {str(i): {"packed_batch": types.SimpleNamespace(
                    qualify_boundary=observer("boundary_qualify") if boundary else forbidden("qualify"),
                    invalidate=observer("invalidate"))} for i in range(16)}
    bindings = types.SimpleNamespace(owner={"rank_bindings": {"0": ident}}, seen={"fixture"},
                    check_new=observer("actual_ingress", []) if boundary else forbidden("ingress_file"))
    book_module = load("_update_mode_book_" + str(id(runner)), DEPS / "book.py")
    book = book_module.Book(["fixture"], {"fixture": 32768}, 1024)
    book.live["fixture"] = {"slot": 0, "epoch": 1, "length": 32768, "pending": None}
    state = {"active": None, "failed": False, "scheduler_type": scheduler_type, "update_seq": 0,
             "frame": {}, "frame_ref": None, "metadata_proofs": {"old": object()}}
    env = dict(vars(I), state=state, diagnostic=False, event={}, owner={"zeroer_writer_receipt_ref": "fixture"},
               layer_contexts=contexts, callback=None, initial_layout="unchanged",
               timing_layout=lambda *args: "changed" if changed_layout else "unchanged",
               identity=observer("identity", ident) if boundary else forbidden("identity"), ident=ident,
               writer_guard=observer("writer_guard") if boundary else forbidden("writer_guard"),
               publish=None, rank=0, ingress_bindings=bindings, orig_update=original,
               send=observer("boundary_publication") if boundary else forbidden("publish"), book=book,
               release=observer("native_finished_release"), layer_names=tuple(str(i) for i in range(16)))
    exec(extract_factory("update"), env)
    return runner, scheduler, deferred, env, trace


class AttentionFixture:
    def __init__(self, diagnostic):
        self.trace = []
        self.runner, self.meta, unused = partition_fixture(self.trace)
        self.meta.attn_state = State.DecodeOnly
        self.book_module = load("_mode_book_" + str(id(self)), DEPS / "book.py")
        self.book = self.book_module.Book(["fixture"], {"fixture": 32768}, 1024)
        self.book.live["fixture"] = {"slot": 0, "epoch": 1, "length": 32768, "pending": None}
        self.book.ever.add("fixture")
        self.book.epochs[0] = 1
        self.request = types.SimpleNamespace(owner="fixture", slot=0, epoch=1, length=32768, generation=1)
        native = (Tensor(base=16384), Tensor(base=20480))
        self.arena = types.SimpleNamespace(active={0: self.request}, dtype="float16", device=types.SimpleNamespace(type="npu"))
        self.arena.owned = lambda request: I.need(request is self.request and request.epoch == 1, "actual owner epoch")
        def append(arena, requests, q, k, v, positions, **kwargs):
            self.trace.append(("packed_append", tuple(r.owner for r in requests), positions, q.shape, k.shape, v.shape,
                               q.values, k.values, v.values, kwargs["capture_raw"]))
            self.trace.append(("pre_refs_present", kwargs["pre_refs"] is not None))
            return Tensor((1, 6, 256), (37,), "float16", trace=self.trace)
        batch = types.SimpleNamespace(append_read=append, hot_qualify=lambda: None, format=lambda tensor: 2)
        contexts = {"layer": {"arena": self.arena, "packed_batch": batch,
                              "before_bind_ref": "fixture-before-ref", "actual_format_ref": "fixture-format-ref"}}
        self.state = {"active": ("layer", None), "dummy_depth": 0, "frame": None,
                      "metadata_proofs": {}, "block_types": {}, "frame_ref": "fixture-frame-ref"}
        self.attn = types.SimpleNamespace(kv_cache=native)
        capture = types.SimpleNamespace(descriptor=lambda tensor, fmt: descriptor(tensor))
        event = {"layers": {"layer": {"views": [descriptor(t) for t in native]}}}
        def send(label, body):
            self.trace.append(("publish", label))
            return "fixture-only-not-an-actual-ref"
        def identity():
            self.trace.append(("identity",))
            return {"pid": 1}
        context = types.SimpleNamespace(get_forward_context=lambda: types.SimpleNamespace(attn_metadata={"layer": self.meta}))
        self.env = dict(vars(I), state=self.state, diagnostic=diagnostic, identity=identity, ident={"pid": 1},
                        layer_contexts=contexts, mixed_module=load("_current_mixed_fixture", ROOT / "mixed.py"),
                        qualify=lambda: self.trace.append(("qualify",)),
                        book_module=self.book_module, book=self.book, torch=TORCH, forward_context=context,
                        members={"layer": (None, self.attn, *native)}, capture=capture, event=event,
                        capture_raw=False, first_decode_capture_only=False, callback=types.SimpleNamespace(scalar_tensor=descriptor),
                        send=send, rank=0, raw_root=None, runner=self.runner,
                        output_event=lambda *args: self.trace.append(("output_observer",)) if diagnostic else None,
                        callable_pin=lambda *args: self.trace.append(("source_pin",)), original_prefills={}, stage_observer=None)
        exec(extract_factory(), self.env)
        self.call = self.env["attention_factory"]("layer", lambda *args, **kwargs: self.trace.append(("original_FA",)))
    def step(self):
        length = self.request.length
        frame = {"epoch": length - 32767, "req_ids": ["fixture"], "req_id_to_index": {"fixture": 0},
                 "scheduled_counts": [1], "computed_tokens": [length], "query_start_loc": [0, 1],
                 "positions": [length], "total_tokens": 1}
        frame["kind"] = self.book.plan(frame)
        self.state["frame"] = frame
        self.state["metadata_proofs"]["layer"] = proof(self.meta, frame)
        q = Tensor((1, 1536), (1, 2, 3), "float16")
        k = Tensor((1, 256), (4, 5), "float16")
        v = Tensor((1, 256), (6, 7), "float16")
        q.device = k.device = v.device = self.arena.device
        output = self.call(self.attn, q, k, v)
        self.book.live["fixture"]["length"] = length + 1
        self.book.live["fixture"]["pending"] = None
        self.request.length += 1
        self.request.generation += 1
        return output.values, output.shape


from enum import Enum
class State(Enum):
    DecodeOnly = 1
    PrefillNoCache = 2
    PrefillCacheHit = 3
    ChunkedPrefill = 4


class Tests(unittest.TestCase):
    def test01_exact_installed_runner_source_and_publication_origin(self):
        data = (DEPS / "runner-94d75.py").read_bytes()
        self.assertEqual((len(data), hashlib.sha256(data).hexdigest()),
                         (258160, "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"))
        tree = ast.parse(data)
        runner = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "NPUModelRunner")
        prepare = next(n for n in runner.body if isinstance(n, ast.FunctionDef) and n.name == "_prepare_inputs")
        text = ast.unparse(prepare)
        self.assertIn("self.query_start_loc.np[1:num_reqs + 1] = cu_num_tokens", text)
        self.assertIn("copy_snapshot_to_gpu(self.query_start_loc)", text)
        build = next(n for n in runner.body if isinstance(n, ast.FunctionDef) and n.name == "_build_attention_metadata")
        calls = [n for n in ast.walk(build) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                 and n.func.id == "AscendCommonAttentionMetadata"]
        self.assertEqual(len(calls), 1)
        keywords = {kw.arg: ast.unparse(kw.value) for kw in calls[0].keywords}
        self.assertEqual(keywords["query_start_loc"], "self.query_start_loc.gpu[:num_reqs_padded + 1]")
        self.assertEqual(keywords["query_start_loc_cpu"], "self.query_start_loc.cpu[:num_reqs_padded + 1]")

    def test02_bound_builder_copy_accepts_without_device_read(self):
        trace = []
        runner, meta, frame = partition_fixture(trace)
        I.timing_partition(TORCH, runner, meta, frame, proof(meta, frame), types.SimpleNamespace(scalar_tensor=descriptor))
        self.assertNotEqual(meta.query_start_loc.base, runner.query_start_loc.gpu.base)
        self.assertEqual(trace, [])

    def test03_partition_rejects_post_builder_changes_and_non_cpu_values(self):
        changes = (
            lambda r, m: setattr(m.query_start_loc, "base", 8192),
            lambda r, m: setattr(m.query_start_loc, "offset", 1),
            lambda r, m: setattr(m.query_start_loc, "dtype", "int64"),
            lambda r, m: setattr(m, "causal", False),
            lambda r, m: setattr(r.query_start_loc.cpu, "values", (0, 2)),
            lambda r, m: setattr(r.query_start_loc, "np", Array((0, 2))),
            lambda r, m: setattr(r.query_start_loc.cpu, "device", types.SimpleNamespace(type="npu")),
        )
        for change in changes:
            with self.subTest(change=change):
                runner, meta, frame = partition_fixture()
                actual_proof = proof(meta, frame)
                change(runner, meta)
                with self.assertRaises(ValueError):
                    I.timing_partition(TORCH, runner, meta, frame, actual_proof,
                                       types.SimpleNamespace(scalar_tensor=descriptor))

    def test04_all64_layout_cannot_borrow_a_fa_only_subset(self):
        runner, event, contexts, callback = layout_fixture()
        stamp = I.timing_layout(runner, event, contexts, callback)
        self.assertEqual((len(stamp[0]), len(stamp[1])), (64, 16))
        runner.compilation_config.static_forward_context["model.layers.0.attn"].kv_cache[0].base += 4
        with self.assertRaisesRegex(ValueError, "all64 actual native"):
            I.timing_layout(runner, event, contexts, callback)

    def test05_initialized_zeroer_has_no_timing_waiver(self):
        runner, event, contexts, callback = layout_fixture()
        runner._kv_block_zeroer = object()
        with self.assertRaisesRegex(ValueError, "absent zeroer"):
            I.timing_layout(runner, event, contexts, callback)

    def test06_cached_scheduler_still_rejects_owner_spec_resume_and_unseen(self):
        cls = type("SchedulerOutput", (), {"__module__": "vllm.v1.core.sched.output"})
        def fresh():
            scheduler = cls()
            scheduler.scheduled_new_reqs = []
            scheduler.finished_req_ids = []
            scheduler.scheduled_spec_decode_tokens = {}
            scheduler.preempted_req_ids = []
            scheduler.scheduled_cached_reqs = types.SimpleNamespace(resumed_req_ids=[], req_ids=["fixture"])
            bindings = types.SimpleNamespace(seen={"fixture"}, owner={"rank_bindings": {"0": {"pid": 1}}})
            return scheduler, bindings
        scheduler, bindings = fresh()
        self.assertEqual(I.timing_cached_ingress(bindings, scheduler, cls, {"pid": 1}, 0), [])
        changes = (
            lambda s, b: s.scheduled_new_reqs.append("new"),
            lambda s, b: s.finished_req_ids.append("fixture"),
            lambda s, b: s.preempted_req_ids.append("fixture"),
            lambda s, b: s.scheduled_spec_decode_tokens.update(fixture=[1]),
            lambda s, b: s.scheduled_cached_reqs.resumed_req_ids.append("fixture"),
            lambda s, b: s.scheduled_cached_reqs.req_ids.append("unseen"),
            lambda s, b: b.owner["rank_bindings"]["0"].update(pid=2),
        )
        for change in changes:
            scheduler, bindings = fresh()
            change(scheduler, bindings)
            with self.assertRaises(ValueError):
                I.timing_cached_ingress(bindings, scheduler, cls, {"pid": 1}, 0)

    def test07_actual_attention_closure_same_two_step_dispatch_and_transport(self):
        audit, timing = AttentionFixture(True), AttentionFixture(False)
        expected = [audit.step(), audit.step()]
        actual = [timing.step(), timing.step()]
        self.assertEqual(expected, actual)
        critical = lambda fixture: [row for row in fixture.trace if row[0] == "packed_append"]
        self.assertEqual(critical(audit), critical(timing))
        self.assertEqual(len(critical(timing)), 2)
        self.assertFalse(any(row[0] in ("publish", "qualify", "identity", "observer_d2h", "source_pin",
                                       "output_observer", "original_FA") for row in timing.trace))
        self.assertTrue(any(row[0] == "observer_d2h" for row in audit.trace))
        self.assertEqual([row for row in timing.trace if row[0] == "pre_refs_present"],
                         [("pre_refs_present", False), ("pre_refs_present", False)])
        self.assertFalse(any(row[0] == "original_FA" for row in audit.trace))

    def test08_owner_epoch_rejects_before_real_output_seam_in_both_modes(self):
        for diagnostic in (True, False):
            fixture = AttentionFixture(diagnostic)
            fixture.request.epoch = 2
            with self.assertRaisesRegex(ValueError, "owner epoch"):
                fixture.step()
            self.assertFalse(any(row[0] == "packed_append" for row in fixture.trace))

    def test09_default_off_returns_before_context_access(self):
        kwargs = {name: None for name, parameter in inspect.signature(I.install).parameters.items()
                  if name != "runner" and parameter.default is inspect.Parameter.empty}
        with mock.patch.dict(I.os.environ, {I.FLAG: "0"}):
            self.assertIsNone(I.install(None, **kwargs))

    def test10_no_claim_of_native_kernel_readiness(self):
        self.assertEqual(I.CRITICAL_SHA["kernel"], "ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a")
        self.assertEqual(I.PRODUCER_SHA, "f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5")

    def test11_actual_80005a_builder_copy_is_retained_not_replaced(self):
        data = (DEPS / "attention_v1.py").read_bytes()
        self.assertEqual((len(data), hashlib.sha256(data).hexdigest()),
                         (88246, "80005aba42bcf61247cc0d91502a0f1338194a4b38dd82bc521f6d3c84958390"))
        tree = ast.parse(data)
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "AscendAttentionMetadataBuilder")
        build = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "build")
        self.assertIn("query_start_loc_cpu.pin_memory().to(self.device, non_blocking=True)", ast.unparse(build))
        build.returns = None
        for argument in build.args.args:
            argument.annotation = None
        class Meta(types.SimpleNamespace):
            pass
        source_env = {"AscendMetadata": Meta, "CrossAttentionSpec": type("CrossAttentionSpec", (), {}),
                      "split_decodes_and_prefills": lambda *args, **kwargs: (1, 0, 1, 0)}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[build], type_ignores=[])),
                     str(DEPS / "attention_v1.py"), "exec"), source_env)
        trace = []
        runner, unused_meta, frame = partition_fixture(trace)
        common = types.SimpleNamespace(num_reqs=1, num_actual_tokens=1, causal=True,
                    query_start_loc_cpu=runner.query_start_loc.cpu, query_start_loc=runner.query_start_loc.gpu,
                    block_table_tensor=None, _seq_lens_cpu=Tensor((1,), (32769,), device="cpu"),
                    seq_lens_cpu=None, slot_mapping=Tensor((1,), (0,)), attn_state=State.DecodeOnly,
                    max_query_len=1, kvcomp_metadata=None)
        builder = types.SimpleNamespace(decode_threshold=1, kv_cache_spec=object(), speculative_config=None,
                    device="npu", attn_mask_builder=types.SimpleNamespace(get_attention_mask=lambda *args: None),
                    model_config=types.SimpleNamespace(runner_type="generate"))
        original = types.MethodType(source_env["build"], builder)
        state = {"frame": frame, "active": None, "failed": False, "dummy_depth": 0, "metadata_proofs": {}}
        env = dict(vars(I), state=state, torch=TORCH, runner=runner,
                   callback=types.SimpleNamespace(scalar_tensor=descriptor))
        exec(extract_factory("metadata_factory"), env)
        hooked = env["metadata_factory"](("layer",), original, Meta)
        result = hooked(builder, 0, common)
        self.assertIs(state["metadata_proofs"]["layer"]["meta"], result)
        self.assertNotEqual(result.query_start_loc.base, runner.query_start_loc.gpu.base)
        self.assertEqual(trace, [("native_h2d",)])
        with self.assertRaisesRegex(ValueError, "one actual complete FA builder"):
            hooked(builder, 0, common)
        self.assertEqual(trace, [("native_h2d",)])

    def test12_copied_meta_and_stale_frame_cannot_reuse_builder_proof(self):
        runner, meta, frame = partition_fixture()
        actual_proof = proof(meta, frame)
        for other_meta, other_frame in ((copy.copy(meta), frame), (meta, dict(frame, epoch=2))):
            with self.assertRaisesRegex(ValueError, "current-frame"):
                I.timing_partition(TORCH, runner, other_meta, other_frame, actual_proof,
                                   types.SimpleNamespace(scalar_tensor=descriptor))

    def test13_actual_steady_update_has_no_observer_file_or_sync_callback(self):
        runner, scheduler, deferred, env, trace = update_fixture()
        self.assertIs(env["update"](runner, scheduler), deferred)
        self.assertEqual(trace, [("native_update", True)])
        self.assertEqual(env["state"]["metadata_proofs"], {})

    def test14_actual_finished_boundary_qualifies_and_preserves_native_retire(self):
        runner, scheduler, deferred, env, trace = update_fixture(boundary=True)
        self.assertIs(env["update"](runner, scheduler), deferred)
        self.assertEqual(trace.count(("boundary_qualify",)), 16)
        self.assertEqual(trace.count(("writer_guard",)), 1)
        self.assertEqual(trace.count(("actual_ingress",)), 1)
        self.assertEqual(trace.count(("native_finished_release",)), 1)
        self.assertLess(trace.index(("writer_guard",)), trace.index(("native_update", True)))
        self.assertLess(trace.index(("native_update", True)), trace.index(("native_finished_release",)))
        self.assertEqual(env["book"].finished, {"fixture"})

    def test15_actual_execute_invalidates_all_producers_on_layout_change(self):
        runner, scheduler, deferred, env, trace = update_fixture(changed_layout=True)
        env["orig_execute"] = lambda *args, **kwargs: env["update"](runner, scheduler)
        exec(extract_factory("execute"), env)
        with self.assertRaisesRegex(ValueError, "allocation changed"):
            env["execute"](runner)
        self.assertIs(env["state"]["failed"], True)
        self.assertEqual(trace, [("invalidate",)] * 16)


    def test16_real_arena_factory_integer_metadata_reproduces_old_failure_and_fixed_stamp(self):
        raw = (DEPS / "callback.py").read_bytes()
        self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                         (10843, "291eb417eaecf97b4199072ae62012180c18af44b5a5d2c5c92c1060e3d38f5e"))
        actual = load("_actual_callback_arena_factory", DEPS / "callback.py")
        calls = []
        class Field(Tensor):
            def numel(self): return 2
            def zero_(self): calls.append(("zero",)); return self
            def __getitem__(self, index):
                return types.SimpleNamespace(fill_=lambda value: calls.append(("shift", index, value)))
        runner, event, contexts, callback = layout_fixture()
        name = next(iter(contexts))
        pool = {field: Field(base=1024 + j*32) for j, field in enumerate(contexts[name]["arena"].pool)
                if field not in ("allocated_bytes", "dense_shadow_bytes")}
        torch = types.SimpleNamespace(npu=types.SimpleNamespace(synchronize=lambda: calls.append(("init_fence",))))
        arena = actual.arena_from_views(torch, types.SimpleNamespace(CompactArena=type("Arena", (), {})), pool,
                    dict(bits=2, pages=384, region={"field_bytes":72}, allocation_replaced=False,
                         original_dense_storage_still_live=True))
        self.assertEqual((arena.pool["allocated_bytes"], arena.pool["dense_shadow_bytes"], arena.pool_bytes), (72,0,72))
        self.assertEqual(calls.count(("zero",)), 8)
        self.assertEqual(calls.count(("init_fence",)), 1)
        contexts[name]["arena"] = arena
        prior = ROOT / "prior_timing_installer.py"
        self.assertEqual(hashlib.sha256(prior.read_bytes()).hexdigest(),
                         "9e41be3e47291ed6552b338934f6b6d804760949d84d8f9751ddde6290a3dc98")
        old = load("_frozen003_timing_failure", prior)
        with self.assertRaises(AttributeError):
            old.timing_layout(runner, event, contexts, callback)
        calls.clear()
        stamp = I.timing_layout(runner, event, contexts, callback)
        self.assertEqual((len(stamp[0]), len(stamp[1])), (64,16))
        self.assertEqual(calls, [])
        self.assertEqual(next(row[2:4] for row in stamp[1] if row[0] == name), (72,0))

    def test17_field_accounting_remains_exact_and_layout_changes_are_stamped(self):
        for mutate in (lambda p: p.update(allocated_bytes=True),
                       lambda p: p.update(dense_shadow_bytes=1),
                       lambda p: p.update(allocated_bytes=73),
                       lambda p: p.update(unexpected=1),
                       lambda p: p.pop("shifts")):
            runner, event, contexts, callback = layout_fixture()
            mutate(next(iter(contexts.values()))["arena"].pool)
            with self.assertRaises(ValueError):
                I.timing_layout(runner, event, contexts, callback)
        runner, event, contexts, callback = layout_fixture()
        before = I.timing_layout(runner, event, contexts, callback)
        next(iter(contexts.values()))["arena"].pool["shifts"].base += 4
        self.assertNotEqual(before, I.timing_layout(runner, event, contexts, callback))


    def test18_staged_original_inputs_precede_candidate_subset_and_preserve_output(self):
        baseline=AttentionFixture(True);staged=AttentionFixture(True);trace=staged.trace
        class Sink:
            def start(self,*args):trace.append(("stage_start",))
            def capture_decode(self,layer):return False
            def append_inputs(self,layer,plan,q,k,v,states):
                trace.append(("original_before_subset",q.shape,k.shape,v.shape,q.values,k.values,v.values))
            def merged_output(self,*args):trace.append(("stage_merge",))
        staged.env["stage_observer"]=Sink()
        self.assertEqual(staged.step(),baseline.step())
        original=next(x for x in trace if x[0]=="original_before_subset")
        self.assertEqual(original[1:4],((1,1536),(1,256),(1,256)))
        self.assertLess(trace.index(original),next(i for i,x in enumerate(trace) if x[0]=="packed_append"))
        self.assertEqual([x for x in trace if x[0]=="packed_append"],
                         [x for x in baseline.trace if x[0]=="packed_append"])

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--deps", type=Path, required=True)
    args, rest = parser.parse_known_args()
    DEPS = args.deps.resolve()
    unittest.main(argv=[sys.argv[0]] + rest, verbosity=2)


