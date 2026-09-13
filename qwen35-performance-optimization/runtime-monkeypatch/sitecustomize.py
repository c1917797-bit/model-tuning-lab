"""Runtime-only Qwen3.5 Ascend optimizations via import-time monkeypatches."""

from __future__ import annotations

import importlib.abc
import importlib.machinery
import contextlib
import functools
import inspect
import os
import sys
import textwrap
import time
from types import ModuleType

# vLLM inspects model classes in a device-less python -m registry subprocess.
# Importing the Ascend plugin from sitecustomize there initializes Triton
# before a device exists. Serving and spawned engine workers do not use -m.
_ENABLED = (
    os.getenv("QWEN35_ASCEND_MONKEYPATCH", "0") == "1"
    and "-m" not in getattr(sys, "orig_argv", ())
)
_RUNTIME_TARGETS = {
    "vllm.compilation.backends",
    "vllm_ascend.ascend_config",
    "vllm_ascend.compilation.acl_graph",
    "vllm_ascend.compilation.compiler_interface",
    "vllm_ascend.compilation.graph_fusion_pass_manager",
    "vllm_ascend.ops.layernorm",
    "vllm_ascend.ops.weight_prefetch",
    "vllm.v1.core.sched.scheduler",
    "vllm_ascend.core.dyntra_lb_scheduler",
    "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn",
    "vllm.model_executor.models.qwen2_moe",
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


def _upstream_fused_prefill_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_UPSTREAM_FUSED_PREFILL", "0") == "1"


def _fused_prefill_metadata_reuse_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_FUSED_PREFILL_METADATA_REUSE", "0") == "1"


def _weight_prefetch_patch_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_WEIGHT_PREFETCH_PATCH", "1") == "1"


def _diagnostics_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_DIAGNOSTICS", "0") == "1"


def _t21_dense_mlp_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_T21_DENSE_MLP", "0") == "1"


def _super_kernel_enabled() -> bool:
    return os.getenv("QWEN35_ASCEND_SUPER_KERNEL", "0") == "1"


def _diagnostics_interval() -> int:
    try:
        return max(1, int(os.getenv("QWEN35_ASCEND_DIAGNOSTICS_INTERVAL", "32")))
    except ValueError:
        return 32


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


def _replace_function_blocks(function, replacements, label: str):
    """Apply multiple exact source anchors before compiling the function once."""
    source = textwrap.dedent(inspect.getsource(function))
    for suffix, old, new in replacements:
        if source.count(old) != 1:
            raise RuntimeError(
                f"{label}.{suffix}: expected exactly one compatible v0.23.0 "
                "source block"
            )
        source = source.replace(old, new)
    namespace = dict(function.__globals__)
    exec(compile(source, function.__code__.co_filename, "exec"), namespace)
    patched = namespace[function.__name__]
    patched.__module__ = function.__module__
    patched.__qualname__ = function.__qualname__
    return patched


def _register_t21_fake_kernel(torch_module) -> None:
    """Keep the T21 output row count symbolic during Dynamo/FakeTensor tracing."""
    operator = torch_module.ops.qwen35_t21.swiglu_gated_mlp
    if getattr(operator, "_qwen35_symbolic_fake_registered", False):
        return

    @torch_module.library.register_fake(
        "qwen35_t21::swiglu_gated_mlp", allow_override=True
    )
    def _t21_swiglu_gated_mlp_fake(x, gate_up_weight, down_weight):
        # The C++ Meta registration in the upstream-derived bridge specializes
        # backed SymInts in torch 2.10. Override only FakeTensor shape
        # propagation; the PrivateUse1 implementation and its numerical path
        # remain unchanged.
        return x.new_empty((x.shape[0], down_weight.shape[1]))

    operator._qwen35_symbolic_fake_registered = True
    _notice("registered symbolic T21 FakeTensor kernel")


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


def _patch_qwen2_moe(module: ModuleType) -> None:
    """Compose the upstream local MLP op with vLLM's existing TP reduction."""
    if not _t21_dense_mlp_enabled():
        return
    cls = module.Qwen2MoeMLP
    if getattr(cls, "_qwen35_t21_dense_mlp_monkeypatched", False):
        return

    # Importing the extension registers a traceable torch.ops node with an NPU
    # implementation and a Meta implementation. Fail closed during startup if
    # the validated bridge artifact is absent or has an incompatible ABI.
    import qwen35_t21_bridge  # noqa: F401
    _register_t21_fake_kernel(module.torch)
    from vllm.distributed.communication_op import (
        tensor_model_parallel_all_reduce,
    )
    from vllm.model_executor.layers.linear import UnquantizedLinearMethod

    original = cls.forward

    @functools.wraps(original)
    def forward(self, x):
        gate_up_proj = self.gate_up_proj
        down_proj = self.down_proj
        gate_up_weight = gate_up_proj.weight
        down_weight = down_proj.weight
        eligible = (
            self.expert_gate is None
            and gate_up_proj.tp_size == 4
            and down_proj.tp_size == 4
            and down_proj.input_is_parallel
            and down_proj.reduce_results
            and isinstance(
                gate_up_proj.quant_method, UnquantizedLinearMethod
            )
            and isinstance(down_proj.quant_method, UnquantizedLinearMethod)
            and gate_up_proj.bias is None
            and down_proj.bias is None
        )
        if not eligible:
            if _diagnostics_enabled():
                if self.expert_gate is not None:
                    raise RuntimeError("T21_DIAG_FAIL=expert_gate")
                if gate_up_proj.tp_size != 4:
                    raise RuntimeError("T21_DIAG_FAIL=gate_tp")
                if down_proj.tp_size != 4:
                    raise RuntimeError("T21_DIAG_FAIL=down_tp")
                if not down_proj.input_is_parallel:
                    raise RuntimeError("T21_DIAG_FAIL=input_parallel")
                if not down_proj.reduce_results:
                    raise RuntimeError("T21_DIAG_FAIL=reduce_results")
                if not isinstance(
                    gate_up_proj.quant_method, UnquantizedLinearMethod
                ):
                    raise RuntimeError("T21_DIAG_FAIL=gate_quant")
                if not isinstance(
                    down_proj.quant_method, UnquantizedLinearMethod
                ):
                    raise RuntimeError("T21_DIAG_FAIL=down_quant")
                if gate_up_proj.bias is not None:
                    raise RuntimeError("T21_DIAG_FAIL=gate_bias")
                if down_proj.bias is not None:
                    raise RuntimeError("T21_DIAG_FAIL=down_bias")
                raise RuntimeError("T21_DIAG_FAIL=aggregate_only")
            return original(self, x)

        # Tensor dtype/device/shape/layout checks intentionally live in the
        # C++ operator. Querying Parameter metadata here introduces non-Tensor
        # values into Dynamo fullgraph capture and prevents a traceable node.
        output_parallel = module.torch.ops.qwen35_t21.swiglu_gated_mlp(
            x, gate_up_weight.t(), down_weight.t()
        )
        return tensor_model_parallel_all_reduce(output_parallel)

    cls.forward = forward
    cls._qwen35_t21_dense_mlp_monkeypatched = True
    _notice("patched Qwen2MoeMLP with opt-in T21 dense path")


def _patch_vllm_backends(module: ModuleType) -> None:
    """Backport upstream's x.size(dim) guard for v0.23.0 graph splitting."""
    if not _t21_dense_mlp_enabled():
        return
    if getattr(module, "_qwen35_size_dim_guard_monkeypatched", False):
        return
    old = """    for node in size_nodes:
        tensor_node = node.args[0]
"""
    new = """    for node in size_nodes:
        # Upstream fix: only x.size() returns the torch.Size tuple that this
        # pass must decompose. x.size(dim) already returns a scalar SymInt.
        if len(node.args) > 1 or "dim" in node.kwargs:
            continue
        tensor_node = node.args[0]
"""
    module._decompose_size_nodes = _replace_function_block(
        module._decompose_size_nodes,
        old,
        new,
        "vllm.compilation.backends._decompose_size_nodes",
    )
    module._qwen35_size_dim_guard_monkeypatched = True
    _notice("backported upstream x.size(dim) graph-split guard")


def _patch_ascend_gdn(module: ModuleType) -> None:
    projection_enabled = _gdn_projection_fusion_enabled()
    fused_prefill_enabled = _upstream_fused_prefill_enabled()
    if not projection_enabled and not fused_prefill_enabled:
        return
    cls = module.AscendGatedDeltaNetAttention
    if (
        projection_enabled
        and not getattr(cls, "_qwen35_projection_forward_monkeypatched", False)
    ):
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

    if (
        fused_prefill_enabled
        and not getattr(cls, "_qwen35_upstream_fused_prefill_monkeypatched", False)
    ):
        import torch_npu

        cls._qwen35_fused_chunk_available = None

        @classmethod
        def _qwen35_probe_fused_chunk(candidate_cls):
            cached = candidate_cls._qwen35_fused_chunk_available
            if cached is not None:
                return cached
            if not hasattr(torch_npu, "npu_chunk_gated_delta_rule"):
                candidate_cls._qwen35_fused_chunk_available = False
                _notice("fused GDN prefill unavailable: operator missing")
                return False
            try:
                device = module.torch.npu.current_device()
                width = 128
                q = module.torch.zeros(
                    (64, 1, width),
                    dtype=module.torch.bfloat16,
                    device=device,
                )
                k = module.torch.zeros_like(q)
                v = module.torch.zeros_like(q)
                beta = module.torch.full_like(q[:, :, 0], 0.5)
                g = module.torch.full(
                    (64, 1),
                    -0.1,
                    dtype=module.torch.float32,
                    device=device,
                )
                state = module.torch.zeros(
                    (1, 1, width, width),
                    dtype=module.torch.bfloat16,
                    device=device,
                )
                lengths = module.torch.tensor(
                    [64], dtype=module.torch.int32, device=device
                )
                torch_npu.npu_chunk_gated_delta_rule(
                    q,
                    k,
                    v,
                    beta=beta,
                    initial_state=state,
                    actual_seq_lengths=lengths,
                    scale=width**-0.5,
                    g=g,
                )
                module.torch.npu.synchronize()
                candidate_cls._qwen35_fused_chunk_available = True
                _notice("fused GDN prefill device probe passed")
            except Exception as exc:
                candidate_cls._qwen35_fused_chunk_available = False
                _notice(
                    "fused GDN prefill device probe failed; using Triton "
                    f"fallback ({type(exc).__name__})"
                )
            return candidate_cls._qwen35_fused_chunk_available

        cls._qwen35_probe_fused_chunk = _qwen35_probe_fused_chunk

        def _qwen35_fused_chunk_gated_delta_rule(
            q,
            k,
            v,
            g,
            beta,
            initial_state,
            cu_seqlens,
            scale,
            attn_metadata,
        ):
            # Upstream vLLM-Ascend commit 77d13e2c0: replace the multi-kernel
            # Triton prefill path with the public fused torch_npu operator.
            q = module.l2norm_fwd(q).squeeze(0).contiguous()
            k = module.l2norm_fwd(k).squeeze(0).contiguous()
            v = v.squeeze(0).contiguous()
            g = g.squeeze(0).to(module.torch.float32).contiguous()
            beta = beta.squeeze(0).to(v.dtype).contiguous()
            initial_state = initial_state.to(
                module.torch.bfloat16
            ).contiguous()

            actual_seq_lengths = module.torch.diff(
                cu_seqlens
            ).to(module.torch.int32)

            output, final_state = torch_npu.npu_chunk_gated_delta_rule(
                q,
                k,
                v,
                beta=beta,
                initial_state=initial_state,
                actual_seq_lengths=actual_seq_lengths,
                scale=scale,
                g=g,
            )
            return output.unsqueeze(0), final_state

        cls._qwen35_fused_chunk_gated_delta_rule = staticmethod(
            _qwen35_fused_chunk_gated_delta_rule
        )
        old = """        initial_state = ssm_state[prefill_state_indices].transpose(-1, -2).contiguous()
        clear_ssm_states(initial_state, prefill_has_initial_state)
        (core_attn_out_non_spec, last_recurrent_state) = chunk_gated_delta_rule(
            q=query_non_spec,
            k=key_non_spec,
            v=value_non_spec,
            g=g_non_spec,
            beta=beta_non_spec,
            initial_state=initial_state,
            output_final_state=True,
            cu_seqlens=prefill_query_start_loc,
            prebuilt_meta=attn_metadata.non_spec_prefill_metadata.chunk,
            head_first=False,
            use_qk_l2norm_in_kernel=True,
        )
        ssm_state[prefill_state_indices] = last_recurrent_state.transpose(-1, -2).contiguous().to(ssm_state.dtype)
"""
        new = """        use_fused_chunk = (
            AscendGatedDeltaNetAttention._qwen35_probe_fused_chunk()
            and get_pcp_group().world_size == 1
        )
        if use_fused_chunk:
            initial_state = ssm_state[prefill_state_indices]
            clear_ssm_states(initial_state, prefill_has_initial_state)
            (core_attn_out_non_spec, last_recurrent_state) = AscendGatedDeltaNetAttention._qwen35_fused_chunk_gated_delta_rule(
                q=query_non_spec,
                k=key_non_spec,
                v=value_non_spec,
                g=g_non_spec,
                beta=beta_non_spec,
                initial_state=initial_state,
                cu_seqlens=prefill_query_start_loc,
                scale=key_non_spec.shape[-1] ** -0.5,
                attn_metadata=attn_metadata,
            )
            ssm_state[prefill_state_indices] = last_recurrent_state.to(ssm_state.dtype)
        else:
            initial_state = ssm_state[prefill_state_indices].transpose(-1, -2).contiguous()
            clear_ssm_states(initial_state, prefill_has_initial_state)
            (core_attn_out_non_spec, last_recurrent_state) = chunk_gated_delta_rule(
                q=query_non_spec,
                k=key_non_spec,
                v=value_non_spec,
                g=g_non_spec,
                beta=beta_non_spec,
                initial_state=initial_state,
                output_final_state=True,
                cu_seqlens=prefill_query_start_loc,
                prebuilt_meta=attn_metadata.non_spec_prefill_metadata.chunk,
                head_first=False,
                use_qk_l2norm_in_kernel=True,
            )
            ssm_state[prefill_state_indices] = last_recurrent_state.transpose(-1, -2).contiguous().to(ssm_state.dtype)
"""
        cls._forward_core = _replace_function_block(
            cls._forward_core,
            old,
            new,
            "AscendGatedDeltaNetAttention._forward_core.upstream_fused_prefill",
        )
        cls._qwen35_upstream_fused_prefill_monkeypatched = True
        _notice(
            "backported upstream 77d13e2c0 fused GDN prefill"
        )


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


def _patch_acl_graph(module: ModuleType) -> None:
    """Backport upstream MRV1 super-kernel capture to the official v0.23 image."""
    if not _super_kernel_enabled():
        return
    cls = module.ACLGraphWrapper
    if getattr(cls, "_qwen35_super_kernel_monkeypatched", False):
        return

    for owner, name in (
        (module.torch.npu, "super_kernel_scope_begin"),
        (module.torch.npu, "super_kernel_scope_end"),
        (module.torch.npu.NPUGraph, "super_kernel_optimize"),
    ):
        if not hasattr(owner, name):
            raise RuntimeError(f"MRV1 super-kernel runtime API is missing: {name}")

    @contextlib.contextmanager
    def _qwen35_super_kernel_scope(scope: str):
        module.torch.npu.super_kernel_scope_begin(scope)
        try:
            yield
        finally:
            module.torch.npu.super_kernel_scope_end(scope)

    # _replace_function_block compiles against the target function's globals.
    module._qwen35_super_kernel_scope = _qwen35_super_kernel_scope
    original_init = cls.__init__

    @functools.wraps(original_init)
    def __init__(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.enable_super_kernel = True

    old_capture = """                    output = self.runnable(*args, **kwargs)
"""
    new_capture = """                    with _qwen35_super_kernel_scope("full_model"):
                        output = self.runnable(*args, **kwargs)
"""
    old_optimize = """        # here we always use weak ref for the workspaces
"""
    new_optimize = """        aclgraph.super_kernel_optimize(
            optimize_options={"dcci_after_kernel_end": [".*"]},
        )
        logger.info(
            "[qwen35-monkeypatch] MRV1 super-kernel optimized ACL graph: %s",
            entry.batch_descriptor,
        )

        # here we always use weak ref for the workspaces
"""
    cls.__init__ = __init__
    cls.__call__ = _replace_function_blocks(
        cls.__call__,
        (
            ("capture", old_capture, new_capture),
            ("optimize", old_optimize, new_optimize),
        ),
        "ACLGraphWrapper.__call__",
    )
    cls._qwen35_super_kernel_monkeypatched = True
    _notice("backported upstream MRV1 ACL Graph super-kernel")


def _patch_compiler_interface(module: ModuleType) -> None:
    """Backport upstream MRV1 options into npugraph-ex static compilation."""
    if not _super_kernel_enabled():
        return
    if getattr(module, "_qwen35_super_kernel_monkeypatched", False):
        return
    old = """            options["_vllm_aclnn_static_kernel_sym_range"] = _compute_decode_cudagraph_batch_sizes(vllm_config)
"""
    new = """            options["_vllm_aclnn_static_kernel_sym_range"] = _compute_decode_cudagraph_batch_sizes(vllm_config)
            options["super_kernel_optimize"] = True
            options["super_kernel_optimize_options"] = {
                "dcci_after_kernel_end": [".*"],
            }
"""
    module._configure_backend = _replace_function_block(
        module._configure_backend,
        old,
        new,
        "compiler_interface._configure_backend",
    )
    module._qwen35_super_kernel_monkeypatched = True
    _notice("backported upstream MRV1 npugraph-ex options")


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
    if not _weight_prefetch_patch_enabled():
        return
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
    if not _weight_prefetch_patch_enabled():
        return
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


def _patch_scheduler_class(cls, label: str) -> None:
    if not _diagnostics_enabled():
        return
    if getattr(cls, "_qwen35_diagnostics_monkeypatched", False):
        return
    original = cls.schedule
    interval = _diagnostics_interval()

    @functools.wraps(original)
    def schedule(self, *args, **kwargs):
        before_running = len(getattr(self, "running", ()))
        before_waiting = len(getattr(self, "waiting", ()))
        throttle_prefills = kwargs.get("throttle_prefills")
        if throttle_prefills is None and args:
            throttle_prefills = args[0]
        started = time.perf_counter()
        output = original(self, *args, **kwargs)
        elapsed_us = (time.perf_counter() - started) * 1_000_000.0
        step = int(getattr(self, "_qwen35_diagnostics_step", 0)) + 1
        setattr(self, "_qwen35_diagnostics_step", step)
        if step <= 5 or step % interval == 0:
            num_tokens = getattr(output, "num_scheduled_tokens", {}) or {}
            total_tokens = sum(int(value) for value in num_tokens.values())
            new_reqs = len(getattr(output, "scheduled_new_reqs", ()) or ())
            cached_reqs = getattr(output, "scheduled_cached_reqs", None)
            cached_count = 0
            if cached_reqs is not None:
                cached_count = len(getattr(cached_reqs, "req_ids", ()) or ())
            prefill_count = sum(
                1
                for request in getattr(self, "running", ())
                if getattr(request, "is_prefill_chunk", False)
            )
            _notice(
                "diagnostic scheduler=%s step=%s elapsed_us=%.3f "
                "tokens=%s new=%s cached=%s running_before=%s "
                "waiting_before=%s running_after=%s prefill_after=%s "
                "throttle_prefills=%s prefill_capacity_bound=%s"
                % (
                    label,
                    step,
                    elapsed_us,
                    total_tokens,
                    new_reqs,
                    cached_count,
                    before_running,
                    before_waiting,
                    len(getattr(self, "running", ())),
                    prefill_count,
                    throttle_prefills,
                    getattr(self, "prefill_capacity_bound", None),
                )
            )
        return output

    cls.schedule = schedule
    cls._qwen35_diagnostics_monkeypatched = True
    _notice(f"patched {label} diagnostics")


def _patch_vllm_scheduler(module: ModuleType) -> None:
    _patch_scheduler_class(module.Scheduler, "vllm.v1.core.sched.scheduler.Scheduler")


def _patch_dyntra_scheduler(module: ModuleType) -> None:
    _patch_scheduler_class(module.DyntraLBScheduler, "DyntraLBScheduler")


_PATCHERS = {
    "vllm.compilation.backends": _patch_vllm_backends,
    "vllm.model_executor.models.registry": _patch_model_registry,
    "vllm.v1.core.sched.scheduler": _patch_vllm_scheduler,
    "vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn": _patch_qwen_gdn_linear_attn,
    "vllm.model_executor.models.qwen2_moe": _patch_qwen2_moe,
    "vllm.model_executor.models.qwen3_5": _patch_qwen35_model,
    "vllm_ascend.ascend_config": _patch_ascend_config,
    "vllm_ascend.compilation.acl_graph": _patch_acl_graph,
    "vllm_ascend.compilation.compiler_interface": _patch_compiler_interface,
    "vllm_ascend.compilation.graph_fusion_pass_manager": _patch_graph_manager,
    "vllm_ascend.ops.gdn": _patch_ascend_gdn,
    "vllm_ascend.ops.layernorm": _patch_layernorm,
    "vllm_ascend.ops.weight_prefetch": _patch_weight_prefetch,
    "vllm_ascend.core.dyntra_lb_scheduler": _patch_dyntra_scheduler,
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
