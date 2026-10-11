"""Independent CPU reconstruction of bounded HYPIC snapshots.

No production HYPIC import, quality verdict, or automatic numerical tolerance.
FP64 reconstruction exposes residuals, not bitwise equivalence to NPU arithmetic.
"""
from __future__ import annotations

import math
import torch

DTYPES = {str(x): x for x in (torch.float16, torch.bfloat16, torch.float32,
                              torch.float64, torch.int32, torch.int64)}
KEYS = ("request_id", "rank", "pid", "step", "layer")


def tensor(record):
    shape, values = record["shape"], record["values"]
    if (not isinstance(shape, list) or not shape
            or any(type(x) is not int or x <= 0 for x in shape)
            or math.prod(shape) > 1_000_000
            or len(values) != math.prod(shape)
            or record["dtype"] not in DTYPES):
        raise ValueError("invalid bounded tensor shape/dtype")
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
        raise ValueError("nonfinite/non-numeric tensor")
    if record["dtype"] in ("torch.int32", "torch.int64") and any(
            type(v) is not int for v in values):
        raise ValueError("noninteger integer tensor")
    return torch.tensor(values, dtype=torch.float64).reshape(shape)


def residual(reference, actual):
    observed = tensor(actual)
    if reference.shape != observed.shape:
        raise ValueError("reference/actual shape mismatch")
    if not torch.isfinite(reference).all():
        raise ValueError("nonfinite reconstruction")
    # Report both FP64 reference and destination-representable reference.
    rounded = reference.to(DTYPES[actual["dtype"]]).to(torch.float64)
    if not torch.isfinite(rounded).all():
        raise ValueError("destination conversion overflow")
    diff = observed - rounded
    return {
        "max_abs": float(diff.abs().max()),
        "rms": float(diff.square().mean().sqrt()),
        "different_coordinates": int(torch.count_nonzero(diff)),
        "coordinates": observed.numel(),
        "fp64_max_abs": float((observed-reference).abs().max()),
        "numerical_acceptance": "not-decided",
    }


def identity(event):
    if event.get("schema") != "hypic-state-capture/v1":
        raise ValueError("unsupported capture schema")
    if (not isinstance(event.get("request_id"), str) or not event["request_id"]
            or type(event.get("rank")) is not int or event["rank"] not in range(4)
            or type(event.get("pid")) is not int or event["pid"] <= 0
            or type(event.get("step")) is not int or event["step"] < 0):
        raise ValueError("invalid capture identity")
    return tuple(event[k] for k in KEYS)


def positions(event):
    actual = event["actual_positions"]
    expected = event["expected_positions"]
    if (actual["dtype"] not in ("torch.int32", "torch.int64")
            or any(type(x) is not int for x in expected)):
        raise ValueError("positions must be exact integers")
    reference = torch.tensor(expected, dtype=torch.float64)
    return residual(reference, actual)


