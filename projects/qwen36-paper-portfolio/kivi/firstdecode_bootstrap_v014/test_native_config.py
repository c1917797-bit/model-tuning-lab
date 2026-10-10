"""16 focused source-extracted config/trace regressions. No framework import.

AST execution tests the exact archived validator/property bodies, not an
invented vLLM config. Actual class construction remains MAIN's CPU8 precheck.
"""
import ast
import copy
import dataclasses
from typing import ClassVar
import hashlib
import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def module(name):
    spec = importlib.util.spec_from_file_location("_config_test_" + name, HERE / (name + ".py"))
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def archive(name, sha):
    local = os.environ.get("KIVI_CONFIG_ARCHIVE_FIXTURE")
    if local:
        path = Path(local) / name
    else:
        manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_bytes())
        rows = [r for r in manifest["dependencies"] if Path(r["path"]).name == name and r["sha256"] == sha]
        if len(rows) != 1:
            raise ValueError("one exact original config dependency")
        path = Path(rows[0]["path"])
    wire = path.read_bytes()
    if hashlib.sha256(wire).hexdigest() != sha:
        # MAIN's read-only Windows copies have exactly one additional LF;
        # no runtime source checker accepts this exception.
        if not local or not wire.endswith(b"\n") or hashlib.sha256(wire[:-1]).hexdigest() != sha:
            raise ValueError("original archive bytes")
        wire = wire[:-1]
    return ast.parse(wire)


def original_method(tree, cls, name, namespace=None):
    owner = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == cls)
    value = next(x for x in owner.body if isinstance(x, ast.FunctionDef) and x.name == name)
    value.decorator_list = []
    value.returns = None
    ns = {} if namespace is None else dict(namespace)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[value], type_ignores=[])), "<exact-native-method>", "exec"), ns)
    return ns[name]



def original_scheduler_constructor(tree):
    """Source-projected stdlib constructor harness, NOT the installed pydantic class.

    All fields/defaults/InitVars and post-init/factory bodies come from exact
    pinned source. Only annotations/decorator and Field's pydantic constraints
    are projected to stdlib dataclasses; actual installed class is CPU8's gate.
    """
    native = next(x for x in tree.body if isinstance(x, ast.ClassDef)
                  and x.name == "SchedulerConfig")
    body = []
    for original in native.body:
        if isinstance(original, ast.AnnAssign):
            value = copy.deepcopy(original)
            ann = value.annotation
            initvar = isinstance(ann, ast.Subscript) and isinstance(ann.value, ast.Name) and ann.value.id == "InitVar"
            classvar = isinstance(ann, ast.Subscript) and isinstance(ann.value, ast.Name) and ann.value.id == "ClassVar"
            value.annotation = (ast.Subscript(value=ast.Name(id="InitVar" if initvar else "ClassVar", ctx=ast.Load()),
                                slice=ast.Name(id="object", ctx=ast.Load()), ctx=ast.Load())
                                if initvar or classvar else ast.Name(id="object", ctx=ast.Load()))
            body.append(value)
        elif isinstance(original, ast.FunctionDef) and original.name in ("default_factory", "__post_init__", "verify_max_model_len"):
            value = copy.deepcopy(original)
            value.returns = None
            for arg in value.args.posonlyargs + value.args.args + value.args.kwonlyargs:
                arg.annotation = None
            if value.args.vararg: value.args.vararg.annotation = None
            if value.args.kwarg: value.args.kwarg.annotation = None
            body.append(value)
    value = ast.ClassDef(name="SchedulerConfig", bases=[], keywords=[], body=body,
                         decorator_list=[ast.Name(id="native_dataclass", ctx=ast.Load())])
    def field_projection(*, default=dataclasses.MISSING, init=True, **constraints):
        if set(constraints) - {"ge"}:
            raise ValueError("unexpected native Field constructor property")
        return dataclasses.field(default=default, init=init)
    logger = types.SimpleNamespace(info=lambda *a, **kw: None, info_once=lambda *a, **kw: None,
                                   warning=lambda *a, **kw: None)
    namespace = dict(native_dataclass=dataclasses.dataclass, InitVar=dataclasses.InitVar,
                     ClassVar=ClassVar, Field=field_projection, logger=logger)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[value], type_ignores=[])),
                 "<source-projected-native-constructor>", "exec"), namespace)
    return namespace["SchedulerConfig"]


