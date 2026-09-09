"""Bounded, eager dense GDN teacher observer. Never use captured timings as performance.

All operator calls are passed through unchanged; only CPU snapshots and protocol
checks are added. Frozen TP4, two prompts, manifest-bound layers, one prefill + eight decode.
This is local fidelity input collection, not a full-model accuracy experiment.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import time
import traceback

import torch
from vllm_ascend.worker.worker import NPUWorker

from layerwise_probe_worker import (
    LayerwiseProbeWorker, PREFIX, file_identity, source_identity, tensor_metadata,
)

SCHEMA = "gdn-teacher-capture-v1"
LAYERS = [0, 12, 25, 38, 50, 62]
MODEL = "/cache/austinov/Qwen3.8-27B"


def require(ok, reason):
    if not ok:
        raise RuntimeError("GDN teacher: " + reason)


def ids_sha256(ids):
    return hashlib.sha256(json.dumps(ids, separators=(",", ":")).encode()).hexdigest()


def validate_layers(value):
    require(isinstance(value, list) and 1 <= len(value) <= 48, "manifest layers")
    require(all(type(layer) is int and 0 <= layer <= 63 for layer in value),
            "manifest layer IDs")
    require(value == sorted(set(value)), "manifest layers must be sorted and unique")
    return list(value)


def validate_manifest(doc):
    require(isinstance(doc, dict) and doc.get("schema") == SCHEMA, "manifest schema")
    expected = {"model": MODEL, "tp_size": 4, "input_tokens": 128,
                "decode_steps": 8, "output_tokens": 9, "no_thinking": True}
    for key, value in expected.items():
        require(type(doc.get(key)) is type(value) and doc[key] == value, "manifest " + key)
    validate_layers(doc.get("layers"))
    sequences = doc.get("sequences")
    require(isinstance(sequences, list) and len(sequences) == 2, "two sequences required")
    for index, seq in enumerate(sequences):
        require(seq.get("id") == f"teacher-{index}", "sequence order/id")
        ids = seq.get("input_ids")
        require(isinstance(ids, list) and len(ids) == 128
                and all(type(x) is int and x >= 0 for x in ids), "input token IDs")
        require(seq.get("input_ids_sha256") == ids_sha256(ids), "input token hash")
    require(sequences[0]["input_ids"] != sequences[1]["input_ids"], "duplicate prompts")
    return doc


def validate_step(seq, step, ids, positions):
    require(type(step) is int and 0 <= step <= 8, "step outside fixed budget")
    require(isinstance(ids, list) and all(type(x) is int and x >= 0 for x in ids), "step IDs")
    expected_positions = list(range(128)) if step == 0 else [127 + step]
    if isinstance(positions, list) and len(positions) == 3 and all(isinstance(x, list) for x in positions):
        require(positions[0] == positions[1] == positions[2], "non-text MRoPE positions")
        positions = positions[0]
    require(positions == expected_positions, "positions/chunked prefill mismatch")
    require(ids == seq["input_ids"] if step == 0 else len(ids) == 1, "prompt/decode token mismatch")


def write_json(path, value):
    # Partial files are retained on failure. The public path appears only when complete.
    path = Path(path)
    partial = path.with_name(path.name + ".partial")
    with partial.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.link(partial, path)
    partial.unlink()


def snapshot(tensor):
    require(isinstance(tensor, torch.Tensor), "expected tensor")
    cpu = tensor.detach().to(device="cpu", copy=True).contiguous()
    require(bool(torch.isfinite(cpu).all()), "nonfinite captured tensor")
    return cpu


def byte_equal(left, right):
    return (left.dtype == right.dtype and left.shape == right.shape
            and torch.equal(left.contiguous().view(torch.uint8), right.contiguous().view(torch.uint8)))


def loaded_libraries():
    paths = set()
    for line in Path("/proc/self/maps").read_text().splitlines():
        parts = line.split()
        if len(parts) < 6 or not parts[-1].startswith("/"):
            continue
        path = parts[-1]
        if (("_cann_ops_custom" in path and ".so" in path)
                or any(x in path for x in ("libopapi.so", "libvllm_ascend_kernels.so", "vllm_ascend_C."))):
            paths.add(path)
    return [file_identity(path) for path in sorted(paths)]


class GdnTeacherCaptureWorker(NPUWorker):
    def _failure(self, error):
        path = self._teacher_dir / f"rank{self.rank}.failure.json"
        if not path.exists() and not path.with_name(path.name + ".partial").exists():
            write_json(path, {"schema": SCHEMA, "rank": self.rank, "error": repr(error),
                              "traceback": traceback.format_exc(), "frame": self._frame,
                              "time_ns": time.time_ns()})

    def _guard(self, function):
        def wrapped(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except BaseException as error:
                self._failure(error)
                raise
        return wrapped

    def load_model(self):
        require(not hasattr(self, "_teacher_dir"), "load_model called twice")
        self._teacher_dir = Path(os.environ["DRRQR_GDN_TEACHER_DIR"])
        require(self._teacher_dir.is_absolute() and self._teacher_dir.is_dir(), "output directory")
        self._frame = None
        self._current = None
        self._pending = {}
        self._last_state = {}
        self._steps = {}
        self._nonces = {}
        self._tokens = {}
        self._receipts = {}
        self._libraries = None
        try:
            raw = Path(os.environ["DRRQR_GDN_TEACHER_MANIFEST"]).read_bytes()
            self._manifest_hash = hashlib.sha256(raw).hexdigest()
            require(self._manifest_hash == os.environ["DRRQR_GDN_TEACHER_MANIFEST_SHA256"],
                    "manifest binding")
            self._manifest = validate_manifest(json.loads(raw))
            self._layers = list(self._manifest["layers"])
            report = {"schema": SCHEMA, "rank": self.rank, "local_rank": self.local_rank,
                      "worker": file_identity(__file__), "manifest_sha256": self._manifest_hash}
            report["observer_helper"] = source_identity(LayerwiseProbeWorker)
            require(report["observer_helper"]["sha256"]
                    == "678f714458f81a6b73c5dd19fc50a69e11c2e444837908460aa8e4aab9a46feb",
                    "observer helper source changed")
            LayerwiseProbeWorker._admit(self, report)
            for path, checksum in {
                "/vllm-workspace/vllm/vllm/v1/worker/gpu_model_runner.py":
                    "6250ca0670c4593aa2f7c4567c9c71d6cb3d8182624a985d4d4e33d5bf054666",
                "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/layernorm_gated.py":
                    "ecdd125ce32f969e1b1c0e4f8b4e84ee8657332cd02cdcc4c72edd2bff13aff2",
            }.items():
                identity = file_identity(path)
                require(identity["sha256"] == checksum, "teacher-specific frozen runtime source changed")
                report["runtime_sources"][path] = identity
            require(self.vllm_config.model_config.enforce_eager, "eager calibration required")
            require(self.vllm_config.model_config.model == MODEL, "original model required")
            require(self.vllm_config.scheduler_config.max_num_seqs == 1, "single request only")
            require(os.environ.get("VLLM_ASCEND_DRRQR_ENABLE") == "0"
                    and os.environ.get("VLLM_ASCEND_DRRQR_CAPTURE_ENABLE") == "0",
                    "old plugin patch/capture must be disabled")
            super().load_model()
            self._install(report)
            write_json(self._teacher_dir / f"rank{self.rank}.ready.json", report)
        except BaseException as error:
            self._failure(error)
            raise

    def _install(self, report):
        import vllm_ascend.ops.gdn as gdn
        from vllm.model_executor.layers.mamba.gdn.base import GatedDeltaNetAttention

        model = self.model_runner.get_model()
        modules = {}
        for name, module in model.named_modules():
            if isinstance(module, GatedDeltaNetAttention):
                match = PREFIX.search(module.prefix)
                require(match is not None, "noncanonical layer prefix")
                layer = int(match[1])
                require(layer not in modules, "duplicate layer")
                modules[layer] = module
        require(len(modules) == 48 and set(self._layers) <= modules.keys(), "GDN layer topology")
        report["model_class"] = source_identity(type(model))
        report["model_forward"] = source_identity(model.forward)
        report["layers"] = []
        self._norm_info = {}
        for layer in self._layers:
            module = modules[layer]
            require((module.tp_size, module.tp_rank, module.head_k_dim, module.head_v_dim,
                     module.num_k_heads, module.num_v_heads, module.num_spec)
                    == (4, self.rank, 128, 128, 16, 48, 0), "dense local geometry")
            require(module._forward_core.__func__ is gdn.AscendGatedDeltaNetAttention._forward_core,
                    "actual core is not frozen Ascend method")
            norm = module.norm
            norm_attrs = {}
            for attr in ("variance_epsilon", "eps", "group_size", "norm_before_gate", "activation"):
                if hasattr(norm, attr):
                    value = getattr(norm, attr)
                    require(value is None or type(value) in (str, int, float, bool), "norm scalar attribute")
                    norm_attrs[attr] = value
            require("variance_epsilon" in norm_attrs or "eps" in norm_attrs, "norm epsilon absent")
            require(norm_attrs.get("norm_before_gate") is True, "unexpected norm/gate order")
            require(norm_attrs.get("eps") == 1e-6 and norm_attrs.get("group_size") is None
                    and getattr(norm, "bias", None) is None, "unexpected norm epsilon/group/bias")
            self._norm_info[layer] = {"class": source_identity(type(norm)),
                                      "forward": source_identity(norm.forward), "attributes": norm_attrs}
            if hasattr(norm, "_forward_method"):
                self._norm_info[layer]["dispatched_forward"] = source_identity(norm._forward_method)
            report["layers"].append({"layer": layer, "prefix": module.prefix,
                                      "core": source_identity(module._forward_core),
                                      "rearrange": source_identity(module.rearrange_mixed_qkv),
                                      "norm": self._norm_info[layer]})
            core = module._forward_core
            rearrange = module.rearrange_mixed_qkv
            module._forward_core = self._guard(self._core_wrapper(layer, module, core))
            module.rearrange_mixed_qkv = self._guard(self._rearrange_wrapper(layer, rearrange))
            norm.register_forward_hook(self._guard(self._norm_hook(layer)))
        original_chunk = gdn.chunk_gated_delta_rule
        self._native = torch.ops._C_ascend.npu_recurrent_gated_delta_rule
        report["chunk"] = source_identity(original_chunk)
        report["l2norm"] = source_identity(gdn.l2norm_fwd)
        report["native_schema"] = str(self._native.default._schema)
        gdn.chunk_gated_delta_rule = self._guard(self._chunk_wrapper(original_chunk))
        torch.ops._C_ascend.npu_recurrent_gated_delta_rule = self._guard(self._decode)
        model.register_forward_pre_hook(self._guard(self._model_before), with_kwargs=True)
        model.register_forward_hook(self._guard(self._model_after), with_kwargs=True)
        report["claim"] = "Pass-through observers; no candidate math, graph or timing evidence."

    def _model_before(self, module, args, kwargs):
        require(self._frame is None and self._current is None and not self._pending, "nested/stale forward")
        arm_path = self._teacher_dir / "armed.json"
        if not arm_path.exists():
            return None
        arm = json.loads(arm_path.read_text())
        require(arm.get("schema") == SCHEMA, "arm schema")
        sid = arm.get("sequence_id")
        require(sid in ("teacher-0", "teacher-1"), "arm sequence")
        seq = self._manifest["sequences"][int(sid[-1])]
        require(arm.get("input_ids_sha256") == seq["input_ids_sha256"], "arm token binding")
        nonce = arm.get("nonce")
        require(isinstance(nonce, str) and re.fullmatch(r"[a-zA-Z0-9-]{16,64}", nonce), "arm nonce")
        if sid == "teacher-1":
            require(self._steps.get("teacher-0") == 9, "sequence ordering")
        if sid in self._nonces:
            require(nonce == self._nonces[sid], "nonce changed within sequence")
        else:
            self._nonces[sid] = nonce
        step = self._steps.get(sid, 0)
        # Qwen's multimodal runner can supply text embeddings with input_ids=None.
        # Bind the same frozen runner token buffer used by its preprocessing path.
        require(not args and kwargs.get("positions") is not None, "root forward input interface")
        positions = snapshot(kwargs["positions"]).tolist()
        token_count = kwargs["positions"].shape[-1]
        tokens = kwargs.get("input_ids")
        token_source = "root_input_ids"
        if tokens is None:
            require(kwargs.get("inputs_embeds") is not None
                    and kwargs["inputs_embeds"].shape[0] == token_count, "embedding token interface")
            tokens = self.model_runner.input_ids.gpu[:token_count]
            token_source = "frozen_runner_input_ids_buffer_with_text_embeddings"
        ids = snapshot(tokens).tolist()
        validate_step(seq, step, ids, positions)
        self._frame = {"sequence_id": sid, "nonce": nonce, "step": step,
                       "input_ids": ids, "positions": positions, "input_ids_source": token_source,
                       "layers": [], "records": []}
        return None

    def _model_after(self, module, args, kwargs, output):
        if self._frame is None:
            return None
        frame = self._frame
        require(self._current is None and not self._pending, "unfinished core/norm")
        layer_count = len(self._layers)
        require(frame["layers"] == self._layers and len(frame["records"]) == layer_count,
                "incomplete/duplicate layers")
        sid = frame["sequence_id"]
        self._tokens.setdefault(sid, []).append(frame["input_ids"])
        self._receipts.setdefault(sid, []).extend(frame["records"])
        self._steps[sid] = frame["step"] + 1
        if self._steps[sid] == 9:
            if self._libraries is None:
                self._libraries = loaded_libraries()
            write_json(self._teacher_dir / f"{sid}.rank{self.rank}.complete.json",
                       {"schema": SCHEMA, "sequence_id": sid, "nonce": frame["nonce"],
                        "rank": self.rank, "steps": 9, "layers": layer_count,
                        "layer_ids": self._layers,
                        "records": len(self._receipts[sid]), "files": self._receipts[sid],
                        "input_ids_per_step": self._tokens[sid],
                        "manifest_sha256": self._manifest_hash, "loaded_libraries": self._libraries,
                        "claim": "Real dense teacher tensors; no candidate fidelity or task accuracy result."})
        self._frame = None
        return None

    def _core_wrapper(self, layer, module, original):
        def call(*args, **kwargs):
            if self._frame is None:
                return original(*args, **kwargs)
            from vllm.forward_context import get_forward_context
            require(self._current is None and not self._pending, "nested/pending core")
            frame = self._frame
            require(len(frame["layers"]) < len(self._layers)
                    and layer == self._layers[len(frame["layers"])],
                    "selected layer order")
            metadata = get_forward_context().attn_metadata
            require(isinstance(metadata, dict) and module.prefix in metadata, "attention metadata")
            meta = metadata[module.prefix]
            step = frame["step"]
            phase = "prefill" if step == 0 else "decode"
            require(meta.spec_sequence_masks is None, "speculation forbidden")
            require((meta.num_prefills, meta.num_decodes, meta.num_actual_tokens)
                    == ((1, 0, 128) if step == 0 else (0, 1, 1)), "mixed/chunked batch forbidden")
            idx = meta.prefill_state_indices if step == 0 else meta.non_spec_state_indices_tensor
            indices = snapshot(idx).reshape(-1).tolist()
            state = module.kv_cache[1]
            require(len(indices) == 1 and 0 <= indices[0] < state.shape[0], "one valid slot required")
            require(state.dtype == torch.float32 and tuple(state.shape[1:]) == (12, 128, 128),
                    "dense FP32 state geometry")
            record = {"schema": SCHEMA, "manifest_sha256": self._manifest_hash,
                      "sequence_id": frame["sequence_id"], "nonce": frame["nonce"],
                      "rank": self.rank, "layer": layer, "step": step, "phase": phase,
                      "input_ids": frame["input_ids"], "positions": frame["positions"],
                      "input_ids_source": frame["input_ids_source"],
                      "state_indices": indices, "state_metadata": tensor_metadata(state),
                      "norm": self._norm_info[layer], "tensors": {}, "tensor_metadata": {}}
            self._current = record
            if step == 0:
                record["has_initial_state"] = snapshot(meta.prefill_has_initial_state).tolist()
                require(not any(snapshot(meta.prefill_has_initial_state).reshape(-1).tolist()),
                        "prefill must reset state")
            result = original(*args, **kwargs)
            require(record.get("operator_calls") == 1 and "raw_q" in record["tensors"],
                    "actual operator/raw input not observed")
            after = snapshot(state[indices[0]:indices[0] + 1])
            require(byte_equal(after, record["tensors"]["state_final"]), "cache write differs from operator")
            require(tensor_metadata(state) == record["state_metadata"], "state storage changed")
            self._last_state[(frame["sequence_id"], layer)] = after
            self._current = None
            self._pending[layer] = record
            frame["layers"].append(layer)
            return result
        return call

    def _add(self, record, name, tensor):
        require(name not in record["tensors"], "duplicate capture " + name)
        record["tensor_metadata"][name] = tensor_metadata(tensor)
        record["tensors"][name] = snapshot(tensor)

    def _rearrange_wrapper(self, layer, original):
        def call(*args, **kwargs):
            result = original(*args, **kwargs)
            record = self._current
            if record is not None and record["layer"] == layer and result[0] is not None:
                for name, tensor in zip(("raw_q", "raw_k", "raw_v"), result):
                    self._add(record, name, tensor)
            return result
        return call

    def _chunk_wrapper(self, original):
        def call(*args, **kwargs):
            record = self._current
            if record is None:
                return original(*args, **kwargs)
            require(record["phase"] == "prefill" and not args, "chunk dispatch interface")
            require(kwargs.get("use_qk_l2norm_in_kernel") is True
                    and kwargs.get("head_first") is False and kwargs.get("output_final_state") is True,
                    "chunk normalization/state flags")
            for name in ("q", "k", "v", "g", "beta", "initial_state", "cu_seqlens"):
                self._add(record, name, kwargs[name])
            for name in ("q", "k", "v"):
                require(byte_equal(record["tensors"][name], record["tensors"]["raw_" + name]),
                        "prefill raw input mismatch")
            require(record["tensors"]["cu_seqlens"].tolist() == [0, 128], "prefill boundaries")
            initial = record["tensors"]["initial_state"].transpose(-1, -2).contiguous()
            require(initial.dtype == torch.float32 and tuple(initial.shape) == (1, 12, 128, 128)
                    and not bool(torch.count_nonzero(initial)), "effective prefill state not zero")
            record["tensors"]["state_initial"] = initial
            record["scale"] = 128 ** -0.5
            out, last = original(*args, **kwargs)
            self._add(record, "operator_output", out)
            self._add(record, "chunk_state_final", last)
            record["tensors"]["state_final"] = record["tensors"]["chunk_state_final"].transpose(-1, -2).contiguous()
            record["operator_calls"] = record.get("operator_calls", 0) + 1
            return out, last
        return call

    def _decode(self, *args, **kwargs):
        record = self._current
        if record is None:
            return self._native(*args, **kwargs)
        require(record["phase"] == "decode" and not args, "native dispatch interface")
        require(kwargs["scale"] == 128 ** -0.5, "native dense scale")
        for name in ("query", "key", "value", "g", "beta", "actual_seq_lengths", "ssm_state_indices"):
            self._add(record, name, kwargs[name])
        require(byte_equal(record["tensors"]["value"], record["tensors"]["raw_v"].squeeze(0)),
                "decode value input mismatch")
        require(record["tensors"]["actual_seq_lengths"].tolist() == [0, 1], "native length ABI")
        require(record["tensors"]["ssm_state_indices"].reshape(-1).tolist() == record["state_indices"],
                "native slot binding")
        state = kwargs["state"]
        slot = record["state_indices"][0]
        self._add(record, "state_initial", state[slot:slot + 1])
        previous = self._last_state.get((record["sequence_id"], record["layer"]))
        require(previous is not None and byte_equal(previous, record["tensors"]["state_initial"]),
                "state trajectory discontinuity")
        record["scale"] = kwargs["scale"]
        out = self._native(*args, **kwargs)
        self._add(record, "operator_output", out)
        self._add(record, "state_final", state[slot:slot + 1])
        record["operator_calls"] = record.get("operator_calls", 0) + 1
        return out

    def _norm_hook(self, layer):
        def hook(module, args, output):
            if self._frame is None:
                return None
            require(layer in self._pending and len(args) == 2, "norm without observed core")
            record = self._pending.pop(layer)
            for name, tensor in (("norm_input", args[0]), ("z", args[1]),
                                 ("norm_output", output), ("norm_weight", module.weight)):
                self._add(record, name, tensor)
            require(byte_equal(record["tensors"]["norm_input"],
                               record["tensors"]["operator_output"].reshape(-1, 128)),
                    "actual norm input differs from core output")
            filename = (f'{record["sequence_id"]}.rank{self.rank}.'
                        f'layer{layer}.step{record["step"]}.pt')
            path = self._teacher_dir / filename
            # torch archive is local trusted evidence; never load untrusted pickle.
            with path.open("xb") as stream:
                torch.save(record, stream)
                stream.flush()
                os.fsync(stream.fileno())
            self._frame["records"].append({"file": filename, **file_identity(path)})
            return None
        return hook