def kv(event):
    rope = event["rope"]
    dimension = rope["rotary_dim"]
    if rope.get("neox") is not True or type(dimension) is not int or dimension <= 0 or dimension % 2:
        raise ValueError("unsupported RoPE geometry")
    if not event["segments"]:
        raise ValueError("no captured hot segment")
    results = []
    seen = set()
    for segment in event["segments"]:
        anchor = segment["anchor"]
        if type(anchor) is not int or anchor < 0:
            raise ValueError("invalid anchor")
        geometry = tensor(rope["rows"][str(anchor)]).reshape(-1)
        if geometry.numel() != dimension:
            raise ValueError("RoPE row width mismatch")
        cos, sin = geometry[:dimension//2], geometry[dimension//2:]
        for sample in segment["samples"]:
            sample_key = (segment["segment_hash"], sample["material_row"])
            if sample_key in seen:
                raise ValueError("duplicate KV coordinate")
            seen.add(sample_key)
            if sample["logical_position"] != anchor + segment["seam"] + sample["material_row"]:
                raise ValueError("KV position identity mismatch")
            key = tensor(sample["canonical_key"])
            actual = sample["actual_key"]
            if key.ndim != 1 or dimension > key.numel():
                raise ValueError("invalid KV head width")
            # Match source/destination conversion, reconstruct rotation separately.
            key = key.to(DTYPES[actual["dtype"]]).to(torch.float64)
            expected = key.clone()
            if anchor:
                c = torch.cat((cos, cos)).to(DTYPES[actual["dtype"]]).to(torch.float64)
                s = torch.cat((sin, sin)).to(DTYPES[actual["dtype"]]).to(torch.float64)
                x = key[:dimension]
                rotated = torch.cat((-x[dimension//2:], x[:dimension//2]))
                expected[:dimension] = x*c + rotated*s
            results.append({
                "segment_hash": segment["segment_hash"],
                "material_row": sample["material_row"],
                "destination_slot": sample["destination_slot"],
                "key": residual(expected, actual),
                "value": residual(tensor(sample["canonical_value"]), sample["actual_value"]),
            })
    if not results:
        raise ValueError("no KV samples")
    return results


def gdn(initial, committed):
    if identity(initial) != identity(committed):
        raise ValueError("GDN initial/committed identity mismatch")
    state = tensor(initial["incoming_state"])
    if state.ndim != 2 or not initial["stages"] or len(initial["stages"]) > 16:
        raise ValueError("invalid GDN stages")
    for stage in initial["stages"]:
        if stage["kind"] not in ("cache", "row"):
            raise ValueError("unknown GDN stage")
        transition, zero = tensor(stage["transition"]), tensor(stage["zero_state"])
        if transition.shape != (state.shape[0], state.shape[0]) or zero.shape != state.shape:
            raise ValueError("GDN composition shape mismatch")
        state = transition @ state + zero
    conv = tensor(initial["conv_initial"])
    state_len, dim_first = initial["state_len"], initial["conv_dim_first"]
    if type(dim_first) is not bool or type(state_len) is not int or state_len <= 0 or conv.ndim != 2:
        raise ValueError("invalid convolution layout")
    tail = conv.T if dim_first else conv
    if tail.shape[0] != state_len:
        raise ValueError("conv state length mismatch")
    for action in initial["conv_actions"]:
        value = tensor(action["value"])
        if action["kind"] == "cache":
            replacement = value.T if dim_first else value
            if replacement.shape != tail.shape:
                raise ValueError("cached conv shape mismatch")
            tail = replacement
        elif action["kind"] == "row":
            tokens = action["original_tokens"]
            if (type(tokens) is not int or tokens <= 0 or value.ndim != 2
                    or value.shape != (min(tokens, state_len), tail.shape[1])):
                raise ValueError("row conv input shape mismatch")
            tail = torch.cat((tail, value), dim=0)[-state_len:]
        else:
            raise ValueError("unknown conv action")
    return {
        "state": residual(state.T, committed["actual_state"]),
        "conv": residual(tail.T if dim_first else tail, committed["actual_conv"]),
    }


def audit(events, *, request_id, kv_layer, gdn_layer):
    """Require all four ranks and one selected step; retain limited coverage."""
    if kv_layer == gdn_layer:
        raise ValueError("distinct attention/GDN layers required")
    indexed, ranks = {}, {}
    for event in events:
        key = identity(event)
        if event["request_id"] != request_id:
            raise ValueError("foreign request in capture")
        stage = event["stage"]
        expected_layer = {
            "positions_committed": None, "kv_committed": kv_layer,
            "gdn_initial": gdn_layer, "gdn_committed": gdn_layer,
        }.get(stage, "__invalid__")
        if event["layer"] != expected_layer:
            raise ValueError("unexpected stage/layer")
        if (key, stage) in indexed:
            raise ValueError("duplicate capture stage")
        indexed[key, stage] = event
        ranks.setdefault(event["rank"], set()).add((event["pid"], event["step"]))
    if set(ranks) != set(range(4)) or any(len(v) != 1 for v in ranks.values()):
        raise ValueError("four ranks/single step coverage missing")
    bindings = {rank: next(iter(values)) for rank, values in ranks.items()}
    if len({x[0] for x in bindings.values()}) != 4 or len({x[1] for x in bindings.values()}) != 1:
        raise ValueError("worker PID/step identity conflict")
    results = []
    for rank, (pid, step) in sorted(bindings.items()):
        def get(stage, layer):
            try:
                return indexed[(request_id, rank, pid, step, layer), stage]
            except KeyError as exc:
                raise ValueError("incomplete component capture") from exc
        results.append({
            "rank": rank, "pid": pid, "step": step,
            "positions": positions(get("positions_committed", None)),
            "kv": kv(get("kv_committed", kv_layer)),
            "gdn": gdn(get("gdn_initial", gdn_layer), get("gdn_committed", gdn_layer)),
        })
    return {
        "schema": "hypic-independent-state-audit/v1", "request_id": request_id,
        "ranks": results, "reference_precision": "CPU float64; destination cast reported",
        "scope": "selected layers, head0, selected KV rows; material inputs are not independently regenerated",
        "numerical_acceptance": "not-decided", "physical_device_proven": False,
        "producer_generation_proven": False, "quality_or_causality_proven": False,
        "hot_receipt_join_required": True,
    }


def join_request_hot_receipts(report, receipts, worker_bindings):
    """Join request/PID only. Old receipts have no step: never claim step proof.

    worker_bindings must come from a separately audited runtime inventory.
    This helper checks identity consistency, not the authenticity of that input
    or continuous physical isolation. NPU admission remains a separate gate.
    """
    expected = {row["rank"]: row["pid"] for row in report["ranks"]}
    if expected != worker_bindings or len(set(expected.values())) != 4:
        raise ValueError("worker inventory mismatch")
    matched = {}
    for receipt in receipts:
        if (receipt.get("event") != "worker_hot_request_verified"
                or receipt.get("request_id") != report["request_id"]):
            continue
        pid = receipt.get("pid")
        if pid not in expected.values():
            raise ValueError("foreign worker hot receipt")
        if pid in matched:
            raise ValueError("ambiguous multiple hot steps")
        if (receipt.get("complete_hybrid_repair_validated") is not True
                or type(receipt.get("skipped_prefix_tokens")) is not int
                or receipt["skipped_prefix_tokens"] <= 0
                or any(type(receipt.get(k)) is not int or receipt[k] <= 0
                       for k in ("expected_full_layers", "expected_gdn_layers"))):
            raise ValueError("incomplete hot receipt")
        matched[pid] = receipt
    if set(matched) != set(expected.values()):
        raise ValueError("missing four-worker request hot receipts")
    return {
        "request_level_hot_receipts_joined": True,
        "step_level_hot_proven": False,
        "physical_device_proven": False,
        "limitation": "legacy hot receipts omit step; producer-generation and step-specific proof still required",
    }
