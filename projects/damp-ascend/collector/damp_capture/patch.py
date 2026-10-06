"""Output-preserving eager-only live hook. No recurrence, gating or state writes."""
from __future__ import annotations
from contextvars import ContextVar
import inspect
import os
import sys
from pathlib import Path
from .contract import GDN_SHA, RUNNER_SHA, digest, file_digest, load_manifest, require
from .session import Session, layer_index
from .writer import Writer
from .bindings import BINDING_SOURCES, bind_aliased_core, live_bindings, verify_native_alias
from .text_positions import (TEXT_METADATA_SOURCES, decode_lengths, ordered_text_positions,
                             text_axis, text_request)

_TURN = ContextVar("damp_capture_turn", default=None)
_GATE = ContextVar("damp_capture_gate", default=None)


def register():
    if os.environ.get("DAMP_CAPTURE_ENABLE") != "1":
        return
    import torch
    import torch.distributed as dist
    import torch_npu  # noqa: F401
    import vllm_ascend.ops  # noqa: F401; retain known v0.23 import ordering
    import vllm_ascend.ops.gdn as gdn
    import vllm_ascend.worker.model_runner_v1 as runner_module
    from vllm.model_executor.layers.mamba.gdn.qwen_gdn_linear_attn import QwenGatedDeltaNetAttention
    from vllm.distributed import get_tensor_model_parallel_rank, get_tensor_model_parallel_world_size
    manifest = load_manifest(os.environ["DAMP_CAPTURE_MANIFEST"])
    root = os.environ["DAMP_CAPTURE_OUTPUT"]
    source = dict(gdn_path=str(Path(gdn.__file__).resolve()), gdn_sha256=file_digest(gdn.__file__),
                  runner_path=str(Path(runner_module.__file__).resolve()),
                  runner_sha256=file_digest(runner_module.__file__),
                  collector_path=str(Path(__file__).resolve()),
                  collector_sha256=file_digest(__file__),
                  device_operator_path=inspect.getfile(gdn.DeviceOperator),
                  device_operator_sha256=file_digest(inspect.getfile(gdn.DeviceOperator)))
    require(source["gdn_sha256"] == GDN_SHA and source["runner_sha256"] == RUNNER_SHA,
            "frozen runtime source mismatch; do not relax without source audit")
    source["text_metadata_sources"] = {path: file_digest(path) for path in TEXT_METADATA_SOURCES}
    require(source["text_metadata_sources"] == TEXT_METADATA_SOURCES,
            "frozen text/sequence metadata source mismatch")
    source["text_positions_helper_sha256"] = file_digest(Path(__file__).with_name("text_positions.py"))
    source["binding_sources"] = {path: file_digest(path) for path in BINDING_SOURCES}
    require(source["binding_sources"] == BINDING_SOURCES, "frozen actual class/dispatcher source mismatch")
    source["bindings_helper_sha256"] = file_digest(Path(__file__).with_name("bindings.py"))
    cls, runner_cls = gdn.AscendGatedDeltaNetAttention, runner_module.NPUModelRunner
    target_cls = QwenGatedDeltaNetAttention
    copier = sys.modules.get("vllm_ascend.patch.worker.patch_qwen3_5")
    require(copier is not None and copier._GDN_PATCH_TARGET is target_cls,
            "actual source-bound Ascend Qwen alias copier did not execute")
    verify_native_alias(cls, target_cls)
    require(not hasattr(cls, "_damp_original_core") and
            not hasattr(runner_cls, "_damp_original_forward"), "collector already installed")
    original_core, original_forward = cls._forward_core, runner_cls._model_forward
    original_gate = gdn.DeviceOperator.fused_gdn_gating
    original_gate_descriptor = inspect.getattr_static(gdn.DeviceOperator, "fused_gdn_gating")
    require(isinstance(original_gate_descriptor, staticmethod), "gating descriptor ABI changed")
    original_signature = inspect.signature(original_forward)
    sessions = {}
    proven_requests = set()
    bound_sessions = set()

    def get_session(runner):
        require(bool(runner.model_config.enforce_eager), "collector requires enforce_eager")
        require(not getattr(runner, "speculative_config", None), "speculation unsupported")
        require(runner.pcp_size == runner.dcp_size == 1, "context parallel positions unsupported")
        require(dist.is_initialized() and get_tensor_model_parallel_world_size() == 4 and
                dist.get_world_size() == 4, "strict TP4/no other parallel groups required")
        rank = get_tensor_model_parallel_rank()
        require(rank in range(4) and torch.npu.current_device() == rank, "logical device/rank mismatch")
        if rank not in sessions:
            schema = str(torch.ops._C_ascend.npu_recurrent_gated_delta_rule.default._schema)
            require("state" in schema and "ssm_state_indices" in schema, "missing recurrent op ABI")
            details = dict(source, recurrent_schema=schema, recurrent_schema_sha256=digest(schema),
                           tp_world=4, logical_device=rank, physical_device=rank + 4,
                           device_mapping_evidence="parent prelaunch inspect required")
            sessions[rank] = Session(manifest, Writer(root, rank, manifest, details))
        return sessions[rank]

    def forward(runner, *args, **kwargs):
        batch = getattr(runner, "input_batch", None)
        count = int(getattr(batch, "num_reqs", 0))
        ids = tuple(batch.req_ids[:count]) if count else ()
        if not ids:  # compilation/warm-up lacks real request identity
            return original_forward(runner, *args, **kwargs)
        session = get_session(runner)
        bound = original_signature.bind(runner, *args, **kwargs)
        positions = bound.arguments.get("positions")
        require(positions is not None and positions.dtype in (torch.int32, torch.int64),
                "integer native positions required")
        context = gdn.get_forward_context()
        require(isinstance(context.attn_metadata, dict), "layer metadata dictionary required")
        if id(session) not in bound_sessions:
            actual_bindings = live_bindings(context.no_compile_layers, cls, target_cls, core)
            require(all(row["prefix"] in context.attn_metadata and
                        hasattr(context.attn_metadata[row["prefix"]], "num_decodes") and
                        hasattr(context.attn_metadata[row["prefix"]], "num_prefills")
                        for row in actual_bindings), "actual GDN instance metadata missing")
            session.writer.event("worker_dispatch_verified", layers=actual_bindings,
                                 runtime_ids=list(ids), scope="actual-receiver-instance-not-donor-only")
            bound_sessions.add(id(session))
        actual_tokens = {int(value.num_actual_tokens) for value in context.attn_metadata.values()
                         if hasattr(value, "num_decodes") and hasattr(value, "num_prefills")}
        require(len(actual_tokens) == 1, "GDN token-count metadata mismatch")
        n = actual_tokens.pop()
        uses_mrope = bool(runner.uses_mrope)
        require(runner.uses_xdrope_dim == 0 and
                ((positions.ndim == 2 and positions.shape[0] == 3) if uses_mrope else positions.ndim == 1)
                and positions.shape[-1] >= n, "unproven native positions shape: " + str(tuple(positions.shape)))
        starts_tensor = runner.gdn_query_start_loc.cpu[:count + 1]
        computed_tensor = batch.num_computed_tokens_cpu_tensor[:count]
        require(starts_tensor.device.type == computed_tensor.device.type == "cpu",
                "existing CPU scheduling mirrors required")
        starts, computed = starts_tensor.tolist(), computed_tensor.tolist()
        expected = ordered_text_positions(starts, computed, n)
        prompt_ids = {}
        for rid in ids:
            cached = runner.requests[rid]
            tokens = getattr(cached, "prompt_token_ids", None)
            require(tokens is not None, "runner CachedRequestState.prompt_token_ids missing")
            prompt_ids[rid] = list(tokens)
            first = (id(session), rid) not in proven_requests
            cached_positions = None
            if uses_mrope and first:
                value = cached.mrope_positions
                require(value is not None and value.device.type == "cpu" and value.ndim == 2 and
                        tuple(value.shape) == (3, len(tokens)), "pure-text prompt MRoPE CPU proof unavailable")
                cached_positions = value.tolist()
            text_request(len(tokens), cached.mm_features, cached.prompt_embeds,
                         cached.prompt_is_token_ids, uses_mrope, cached.mrope_position_delta, cached_positions)
            proven_requests.add((id(session), rid))
        # Read-only diagnostic copy. The original multidimensional tensor and
        # all original call arguments are still passed unchanged to native.
        copied = (positions[:, :n] if uses_mrope else positions[:n]).detach().cpu().tolist()
        axis = text_axis(copied, expected, uses_mrope)
        session.cpu_query_starts = tuple(starts)
        session.writer.event("text_positions_verified", runtime_ids=list(ids),
                             native_shape=list(positions.shape), actual_tokens=n,
                             mode="pure-text-mrope-3-identical-rows" if uses_mrope else "pure-text-1d",
                             cpu_query_starts=starts, cpu_computed_tokens=computed,
                             text_axis_sha256=digest(list(axis)), native_arguments_unmodified=True)
        session.begin(ids, prompt_ids, tuple(runner.requests), axis)
        token = _TURN.set(session)
        try:
            result = original_forward(runner, *args, **kwargs)
            session.finish()
            return result
        except Exception as error:
            session.writer.event("capture_failed", error=type(error).__name__, detail=str(error))
            raise
        finally:
            _TURN.reset(token)

    def gate(*args, **kwargs):
        result = original_gate(*args, **kwargs)
        capture = _GATE.get()
        if capture is not None:
            require(capture["calls"] == 0, "multiple gating calls in one GDN layer")
            capture["calls"] += 1
            g = result[0]
            require(tuple(g.shape) == (1, capture["tokens"], 12) and g.dtype == torch.float32,
                    "gating log-decay ABI differs from expected FP32")
            # Copy the actual output, not recomputed gate; never modify the original tuple.
            capture["g"] = g[0, :capture["decode"]].detach().cpu().contiguous()
        return result

    def core(attention, mixed_qkv, b, a, core_attn_out):
        session = _TURN.get()
        if session is None:
            return original_core(attention, mixed_qkv, b, a, core_attn_out)
        metadata = gdn.get_forward_context().attn_metadata[attention.prefix]
        require(metadata.spec_sequence_masks is None, "speculative metadata unsupported")
        layer = layer_index(attention.prefix)
        nd, np = int(metadata.num_decodes), int(metadata.num_prefills)
        require(int(metadata.num_decode_tokens) == nd, "one-token decode required")
        state = attention.kv_cache[1]
        require(state.dtype == torch.float32 and state.ndim == 4 and
                tuple(state.shape[1:]) == (12, 128, 128), "native FP32 recurrent-state geometry mismatch")
        ds = metadata.non_spec_state_indices_tensor[:nd].detach().cpu().tolist() if nd else []
        ps = metadata.prefill_state_indices.detach().cpu().tolist() if np else []
        initial = metadata.prefill_has_initial_state.detach().cpu().tolist() if np else []
        loc = metadata.prefill_query_start_loc.detach().cpu().tolist() if np else [0]
        lengths = [end - start for start, end in zip(loc, loc[1:])]
        require(len(loc) == np + 1 and loc[0] == 0 and
                nd + sum(lengths) == int(metadata.num_actual_tokens), "prefill boundaries mismatch")
        require(all(slot < state.shape[0] for slot in ds + ps), "slot exceeds native arena")
        if nd:
            actual = metadata.non_spec_decode_metadata.actual_seq_lengths.detach().cpu().tolist()
            decode_lengths(actual, session.cpu_query_starts, ds, nd)
        decode = session.plan(layer, ds, ps, lengths, initial)
        capture = dict(tokens=int(metadata.num_actual_tokens), decode=nd, calls=0, g=None)
        token = _GATE.set(capture)
        try:
            result = original_core(attention, mixed_qkv, b, a, core_attn_out)
        finally:
            _GATE.reset(token)
        require(capture["calls"] == 1 and capture["g"] is not None, "native gating not observed")
        require(bool(torch.isfinite(capture["g"]).all()), "nonfinite live log-decay")
        for i, (rid, slot, timeline) in enumerate(decode):
            was_complete = timeline.complete
            anchor, closed = timeline.advance(capture["g"][i].tolist())
            row = session.logical_row(rid)
            if anchor:
                session.writer.anchor(row, layer, timeline.step, state[slot].detach().cpu().contiguous())
            for step in closed:
                session.writer.future(row, layer, step, timeline.finished[step])
            if timeline.complete and not was_complete:
                session.writer.complete(row, layer, timeline)
        return result  # EXACT original return value; core_attn_out and state untouched

    require(bind_aliased_core(cls, target_cls, core) is original_core,
            "native receiver alias changed during collector installation")
    runner_cls._damp_original_forward = original_forward
    runner_cls._model_forward = forward
    gdn.DeviceOperator.fused_gdn_gating = staticmethod(gate)
