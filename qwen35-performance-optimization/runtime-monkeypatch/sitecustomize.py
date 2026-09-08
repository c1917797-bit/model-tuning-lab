"""Runtime-only Qwen3.5 Ascend optimizations via import-time monkeypatches."""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import functools
import inspect
import os
import sys
import textwrap
from types import ModuleType

# vLLM inspects model classes in a device-less python -m registry subprocess.
# Importing the Ascend plugin from sitecustomize there initializes Triton
# before a device exists. Serving and spawned engine workers do not use -m.
_ENABLED = (
    os.getenv("QWEN35_ASCEND_MONKEYPATCH", "0") == "1"
    and "-m" not in getattr(sys, "orig_argv", ())
)
_RUNTIME_TARGETS = {
    "vllm_ascend.ascend_config",
    "vllm_ascend.compilation.graph_fusion_pass_manager",
    "vllm_ascend.ops.layernorm",
    "vllm_ascend.ops.weight_prefetch",
    "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn",
    "vllm.model_executor.models.qwen3_5",
    "vllm_ascend.ops.gdn",
}
_TARGETS = {"vllm.model_executor.models.registry"}


def _is_multiprocessing_child(argv) -> bool:
    return (
        "--multiprocessing-fork" in argv
        or any("multiprocessing.spawn" in arg for arg in argv)
        or any("multiprocessing.forkserver" in arg for arg in argv)
    )


_MULTIPROCESSING_CHILD = _is_multiprocessing_child(
    getattr(sys, "orig_argv", ())
)
_RUNTIME_ACTIVE = _MULTIPROCESSING_CHILD
if _MULTIPROCESSING_CHILD:
    _TARGETS.update(_RUNTIME_TARGETS)


def _notice(message: str) -> None:
    print(f"[qwen35-monkeypatch] {message}", file=sys.stderr, flush=True)


def _gdn_projection_fusion_enabled() -> bool:
    return os.getenv("VLLM_ASCEND_FUSE_QWEN35_GDN_PROJECTIONS", "0") == "1"


def _replace_function_block(function, old: str, new: str, label: str):
    source = textwrap.dedent(inspect.getsource(function))
    if source.count(old) != 1:
        raise RuntimeError(
            f"{label}: expected exactly one compatible v0.23.0 source block"
        )
    namespace = dict(function.__globals__)
    exec(
        compile(source.replace(old, new), function.__code__.co_filename, "exec"),
        namespace,
    )
    patched = namespace[function.__name__]
    patched.__module__ = function.__module__
    patched.__qualname__ = function.__qualname__
    return patched


def _patch_qwen_gdn_linear_attn(module: ModuleType) -> None:
    if not _gdn_projection_fusion_enabled():
        return
    cls = module.QwenGatedDeltaNetAttention
    if getattr(cls, "_qwen35_projection_fusion_monkeypatched", False):
        return
    original_init = cls.__init__

    @functools.wraps(original_init)
    def __init__(self, *args, **kwargs):
        bound = inspect.signature(original_init).bind(self, *args, **kwargs)
        bound.apply_defaults()
        original_init(self, *args, **kwargs)
        if self.gqa_interleaved_layout or self.quant_config is not None:
            self.fuse_qwen35_gdn_projections = False
            return
        prefix = bound.arguments["prefix"]
        fused = module.MergedColumnParallelLinear(
            input_size=self.hidden_size,
            output_sizes=[
                self.key_dim,
                self.key_dim,
                self.value_dim,
                self.value_dim,
                self.num_v_heads,
                self.num_v_heads,
            ],
            bias=False,
            quant_config=None,
            prefix=f"{prefix}.in_proj_qkvzba",
        )
        for name in ("in_proj_qkvz", "in_proj_ba"):
            if hasattr(self, name):
                delattr(self, name)
        self.in_proj_qkvzba = fused
        self.fuse_qwen35_gdn_projections = True
        self.disable_tp_for_ba_proj = False

    def project_qkvz_ba(self, hidden_states):
        if hasattr(self, "in_proj_qkvzba"):
            qkvzba, _ = self.in_proj_qkvzba(hidden_states)
            qkvz_size = (
                self.key_dim * 2 + self.value_dim * 2
            ) // self.tp_size
            ba_size = (self.num_v_heads * 2) // self.tp_size
            return qkvzba.split([qkvz_size, ba_size], dim=-1)
        mixed_qkvz, _ = self.in_proj_qkvz(hidden_states)
        ba, _ = self.in_proj_ba(hidden_states)
        return mixed_qkvz, ba

    cls.__init__ = __init__
    cls.project_qkvz_ba = project_qkvz_ba
    cls._qwen35_projection_fusion_monkeypatched = True
    _notice("patched Qwen3.5 GDN fused projection construction")