def model():
    return types.SimpleNamespace(architecture="Qwen3_5ForConditionalGeneration",
        hf_config=types.SimpleNamespace(model_type="qwen3_5"), runner_type="generate",
        is_encoder_decoder=False, is_chunked_prefill_supported=True,
        max_model_len=33792, enforce_eager=True)


def scheduler():
    return types.SimpleNamespace(max_num_batched_tokens=32768, max_num_seqs=1,
        enable_chunked_prefill=True, async_scheduling=False,
        long_prefill_token_threshold=0, max_num_partial_prefills=1,
        max_long_partial_prefills=1, max_num_scheduled_tokens=None,
        scheduler_reserve_full_isl=True)


class NativeConfig(unittest.TestCase):
    def setUp(self):
        self.proof = module("config_cpu")
        self.server = module("server_entry")
        self.reader = module("consume_first_decode")

    def test_only_chunked_boolean_action_changed(self):
        new = self.server.native_argv(8250, 10 * 1024**3)
        self.assertIn("--enable-chunked-prefill", new)
        self.assertNotIn("--no-enable-chunked-prefill", new)
        self.assertEqual(new[new.index("--max-num-batched-tokens") + 1], "32768")
        self.assertEqual(new[new.index("--max-model-len") + 1], "33792")
        old = list(new)
        old[old.index("--enable-chunked-prefill")] = "--no-enable-chunked-prefill"
        self.assertEqual(self.proof.corrected_argv(old), new)
        self.assertEqual(sum(a != b for a, b in zip(old, new)), 1)

    def test_duplicate_or_missing_original_action_rejected(self):
        for value in ([], ["--no-enable-chunked-prefill"] * 2,
                      ["--enable-chunked-prefill", "--no-enable-chunked-prefill"]):
            with self.assertRaises(ValueError):
                self.proof.corrected_argv(value)

    def validator(self):

        logger = types.SimpleNamespace(warning=lambda *a, **kw: None)
        return original_method(archive("scheduler.py", self.proof.PINS["vllm.config.scheduler"]),
                               "SchedulerConfig", "verify_max_model_len", dict(logger=logger))

    def test_actual_probe_explicit_backend_import_before_namespace_check(self):
        tree = ast.parse((HERE / "config_cpu.py").read_bytes())
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "run")
        first = next(i for i, x in enumerate(fn.body) if isinstance(x, ast.Assign)
                     and any(isinstance(y, ast.Name) and y.id == "torch" for y in x.targets))
        actual = fn.body[first:first + 3]
        calls = []
        torch = types.SimpleNamespace()
        def importing(name):
            calls.append(name)
            if name == "torch": return torch
            if name == "torch_npu":
                torch.npu = types.SimpleNamespace(is_initialized=lambda: False)
                return types.SimpleNamespace()
            raise ValueError("unexpected import")
        ns = dict(importlib=types.SimpleNamespace(import_module=importing), need=self.proof.need)
        exec(compile(ast.fix_missing_locations(ast.Module(body=actual, type_ignores=[])),
                     "<actual-probe-import-order>", "exec"), ns)
        self.assertEqual(calls, ["torch", "torch_npu"])
        del torch.npu
        with self.assertRaises(AttributeError):
            exec(compile(ast.fix_missing_locations(ast.Module(body=[actual[0], actual[2]], type_ignores=[])),
                         "<old-probe-without-backend>", "exec"), ns)

    def test_original_actual_validator_rejects_old_configuration(self):
        value = scheduler()
        value.enable_chunked_prefill = False
        with self.assertRaisesRegex(ValueError, "smaller than max_model_len"):
            self.validator()(value, 33792)

    def test_original_actual_validator_accepts_corrected_not_increased_batch(self):
        value = scheduler()
        self.assertIs(self.validator()(value, 33792), value)
        self.assertEqual(value.max_num_batched_tokens, 32768)

    def test_exact_constructor_kwargs_match_native_engine_args(self):
        native = archive("arg_utils.py", self.proof.PINS["vllm.engine.arg_utils"])
        cls = next(x for x in native.body if isinstance(x, ast.ClassDef) and x.name == "EngineArgs")
        fn = next(x for x in cls.body if isinstance(x, ast.FunctionDef) and x.name == "create_engine_config")
        call = next(x for x in ast.walk(fn) if isinstance(x, ast.Call)
                    and isinstance(x.func, ast.Name) and x.func.id == "SchedulerConfig")
        own = ast.parse((HERE / "config_cpu.py").read_bytes())
        helper = next(x for x in own.body if isinstance(x, ast.FunctionDef) and x.name == "scheduler_config")
        actual = next(x for x in ast.walk(helper) if isinstance(x, ast.Call)
                      and isinstance(x.func, ast.Name) and x.func.id == "scheduler_cls")
        self.assertEqual([x.arg for x in call.keywords], [x.arg for x in actual.keywords])
        # Only self -> engine, model_config -> model renaming is permitted.
        class Rename(ast.NodeTransformer):
            def visit_Name(self, node):
                if node.id in ("self", "model_config"):
                    node.id = {"self": "engine", "model_config": "model"}[node.id]
                return node
        for expected, supplied in zip(call.keywords, actual.keywords):
            self.assertEqual(ast.dump(Rename().visit(expected.value)), ast.dump(supplied.value))

    def test_exact_required_initvars_and_native_default_factory_constructor(self):
        tree = archive("scheduler.py", self.proof.PINS["vllm.config.scheduler"])
        owner = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == "SchedulerConfig")
        required = [x.target.id for x in owner.body if isinstance(x, ast.AnnAssign)
                    and isinstance(x.annotation, ast.Subscript)
                    and isinstance(x.annotation.value, ast.Name) and x.annotation.value.id == "InitVar"
                    and x.value is None]
        self.assertEqual(required, ["max_model_len", "is_encoder_decoder"])
        cls = original_scheduler_constructor(tree)
        with self.assertRaisesRegex(TypeError, "is_encoder_decoder"):
            cls(max_model_len=33792, max_num_batched_tokens=32768, enable_chunked_prefill=True)
        value = cls.default_factory(max_model_len=33792, max_num_batched_tokens=32768,
                                    enable_chunked_prefill=True)
        self.assertEqual(value.max_num_batched_tokens, 32768)
        self.assertTrue(value.enable_chunked_prefill)
        explicit_encoder = cls.default_factory(max_model_len=33792, max_num_batched_tokens=33792,
                                               enable_chunked_prefill=True, is_encoder_decoder=True)
        self.assertFalse(explicit_encoder.enable_chunked_prefill)

    def test_cpu_helper_uses_original_factory_with_both_real_initvar_branches(self):
        cls = original_scheduler_constructor(archive("scheduler.py", self.proof.PINS["vllm.config.scheduler"]))
        args = types.SimpleNamespace(model="/models/Qwen3.6-27B", max_model_len=33792,
            enforce_eager=True, enable_prefix_caching=False, mamba_cache_mode="none",
            max_num_batched_tokens=32768, max_num_seqs=1, enable_chunked_prefill=True,
            disable_chunked_mm_input=False, scheduling_policy="fcfs", scheduler_cls=None,
            max_num_partial_prefills=1, max_long_partial_prefills=1, long_prefill_token_threshold=0,
            scheduler_reserve_full_isl=True, disable_hybrid_kv_cache_manager=None,
            async_scheduling=False, stream_interval=1)
        value = self.proof.cpu_scheduler_config(args, cls)
        self.proof.require_cpu_policy(args, value, 10 * 1024**3)
        args.enable_chunked_prefill = False
        with self.assertRaisesRegex(ValueError, "smaller than max_model_len"):
            self.proof.cpu_scheduler_config(args, cls)
        self.assertEqual(args.max_num_batched_tokens, 32768)

    def test_cpu_decoder_assumption_is_named_and_actual_n1_encoder_rejected(self):
        self.assertEqual(self.proof.CPU_SCHEDULER_ASSUMPTIONS, dict(is_encoder_decoder=False,
            checkpoint_verified=False, origin="installed SchedulerConfig.default_factory decoder fallback"))
        tree = ast.parse((HERE / "config_cpu.py").read_bytes())
        helper = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "cpu_scheduler_config")
        calls = [x.func.attr for x in ast.walk(helper) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)]
        self.assertIn("default_factory", calls)
        server_tree = ast.parse((HERE / "server_entry.py").read_bytes())
        fn = next(x for x in server_tree.body if isinstance(x, ast.FunctionDef) and x.name == "actual_config_precheck")
        keys = [x.arg for x in ast.walk(fn) if isinstance(x, ast.keyword)]
        self.assertIn("cpu_scheduler_assumptions", keys)
        native_model = model()
        native_model.is_encoder_decoder = True
        with self.assertRaisesRegex(ValueError, "actual checkpoint architecture"):
            self.proof.require_firstdecode_policy(native_model, scheduler(), 10 * 1024**3)

    def test_actual_model_capability_generate_vs_encoder_decoder(self):
        fn = original_method(archive("model.py", self.proof.PINS["vllm.config.model"]),
                             "ModelConfig", "is_chunked_prefill_supported",
                             dict(logger=types.SimpleNamespace(debug=lambda *a: None)))
        value = types.SimpleNamespace(attn_type="decoder", pooler_config=None)
        self.assertTrue(fn(value))
        value.attn_type = "encoder_decoder"
        self.assertFalse(fn(value))

    def test_policy_keeps_original_bounds_and_rejects_subchunk(self):
        self.proof.require_firstdecode_policy(model(), scheduler(), 10 * 1024**3)
        for key, bad in (("max_num_batched_tokens", 33792), ("long_prefill_token_threshold", 8192),
                         ("enable_chunked_prefill", False), ("async_scheduling", True),
                         ("max_num_scheduled_tokens", 8192), ("max_num_seqs", 2)):
            value = scheduler()
            setattr(value, key, bad)
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.proof.require_firstdecode_policy(model(), value, 10 * 1024**3)

    def test_actual_n1_full_engine_call_and_cpu_partial_scope(self):
        tree = ast.parse((HERE / "server_entry.py").read_bytes())
        fn = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "actual_config_precheck")
        calls = [x for x in ast.walk(fn) if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)]
        self.assertEqual(sum(x.func.attr == "create_model_config" for x in calls), 0)
        branch = next(x for x in fn.body if isinstance(x, ast.If) and isinstance(x.test, ast.Compare)
                      and isinstance(x.test.left, ast.Name) and x.test.left.id == "stage"
                      and x.test.comparators[0].value == "cpu" and len(x.body) > 1)
        cpu_calls = [x.func.attr for stmt in branch.body for x in ast.walk(stmt)
                     if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute)]
        self.assertNotIn("from_cli_args", cpu_calls)
        self.assertNotIn("create_engine_config", cpu_calls)
        self.assertNotIn("create_model_config", cpu_calls)
        self.assertIn("cpu_scheduler_config", cpu_calls)
        self.assertIn("require_cpu_policy", cpu_calls)
        self.assertEqual(sum(x.func.attr == "create_engine_config" for x in calls), 1)
        self.assertNotIn("run_server", ast.unparse(fn))
        self.assertNotIn("AsyncLLM(", ast.unparse(fn))
        gate = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == "install_engine_config_gate")
        checked = next(x for x in gate.body if isinstance(x, ast.FunctionDef) and x.name == "checked")
        self.assertIsInstance(checked.body[-1], ast.Return)
        self.assertEqual(checked.body[-1].value.id, "config")
        self.assertEqual(checked.body[0].value.func.id, "original")

    def trace(self, computed=0, scheduled=32768):
        return dict(schema="kivi.actual-packed-qwen-frame/v1", kind="prefill", rank=0,
            identity={"pid": 123, "start_ticks": 456}, req_ids=["actual-id"],
            req_id_to_index={"actual-id": 0}, computed_tokens=[computed],
            scheduled_counts=[scheduled], query_start_loc=[0, scheduled], total_tokens=scheduled,
            positions=list(range(computed, computed + scheduled)), epoch=1)

    def book(self):
        path = os.environ.get("KIVI_BOOK_ARCHIVE_FIXTURE")
        if path:
            wire = Path(path).read_bytes()
        else:
            manifest = json.loads((HERE / "SOURCE_MANIFEST.json").read_bytes())
            wire = Path(manifest["runtime_roles"]["book"]["path"]).read_bytes()
        expected = "6488a5ca3fb6f606bbb82bf86e226fc30741e8dc7288ff03e3e5e8b71cec07c7"
        if hashlib.sha256(wire).hexdigest() != expected:
            if not path or not wire.endswith(b"\n") or hashlib.sha256(wire[:-1]).hexdigest() != expected:
                raise ValueError("exact original scalar Book")
            wire = wire[:-1]
        ns = {}
        exec(compile(wire, "<original-book>", "exec"), ns)
        return types.SimpleNamespace(frame_valid=ns["frame_valid"])

    def test_actual_full_prefill_trace_keeps_all_original_positions(self):
        value = self.trace()
        self.assertTrue(self.reader.require_one_prefill(value, 0, value["identity"], "actual-id", self.book()))

    def test_chunk_ending_at32768_cannot_pass_single_prefill(self):
        value = self.trace(16384, 16384)
        self.assertEqual(sum((value["computed_tokens"][0], value["scheduled_counts"][0])), 32768)
        with self.assertRaisesRegex(ValueError, "one complete32768"):
            self.reader.require_one_prefill(value, 0, value["identity"], "actual-id", self.book())

    def test_full_length_bad_position_or_actual_identity_rejected(self):
        value = self.trace()
        value["positions"][123] = 999
        with self.assertRaises(ValueError):
            self.reader.require_one_prefill(value, 0, value["identity"], "actual-id", self.book())
        value = self.trace()
        with self.assertRaises(ValueError):
            self.reader.require_one_prefill(value, 1, value["identity"], "actual-id", self.book())

    def test_full_config_does_not_weaken_common_native_fields(self):
        cfg = types.SimpleNamespace(model_config=model(), scheduler_config=scheduler(),
            parallel_config=types.SimpleNamespace(tensor_parallel_size=4, pipeline_parallel_size=1,
                data_parallel_size=1, prefill_context_parallel_size=1, decode_context_parallel_size=1,
                worker_cls="kivi_firstdecode_bootstrap.FirstDecodeWorker", enable_dbo=False),
            cache_config=types.SimpleNamespace(enable_prefix_caching=False, mamba_cache_mode="none",
                kv_cache_memory_bytes=10 * 1024**3), speculative_config=None, kv_transfer_config=None,
            ec_transfer_config=None, compilation_config=types.SimpleNamespace(
                cudagraph_mode=types.SimpleNamespace(name="NONE"), mode=types.SimpleNamespace(name="NONE")))
        self.server.require_engine_config(cfg, self.proof, 10 * 1024**3)
        cfg.cache_config.enable_prefix_caching = True
        with self.assertRaises(ValueError):
            self.server.require_engine_config(cfg, self.proof, 10 * 1024**3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
