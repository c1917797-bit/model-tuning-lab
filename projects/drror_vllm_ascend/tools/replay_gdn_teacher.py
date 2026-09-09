#!/usr/bin/env python3
"""Bounded real-tensor DRRQR energy64/beta64 replay; not model accuracy or throughput."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import signal
import statistics
import sys
import time
import traceback
from types import SimpleNamespace
from unittest.mock import patch

import torch

ROOT = Path("/cache/cch/drror_vllm_ascend")
RESULT_ROOT = Path("/drrqr-results")
LAYERS = (0, 12, 25, 38, 50, 62)
VARIANTS = ("dense128", "energy64", "beta64")
PLAN_SHA256 = "b1fcb727d3e58be66cc24148e30a5a1722d3bdc0914784f01cad02f11f741b8c"
STATS_SHA256 = "8882d60948ed773bb200303a1878d43441bda105bac4090e776b34ad684ceb7b"
AUDITOR_SHA256 = "fd9b4f30d47d6f1763683f6dfa62a533c7c365ab73a7503de628445194e2e6f7"
GOLDEN_SHA256 = "1a2d1a61040a58a6f0c1d90cdbf0fc17058f3273eaef8b3d1b80116c97d92cb9"
PROBE_SHA256 = "86c31fb67503226ed7ba6daf3c1d7a56db8e15d803eca764d64ac08772aded83"
CALIBRATION_SHA256 = "81748f94c4eff0ad5e4053eb7c4a30b1a397a82d45676a8b0b42394bd612bd47"
PREFILL_RTOL, PREFILL_ATOL = 1e-2, 1e-2
DECODE_RTOL, DECODE_ATOL = 3e-3, 1e-2
RELATIVE_L2_LIMIT, NORMALIZED_MAX_LIMIT = 2.0 ** -7, 2.0 ** -6
SOURCE_HASHES = {
    "/vllm-workspace/vllm/vllm/model_executor/layers/fla/ops/l2norm.py":
        "520f4513ef4fc97e6b88dc07877cca8e29da0d34e44673fe989e3af002d86381",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py":
        "d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn_attn_builder.py":
        "42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/chunk.py":
        "6f93b9face32999c93976fccaeb2d6a9d8dc85c8c41d3d26d92e1820f62d7ca5",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/l2norm.py":
        "07657e33f2240cf39e8dec9991d00022181b43946a8c1497c6c236bf4c230126",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/layernorm.py":
        "f8ba0c77b8d9a48b14118ae23e19b1711492de16549e994ced73396db960f485",
    "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/layernorm_gated.py":
        "ecdd125ce32f969e1b1c0e4f8b4e84ee8657332cd02cdcc4c72edd2bff13aff2",
}
CLAIM = ("Local dense-driven real-tensor replay of the energy-selector DRRQR variant "
         "and fixed retained-key beta compensation. Not exact StrongRRQR paper reproduction, "
         "autoregressive/model accuracy, timing, throughput or final joint acceptance.")


def require(value, message):
    if not value:
        raise ValueError(message)


def checksum(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def load_tool(name, expected):
    path = Path(__file__).resolve().with_name(name + ".py")
    require(not path.is_symlink() and checksum(path) == expected, "helper source changed: " + name)
    spec = importlib.util.spec_from_file_location("teacher_replay_" + name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def coefficients(plan, stats, layer, rank):
    require(layer in LAYERS and type(rank) is int and 0 <= rank < 4, "layer/rank outside protocol")
    for key, expected in {
        "schema": "ascend-drrqr-plan/v1", "old_head_k_dim": 128, "target_head_k_dim": 64,
        "num_key_heads": 16, "num_value_heads": 48, "head_v_dim": 128,
        "selection_objective": "energy-kernel",
    }.items():
        require(plan.get(key) == expected, "energy plan geometry/objective " + key)
    require(stats.get("schema") == "drrqr-retained-key-energy-stats/v1"
            and stats.get("status") == "completed_descriptive_only", "retained statistics status")
    require(stats.get("plan", {}).get("sha256") == PLAN_SHA256
            and stats["plan"].get("objective") == "energy-kernel", "stats/plan identity")
    calibration = stats.get("calibration", {})
    require(calibration.get("sha256") == CALIBRATION_SHA256
            and calibration.get("scalar_train_rows") == list(range(12))
            and calibration.get("scalar_holdout_rows") == [12, 13, 14, 15], "frozen scalar training split")
    rows = stats.get("head_records")
    require(isinstance(rows, list) and len(rows) == 96, "96 coefficient records required")
    lookup = {}
    for row in rows:
        key = (row.get("layer"), row.get("rank"), row.get("local_head"))
        require(key not in lookup, "duplicate coefficient")
        require(key[0] in LAYERS and type(key[1]) is int and 0 <= key[1] < 4
                and type(key[2]) is int and 0 <= key[2] < 4, "coefficient coordinate")
        require(row.get("global_head") == key[1] * 4 + key[2], "global/local coefficient mapping")
        r = row.get("train_k_mean")
        require(type(r) in (float, int) and math.isfinite(r) and 0 < r <= 1, "train_k_mean range")
        lookup[key] = row
    raw = plan.get("keep_indices", {}).get(str(layer))
    require(isinstance(raw, list) and len(raw) == 1024
            and all(type(x) is int for x in raw), "16 x 64 ordered plan indices")
    all_keep = torch.tensor(raw, dtype=torch.int64).reshape(16, 64)
    for head in range(16):
        require(bool(((all_keep[head] >= head * 128)
                      & (all_keep[head] < (head + 1) * 128)).all())
                and all_keep[head].unique().numel() == 64, "selection crosses/duplicates head coordinates")
    global_heads = torch.arange(rank * 4, rank * 4 + 4)
    keep = all_keep[global_heads] - global_heads[:, None] * 128
    r4 = torch.tensor([lookup[layer, rank, head]["train_k_mean"] for head in range(4)],
                      dtype=torch.float32)
    return keep.contiguous(), r4, r4.repeat_interleave(3)


def select_qk(tensor, keep):
    require(tensor.ndim >= 2 and tuple(tensor.shape[-2:]) == (4, 128)
            and keep.dtype == torch.int64 and tuple(keep.shape) == (4, 64)
            and tensor.device == keep.device, "head-local Q/K selection shape/device")
    require(bool(((keep >= 0) & (keep < 128)).all()), "head-local selection range")
    indices = keep.reshape((1,) * (tensor.ndim - 2) + (4, 64))
    return tensor.gather(-1, indices.expand(*tensor.shape[:-2], 4, 64)).contiguous()


def beta_product(beta_base, r12):
    require(beta_base.dtype == torch.bfloat16 and beta_base.ndim in (2, 3)
            and beta_base.shape[-1] == 12 and r12.dtype == torch.float32
            and tuple(r12.shape) == (12,) and beta_base.device == r12.device,
            "beta BF16 [...,12] / r FP32 [12] contract")
    # Called inside graph: no host extraction, branches on tensor values or .item().
    product = beta_base.float() * r12
    return product, product.to(torch.bfloat16)


def cpu(tensor):
    return tensor.detach().to(device="cpu", copy=True).contiguous()


def exact(left, right):
    left, right = cpu(left), cpu(right)
    return (left.shape == right.shape and left.dtype == right.dtype
            and bool(torch.isfinite(left).all() and torch.isfinite(right).all())
            and torch.equal(left.reshape(-1).view(torch.uint8), right.reshape(-1).view(torch.uint8)))


def metrics(actual, reference, phase):
    require(phase in ("prefill", "decode"), "metric phase")
    result = {"shape_matches": actual.shape == reference.shape,
              "dtype_matches": actual.dtype == reference.dtype,
              "finite": False, "allclose": False, "passed": False}
    if not result["shape_matches"] or not result["dtype_matches"]:
        return result
    a, b = cpu(actual).float(), cpu(reference).float()
    result["finite"] = bool(torch.isfinite(a).all() and torch.isfinite(b).all())
    if not result["finite"]:
        return result
    delta = a - b
    epsilon = torch.finfo(torch.float32).eps
    maximum = float(delta.abs().max())
    relative = float(torch.linalg.vector_norm(delta)) / max(float(torch.linalg.vector_norm(b)), epsilon)
    normalized = maximum / max(float(b.abs().max()), epsilon)
    rtol, atol = (PREFILL_RTOL, PREFILL_ATOL) if phase == "prefill" else (DECODE_RTOL, DECODE_ATOL)
    close = bool(torch.allclose(a, b, rtol=rtol, atol=atol))
    result.update(max_abs=maximum, relative_l2=relative, normalized_max=normalized,
                  rtol=rtol, atol=atol, allclose=close,
                  passed=close and (phase == "prefill" or
                      (relative <= RELATIVE_L2_LIMIT and normalized <= NORMALIZED_MAX_LIMIT)))
    return result


def fidelity_screen(rows):
    expected = {(f"teacher-{s}", r, layer, position)
                for s in range(2) for r in range(4) for layer in LAYERS for position in range(136)}
    lookup = {}
    for row in rows:
        key = (row["sequence_id"], row["rank"], row["layer"], row["position"])
        require(key in expected and key not in lookup, "fidelity coordinate missing/duplicate/outside protocol")
        require(all(type(row[name]) in (float, int) and math.isfinite(row[name]) and row[name] >= 0
                    for name in ("energy64_relative_l2", "beta64_relative_l2")), "nonfinite fidelity")
        lookup[key] = row
    require(set(lookup) == expected, "complete 48 x 136 token fidelity required")
    def summary(values):
        baseline = statistics.fmean(x["energy64_relative_l2"] for x in values)
        candidate = statistics.fmean(x["beta64_relative_l2"] for x in values)
        return {"energy64_mean": baseline, "beta64_mean": candidate,
                "ratio_with_floor": candidate / max(baseline, 1e-6)}
    overall = summary(rows)
    groups = []
    for sid, rank, layer in sorted({key[:3] for key in expected}):
        for window, positions in (("all", range(136)), ("prefill_late", range(64, 128)),
                                  ("decode_late", range(132, 136))):
            value = summary([lookup[sid, rank, layer, p] for p in positions])
            groups.append({"sequence_id": sid, "rank": rank, "layer": layer, "window": window,
                           **value, "passed": value["ratio_with_floor"] <= 1.05})
    return {"passed": overall["ratio_with_floor"] <= 0.9 and all(x["passed"] for x in groups),
            "overall": overall, "groups": groups, "denominator_floor": 1e-6,
            "global_ratio_limit": 0.9, "group_window_ratio_limit": 1.05,
            "aggregation": "equal-weight per-token relative-L2 across local 12 x 128 post-RMS",
            "late_windows": {"prefill_late": [64, 127], "decode_late": [132, 135]}}


def bind_inputs(args):
    audit = load_tool("validate_gdn_teacher_capture", AUDITOR_SHA256)
    receipt = audit.bound_json(args.audit_report, args.audit_sha256)
    require(receipt.get("schema") == audit.AUDIT_SCHEMA
            and receipt.get("status") == "dense_teacher_evidence_validated_local_only"
            and receipt.get("auditor_sha256") == AUDITOR_SHA256, "passed validator receipt required")
    manifest = audit.bound_json(args.manifest, args.manifest_sha256)
    audit.check_manifest(manifest)
    require(receipt.get("manifest") == {"path": str(args.manifest), "sha256": args.manifest_sha256},
            "explicit capture manifest differs from validator")
    service_file = audit.regular(receipt["service_manifest"]["path"])
    service_dir = service_file.parent
    service = audit.bound_json(service_file, receipt["service_manifest"]["sha256"])
    collector = audit.bound_json(receipt["collector_receipt"]["path"], receipt["collector_receipt"]["sha256"])
    exit_path = audit.regular(service_dir / "service-exit.json")
    exit_doc = json.loads(exit_path.read_bytes())
    require(exit_doc.get("group_remaining") is False and exit_doc.get("stop_reason") == "stop_request",
            "capture service must be stopped and its process group reaped")
    # Full CPU shape/state/source audit precedes ANY numerical NPU execution.
    recomputed = audit.audit(service_dir, args.manifest, args.manifest_sha256,
                             receipt["collector_receipt"]["sha256"],
                             collector["script_sha256"], service["worker_sha256"])
    for key in ("files", "archive_count", "checks", "native_schema", "ready_reports", "complete_reports"):
        require(receipt.get(key) == recomputed[key], "validator recheck differs: " + key)
    plan = audit.bound_json(args.energy_plan, PLAN_SHA256)
    stats = audit.bound_json(args.retained_stats, STATS_SHA256)
    for layer in LAYERS:
        for rank in range(4):
            coefficients(plan, stats, layer, rank)
    entries = {}
    for row in receipt["files"]:
        key = (row["sequence_id"], row["rank"], row["layer"], row["step"])
        require(key not in entries, "duplicate audit archive")
        entries[key] = row
    expected = {(f"teacher-{s}", r, layer, step)
                for s in range(2) for r in range(4) for layer in LAYERS for step in range(9)}
    require(set(entries) == expected, "432 archive coverage")
    binding = {"audit": {"path": str(args.audit_report), "sha256": args.audit_sha256},
               "manifest": receipt["manifest"], "energy_plan": {"path": str(args.energy_plan), "sha256": PLAN_SHA256},
               "retained_stats": {"path": str(args.retained_stats), "sha256": STATS_SHA256},
               "service_exit": {"path": str(exit_path), "sha256": checksum(exit_path)},
               "coefficient_source": "train_k_mean only; frozen old calibration rows 0..11",
               "audit_rechecked_before_npu": True}
    return SimpleNamespace(audit=audit, receipt=receipt, capture=service_dir / "teacher-capture",
                           entries=entries, plan=plan, stats=stats, binding=binding)


def init_runtime(report, phase):
    for path, expected in SOURCE_HASHES.items():
        require(checksum(path) == expected, "frozen runtime changed: " + path)
    golden = load_tool("gdn_golden_parity", GOLDEN_SHA256)
    probe = load_tool("gdn_retained_energy_probe", PROBE_SHA256)
    report["plugin_isolation"] = probe.disable_plugin()
    probe.initialize_npu(report, phase)
    from vllm_ascend.ops.triton.fla import chunk
    from vllm_ascend.ops.layernorm import LayerNormFn
    from vllm.model_executor.layers.fla.ops.l2norm import l2norm_fwd as decode_l2norm
    decode_norm = sys.modules[decode_l2norm.__module__]
    decode_path = "/vllm-workspace/vllm/vllm/model_executor/layers/fla/ops/l2norm.py"
    require(Path(decode_norm.__file__).resolve() == Path(decode_path),
            "decode L2 implementation source path differs from frozen GDN import")
    report["normalization_dispatch"] = {
        "decode": {"path": decode_path, "sha256": SOURCE_HASHES[decode_path],
                   "module": decode_l2norm.__module__,
                   "USE_DEFAULT_FLA_NORM": decode_norm.USE_DEFAULT_FLA_NORM},
        "prefill": {"path": "/vllm-workspace/vllm-ascend/vllm_ascend/ops/triton/fla/l2norm.py",
                    "use_qk_l2norm_in_kernel": True, "dispatch": "Ascend chunk internal L2"},
    }
    require((golden.PREFILL_RTOL, golden.PREFILL_ATOL, golden.DECODE_RTOL, golden.DECODE_ATOL)
            == (PREFILL_RTOL, PREFILL_ATOL, DECODE_RTOL, DECODE_ATOL), "golden tolerances changed")
    report["source_sha256"].update(SOURCE_HASHES)
    return SimpleNamespace(golden=golden, probe=probe, chunk=chunk, norm=LayerNormFn,
                           decode_l2norm=decode_l2norm,
                           native=torch.ops._C_ascend.npu_recurrent_gated_delta_rule)


def cpu_reference(data, state, dk, compensated, golden):
    # Existing independent FP32 recurrence, with existing explicit sum-square
    # L2 normalization; one length-T sequence, one private local state slot.
    beta = beta_product(data["beta"], data["r"])[1] if compensated else data["beta"]
    tokens = data["q"].shape[1]
    q = golden._cpu_l2norm(data["q"]).reshape(tokens, 4, dk)
    k = golden._cpu_l2norm(data["k"]).reshape(tokens, 4, dk)
    return golden._decode_golden(
        q, k, data["v"].reshape(tokens, 12, 128), state,
        beta.reshape(tokens, 12), dk ** -0.5,
        torch.tensor([tokens], dtype=torch.int32),
        torch.zeros(tokens, dtype=torch.int32), data["g"].reshape(tokens, 12))


def operation(data, state, dk, compensated, runtime):
    # Frozen gdn.py imports generic vLLM L2 for decode; prefill's Ascend
    # chunk uses its own L2 implementation. Do not collapse these bindings.
    q = runtime.decode_l2norm(data["q"]).squeeze(0)
    k = runtime.decode_l2norm(data["k"]).squeeze(0)
    product, beta = beta_product(data["beta"], data["r"]) if compensated else (data["beta"], data["beta"])
    output = runtime.native(query=q, key=k, value=data["v"].squeeze(0),
                            g=data["g"], beta=beta, state=state, scale=dk ** -0.5,
                            actual_seq_lengths=data["lengths"], ssm_state_indices=data["indices"])
    norm = runtime.norm.apply(output.reshape(-1, 128), data["weight"], None, data["z"],
                              1e-6, None, True, True).reshape(-1, 12, 128)
    return {"output": output, "norm": norm, "q": q, "k": k, "product": product, "beta": beta}


def prefill(data, dk, compensated, runtime):
    product, beta = beta_product(data["beta"], data["r"]) if compensated else (data["beta"], data["beta"])
    cu = torch.tensor([0, 128], dtype=torch.int64)
    meta = runtime.golden._build_prefill_metadata(torch.device("npu:0"), cu)
    initial = torch.zeros((1, 12, dk, 128), dtype=torch.float32, device="npu:0")
    with (
        patch.object(runtime.chunk, "get_forward_context", return_value=SimpleNamespace(attn_metadata=None)),
        patch.object(runtime.chunk, "get_pcp_group", return_value=SimpleNamespace(world_size=1)),
    ):
        output, state = runtime.chunk.chunk_gated_delta_rule(
            q=data["q"], k=data["k"], v=data["v"], g=data["g"], beta=beta,
            scale=dk ** -0.5, initial_state=initial, output_final_state=True,
            cu_seqlens=cu.to("npu:0"), prebuilt_meta=meta, head_first=False,
            use_qk_l2norm_in_kernel=True)
    output = output.reshape(128, 12, 128)
    norm = runtime.norm.apply(output.reshape(-1, 128), data["weight"], None, data["z"],
                              1e-6, None, True, True).reshape(128, 12, 128)
    return {"output": output, "norm": norm, "product": product, "beta": beta}, state.transpose(-1, -2).contiguous()


def data_from(record, keep, r12, dk):
    tensors = record["tensors"]
    q, k = tensors["raw_q"], tensors["raw_k"]
    if dk == 64:
        q, k = select_qk(q, keep), select_qk(k, keep)
    return {"q": q.clone(), "k": k.clone(), "v": tensors["raw_v"].clone(),
            "g": tensors["g"].clone(), "beta": tensors["beta"].clone(),
            "r": r12.clone(), "z": tensors["z"].clone(), "weight": tensors["norm_weight"].clone(),
            "lengths": torch.tensor([0, 1], dtype=torch.int32),
            "indices": torch.zeros(1, dtype=torch.int32)}


def archive(path, payload):
    with path.open("xb") as stream:
        torch.save(payload, stream)
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": str(path), "sha256": checksum(path), "size_bytes": path.stat().st_size}


def token_errors(actual, teacher):
    a, b = cpu(actual).float().reshape(-1, 12 * 128), teacher.float().reshape(-1, 12 * 128)
    require(a.shape == b.shape and bool(torch.isfinite(a).all() and torch.isfinite(b).all()),
            "finite token comparison")
    return (torch.linalg.vector_norm(a - b, dim=1)
            / torch.linalg.vector_norm(b, dim=1).clamp_min(1e-6)).tolist()


def run_trajectory(records, variant, keep, r12, runtime, group, out, report, save, phase):
    dk, compensated = (128 if variant == "dense128" else 64), variant == "beta64"
    row = {"sequence_id": group[0], "rank": group[1], "layer": group[2],
           "variant": variant, "dk": dk, "passed": False, "steps": [],
           "r12": r12.tolist() if compensated else None, "graph_warmups": 3}
    report["trajectories"].append(row)
    graph = None
    token_rows = []
    try:
        phase("trajectory_prefill", group=list(group), variant=variant)
        data_cpu = data_from(records[0], keep, r12, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        state_cpu = torch.zeros((1, 12, 128, dk), dtype=torch.float32)
        cpu_output, next_cpu = cpu_reference(data_cpu, state_cpu, dk, compensated, runtime.golden)
        result, eager_state = prefill(data, dk, compensated, runtime)
        torch.npu.synchronize()

        def record_step(step, result, expected_output, expected_state, graph_state=None, graph_result=None):
            phase_name = "prefill" if step == 0 else "decode"
            teacher = records[step]["tensors"]
            checks = {
                "output_cpu": metrics(result["output"], expected_output, phase_name),
                "full_state_cpu": metrics(eager_state, expected_state, phase_name),
            }
            product_cpu, beta_cpu = (beta_product(data_cpu["beta"], data_cpu["r"])
                                    if compensated else (data_cpu["beta"], data_cpu["beta"]))
            bools = {"beta_product_cpu_bytes": exact(result["product"], product_cpu),
                     "beta_bf16_cpu_bytes": exact(result["beta"], beta_cpu)}
            if variant == "dense128":
                checks.update(
                    output_capture=metrics(result["output"], teacher["operator_output"].reshape(-1, 12, 128), phase_name),
                    full_state_capture=metrics(eager_state, teacher["state_final"], phase_name),
                    post_rms_capture=metrics(result["norm"], teacher["norm_output"].reshape(-1, 12, 128), phase_name))
                if step:
                    bools.update(query_capture_bytes=exact(result["q"], teacher["query"]),
                                 key_capture_bytes=exact(result["k"], teacher["key"]))
            if graph_result is not None:
                bools["graph_eager_full_state_bytes"] = exact(graph_state, eager_state)
                for key in result:
                    bools["graph_eager_" + key + "_bytes"] = exact(graph_result[key], result[key])
                bools["graph_persistent_metadata"] = tracked == {
                    key: runtime.probe.metadata(value) for key, value in tracked_tensors.items()}
            passed = all(value["passed"] for value in checks.values()) and all(bools.values())
            payload = {"schema": "drrqr-real-teacher-trajectory/v1", "group": list(group),
                       "variant": variant, "step": step, "state_layout": "N,Nv,Dv,Dk",
                       "state": cpu(eager_state), "cpu_reference_state": cpu(expected_state),
                       "cpu_reference_output": cpu(expected_output),
                       "tensors": {key: cpu(value) for key, value in result.items()},
                       "graph_state": cpu(graph_state) if graph_state is not None else None,
                       "metrics": checks, "checks": bools, "passed": passed}
            filename = f"{variant}.{group[0]}.rank{group[1]}.layer{group[2]}.step{step}.pt"
            item = {"step": step, "phase": phase_name, "metrics": checks, "checks": bools,
                    "passed": passed, "archive": archive(out / filename, payload)}
            row["steps"].append(item)
            save()
            require(passed, "predeclared numerical/capture/graph gate failed; no retry")
            errors = token_errors(result["norm"], teacher["norm_output"])
            start = 0 if step == 0 else 127 + step
            token_rows.extend({"position": start + offset, "relative_l2": value}
                              for offset, value in enumerate(errors))

        record_step(0, result, cpu_output, next_cpu)
        state_cpu = next_cpu
        # Private persistent graph state starts from this variant's own prefill,
        # never from the dense capture or another variant.
        graph_state = eager_state.clone()
        graph_initial = eager_state.clone()
        data_cpu = data_from(records[1], keep, r12, dk)
        data = {key: value.to("npu:0") for key, value in data_cpu.items()}
        phase("graph_warmup", group=list(group), variant=variant)
        for _ in range(3):
            operation(data, graph_state, dk, compensated, runtime)
            torch.npu.synchronize()
        phase("graph_capture", group=list(group), variant=variant)
        graph = torch.npu.NPUGraph()
        with torch.npu.graph(graph):
            graph_result = operation(data, graph_state, dk, compensated, runtime)
        torch.npu.synchronize()
        graph_state.copy_(graph_initial)
        torch.npu.synchronize()
        tracked_tensors = {**{"input." + k: v for k, v in data.items()},
                           **{"result." + k: v for k, v in graph_result.items()},
                           "eager_state": eager_state, "graph_state": graph_state}
        tracked = {key: runtime.probe.metadata(value) for key, value in tracked_tensors.items()}
        row["graph_tracked_metadata"] = tracked
        for step in range(1, 9):
            phase("trajectory_decode", group=list(group), variant=variant, step=step)
            data_cpu = data_from(records[step], keep, r12, dk)
            for key, value in data_cpu.items():
                data[key].copy_(value)
            cpu_output, next_cpu = cpu_reference(data_cpu, state_cpu, dk, compensated, runtime.golden)
            result = operation(data, eager_state, dk, compensated, runtime)
            graph.replay()
            torch.npu.synchronize()
            record_step(step, result, cpu_output, next_cpu, graph_state, graph_result)
            state_cpu = next_cpu
        require(len(token_rows) == 136 and len(row["steps"]) == 9, "complete trajectory")
        row["passed"] = True
        return token_rows
    except BaseException as error:
        row.update(passed=False, error=repr(error), traceback=traceback.format_exc())
        raise
    finally:
        original_error = sys.exc_info()[1]
        if graph is not None:
            try:
                graph.reset()
                row["graph_reset"] = True
            except BaseException as error:
                row.update(passed=False, graph_reset=False, graph_cleanup_error=repr(error))
                if original_error is None:
                    raise
        save()


def check_runtime_libraries(libraries, teacher_identities, report, save):
    """Persist observations before strict canonical-path and byte-identity checks."""
    report["loaded_libraries"] = libraries
    report["library_checks"] = []
    report["runtime_evidence_passed"] = False
    report["library_scope"] = "mapped-file hashes, not proof of same-name ACLNN symbol resolution"
    save()
    teacher = {item["path"]: item["sha256"] for item in teacher_identities
               if item["kind"] == "mapped_library"}
    for item in libraries:
        row = {"raw_path": item["path"], "resolved_path": None, "sha256": item["sha256"],
               "current_sha256": None, "teacher_sha256": None,
               "in_teacher": False, "matched": False, "reason": "inspection_failed"}
        report["library_checks"].append(row)
        try:
            raw_path = Path(item["path"])
            require(raw_path.is_absolute(), "mapped library path must be absolute")
            resolved = raw_path.resolve(strict=True)
            require(resolved.is_file(), "mapped library must resolve to a regular file")
            row.update(resolved_path=str(resolved), current_sha256=checksum(resolved),
                       in_teacher=str(resolved) in teacher, teacher_sha256=teacher.get(str(resolved)))
            if item["sha256"] != row["current_sha256"]:
                row["reason"] = "observed_hash_changed"
            elif not row["in_teacher"]:
                row["reason"] = "canonical_path_not_in_teacher"
            elif item["sha256"] != row["teacher_sha256"]:
                row["reason"] = "teacher_hash_mismatch"
            else:
                row.update(matched=True, reason="canonical_path_and_sha256_match")
        except Exception as error:
            row["error"] = repr(error)
        finally:
            save()
    require(any("libcust_opapi" in item["raw_path"] for item in report["library_checks"]),
            "mapped native opapi absent")
    require(all(item["matched"] for item in report["library_checks"]),
            "replay native library absent/changed from teacher evidence; see library_checks")
    report["runtime_evidence_passed"] = True
    save()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("audit-report", "manifest", "energy-plan", "retained-stats", "output-dir"):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("audit-sha256", "manifest-sha256"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--max-seconds", type=int, default=1800)
    args = parser.parse_args(argv)
    require(os.environ.get("ASCEND_RT_VISIBLE_DEVICES") == "0,1,2,3",
            "audited four-device namespace required; this process uses logical npu0 only")
    require(1 <= args.max_seconds <= 1800, "bounded 1..1800-second replay")
    out = args.output_dir
    require(out.is_absolute() and out == out.resolve() and RESULT_ROOT in out.parents
            and not out.exists(), "fresh canonical output below /drrqr-results")
    out.mkdir(parents=False, exist_ok=False)
    report = {"schema": "drrqr-real-teacher-replay/v1", "status": "failed", "claim": CLAIM,
              "script_sha256": checksum(__file__), "phase": "cpu_admission",
              "created_unix_ns": time.time_ns(), "trajectories": [],
              "dense_gate_passed": False, "candidate_numerical_gate_passed": False,
              "prefill_graph_gate": "not_implemented_not_required_by_FULL_DECODE_ONLY",
              "goal_checkpoint": "Test beta compensation of the current energy-selector DRRQR limitation; "
                                 "local evidence can only admit a later joint-target model screen.",
              "protocol": {"variants": list(VARIANTS), "groups": 48, "input_tokens": 128, "decode_steps": 8,
                           "prefill": "eager complete chunk path from zero",
                           "decode_graph": "raw Q/K L2 + beta FP32 multiply/BF16 cast + native + actual gated RMS",
                           "prefill_rtol": PREFILL_RTOL, "prefill_atol": PREFILL_ATOL,
                           "decode_rtol": DECODE_RTOL, "decode_atol": DECODE_ATOL,
                           "decode_relative_l2_limit": RELATIVE_L2_LIMIT,
                           "decode_normalized_max_limit": NORMALIZED_MAX_LIMIT,
                           "graph_comparison": "finite bitwise eager/graph outputs, full state, beta and metadata",
                           "max_seconds": args.max_seconds, "retry_count": 0,
                           "execution": "all 4 ranks' local tensors replayed sequentially on logical npu0",
                           "hard_deadline": "parent must enforce own-process timeout for a stuck native call"}}
    deadline = time.monotonic() + args.max_seconds
    def save():
        partial = out / "report.json.tmp"
        partial.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        partial.replace(out / "report.json")
    def phase(name, **details):
        report.update(phase=name, active=details)
        save()
        if time.monotonic() > deadline:
            raise TimeoutError("fixed replay budget exceeded")
    def interrupted(signum, frame):
        raise InterruptedError("replay interrupted by signal " + str(signum))
    previous_handlers = {sig: signal.signal(sig, interrupted) for sig in (signal.SIGTERM, signal.SIGINT)}
    runtime = None
    current_variant = None
    save()
    try:
        bound = bind_inputs(args)
        report["bindings"] = bound.binding
        phase("runtime_init")
        runtime = init_runtime(report, lambda name: phase(name))
        require(report["operator_schema"] == bound.receipt["native_schema"], "native schema differs from teacher")
        groups = [(f"teacher-{s}", r, layer) for s in range(2) for r in range(4) for layer in LAYERS]
        fidelity = {}
        for variant in VARIANTS:
            current_variant = variant
            if variant != "dense128":
                require(report["dense_gate_passed"], "dense gate precedes candidate attribution")
            for group in groups:
                phase("load_group", group=list(group), variant=variant)
                records = []
                for step in range(9):
                    entry = bound.entries[(*group, step)]
                    record, _ = bound.audit.load_record(bound.capture / entry["file"], entry["sha256"])
                    records.append(record)
                keep, _, r12 = coefficients(bound.plan, bound.stats, group[2], group[1])
                errors = run_trajectory(records, variant, keep, r12, runtime, group, out, report, save, phase)
                if variant != "dense128":
                    for row in errors:
                        key = (*group, row["position"])
                        fidelity.setdefault(key, {})[variant + "_relative_l2"] = row["relative_l2"]
            if variant == "dense128":
                report["dense_gate_passed"] = True
                save()
        require(len(report["trajectories"]) == 144 and all(x["passed"] for x in report["trajectories"]),
                "all dense and candidate trajectories must complete")
        report["candidate_numerical_gate_passed"] = True
        rows = [{"sequence_id": key[0], "rank": key[1], "layer": key[2], "position": key[3], **value}
                for key, value in sorted(fidelity.items())]
        report["fidelity"] = fidelity_screen(rows)
        with (out / "token-fidelity.json").open("x") as stream:
            json.dump(rows, stream, allow_nan=False)
        report["token_fidelity"] = {"path": str(out / "token-fidelity.json"),
                                    "sha256": checksum(out / "token-fidelity.json")}
        report["status"] = ("local_fidelity_screen_pass" if report["fidelity"]["passed"]
                            else "local_fidelity_screen_failed")
        report["phase"] = "complete"
    except BaseException as error:
        report.update(status="blocked_dense_replay" if current_variant == "dense128"
                      else "failed_candidate_numerical" if current_variant else "failed_admission",
                      error=repr(error), traceback=traceback.format_exc())
    finally:
        if runtime is not None:
            try:
                libraries = runtime.probe.loaded_libraries()
                check_runtime_libraries(libraries, bound.receipt["identities"], report, save)
            except BaseException as error:
                report.update(runtime_evidence_passed=False, library_error=repr(error))
                if report["status"] == "local_fidelity_screen_pass":
                    report["status"] = "failed_runtime_evidence"
        report["completed_unix_ns"] = time.time_ns()
        save()
        for sig, handler in previous_handlers.items():
            signal.signal(sig, handler)
    print(json.dumps({"status": report["status"], "report": str(out / "report.json")}), flush=True)
    return 0 if report["status"] == "local_fidelity_screen_pass" else 1


if __name__ == "__main__":
    sys.exit(main())