def _patch_qwen35_model(module: ModuleType) -> None:
    if not _gdn_projection_fusion_enabled():
        return
    cls = module.Qwen3_5Model
    if getattr(cls, "_qwen35_projection_weight_loader_monkeypatched", False):
        return
    old = """    params_dict = dict(self.named_parameters())
    loaded_params: set[str] = set()
"""
    new = """    params_dict = dict(self.named_parameters())
    if any(".in_proj_qkvzba." in name for name in params_dict):
        stacked_params_mapping = [
            ("in_proj_qkvzba", "in_proj_qkv", (0, 1, 2)),
            ("in_proj_qkvzba", "in_proj_z", 3),
            ("in_proj_qkvzba", "in_proj_b", 4),
            ("in_proj_qkvzba", "in_proj_a", 5),
            ("qkv_proj", "q_proj", "q"),
            ("qkv_proj", "k_proj", "k"),
            ("qkv_proj", "v_proj", "v"),
            ("gate_up_proj", "gate_proj", 0),
            ("gate_up_proj", "up_proj", 1),
        ]
    loaded_params: set[str] = set()
"""
    cls.load_weights = _replace_function_block(
        cls.load_weights, old, new, "Qwen3_5Model.load_weights"
    )
    cls._qwen35_projection_weight_loader_monkeypatched = True
    _notice("patched Qwen3.5 six-way fused projection weight mapping")


def _patch_ascend_gdn(module: ModuleType) -> None:
    if not _gdn_projection_fusion_enabled():
        return
    cls = module.AscendGatedDeltaNetAttention
    if getattr(cls, "_qwen35_projection_forward_monkeypatched", False):
        return
    old = """    num_tokens = hidden_states.size(0)
    if hasattr(self, "in_proj_qkv"):
"""
    new = """    num_tokens = hidden_states.size(0)
    if hasattr(self, "in_proj_qkvzba"):
        mixed_qkvz, ba = self.project_qkvz_ba(hidden_states)
        num_tokens = mixed_qkvz.size(0)
        qkv_size = (self.key_dim * 2 + self.value_dim) // self.tp_size
        z_size = self.value_dim // self.tp_size
        mixed_qkv, z = mixed_qkvz.split([qkv_size, z_size], dim=-1)
        z = z.reshape(z.size(0), -1, self.head_v_dim)
        b, a = self._split_ba_for_tp(ba)
        b = b.contiguous()
        a = a.contiguous()
    elif hasattr(self, "in_proj_qkv"):
"""
    cls.forward = _replace_function_block(
        cls.forward, old, new, "AscendGatedDeltaNetAttention.forward"
    )
    cls._qwen35_projection_forward_monkeypatched = True
    _notice("patched Ascend GDN fused projection forward path")


def _activate_runtime_patches() -> None:
    global _RUNTIME_ACTIVE
    if _RUNTIME_ACTIVE:
        return
    _RUNTIME_ACTIVE = True
    _TARGETS.update(_RUNTIME_TARGETS)
    for name in sorted(_RUNTIME_TARGETS):
        if name in sys.modules:
            _PATCHERS[name](sys.modules[name])
    _notice("runtime optimization hooks activated after model inspection")


def _patch_model_registry(module: ModuleType) -> None:
    cls = module._LazyRegisteredModel
    if getattr(cls, "_qwen35_deferred_runtime_monkeypatched", False):
        return
    original = cls.inspect_model_cls

    def inspect_model_cls(self):
        result = original(self)
        _activate_runtime_patches()
        return result

    cls.inspect_model_cls = inspect_model_cls
    cls._qwen35_deferred_runtime_monkeypatched = True
    _notice("deferred runtime patches until model inspection completes")


