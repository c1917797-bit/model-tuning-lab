"""Fail-closed vLLM-Ascend v0.23 adapter for Qwen3.6 KVBuffer."""

from __future__ import annotations
from contextvars import ContextVar
from .contract import (SOURCES, IMAGE, MODEL_CONFIG, LAYERS, source_identity, require, sha,
                       aux_bytes, admit_lengths, admit_text_request, bind, live_bindings)

import hashlib
import inspect
import json
import logging
import os
from pathlib import Path
import threading
import time
from typing import Any


LOGGER = logging.getLogger(__name__)
PATCH_VERSION = "0.1.0-P1-parallel-fp32"
ENABLE_ENV = "QWEN36_KVBP_ENABLE"
LIBRARY_ENV = "QWEN36_KVBP_LIBRARY"
AUDIT_ENV = "QWEN36_KVBP_AUDIT"
EXPECTED_GDN_SHA256 = "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
LIBRARY_SHA_ENV = "QWEN36_KVBP_LIBRARY_SHA256"
_TURN = ContextVar("kvbp_admitted_turn", default=None)
EXPECTED_SCHEMA = (
    "qwen36_kvbuffer_parallel_fp32::decode(Tensor query, Tensor key, Tensor value, Tensor g, "
    "Tensor beta, Tensor(a!) base_state, Tensor(b!) k_log, Tensor(c!) u_log, "
    "Tensor(d!) lambda_log, Tensor(e!) cumulative_decay, Tensor(f!) log_length, "
    "Tensor actual_seq_lengths, Tensor state_indices) -> Tensor"
)
PACKED_WIDTH = 2560
KEY_HEADS = 4
VALUE_HEADS = 12
HEAD_DIM = 128
CAPACITY = 16
META_STRIDE = 32
_LOCK = threading.Lock()
_SEEN: set[tuple[int, str, str]] = set()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _audit(event: str, **fields: Any) -> None:
    path_value = os.environ.get(AUDIT_ENV)
    if not path_value:
        return
    payload = {
        "event": event,
        "patch_version": PATCH_VERSION,
        "pid": os.getpid(),
        "rank": os.environ.get("RANK"),
        "local_rank": os.environ.get("LOCAL_RANK"),
        "time_ns": time.time_ns(),
        **fields,
    }
    data = (json.dumps(payload, sort_keys=True, allow_nan=False) + "\n").encode()
    path = Path(path_value)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)


def _audit_once(event: str, key: str, **fields: Any) -> None:
    identity = (os.getpid(), event, key)
    with _LOCK:
        if identity in _SEEN:
            return
        _SEEN.add(identity)
    _audit(event, key=key, **fields)


def _valid_base(torch: Any, self: Any) -> Any | None:
    if len(getattr(self, "kv_cache", ())) < 2:
        return None
    base = self.kv_cache[1]
    if not isinstance(base, torch.Tensor):
        return None
    if base.device.type != "npu" or base.dtype != torch.float32 or base.ndim != 4:
        return None
    if list(base.shape[1:]) != [VALUE_HEADS, HEAD_DIM, HEAD_DIM]:
        return None
    return base


