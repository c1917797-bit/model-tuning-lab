"""Actual pinned official warmup sequence with CPU compiler order controls.

Only the official _warmup_and_capture function's code is executed. Dummy tensor
allocation and capture are CPU fixtures, not official module imports or NPU
evidence. The actual candidate router, forward signature and layer gates run.
"""
from dataclasses import dataclass
from enum import Enum
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
import types
import unittest
import torch
import numpy as np

from graph_candidate.entry_router import SelectiveEntryRouter
from graph_candidate.native_warmup import NativeWarmupProof, _codes

_SOURCE = os.environ.get("HYPIC_GRAPH_GPU_RUNNER_SOURCE")
_WORKER_SOURCE = os.environ.get("HYPIC_GRAPH_NPU_RUNNER_SOURCE")
_WORKER_SHA256 = "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968"
_SHA256 = "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666"


class GM(Enum):
    NONE = 0
    FULL = 2
    FULL_DECODE_ONLY = (2, 0)


class CM(Enum):
    VLLM_COMPILE = 3


@dataclass
class Descriptor:
    num_tokens: int = 4
    num_reqs: int | None = None
    uniform: bool = False
    has_lora: bool = False
    num_active_loras: int = 0


@dataclass
class Context:
    cudagraph_runtime_mode: object = GM.NONE
    ubatch_slices: object = None
    skip_compiled: bool = False
    batch_descriptor: object = None
    attn_metadata: object = None


class CompilationDuringCapture(RuntimeError):
    pass


def official_warmup():
    path = Path(_SOURCE).resolve()
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != _SHA256:
        raise ValueError("fixed official GPU runner source drift")
    methods = [code for code in _codes(compile(source, str(path), "exec",
                dont_inherit=True)) if code.co_qualname == "GPUModelRunner._warmup_and_capture"]
    if len(methods) != 1 or methods[0].co_firstlineno != 6592:
        raise ValueError("exact official warmup function required")
    return types.FunctionType(methods[0], {
        "__builtins__": __builtins__, "CUDAGraphMode": GM,
    }, "_warmup_and_capture", argdefs=(None, False, None))


def official_determine():
    path = Path(_WORKER_SOURCE).resolve()
    source = path.read_bytes()
    if hashlib.sha256(source).hexdigest() != _WORKER_SHA256:
        raise ValueError("fixed official NPU runner source drift")
    methods = [code for code in _codes(compile(source,str(path),"exec",dont_inherit=True))
               if code.co_qualname == "NPUModelRunner._determine_batch_execution_and_padding"]
    if len(methods) != 1 or methods[0].co_firstlineno != 2933:
        raise ValueError("exact official dispatch function required")
    return types.FunctionType(methods[0], {
        "__builtins__":__builtins__,"np":np,"CUDAGraphMode":GM,
        "BatchDescriptor":Descriptor,"enable_sp":lambda config:False,
    }, "_determine_batch_execution_and_padding",argdefs=(False,False,None,None,None,0))


class FakeRunner:
    """CPU allocation fixture; serving proof uses source-bound NPU runner code."""
    def __init__(self, scenario):
        self.scenario = scenario
        self.compilation_config = scenario.config
        self.uniform_decode_query_len = 1
        self.speculative_config = None
        self.input_batch = SimpleNamespace(num_computed_tokens_cpu=np.zeros(4))
        self.model_config = SimpleNamespace(is_encoder_decoder=False)
        self.parallel_config = SimpleNamespace(data_parallel_size=1)
        self.vllm_config = SimpleNamespace(
            parallel_config=self.parallel_config,
            observability_config=SimpleNamespace(cudagraph_metrics=False))
        self._pad_for_sequence_parallelism = lambda n:n

    def _dummy_run(self, num_tokens, *, cudagraph_runtime_mode=None,
                   force_attention=False, uniform_decode=False,
                   allow_microbatching=False, skip_eplb=True, remove_lora=False,
                   num_active_loras=0, profile_seq_lens=None,
                   is_graph_capturing=False, is_profile=False, with_prefill=False,
                   create_mixed_batch=False):
        max_query_len, num_reqs = 1, num_tokens
        mode = cudagraph_runtime_mode or GM.NONE
        if mode is GM.NONE:
            _,batch_desc,_,_,_ = official_determine()(self,
                num_tokens=num_tokens,num_reqs=num_reqs,
                num_scheduled_tokens_np=np.ones(num_reqs,dtype=np.int32),
                max_num_scheduled_tokens=max_query_len,use_cascade_attn=False,
                force_eager=True,force_uniform_decode=uniform_decode,
                force_has_lora=False,force_num_active_loras=0)
        else:
            batch_desc = Descriptor(num_tokens,num_tokens,True)
        num_tokens_padded = batch_desc.num_tokens
        self.scenario.context.batch_descriptor = batch_desc
        self.scenario.capture = is_graph_capturing
        try:
            return self.scenario.call(cudagraph_runtime_mode or GM.NONE)
        finally:
            self.scenario.capture = False