def _patch_ascend_config(module: ModuleType) -> None:
    cls = module.AscendConfig
    if getattr(cls, "_qwen35_compile_ranges_monkeypatched", False):
        return
    original = cls.update_compile_ranges_split_points

    def update_compile_ranges_split_points(self):
        original(self)
        threshold = int(os.getenv("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD", "0"))
        max_tokens = int(os.getenv("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS", "0"))
        if threshold <= 0:
            return
        points = set(self._get_compile_ranges(self.vllm_config.compilation_config))
        points.add(threshold)
        if max_tokens > threshold:
            points.add(max_tokens)
        ordered = sorted(points)
        self._set_compile_ranges(self.vllm_config.compilation_config, ordered)
        module.logger.info("[qwen35-monkeypatch] compile ranges: %s", ordered)

    cls.update_compile_ranges_split_points = update_compile_ranges_split_points
    cls._qwen35_compile_ranges_monkeypatched = True
    _notice("patched AscendConfig compile ranges")


def _make_mmar_pass():
    import torch
    from vllm.compilation.passes.vllm_inductor_pass import VllmInductorPass
    from vllm.distributed.parallel_state import get_tp_group
    from vllm.logger import logger

    def decompose(graph, group_name: str) -> int:
        fx_graph = graph.graph if isinstance(graph, torch.fx.GraphModule) else graph
        target = torch.ops.npu.npu_mm_all_reduce_base.default
        count = 0
        for node in list(fx_graph.nodes):
            if node.op != "call_function" or node.target != target:
                continue
            if len(node.args) < 3 or node.kwargs.get("reduce_op", "sum") != "sum":
                continue
            unsupported = {
                name: value
                for name, value in node.kwargs.items()
                if name not in {"reduce_op", "bias"} and value is not None
            }
            if unsupported:
                continue
            input_, transposed_weight = node.args[:2]
            bias = node.kwargs.get("bias")
            if (
                isinstance(transposed_weight, torch.fx.Node)
                and transposed_weight.op == "call_function"
                and transposed_weight.target == torch.ops.aten.t.default
            ):
                weight = transposed_weight.args[0]
            else:
                with fx_graph.inserting_before(node):
                    weight = fx_graph.call_function(torch.ops.aten.t.default, (transposed_weight,))
            with fx_graph.inserting_before(node):
                matmul = fx_graph.call_function(
                    torch.ops.vllm.unquantized_gemm.default, (input_, weight, bias)
                )
                all_reduce = fx_graph.call_function(
                    torch.ops.vllm.all_reduce.default,
                    (matmul,),
                    {"group_name": group_name},
                )
            matmul.meta = node.meta.copy()
            all_reduce.meta = node.meta.copy()
            node.replace_all_uses_with(all_reduce)
            fx_graph.erase_node(node)
            count += 1
        return count

    class MmarPrefillDecomposePass(VllmInductorPass):
        _qwen35_mmar_prefill_monkeypatch = True

        def __init__(self, vllm_config):
            super().__init__(vllm_config)
            self.min_tokens = int(os.getenv("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD", "0"))
            self.max_tokens = int(os.getenv("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_MAX_TOKENS", "0"))

        def __call__(self, graph):
            self.begin()
            self.matched_count = decompose(graph, get_tp_group().unique_name)
            logger.info(
                "[qwen35-monkeypatch] decomposed %s MMAR nodes for bounded prefill",
                self.matched_count,
            )
            self.end_and_log()

        def is_applicable_for_range(self, compile_range):
            if self.min_tokens <= 0 or compile_range.start <= self.min_tokens:
                return False
            return self.max_tokens <= 0 or compile_range.end <= self.max_tokens

    return MmarPrefillDecomposePass


def _patch_graph_manager(module: ModuleType) -> None:
    if int(os.getenv("VLLM_ASCEND_MMAR_PREFILL_FALLBACK_THRESHOLD", "0")) <= 0:
        _notice("bounded MMAR pass disabled")
        return
    cls = module.GraphFusionPassManager
    if getattr(cls, "_qwen35_mmar_pass_monkeypatched", False):
        return
    original = cls.configure
    pass_cls = _make_mmar_pass()

    def configure(self, config):
        original(self, config)
        if not self.ascend_compilation_config.get("fuse_allreduce_rms", True):
            return
        if any(getattr(item, "_qwen35_mmar_prefill_monkeypatch", False) for item in self.passes):
            return
        insertion = next(
            (
                index
                for index, item in enumerate(self.passes)
                if type(item).__name__ == "MatmulAllReduceAddRMSNormPass"
            ),
            len(self.passes),
        )
        self.passes.insert(insertion, pass_cls(config))
        _notice(f"inserted bounded MMAR pass at index {insertion}")

    cls.configure = configure
    cls._qwen35_mmar_pass_monkeypatched = True
    _notice("patched GraphFusionPassManager")