def _ensure_aux(torch: Any, self: Any) -> dict[str, Any] | None:
    base = _valid_base(torch, self)
    if base is None:
        return None
    import torch_npu
    require(torch_npu.get_npu_format(base) == 2, "native base physical ND required")
    existing = getattr(self, "_kvbp_aux", None)
    base_ptr = base.untyped_storage().data_ptr()
    if existing is not None:
        require(existing["base_ptr"] == base_ptr and existing["slots"] == int(base.shape[0]),
                "native cache storage changed; migration unsupported")
        return existing
    require(getattr(self, "_kvbp_allocation_admitted", False), "reserve full48 auxiliary budget first")
    def zeros(shape, dtype):
        t = torch.zeros(shape, dtype=dtype, device=base.device)
        t = torch_npu.npu_format_cast(t, 2)
        require(torch_npu.get_npu_format(t) == 2 and t.is_contiguous(), "aux ND allocation failed")
        return t

    slots = int(base.shape[0])
    options = {"device": base.device}
    aux = {
        "base_ptr": base_ptr,
        "slots": slots,
        "k_log": zeros((slots, KEY_HEADS, CAPACITY, HEAD_DIM), torch.bfloat16),
        "u_log": zeros((slots, VALUE_HEADS, CAPACITY, HEAD_DIM), torch.float32),
        "lambda_log": zeros((slots, VALUE_HEADS, META_STRIDE), torch.float32),
        "decay": zeros((slots, VALUE_HEADS, META_STRIDE), torch.float32),
        "length": zeros((slots, VALUE_HEADS, META_STRIDE), torch.int32),
    }
    self._kvbp_aux = aux
    bytes_allocated = sum(
        tensor.numel() * tensor.element_size()
        for tensor in aux.values()
        if isinstance(tensor, torch.Tensor)
    )
    _audit(
        "aux_allocated",
        prefix=getattr(self, "prefix", None),
        slots=slots,
        bytes=bytes_allocated,
        base_ptr=base_ptr,
    )
    return aux


def _reset_selected(aux: dict[str, Any], indices: Any) -> None:
    if indices is None or indices.numel() == 0:
        return
    selected = indices.flatten().long()
    for name in ("k_log", "u_log", "lambda_log", "decay", "length"):
        aux[name].index_fill_(0, selected, 0)


