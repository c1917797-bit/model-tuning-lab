"""Small source-bound eager candidate; not a verified serving optimization."""
import functools
import hashlib
import inspect
import json
import os
from contextvars import ContextVar
from pathlib import Path
from .contract import (GDN_LAYERS, Ownership, Row, admit, admit_text_forward,
                       admit_text_request, byte_counts, require, require_copied_native,
                       typed_gdn_target, typed_shapes, verify_live_layers)
from .plan import MODEL_CONFIG_SHA256, PlanStore
from .state import cache_contract, pack_native

SOURCES = {
    "/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py": "21fc9a2064f9b490ffcf3d61bacc8ddb67806a4c7490895a33128e65438838d3",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py": "885c56f5e3584ab60bb4ce4b42cf8259e5e92c86ba13aa6128e6ed7a2a20d2b0",
    "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py": "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
    "/vllm-workspace/vllm/vllm/v1/worker/gpu_input_batch.py": "caeeb20f5010d74663c45f9419237191e3c0a149f4c7aa25bc1b73b1112d67ae",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/npu_input_batch.py": "a4dc08a9918f07797622f8d0915785e8c7b6899e0d10d92603e1dddec218acc3",
    "/vllm-workspace/vllm/vllm/v1/attention/backends/utils.py": "f4f2f106ad84aa77cdf0b09d6948878f4e74c56568309312ec47bd190cc710cd",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py": "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py": "94d75dbeb5d23ab5b383cdc69114167392b967994bb21342cf748b733ba9a968",
    "/vllm-workspace/vllm-ascend/vllm_ascend/worker/block_table.py": "8f77809c12af3bd9d56974edbbe5c792995f2620aadfe62411806f2e68d2ef0a",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py": "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/abstract.py": "d7cba061c9d8c55b00e18bc7af515cfd28d875eee76c04fea7f6861f2d1c4e08",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/mamba_utils.py": "aa9b7dc46725a012fc61b83a7181baaddad7ab4b0eb8e4144350799697ad6a42",
    "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/base.py": "7fec748fc74131f5a45bcaf2644b3fa3a0598fd437d7347f8207ea3644a951c5",
    "/vllm-workspace/vllm/vllm/v1/kv_cache_interface.py": "8d6be98bbf75b3d55007b64ccf5afef047ca01790a432522f70a196412c103d9",
    "/vllm-workspace/vllm/vllm/model_executor/models/qwen3_5.py": "04f3de5372973770d71c5c05f2e8a5e221ec52b62cca7a1e302d9201b61b8adc"
}
_ACTIVE = ContextVar("damp_packed_turn", default=None)
_INSTALLED = False
_VERIFIED_MODELS = set()

def verify_sources():
    for path, expected in SOURCES.items():
        require(hashlib.sha256(Path(path).read_bytes()).hexdigest() == expected,
                "DAMP unsupported source drift: " + path)

def _config(config, torch, max_batch):
    c, p, s, m = config.cache_config, config.parallel_config, config.scheduler_config, config.model_config
    model_path = str(Path(m.model).resolve(strict=True))
    if model_path not in _VERIFIED_MODELS:
        require(hashlib.sha256((Path(model_path) / "config.json").read_bytes()).hexdigest() ==
                MODEL_CONFIG_SHA256, "loaded model configuration does not match DAMP plan")
        _VERIFIED_MODELS.add(model_path)
    require(c.enable_prefix_caching is False and c.mamba_cache_mode == "none",
            "DAMP v1 requires prefix off and mamba cache none")
    require(config.speculative_config is None and config.kv_transfer_config is None,
            "speculation/PD connectors are unsupported")
    require(m.dtype == torch.bfloat16 and m.enforce_eager is True, "BF16 eager only; graph is unvalidated")
    require(m.is_encoder_decoder is False and m.runner_type == "generate" and
            m.enable_prompt_embeds is False, "text generation only; encoder/prompt-embedding modes unsupported")
    require(s.enable_chunked_prefill is False, "continuation/chunked prefill unsupported")
    require(s.max_num_seqs <= max_batch, "scheduler batch cap exceeds admitted operator regime")
    require(p.tensor_parallel_size == 4 and p.pipeline_parallel_size == 1
            and p.prefill_context_parallel_size == 1 and p.decode_context_parallel_size == 1,
            "only local TP4 without PP/CP is admitted")
    require(not getattr(s, "async_scheduling", False), "async scheduling unsupported")