def _patch_weight_prefetch(module: ModuleType) -> None:
    cls = module.WeightPrefetchMethod
    if getattr(cls, "_qwen35_linear_attention_monkeypatched", False):
        return
    original = cls._maybe_prefetch_mlp_gate_up_weight_preprocess

    def _maybe_prefetch_mlp_gate_up_weight_preprocess(
        self, x_dependency, forward_context, curr_layer_prefix
    ):
        if not curr_layer_prefix or curr_layer_prefix.split(".")[-2] != "linear_attn":
            return original(self, x_dependency, forward_context, curr_layer_prefix)
        from vllm.model_executor.models.utils import extract_layer_index

        model_instance = module._EXTRA_CTX.model_instance
        layer_idx = extract_layer_index(curr_layer_prefix)
        weight = model_instance.model.layers[layer_idx].mlp.gate_up_proj.weight
        weight_size = (
            weight.data.element_size()
            * weight.data.numel()
            * self.mlp.prefetch_ratio.get(self.MLP_GATE_UP, 0)
        )
        weight_size = min(weight_size, module.MAX_PREFETCH_WEIGHT_SIZE)
        module.torch.ops.vllm.prefetch_preprocess(
            weight=weight, start_flag=x_dependency, max_weight_size=int(weight_size)
        )
        module._EXTRA_CTX.prefetch_mlp_gate_up_proj = True

    cls._maybe_prefetch_mlp_gate_up_weight_preprocess = (
        _maybe_prefetch_mlp_gate_up_weight_preprocess
    )
    cls._qwen35_linear_attention_monkeypatched = True
    _notice("patched linear-attention gate/up prefetch")


def _patch_layernorm(module: ModuleType) -> None:
    cls = module.AscendGemmaRMSNorm
    if getattr(cls, "_qwen35_prefetch_postprocess_monkeypatched", False):
        return
    original = cls.forward_oot

    def forward_oot(self, x, residual=None):
        result = original(self, x, residual)
        if residual is None:
            module.get_weight_prefetch_method().maybe_prefetch_mlp_weight_postprocess(result)
        return result

    cls.forward_oot = forward_oot
    cls._qwen35_prefetch_postprocess_monkeypatched = True
    _notice("patched Gemma RMSNorm prefetch postprocess")


_PATCHERS = {
    "vllm.model_executor.models.registry": _patch_model_registry,
    "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn": _patch_qwen_gdn_linear_attn,
    "vllm.model_executor.models.qwen3_5": _patch_qwen35_model,
    "vllm_ascend.ascend_config": _patch_ascend_config,
    "vllm_ascend.compilation.graph_fusion_pass_manager": _patch_graph_manager,
    "vllm_ascend.ops.gdn": _patch_ascend_gdn,
    "vllm_ascend.ops.layernorm": _patch_layernorm,
    "vllm_ascend.ops.weight_prefetch": _patch_weight_prefetch,
}


class _PatchLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, wrapped):
        self.fullname = fullname
        self.wrapped = wrapped

    def create_module(self, spec):
        creator = getattr(self.wrapped, "create_module", None)
        return None if creator is None else creator(spec)

    def exec_module(self, module):
        self.wrapped.exec_module(module)
        _PATCHERS[self.fullname](module)


class _PatchFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname not in _TARGETS:
            return None
        spec = importlib.machinery.PathFinder.find_spec(fullname, path)
        if spec is None or spec.loader is None or isinstance(spec.loader, _PatchLoader):
            return spec
        spec.loader = _PatchLoader(fullname, spec.loader)
        return spec


if _ENABLED:
    sys.meta_path.insert(0, _PatchFinder())
    for _name in sorted(_TARGETS):
        if _name in sys.modules:
            _PATCHERS[_name](sys.modules[_name])
    if _MULTIPROCESSING_CHILD:
        _notice("runtime hooks enabled for multiprocessing child")
    _notice("import hooks installed")