class Scenario:
    def __init__(self, *, fixed):
        self.capture = False
        self.compiles = []
        self.calls = []
        self.pic_calls = []
        self.config = SimpleNamespace(mode=CM.VLLM_COMPILE,
            cudagraph_mode=GM.FULL_DECODE_ONLY, cudagraph_num_of_warmups=1)
        self.context = Context(batch_descriptor=Descriptor(4,4,True),
            attn_metadata={"GDN": SimpleNamespace(num_prefills=0),
                           "FA": SimpleNamespace(num_prefills=0)})
        outer = self
        class Layer:
            def forward(self, x):
                return x + 2
        class Model:
            def forward(self, input_ids, positions,
                        intermediate_tensors=None, inputs_embeds=None):
                return self.layer.forward(input_ids) + positions
            def __call__(self, x, positions):
                outer.calls.append((outer.context.cudagraph_runtime_mode.name,
                                    outer.context.skip_compiled))
                if outer.context.skip_compiled:
                    return self.forward(x, positions)
                return outer.compiled(x, positions)
        native_forward, native_call, native_layer = Model.forward, Model.__call__, Layer.forward
        self.model = Model()
        self.model.layer = Layer()
        self.model.compilation_config = self.config
        self.model.do_not_compile = False
        self.model.vllm_config = SimpleNamespace(compilation_config=self.config,
            model_config=SimpleNamespace(enforce_eager=False),
            parallel_config=SimpleNamespace(tensor_parallel_size=4,
                pipeline_parallel_size=1,data_parallel_size=1),
            speculative_config=None,lora_config=None)
        def hypic(layer, x):
            outer.pic_calls.append("layer")
            return native_layer(layer, x)
        def prefill(model, *args, **kwargs):
            outer.pic_calls.append("model")
            return native_forward(model, *args, **kwargs)
        Layer.forward = hypic
        def backend(gm, inputs):
            outer.compiles.append(outer.capture)
            if outer.capture:
                raise CompilationDuringCapture("native compiler synchronization in capture")
            return gm.forward
        self.warmup = official_warmup()
        self.runner = FakeRunner(self)
        self.proof = NativeWarmupProof(
            FakeRunner._dummy_run.__code__, FakeRunner._dummy_run.__globals__,
            self.warmup.__code__, self.warmup.__globals__, FakeRunner, GM)
        self.router = SelectiveEntryRouter(model_class=Model, native_call=native_call,
            native_forward=native_forward,compilation_mode=CM,graph_mode=GM,
            forward_context_class=Context,batch_descriptor_class=Descriptor,
            get_context=lambda:self.context,is_compiling=torch.compiler.is_compiling,
            assert_ownership=lambda:None,prefill_forward=prefill,
            startup_proof=self.proof if fixed else None)
        self.stop = self.router.install(enabled=True,
            layers=((Layer,"forward",native_layer,hypic),))
        self.compiled = torch.compile(self.model.forward, backend=backend,fullgraph=True)

    def call(self, mode):
        self.context.cudagraph_runtime_mode = mode
        return self.model(torch.arange(4.0), torch.ones(4))

    def sequence(self):
        return self.warmup(self.runner, Descriptor(4,4,True), GM.FULL)


@unittest.skipUnless(_SOURCE and _WORKER_SOURCE, "explicit immutable official GPU runner source required")
class OfficialWarmupSequenceTests(unittest.TestCase):
    def scenario(self, *, fixed):
        value = Scenario(fixed=fixed)
        self.addCleanup(value.stop)
        return value

    def test_old_all_none_bypass_compiles_inside_capture_and_fails(self):
        s = self.scenario(fixed=False)
        with self.assertRaises(Exception) as failure:
            s.sequence()
        self.assertIn("native compiler synchronization in capture", str(failure.exception))
        self.assertEqual(s.calls[:2], [("NONE", True), ("FULL", False)])
        self.assertEqual(s.compiles, [True])
        self.assertFalse(s.router._native_execution)
        self.assertFalse(s.context.skip_compiled)

    def test_actual_sequence_warmup_compiles_before_capture_and_full_reuses(self):
        s = self.scenario(fixed=True)
        s.sequence()
        self.assertEqual(s.calls[:2], [("NONE", False), ("FULL", False)])
        self.assertEqual(s.compiles, [False])
        self.assertEqual(s.pic_calls, [])
        s.context.batch_descriptor = Descriptor(4,4,True)
        s.call(GM.FULL)
        self.assertEqual(s.compiles, [False])
        s.call(GM.NONE)
        self.assertEqual(s.calls[-1], ("NONE", True))
        self.assertEqual(s.pic_calls, ["model","layer"])
        self.assertEqual(s.compiles, [False])

    def test_dummy_without_official_warmup_cannot_claim_native_compile(self):
        s = self.scenario(fixed=True)
        s.runner._dummy_run(4,cudagraph_runtime_mode=GM.NONE,
                            uniform_decode=True,force_attention=True)
        self.assertEqual(s.calls, [("NONE",True)])
        self.assertEqual(s.compiles, [])
        self.assertEqual(s.pic_calls, ["model","layer"])

    def test_explicit_skip_remains_eager_even_in_official_warmup(self):
        s = self.scenario(fixed=True)
        s.context.skip_compiled = True
        with self.assertRaises(ValueError):
            s.sequence()
        self.assertEqual(s.calls, [("NONE",True)])
        self.assertEqual(s.compiles, [])
        self.assertTrue(s.context.skip_compiled)

    def test_warmup_with_prefill_metadata_fails_before_native_call(self):
        s = self.scenario(fixed=True)
        s.context.attn_metadata["GDN"].num_prefills = 1
        with self.assertRaisesRegex(ValueError,"zero-prefill"):
            s.sequence()
        self.assertEqual(s.calls, [])
        self.assertEqual(s.compiles, [])

    def test_wrong_source_code_or_globals_never_authorizes(self):
        s = self.scenario(fixed=True)
        good = s.proof
        s.router.startup_proof = NativeWarmupProof(
            good.dummy_code, {}, good.warmup_code, good.warmup_globals, FakeRunner, GM)
        with self.assertRaises(Exception):
            s.sequence()
        self.assertEqual(s.calls[:2], [("NONE",True),("FULL",False)])
        self.assertEqual(s.compiles,[True])


if __name__ == "__main__":
    unittest.main()
