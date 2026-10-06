"""Output-preserving eager-only live hook. No recurrence, gating or state writes."""
from __future__ import annotations
from contextvars import ContextVar
import inspect
import os
from pathlib import Path
from .contract import GDN_SHA, RUNNER_SHA, digest, file_digest, load_manifest, require
from .session import Session, layer_index
from .writer import Writer

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
    cls, runner_cls = gdn.AscendGatedDeltaNetAttention, runner_module.NPUModelRunner
    require(not hasattr(cls, "_damp_original_core") and
            not hasattr(runner_cls, "_damp_original_forward"), "collector already installed")
    original_core, original_forward = cls._forward_core, runner_cls._model_forward
    original_gate = gdn.DeviceOperator.fused_gdn_gating
    original_gate_descriptor = inspect.getattr_static(gdn.DeviceOperator, "fused_gdn_gating")
    require(isinstance(original_gate_descriptor, staticmethod), "gating descriptor ABI changed")
    original_signature = inspect.signature(original_forward)
    sessions = {}

    def get_session(runner):
        require(bool(runner.model_config.enforce_eager), "collector requires enforce_eager")
        require(not getattr(runner, "speculative_config", None), "speculation unsupported")
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
        require(positions is not None and positions.ndim == 1, "text-only 1D positions required")
        context = gdn.get_forward_context()
        require(isinstance(context.attn_metadata, dict), "layer metadata dictionary required")
        actual_tokens = {int(value.num_actual_tokens) for value in context.attn_metadata.values()
                         if hasattr(value, "num_decodes") and hasattr(value, "num_prefills")}
        require(len(actual_tokens) == 1, "GDN token-count metadata mismatch")
        n = actual_tokens.pop()
        prompt_ids = {}
        for rid in ids:
            cached = runner.requests[rid]
            tokens = getattr(cached, "prompt_token_ids", None)
            require(tokens is not None, "runner CachedRequestState.prompt_token_ids missing")
            prompt_ids[rid] = list(tokens)
        session.begin(ids, prompt_ids, tuple(runner.requests), positions[:n].detach().cpu().tolist())
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
            require(actual == list(range(1, nd + 1)), "decode token/request order not one-to-one")
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

    cls._damp_original_core = original_core
    runner_cls._damp_original_forward = original_forward
    cls._forward_core = core
    runner_cls._model_forward = forward
    gdn.DeviceOperator.fused_gdn_gating = staticmethod(gate)