def _flush_slots(
    torch: Any, self: Any, aux: dict[str, Any], indices: Any, reason: str,
    selection: str = "batch",
) -> None:
    if indices.numel() == 0:
        return
    base = self.kv_cache[1]
    if indices.device != base.device or indices.dtype not in (torch.int32, torch.int64):
        raise RuntimeError("KVBuffer fallback slot indices must be NPU int32/int64")
    selected = indices.reshape(-1).long()
    selected_base = base.index_select(0, selected)
    k_log = (
        aux["k_log"]
        .index_select(0, selected)
        .float()
        .repeat_interleave(VALUE_HEADS // KEY_HEADS, dim=1)
    )
    u_log = aux["u_log"].index_select(0, selected).float()
    lambda_log = aux["lambda_log"].index_select(0, selected)[:, :, :CAPACITY]
    decay = aux["decay"].index_select(0, selected)[:, :, 0]
    length = aux["length"].index_select(0, selected)[:, :, 0]
    live = (
        torch.arange(CAPACITY, dtype=torch.int32, device=base.device)
        .view(1, 1, CAPACITY)
        < length.unsqueeze(-1)
    )
    # Dead entries retain stale payload after a selected-slot flush. Mask the
    # exponent *before* exp: multiplying an overflowed exp by zero is NaN.
    safe_lambda = torch.where(live, lambda_log, decay.unsqueeze(-1))
    coeff = torch.exp(decay.unsqueeze(-1) - safe_lambda) * live.float()
    contribution = torch.einsum("shl,shlv,shlk->shvk", coeff, u_log, k_log)
    logical = (
        torch.exp(decay).unsqueeze(-1).unsqueeze(-1) * selected_base
        + contribution
    )
    base.index_copy_(0, selected, logical)
    # A zero length makes K/U/lambda payloads invisible. Clearing those large
    # tensors on every mixed batch would undo the deferred-write saving; the
    # next append overwrites entry zero before it becomes live again.
    aux["decay"].index_fill_(0, selected, 0)
    aux["length"].index_fill_(0, selected, 0)
    _audit(
        "aux_materialized_for_fallback",
        prefix=getattr(self, "prefix", None),
        reason=reason,
        selection=selection,
        selected_slots=int(selected.numel()),
    )


def _eligibility_reason(
    torch: Any,
    self: Any,
    metadata: Any,
    aux: dict[str, Any] | None,
    mixed_qkv: Any,
    b: Any,
    a: Any,
    core: Any,
) -> str | None:
    if aux is None:
        return "aux_unavailable"
    if metadata.spec_sequence_masks is not None:
        return "speculative_or_multi_query"
    if metadata.num_prefills != 0 or metadata.num_decodes <= 0:
        return "not_pure_decode"
    tokens = int(metadata.num_actual_tokens)
    if tokens != int(metadata.num_decodes) or tokens != int(metadata.num_decode_tokens):
        return "decode_token_count_mismatch"
    if tokens < 1 or tokens > 16:
        return "decode_token_count_unsupported"
    tensors = (mixed_qkv, b, a, core)
    if any(not isinstance(t, torch.Tensor) or t.device.type != "npu" for t in tensors):
        return "non_npu_tensor"
    if mixed_qkv.dtype != torch.bfloat16 or list(mixed_qkv.shape) != [tokens, PACKED_WIDTH]:
        return "packed_qkv_contract"
    if b.dtype != torch.bfloat16 or a.dtype != torch.bfloat16:
        return "gating_dtype"
    if list(b.shape) != [tokens, VALUE_HEADS] or list(a.shape) != [tokens, VALUE_HEADS]:
        return "gating_shape"
    if core.dtype != torch.bfloat16 or list(core.shape[1:]) != [VALUE_HEADS, HEAD_DIM]:
        return "output_contract"
    if getattr(self, "tp_size", None) != 4:
        return "tp_size"
    if getattr(self, "head_k_dim", None) != HEAD_DIM or getattr(self, "head_v_dim", None) != HEAD_DIM:
        return "head_dim"
    if getattr(self, "num_k_heads", None) // self.tp_size != KEY_HEADS:
        return "local_key_heads"
    if getattr(self, "num_v_heads", None) // self.tp_size != VALUE_HEADS:
        return "local_value_heads"
    indices = metadata.non_spec_state_indices_tensor
    if indices is None or indices.device.type != "npu" or indices.dtype != torch.int32:
        return "state_indices_contract"
    if indices.numel() != tokens:
        return "state_indices_shape"
    decode = metadata.non_spec_decode_metadata
    if decode is None or decode.causal_conv1d is None:
        return "decode_metadata"
    seq = decode.actual_seq_lengths
    if seq is None or seq.device.type != "npu" or seq.dtype != torch.int32:
        return "actual_seq_lengths_contract"
    if seq.numel() != tokens + 1:
        return "actual_seq_lengths_shape"
    return None


def register() -> None:
    """Install the adapter only when explicitly enabled."""
    if os.environ.get(ENABLE_ENV) != "1":
        return

    import torch

    library_value = os.environ.get(LIBRARY_ENV)
    if not library_value:
        raise RuntimeError(f"{LIBRARY_ENV} is required when {ENABLE_ENV}=1")
    library = Path(library_value).resolve()
    if not library.is_file():
        raise RuntimeError(f"candidate library not found: {library}")
    library_sha256 = _sha256(library)
    expected_library_sha256 = os.environ.get(LIBRARY_SHA_ENV, "")
    require(len(expected_library_sha256) == 64 and
            all(c in "0123456789abcdef" for c in expected_library_sha256),
            "explicit built artifact SHA256 required")
    if library_sha256 != expected_library_sha256:
        raise RuntimeError(
            f"candidate library identity changed: {library_sha256}; "
            f"expected {expected_library_sha256}"
        )

    from vllm_ascend.utils import enable_custom_op

    if not enable_custom_op():
        raise RuntimeError("vLLM-Ascend custom operators are unavailable")
    torch.ops.load_library(str(library))
    schema = str(torch.ops.qwen36_kvbuffer_parallel_fp32.decode.default._schema)
    if schema != EXPECTED_SCHEMA:
        raise RuntimeError(f"candidate schema changed: {schema}")

    import vllm_ascend.ops  # retain deployed v0.23 import order
    import vllm_ascend.ops.gdn as gdn
    import vllm_ascend.worker.model_runner_v1 as runner_module
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    from vllm.distributed import get_tensor_model_parallel_rank, get_tensor_model_parallel_world_size
    import torch.distributed as dist
    actual_sources = source_identity()
    require(os.environ.get(AUDIT_ENV), "durable external audit path is mandatory")
    require(sha(os.environ.get("QWEN36_KVBP_MODEL_CONFIG", "/models/Qwen3.6-27B/config.json")) ==
            MODEL_CONFIG, "checkpoint configuration changed")

    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd
    from vllm_ascend.device.device_op import DeviceOperator

    source = Path(gdn.__file__).resolve()
    source_sha256 = _sha256(source)
    if source_sha256 != EXPECTED_GDN_SHA256:
        raise RuntimeError(
            f"vLLM-Ascend GDN source changed: {source_sha256}; re-audit required"
        )

    cls = gdn.AscendGatedDeltaNetAttention
    if getattr(cls, "_kvbp_patch_version", None) == PATCH_VERSION:
        return
    if hasattr(cls, "_kvbp_original_forward_core"):
        raise RuntimeError("another KVBuffer patch is already installed")
    if hasattr(cls, "_qwen36_deltalog_original_forward_core"):
        raise RuntimeError("the incompatible DeltaLog patch is installed")
    if hasattr(cls, "_qwen36_decode_core_patch_version"):
        raise RuntimeError("the incompatible GDN decode-core patch is installed")

    target, runner_cls = QwenGatedDeltaNetAttention, runner_module.NPUModelRunner
    require(target._forward_core is cls._forward_core and target.forward is cls.forward,
            "real Qwen receiver did not acquire pinned Ascend aliases")
    original = cls._forward_core
    require(Path(inspect.getfile(original)).resolve() == source and
            Path(inspect.getfile(target.forward)).resolve() == source,
            "native owning function changed despite matching source files")
    original_forward = runner_cls._model_forward
    require(not hasattr(runner_cls, "_kvbp_original_forward"), "runner already patched")
    ranks_initialized = set()
    owners = {}
    request_slots = {}
    frame_count = 0

    def runner_forward(runner, *args, **kwargs):
        nonlocal frame_count
        batch = runner.input_batch
        count = int(batch.num_reqs)
        ids = tuple(batch.req_ids[:count])
        if not ids:
            require(not ranks_initialized, "post-allocation warmup outside admitted real requests")
            return original_forward(runner, *args, **kwargs)
        require(dist.is_initialized() and dist.get_world_size() == 4 and
                get_tensor_model_parallel_world_size() == 4, "TP4/world4 required")
        rank = get_tensor_model_parallel_rank()
        require(rank in range(4) and torch.npu.current_device() == rank, "device/rank mismatch")
        require(runner.model_config.enforce_eager, "P1 service adapter is eager-only; graph probe is separate")
        require(not runner.speculative_config and runner.pcp_size == runner.dcp_size == 1,
                "speculation/context parallel unsupported")
        config = runner.vllm_config
        require(config.cache_config.enable_prefix_caching is False and
                str(config.cache_config.mamba_cache_mode) == "none" and
                config.scheduler_config.enable_chunked_prefill is False,
                "prefix/chunked cache lifecycle not admitted")
        active_ids = set(runner.requests)
        require(ids and len(set(ids)) == len(ids), "nonunique scheduled IDs")
        for rid in ids:
            request = runner.requests[rid]
            admit_text_request(request.prompt_token_ids, request.prompt_embeds,
                               request.mm_features, request.prompt_is_token_ids)
        context = gdn.get_forward_context()
        require(isinstance(context.attn_metadata, dict), "metadata mapping missing")
        bindings = live_bindings(context.no_compile_layers, cls, target, patched_forward_core)
        layers = [context.no_compile_layers[row["prefix"]] for row in bindings]
        starts = runner.gdn_query_start_loc.cpu[:count+1].tolist()
        require(len(starts)==count+1 and starts[0]==0 and
                all(x<y for x,y in zip(starts,starts[1:])), "CPU query starts invalid")
        frame = {"rows": {}, "seen": set(), "rank": rank}
        mirror_cache = {}
        for attention in layers:
            meta = context.attn_metadata[attention.prefix]
            require(meta.spec_sequence_masks is None, "speculative masks unsupported")
            nd, np = int(meta.num_decodes), int(meta.num_prefills)
            require(nd+np==count and int(meta.num_decode_tokens)==nd and nd<=16 and
                    int(meta.num_actual_tokens)==starts[-1], "real request/token partition mismatch")
            require(starts[:nd+1]==list(range(nd+1)), "decode order/one-token CPU proof")
            base = _valid_base(torch, attention)
            require(base is not None, "native FP32 state unavailable")
            def mirror(t):
                key=(t.data_ptr(),tuple(t.shape),str(t.dtype))
                if key not in mirror_cache:
                    mirror_cache[key]=t.detach().cpu().tolist()
                return mirror_cache[key]
            ds = mirror(meta.non_spec_state_indices_tensor)[:nd] if nd else []
            ps = mirror(meta.prefill_state_indices) if np else []
            if nd:
                seq = mirror(meta.non_spec_decode_metadata.actual_seq_lengths)
                require(len(seq)==nd+1, "P1 eager seq must not contain graph padding")
                admit_lengths(seq,ds,nd,int(base.shape[0]),nd)
            if np:
                require(not any(mirror(meta.prefill_has_initial_state)), "restored/continued prefix rejected")
                loc=mirror(meta.prefill_query_start_loc)
                require(loc==[v-nd for v in starts[nd:]], "native prefill timeline differs from CPU starts")
            slots=ds+ps
            require(len(slots)==count and len(set(slots))==count and
                    all(type(s) is int and 0<=s<base.shape[0] for s in slots),
                    "cross-request state slots invalid")
            for rid,slot in zip(ids,slots):
                key=(attention.prefix,slot)
                owner=owners.get(key)
                require(owner is None or owner==rid or owner not in active_ids,
                        "state slot still belongs to another live request")
                previous=request_slots.get((attention.prefix,rid))
                require(previous is None or previous==slot, "cache migration/slot move unsupported")
                owners[key]=rid; request_slots[(attention.prefix,rid)]=slot
            frame["rows"][attention.prefix]=(meta,ds,ps)
        # Reject whole turn before mutation. GPU read-only metadata copies are
        # deduplicated by pointer; safety overhead is measured, not hidden.
        if rank not in ranks_initialized:
            slots={int(att.kv_cache[1].shape[0]) for att in layers}
            require(len(slots)==1, "heterogeneous native arena geometry unsupported")
            required=aux_bytes(slots.pop())
            budget=int(os.environ.get("QWEN36_KVBP_AUX_BUDGET_BYTES", "0"))
            total=int(os.environ.get("QWEN36_KVBP_TOTAL_BUDGET_BYTES", "0"))
            native=int(config.cache_config.kv_cache_memory_bytes or 0)
            require(native>0 and required<=budget and native+budget<=total,
                    "explicit total/native/aux memory reservation insufficient")
            for att in layers: att._kvbp_allocation_admitted=True
            for att in layers: require(_ensure_aux(torch,att) is not None, "aux allocation failed")
            for t in range(1,17):
                q=torch.empty((t,4,128),dtype=torch.bfloat16,device=layers[0].kv_cache[1].device)
                import torch_npu
                q=torch_npu.npu_format_cast(q,2)
                torch.ops.qwen36_kvbuffer_parallel_fp32.prepare(q,layers[0].kv_cache[1])
            torch.npu.synchronize()
            ranks_initialized.add(rank)
            _audit("worker_dispatch_verified",rank=rank,physical_device=rank+4,
                   layers=bindings,source=actual_sources,aux_bytes=required,aux_budget_bytes=budget,
                   native_budget_bytes=native,total_budget_bytes=total,
                   scope="P1-eager-only-real48-receiver")
        token=_TURN.set(frame)
        try:
            result=original_forward(runner,*args,**kwargs)
            require(frame["seen"]==set(frame["rows"]), "not all48 GDN cores dispatched")
            frame_count+=1
            if frame_count==1 or frame_count%128==0:
                _audit("turn_coverage",rank=rank,turns=frame_count,layers=48,
                       native_arguments_unmodified=True)
            return result
        finally:
            _TURN.reset(token)


    def patched_forward_core(
        self: Any,
        mixed_qkv: Any,
        b: Any,
        a: Any,
        core_attn_out: Any,
    ) -> Any:
        frame = _TURN.get()
        if frame is None:
            require(not hasattr(self,"_kvbp_aux"), "live buffered state outside runner admission")
            return original(self,mixed_qkv,b,a,core_attn_out)
        require(self.prefix in frame["rows"] and self.prefix not in frame["seen"],
                "unadmitted/repeated GDN core")
        frame["seen"].add(self.prefix)
        metadata,ds,ps = frame["rows"][self.prefix]
        aux = self._kvbp_aux
        if metadata.num_prefills:
            # P1 retains native mixed/prefill fallback. P2 is not implemented.
            if ds:
                _flush_slots(torch,self,aux,metadata.non_spec_state_indices_tensor[:len(ds)],"P1_native_mixed")
            result = original(self,mixed_qkv,b,a,core_attn_out)
            _reset_selected(aux,metadata.prefill_state_indices)
            _audit_once("native_fallback","P1_native_mixed",prefix=self.prefix)
            return result
        reason = _eligibility_reason(torch,self,metadata,aux,mixed_qkv,b,a,core_attn_out)
        require(reason is None, "P1 pure decode admission failed: "+str(reason))

        tokens = int(metadata.num_actual_tokens)
        packed = mixed_qkv[:tokens]
        a_decode = a[:tokens]
        b_decode = b[:tokens]
        conv_weights = self.conv1d.weight.view(
            self.conv1d.weight.size(0), self.conv1d.weight.size(2)
        )
        conv_metadata = metadata.non_spec_decode_metadata.causal_conv1d
        post_conv = torch.empty_like(packed)
        torch.ops._C_ascend.npu_causal_conv1d_custom(
            post_conv,
            packed,
            conv_weights.transpose(0, 1),
            conv_state=self.kv_cache[0],
            bias_opt=self.conv1d.bias,
            query_start_loc_opt=conv_metadata.query_start_loc,
            cache_indices_opt=conv_metadata.cache_indices,
            initial_state_mode_opt=None,
            num_accepted_tokens_opt=None,
            activation_mode=1 if self.activation else 0,
            pad_slot_id=gdn.PAD_SLOT_ID,
            run_mode=1,
        )
        try:
            query, key, value = self.rearrange_mixed_qkv(post_conv)
            query = l2norm_fwd(query).squeeze(0).contiguous()
            key = l2norm_fwd(key).squeeze(0).contiguous()
            value = value.squeeze(0).contiguous()
            gating, beta = DeviceOperator.fused_gdn_gating(
                self.A_log, a_decode, b_decode, self.dt_bias
            )
            result = torch.ops.qwen36_kvbuffer_parallel_fp32.decode(
                query,
                key,
                value,
                gating.squeeze(0).contiguous(),
                beta.squeeze(0).contiguous(),
                self.kv_cache[1],
                aux["k_log"],
                aux["u_log"],
                aux["lambda_log"],
                aux["decay"],
                aux["length"],
                metadata.non_spec_decode_metadata.actual_seq_lengths,
                metadata.non_spec_state_indices_tensor,
            )
            core_attn_out[:tokens].copy_(result)
        except BaseException:
            _audit(
                "candidate_dispatch_failed",
                prefix=self.prefix,
                num_tokens=tokens,
                library_sha256=library_sha256,
            )
            raise

        _audit_once(
            "candidate_dispatch",
            str(self.prefix),
            prefix=self.prefix,
            num_tokens=tokens,
            library_sha256=library_sha256,
        )
        return None

    require(bind(cls,target,patched_forward_core) is original, "native alias changed during patch")
    cls._kvbp_patch_version = PATCH_VERSION
    target._kvbp_patch_version = PATCH_VERSION
    runner_cls._kvbp_original_forward = original_forward
    runner_cls._model_forward = runner_forward
    _audit(
        "plugin_installed",
        library=str(library),
        library_sha256=library_sha256,
        source=str(source),
        source_sha256=source_sha256,
        sources=actual_sources,
        schema=schema,
        scope="P1-eager-only-NPU-unverified-draft",
    )
    LOGGER.warning(
        "Installed Qwen3.6 KVBuffer plugin %s with library %s",
        PATCH_VERSION,
        library,
    )