def _cpu_list(value, name):
    require(getattr(value, "device", None) is not None and value.device.type == "cpu",
            name + " must already be CPU; no hot-path device-to-host metadata copy")
    return value.tolist()

def install():
    global _INSTALLED
    if _INSTALLED:
        return
    require(os.environ.get("DAMP_PACKED_ENABLED") == "1", "explicit DAMP opt-in missing")
    verify_sources()
    # Preserve the image ops initialization order (no early direct attention import).
    import torch
    import vllm_ascend.ops
    from vllm_ascend.ops import gdn
    from vllm_ascend.worker.model_runner_v1 import NPUModelRunner
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention as qwen_cls
    from vllm.model_executor.layers.mamba.abstract import MambaBase
    from vllm.model_executor.layers.mamba.mamba_utils import (
        MambaStateShapeCalculator, MambaStateDtypeCalculator,
        MambaStateCopyFuncCalculator, get_conv_copy_spec, get_temporal_copy_spec,
        get_conv_state_layout,
    )
    # File hashes alone cannot prove that a different installed plugin did not
    # replace a live callable. Check actual code ownership before any patches.
    seams = (
        (gdn.AscendGatedDeltaNetAttention._forward_core, "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py"),
        (MambaBase.get_kv_cache_spec, "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/abstract.py"),
        (NPUModelRunner._model_forward, "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py"),
        (NPUModelRunner._reshape_kv_cache_tensors, "/vllm-workspace/vllm-ascend/vllm_ascend/worker/model_runner_v1.py"),
        (MambaStateShapeCalculator.gated_delta_net_state_shape, "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/mamba_utils.py"),
        (MambaStateDtypeCalculator.gated_delta_net_state_dtype, "/vllm-workspace/vllm/vllm/model_executor/layers/mamba/mamba_utils.py"),
    )
    for seam, expected_path in seams:
        require(str(Path(inspect.getfile(seam)).resolve()) == expected_path,
                "another live plugin already owns DAMP seam: " + expected_path)
    require_copied_native(qwen_cls, gdn.AscendGatedDeltaNetAttention)
    native_forward = gdn.AscendGatedDeltaNetAttention.forward
    require(get_conv_state_layout() == "SD", "first candidate requires native SD conv layout")
    max_batch = int(os.environ.get("DAMP_MAX_DECODE_BATCH", "1"))
    require(max_batch in (1, 16), "only exact B1/B16 operator variants exist")
    library = Path(os.environ["DAMP_PACKED_LIBRARY"]).resolve(strict=True)
    plans = PlanStore(os.environ["DAMP_SERVING_PLAN"], library, torch)
    torch.ops.load_library(str(library))
    require(hasattr(torch.ops.qwen36_damp, "prepare") and hasattr(torch.ops.qwen36_damp, "decode"),
            "independently named DAMP operator unavailable")
    original_shape = MambaStateShapeCalculator.gated_delta_net_state_shape.__func__
    original_dtype = MambaStateDtypeCalculator.gated_delta_net_state_dtype.__func__
    original_spec = MambaBase.get_kv_cache_spec
    original_runner = NPUModelRunner._model_forward
    original_runner_signature = inspect.signature(original_runner)
    original_reshape = NPUModelRunner._reshape_kv_cache_tensors
    layers, owners, prepared = {}, {}, set()
    verified_runners = set()

    @classmethod
    def shape_calc(cls, *args, **kwargs):
        conv, native = original_shape(cls, *args, **kwargs)
        require(tuple(native) == (12, 128, 128), "DAMP requires TP4 Hv12 V128 K128")
        return typed_shapes(conv)

    @classmethod
    def dtype_calc(cls, *args, **kwargs):
        conv, native = original_dtype(cls, *args, **kwargs)
        require(conv == torch.bfloat16 and native == torch.float32,
                "native BF16-conv/FP32-state contract is required")
        return conv, torch.float16, torch.int8, torch.float32

    def checked_copy(native_func):
        def copy(state, block_ids, cur_block_idx, num_accepted_tokens):
            require(num_accepted_tokens == 1, "speculative typed-state copy unsupported")
            return native_func(state, block_ids, cur_block_idx, num_accepted_tokens)
        return copy

    @classmethod
    def copy_calc(cls):
        # The first candidate never enters align/all. Cardinality is still exact.
        return (checked_copy(get_conv_copy_spec),) + (checked_copy(get_temporal_copy_spec),) * 3

    @functools.wraps(original_spec)
    def cache_spec(layer, config):
        if not typed_gdn_target(layer, gdn.GatedDeltaNetAttention, qwen_cls):
            return original_spec(layer, config)
        _config(config, torch, max_batch)
        require(int(layer.layer_idx) in GDN_LAYERS and layer.tp_size == 4,
                "unexpected installed GDN layer")
        result = original_spec(layer, config)
        require(len(result.shapes) == len(result.dtypes) == 4, "typed cache spec cardinality mismatch")
        layers[layer.prefix] = layer
        owners.setdefault(layer.prefix, Ownership())
        return result

    @functools.wraps(original_reshape)
    def reshape(runner, config, raw):
        result = original_reshape(runner, config, raw)
        for name, layer in layers.items():
            require(name in result, "GDN cache missing from real allocator")
            slots = cache_contract(result[name], torch)
            require(slots >= config.num_blocks, "allocator slot count insufficient")
            # Emit once per rank/layer; page padding is NOT claimed as byte saving.
            spec = runner._get_layer_kv_cache_specs(config)[name]
            receipt = dict(event="damp_typed_cache_allocated", rank=int(layer.tp_rank),
                           layer=int(layer.layer_idx), slots=slots,
                           persistent_state_dtypes=[str(t.dtype) for t in result[name]],
                           **byte_counts(result[name][0].shape[1:], spec.page_size_padded))
            print("DAMP_EVIDENCE " + json.dumps(receipt, sort_keys=True), flush=True)
        return result

    @functools.wraps(original_runner)
    def model_forward(runner, num_tokens_padded, *args, **kwargs):
        ctx = gdn.get_forward_context()
        metadata = ctx.attn_metadata
        if metadata is None:
            require(int(runner.input_batch.num_reqs) == 0, "real requests without attention metadata unsupported")
            return original_runner(runner, num_tokens_padded, *args, **kwargs)
        _config(runner.vllm_config, torch, max_batch)
        require(isinstance(metadata, dict), "microbatch metadata unsupported")
        require(len(layers) == 48 and {int(l.layer_idx) for l in layers.values()} == set(GDN_LAYERS),
                "all 48 installed GDN layers must be patched")
        batch = runner.input_batch
        n = int(batch.num_reqs)
        ids = list(batch.req_ids[:n])
        require(len(ids) == n, "ordered request identity count mismatch")
        require(n > 0 and all(isinstance(rid, str) and rid for rid in ids),
                "real ordered request identities required")
        starts = _cpu_list(runner.query_start_loc.cpu[:n + 1], "query_start_loc")
        computed = _cpu_list(batch.num_computed_tokens_cpu_tensor[:n], "computed tokens")
        prompt = _cpu_list(batch.num_prompt_tokens_cpu_tensor[:n], "prompt tokens")
        require(starts[0] == 0 and starts[-1] == int(num_tokens_padded), "dummy token padding unsupported")
        try:
            bound = original_runner_signature.bind(runner, num_tokens_padded, *args, **kwargs)
        except TypeError as error:
            require(False, "unsupported model-forward call: " + str(error))
        bound.apply_defaults()
        require(not runner.supports_mm_inputs or hasattr(runner.model, "requires_raw_input_tokens"),
                "native multimodal input capability schema missing")
        requires_raw = runner.model.requires_raw_input_tokens if runner.supports_mm_inputs else False
        kind = admit_text_forward(bound.arguments["input_ids"], bound.arguments["inputs_embeds"],
                                  bound.arguments["intermediate_tensors"], bound.arguments["model_kwargs"],
                                  runner.supports_mm_inputs, requires_raw)
        require(all(hasattr(batch, name) for name in ("req_prompt_embeds", "is_token_ids_tensor")),
                "batch token/embedding payload schema missing")
        require(isinstance(batch.req_prompt_embeds, dict) and not batch.req_prompt_embeds,
                "batch prompt-embedding payload unsupported")
        require(isinstance(runner.encoder_cache, dict) and not runner.encoder_cache,
                "encoder/media cache payload unsupported")
        mask = batch.is_token_ids_tensor
        require(mask.device.type == "cpu" and mask.dtype == torch.bool and mask.ndim == 2 and
                mask.shape[0] >= n, "existing CPU token/embedding mask required")
        for i, rid in enumerate(ids):
            require(rid in runner.requests, "scheduled request has no cached payload")
            admit_text_request(runner.requests[rid], rid, int(prompt[i]))
            begin, end = int(computed[i]), int(computed[i] + starts[i + 1] - starts[i])
            require(0 <= begin < end <= mask.shape[1] and bool(mask[i, begin:end].all().item()),
                    "scheduled soft/mixed tokens unsupported")
        input_kinds = (kind, "input_ids") if kind == "inputs_embeds" and requires_raw else (kind,)
        for input_kind in input_kinds:
            value = bound.arguments[input_kind]
            native = getattr(runner, input_kind).gpu
            require(isinstance(value, torch.Tensor) and value.shape == native[:int(num_tokens_padded)].shape and
                    value.dtype == native.dtype and value.device == native.device and
                    value.untyped_storage().data_ptr() == native.untyped_storage().data_ptr() and
                    value.storage_offset() == native.storage_offset(), "non-native model input buffer unsupported")
        prefixes = verify_live_layers(ctx.no_compile_layers, layers, qwen_cls, core, native_forward)
        if id(runner) not in verified_runners:
            receipt = dict(event="damp_actual_qwen_bindings_verified", layers=len(prefixes),
                           rank=int(next(iter(layers.values())).tp_rank), prefixes=list(prefixes),
                           actual_class=qwen_cls.__module__ + "." + qwen_cls.__qualname__,
                           target_source_sha256=SOURCES["/vllm-workspace/vllm/vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py"],
                           copier_source_sha256=SOURCES["/vllm-workspace/vllm-ascend/vllm_ascend/patch/worker/patch_qwen3_5.py"])
            print("DAMP_EVIDENCE " + json.dumps(receipt, sort_keys=True), flush=True)
            verified_runners.add(id(runner))
        turns = {}
        for name, layer in layers.items():
            matches = [i for i, group in enumerate(runner.kv_cache_config.kv_cache_groups)
                       if name in group.layer_names]
            require(len(matches) == 1, "ambiguous GDN cache group")
            table = batch.block_table[matches[0]].get_cpu_tensor()
            require(table.device.type == "cpu", "block table CPU mirror unavailable")
            slots = int(layer.kv_cache[0].shape[0])
            rows = tuple(Row(str(rid), int(table[i, 0]), int(starts[i + 1] - starts[i]),
                             int(computed[i]), int(prompt[i])) for i, rid in enumerate(ids))
            turn = admit(rows, slots, max_batch)
            owners[name].check(turn)
            md = metadata[name]
            require(md.spec_sequence_masks is None and md.num_actual_tokens == starts[-1],
                    "speculative/padded GDN metadata unsupported")
            require((md.num_prefills, md.num_decodes) ==
                    ((1, 0) if turn.mode == "prefill" else (0, n)), "CPU/native scheduling order mismatch")
            turns[name] = turn
        marker = _ACTIVE.set(turns)
        try:
            result = original_runner(runner, num_tokens_padded, *args, **kwargs)
        finally:
            _ACTIVE.reset(marker)
        for name, turn in turns.items():
            owners[name].publish(turn)
        return result

    def core(layer, mixed_qkv, b, a, core_attn_out):
        metadata = gdn.get_forward_context().attn_metadata
        if metadata is None:
            return  # native V1 profile behavior; no persistent state read/write
        active = _ACTIVE.get()
        require(active is not None and layer.prefix in active, "missing pre-dispatch CPU admission")
        turn = active[layer.prefix]
        md = metadata[layer.prefix]
        cache_contract(layer.kv_cache, torch)
        conv, high, low, scales = layer.kv_cache
        tokens = int(md.num_actual_tokens)
        require(mixed_qkv.shape[0] == tokens and b.shape[0] == tokens and a.shape[0] == tokens,
                "profile/dummy padding unsupported")
        plan = plans.get(layer.tp_rank, layer.layer_idx, mixed_qkv.device)
        weights = layer.conv1d.weight.view(layer.conv1d.weight.size(0), layer.conv1d.weight.size(2))
        conv_metadata = (md.non_spec_prefill_metadata if turn.mode == "prefill"
                         else md.non_spec_decode_metadata).causal_conv1d
        convolved = torch.empty_like(mixed_qkv)
        torch.ops._C_ascend.npu_causal_conv1d_custom(
            convolved, mixed_qkv, weights.transpose(0, 1), conv_state=conv,
            bias_opt=layer.conv1d.bias, query_start_loc_opt=conv_metadata.query_start_loc,
            cache_indices_opt=conv_metadata.cache_indices,
            initial_state_mode_opt=conv_metadata.initial_state_mode if turn.mode == "prefill" else None,
            num_accepted_tokens_opt=None, activation_mode=1 if layer.activation else 0,
            pad_slot_id=gdn.PAD_SLOT_ID, run_mode=0 if turn.mode == "prefill" else 1)
        query, key, value = layer.rearrange_mixed_qkv(convolved)
        g, beta = gdn.DeviceOperator.fused_gdn_gating(layer.A_log, a, b, layer.dt_bias)
        if turn.mode == "prefill":
            # Exactly one transient FP32 state; never S-slot dense sidecar.
            scratch = torch.zeros((1, 12, 128, 128), dtype=torch.float32, device=mixed_qkv.device)
            out, last = gdn.chunk_gated_delta_rule(
                q=query, k=key, v=value, g=g, beta=beta, initial_state=scratch,
                output_final_state=True, cu_seqlens=md.prefill_query_start_loc,
                prebuilt_meta=md.non_spec_prefill_metadata.chunk,
                head_first=False, use_qk_l2norm_in_kernel=True)
            packed = pack_native(last.transpose(-1, -2).contiguous(), plan, torch)
            slot = turn.rows[0].slot
            for target, source in zip((high, low, scales), packed):
                target[slot].copy_(source[0])
            # scratch/last/packed die with this call; no full-state retention.
        else:
            query = gdn.l2norm_fwd(query).squeeze(0).contiguous()
            key = gdn.l2norm_fwd(key).squeeze(0).contiguous()
            identity = (layer.prefix, tokens, high.shape[0], str(high.device))
            if identity not in prepared:
                # Eager-only initial prepare, outside all graph capture.
                torch.ops.qwen36_damp.prepare(query, high, plan.pk, plan.pv, plan.inv_pv, plan.sr)
                prepared.add(identity)
            out = torch.ops.qwen36_damp.decode(
                query, key, value.squeeze(0).contiguous(), g.squeeze(0).contiguous(),
                beta.squeeze(0).contiguous(), high, low, scales,
                plan.pk, plan.pv, plan.inv_pv, plan.sr,
                md.non_spec_decode_metadata.actual_seq_lengths,
                md.non_spec_state_indices_tensor).unsqueeze(0)
        core_attn_out[:tokens] = out.squeeze(0)

    MambaStateShapeCalculator.gated_delta_net_state_shape = shape_calc
    MambaStateDtypeCalculator.gated_delta_net_state_dtype = dtype_calc
    MambaStateCopyFuncCalculator.gated_delta_net_state_copy_func = copy_calc
    MambaBase.get_kv_cache_spec = cache_spec
    NPUModelRunner._reshape_kv_cache_tensors = reshape
    NPUModelRunner._model_forward = model_forward
    gdn.AscendGatedDeltaNetAttention._forward_core = core
    qwen_cls._forward_core = core
    _INSTALLED = True
    print("DAMP_EVIDENCE " + json.dumps(dict(event="damp_packed_patch_installed",
          purpose=plans.manifest["purpose"], max_decode_batch=max_batch,
          source_hashes=SOURCES, graph_supported=False)), flush=True)
