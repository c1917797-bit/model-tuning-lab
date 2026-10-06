#!/usr/bin/env python3
"""Pre-registered DAMP numerical gate; NOT an E2E or performance benchmark."""
import argparse
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import time
import traceback
import torch

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent
REPO = PROJECT.parent.parent
sys.path.insert(0, str(HERE))
from independent_oracle import (
    RECIPROCAL, RECIPROCAL_BITS, OracleLayout, ValueMajorPacked,
    compressed_step, errors, f32, f32_bits, original_coordinate_errors,
    pack_value_major, restore_state, scalar_div_f32, scalar_scale_f32,
    transform_state, uncompressed_step, unpack_value_major)

# These are implementation-parity limits, not the user's task-accuracy limit.
LIMITS = {"state_selected_max_head_relative_l2": 1e-5,
          "output_max_head_relative_l2": 0.00303}
SEED = 260827513
HV, HQ, DV, DK = 12, 4, 128, 128
STEPS = 160
ABI = {
    "operator": "qwen36_damp.decode",
    "q_k": "BF16[B,4,128], already normalized; head=h//3",
    "v": "BF16[B,12,128]",
    "g": "FP32[B,12], log decay <=0",
    "beta": "BF16[B,12], [0,1]",
    "high": "FP16[S,12,128,16], value-major",
    "low": "INT8[S,12,128,112], value-major",
    "scales": "FP32[S,12,4,112], groups of 32 reordered V channels",
    "pk_pv_inv_pv": "INT32[12,128], logical indices, NOT byte offsets",
    "sr": "FP32[12,128], original-coordinate c[h,v]",
    "pv_direction": "reordered -> original; inverse_pv original -> reordered",
    "q_scale": "128**-0.5",
    "actual_seq_lengths": "INT32[0,1,...,1], pinned single-token length ABI",
    "state_indices": "INT32[B], unique in-range slot IDs",
    "readout_order": "updated FP32 readout -> original V coordinates -> BF16; then pack",
    "unsupported": ["mixed prefill/decode", "multi-token query", "duplicate slots",
                    "graph", "serving allocator", "performance/quality acceptance"],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def exact(actual, expected):
    a, e = actual.detach().cpu().contiguous(), expected.detach().cpu().contiguous()
    return (a.shape == e.shape and a.dtype == e.dtype and
            torch.equal(a.view(torch.uint8), e.view(torch.uint8)))


def safe_json(value):
    if isinstance(value, dict):
        return {str(k): safe_json(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [safe_json(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return {"nonfinite": repr(value)}
    return value


def retain_failure(report, save, fixture):
    """One immutable CPU tensor fixture; never overwrite a previous failure."""
    path = Path(report["artifact_root"]) / "first_failure.pt"
    if path.exists():
        return
    def cpu_only(value):
        if isinstance(value, torch.Tensor):
            return value.detach().cpu().clone()
        if isinstance(value, dict):
            return {key: cpu_only(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [cpu_only(item) for item in value]
        return value
    try:
        torch.save(cpu_only(fixture), path)
        report["first_failure_fixture"] = {"path": str(path), "sha256": sha(path)}
    except BaseException as artifact_error:
        report["failure_fixture_save_error"] = repr(artifact_error)
    try:
        save()
    except BaseException as report_error:
        report["failure_fixture_report_save_error"] = repr(report_error)


def packed_dict(packed):
    return {"high": packed.high, "low": packed.low, "scales": packed.scales}


def layout_dict(layout):
    return {"c": layout.c, "pv": layout.pv, "pk": layout.pk,
            "khi": layout.khi, "group": layout.group}


def load_candidate():
    path = PROJECT / "reference.py"
    spec = importlib.util.spec_from_file_location("damp_candidate_reference", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def identity_layout(hv, dv, dk):
    return OracleLayout(torch.ones(hv, dv, dtype=torch.float32),
                        torch.arange(dv).repeat(hv, 1),
                        torch.arange(dk).repeat(hv, 1))


def random_layout(generator):
    c = torch.linspace(-0.3, 0.3, DV).exp().repeat(HV, 1)
    pv = torch.stack([torch.randperm(DV, generator=generator) for _ in range(HV)])
    pk = torch.stack([torch.randperm(DK, generator=generator) for _ in range(HV)])
    return OracleLayout(c, pv, pk)


def candidate_layout(candidate, layout, device):
    return candidate.Layout(layout.c.to(device), layout.pv.to(device),
                            layout.pk.to(device), layout.khi, layout.group)


def key_major_to_value_major(candidate_packed):
    """Explicit reference-only adapter. This is NOT the custom operator ABI."""
    return ValueMajorPacked(candidate_packed.high.transpose(-1, -2).cpu().contiguous(),
                            candidate_packed.codes.transpose(-1, -2).cpu().contiguous(),
                            candidate_packed.scales.transpose(-1, -2).cpu().contiguous())


def boundary_state():
    # Each column has its own group maximum; crafted inputs span true V groups.
    layout = identity_layout(1, 96, 64)
    state = torch.zeros(1, 1, 96, 64, dtype=torch.float32)
    descriptors = []
    half_ties = [-2.5, -1.5, -0.5, 0.5, 1.5, 2.5]
    for column, maximum in enumerate((127.0, f32(0.40259), f32(1e-35),
                                     torch.finfo(torch.float32).max)):
        scale = scalar_scale_f32(maximum)
        values = [-maximum, maximum]
        for half in half_ties:
            center = torch.tensor(f32(half*scale), dtype=torch.float32)
            values.extend([float(torch.nextafter(center, torch.tensor(-math.inf))),
                           float(center),
                           float(torch.nextafter(center, torch.tensor(math.inf)))])
        for group in (0, 2):
            start = group*32
            state[0, 0, start:start+len(values), 16+column] = torch.tensor(values)
        descriptors.append({"column": 16+column, "amax": maximum,
                            "scale_bits": hex(f32_bits(scale)),
                            "cases": "±127 endpoints; ±half and input ±1 ULP"})
    state[..., 0] = 65504.0
    state[..., 1] = -65504.0
    # Entire middle V group remains zero; last low key remains an all-zero column.
    return state, layout, descriptors


def packed_metrics(actual, expected):
    return {"high_bitwise": exact(actual.high, expected.high),
            "low_bitwise": exact(actual.low, expected.low),
            "scales_bitwise": exact(actual.scales, expected.scales),
            "high_dtype": str(actual.high.dtype), "low_dtype": str(actual.low.dtype),
            "scales_dtype": str(actual.scales.dtype)}


def packed_exact(metrics):
    return all(metrics[key] for key in ("high_bitwise", "low_bitwise", "scales_bitwise"))


def selftests(check):
    check("reciprocal_bits", {"bits": hex(f32_bits(RECIPROCAL))},
          f32_bits(RECIPROCAL) == RECIPROCAL_BITS)
    ties = torch.tensor([-2.5, -1.5, -0.5, 0.5, 1.5, 2.5])
    check("nearest_even_known_ties", {"count": 6},
          torch.equal(ties.round().to(torch.int8),
                      torch.tensor([-2, -2, 0, 0, 2, 2], dtype=torch.int8)))
    quotient_count = 0
    for scale in (1.0, f32(0.00317), f32(1e-35)):
        for half in ties.tolist():
            center = torch.tensor(f32(half*scale), dtype=torch.float32)
            for direction in (-math.inf, None, math.inf):
                value = float(center if direction is None else torch.nextafter(
                    center, torch.tensor(direction, dtype=torch.float32)))
                expected = scalar_div_f32(value, scale)
                actual = float(torch.tensor(value)/torch.tensor(scale))
                if f32_bits(actual) != f32_bits(expected):
                    raise AssertionError("CPU tensor division differs from exact rational FP32 oracle")
                quotient_count += 1
    check("scalar_fraction_division_boundary_oracle", {"count": quotient_count}, True)
    state, layout, description = boundary_state()
    packed = pack_value_major(state, layout)
    unpacked = unpack_value_major(packed, layout)
    # Independent scalar quantization at the actual scale, not candidate round().
    correct = True
    for column in range(4):
        for row in range(32):
            scale = float(packed.scales[0, 0, 0, column])
            value = float(state[0, 0, row, 16+column])
            code = min(127, max(-127, round(scalar_div_f32(value, scale))))
            correct &= int(packed.low[0, 0, row, column]) == code
    check("group_boundary_scalar_codes", {"columns": description}, correct)
    check("zero_group", {}, exact(packed.scales[:, :, 1], torch.ones_like(
        packed.scales[:, :, 1])) and bool((packed.low[:, :, 32:64] == 0).all()))
    check("fp16_extrema", {}, bool(torch.isfinite(unpacked).all()) and
          bool((packed.high[..., 0] == 65504).all()))
    for name, invalid in (("nonfinite", torch.full_like(state, math.nan)),
                          ("fp16_overflow", torch.full_like(state, 70000)),
                          ("scale_underflow", torch.full_like(
                              state, torch.finfo(torch.float32).smallest_normal * 2**-23))):
        try:
            pack_value_major(invalid, layout)
        except ValueError as error:
            check("reject_"+name, {"error": str(error)}, True)
        else:
            check("reject_"+name, {}, False)
    metric = errors(torch.full((1, 1, 2), math.inf), torch.ones(1, 1, 2))
    check("nonfinite_metrics_are_json_safe", metric, not metric["finite"] and
          metric["relative_l2"] is None)
    # Construct a readout where repacking changes a non-maximal V row.
    small = identity_layout(1, 32, 32)
    packed0 = pack_value_major(torch.zeros(4, 1, 32, 32), small)
    q = torch.zeros(1, 1, 32); q[..., 20] = 1
    k = q.clone()
    v = torch.zeros(1, 1, 32); v[..., 0] = 0.3; v[..., 1] = 0.25
    ids = torch.tensor([2], dtype=torch.int32)
    packed1, before_output, updated = compressed_step(
        packed0, small, q, k, v, torch.zeros(1, 1),
        torch.full((1, 1), 0.91), ids)
    after_state = unpack_value_major(packed1, small)
    after_output = (after_state[2, 0] @ q[0, 0]) * (32**-0.5)
    expected_before = (updated[2, 0] @ q[0, 0]) * (32**-0.5)
    check("readout_before_pack_not_after", {},
          exact(before_output[0, 0], expected_before) and
          not exact(before_output[0, 0], after_output))
    check("untouched_slots_oracle", {}, all(
        exact(getattr(packed0, field)[[0, 1, 3]], getattr(packed1, field)[[0, 1, 3]])
        for field in ("high", "low", "scales")))
    try:
        compressed_step(packed0, small, q.repeat(2, 1, 1), k.repeat(2, 1, 1),
                        v.repeat(2, 1, 1), torch.zeros(2, 1), torch.ones(2, 1),
                        torch.tensor([2, 2], dtype=torch.int32))
    except ValueError:
        check("duplicate_slots_rejected", {}, True)
    else:
        check("duplicate_slots_rejected", {}, False)
    # Verify independent per-Hv key plans after shared-head expansion.
    generator = torch.Generator().manual_seed(SEED+912)
    layout = random_layout(generator)
    zero = torch.zeros(5, HV, DV, DK)
    packed0 = pack_value_major(transform_state(zero, layout), layout)
    q, k, v, g, beta, ids = make_turn(2, 5, 0, generator)
    _, before_output, updated = compressed_step(
        packed0, layout, q, k, v, g, beta, ids)
    expected_state, expected_output = uncompressed_step(zero, q, k, v, g, beta, ids)
    state_metric = errors(restore_state(updated, layout).index_select(0, ids.long()),
                          expected_state.index_select(0, ids.long()))
    output_metric = errors(before_output, expected_output)
    check("gqa_per_hv_key_gather_covariance",
          {"state": state_metric, "output": output_metric,
           "qk_head_mapping": "h//3; independent Pk per Hv"},
          state_metric["max_head_relative_l2"] <= 1e-5 and
          output_metric["max_head_relative_l2"] <= 1e-5)


def packing_parity(candidate, device, check):
    generator = torch.Generator().manual_seed(SEED)
    fixtures = []
    for dv, dk in ((96, 64), (128, 128)):
        state = torch.randn((2, HV, dv, dk), generator=generator)*0.1
        layout = identity_layout(HV, dv, dk)
        fixtures.append((f"random_{dv}_{dk}", state, layout, {}))
    state, layout, descriptor = boundary_state()
    fixtures.append(("boundary_groups_extremes", state, layout, {"cases": descriptor}))
    for name, state, layout, extra in fixtures:
        expected = pack_value_major(state, layout)
        cp = candidate.pack(state.to(device), candidate_layout(candidate, layout, device))
        actual = key_major_to_value_major(cp)
        metrics = {**packed_metrics(actual, expected), **extra,
                   "adapter": "key-major reference -> value-major; not operator ABI"}
        check(name+"_packing", metrics, packed_exact(metrics),
              {"name": name, "transformed_state": state, "layout": layout_dict(layout),
               "expected": packed_dict(expected), "actual": packed_dict(actual)})
        expected_unpacked = unpack_value_major(expected, layout)
        actual_unpacked = candidate.unpack(cp, candidate_layout(candidate, layout, device))
        check(name+"_unpacking", errors(actual_unpacked, expected_unpacked),
              exact(actual_unpacked, expected_unpacked),
              {"name": name, "expected_unpacked": expected_unpacked,
               "actual_unpacked": actual_unpacked})
    # Non-identity SR/permutation packing is checked against original coordinates.
    layout = random_layout(generator)
    original = torch.randn(2, HV, DV, DK, generator=generator)*0.01
    transformed = transform_state(original, layout)
    expected = pack_value_major(transformed, layout)
    cp = candidate.pack(transformed.to(device), candidate_layout(candidate, layout, device))
    actual = key_major_to_value_major(cp)
    metrics = packed_metrics(actual, expected)
    metrics["original_coordinate_quantization_drift"] = original_coordinate_errors(
        expected, layout, original)
    check("nonidentity_packing", metrics, packed_exact(metrics),
          {"original": original, "transformed": transformed, "layout": layout_dict(layout),
           "actual": packed_dict(actual), "expected": packed_dict(expected)})
    restored = candidate.restore_state(candidate.unpack(cp, candidate_layout(
        candidate, layout, device)), candidate_layout(candidate, layout, device))
    check("nonidentity_restore_oracle", errors(restored, restore_state(
        unpack_value_major(expected, layout), layout)),
        errors(restored, restore_state(unpack_value_major(expected, layout), layout))[
            "max_head_relative_l2"] <= 1e-6)


def make_turn(batch, slots, step, generator):
    q = torch.nn.functional.normalize(torch.randn(batch, HQ, DK, generator=generator),
                                      dim=-1).bfloat16()
    k = torch.nn.functional.normalize(torch.randn(batch, HQ, DK, generator=generator),
                                      dim=-1).bfloat16()
    v = (torch.randn(batch, HV, DV, generator=generator)*0.2).bfloat16()
    g = -(0.002+0.18*torch.rand(batch, HV, generator=generator))
    beta = torch.sigmoid(torch.randn(batch, HV, generator=generator)).bfloat16()
    indices = (torch.arange(batch, dtype=torch.int32)+step) % slots
    return q, k, v, g, beta, indices


def compressed_reference_case(candidate, device, batch, steps, check, report, save):
    """Packed multi-step PyTorch reference parity, NOT the new operator ABI."""
    generator = torch.Generator().manual_seed(SEED+batch)
    slots = batch+3
    layout = random_layout(generator)
    original = torch.randn(slots, HV, DV, DK, generator=generator)*0.005
    expected = pack_value_major(transform_state(original, layout), layout)
    cl = candidate_layout(candidate, layout, device)
    cp = candidate.pack(transform_state(original, layout).to(device), cl)
    dense = original.clone()
    case = {"mode": "packed-pytorch-reference", "batch": batch, "steps": [],
            "status": "running", "key_major_adapter_not_operator": True}
    report["recurrence_cases"].append(case); save()
    try:
        for step in range(steps):
            q, k, v, g, beta, indices = make_turn(batch, slots, step, generator)
            expected_before = expected.clone()
            actual_before = key_major_to_value_major(cp)
            expected, output, _ = compressed_step(expected, layout, q, k, v, g, beta, indices)
            dense, dense_output = uncompressed_step(dense, q, k, v, g, beta, indices)
            unpacked = candidate.unpack(cp, cl)
            i64 = indices.long().to(device)
            qp, kp, vp = candidate.transformed_inputs(
                q.float().repeat_interleave(3, 1).to(device),
                k.float().repeat_interleave(3, 1).to(device), v.to(device), cl)
            updated, out = candidate.gdn_step(unpacked.index_select(0, i64),
                qp, kp, vp, g.to(device), beta.to(device), DK**-0.5)
            actual_output = candidate.restore_output(out, cl).bfloat16()
            # Preserve the actual packed lifecycle: only selected slots repack.
            # Full-arena dequant/requant changes untouched FP32 scales.
            selected_packed = candidate.pack(updated, cl)
            cp.high.index_copy_(0, i64, selected_packed.high)
            cp.codes.index_copy_(0, i64, selected_packed.codes)
            cp.scales.index_copy_(0, i64, selected_packed.scales)
            actual = key_major_to_value_major(cp)
            untouched = [i for i in range(slots) if i not in indices.tolist()]
            untouched_exact = all(exact(getattr(actual, field)[untouched],
                                        getattr(actual_before, field)[untouched])
                                  for field in ("high", "low", "scales"))
            actual_original = restore_state(unpack_value_major(actual, layout), layout)
            expected_original = restore_state(unpack_value_major(expected, layout), layout)
            state_metrics = errors(actual_original.index_select(0, indices.long()),
                                   expected_original.index_select(0, indices.long()))
            output_metrics = errors(actual_output, output.bfloat16())
            data = {"step": step+1, "indices": indices.tolist(),
                    "untouched_regions_bitwise": untouched_exact,
                    "implementation_state": state_metrics,
                    "implementation_output": output_metrics,
                    "quantized_vs_dense_state_diagnostic": original_coordinate_errors(
                        expected, layout, dense, indices),
                    "quantized_vs_dense_output_diagnostic": errors(output.bfloat16(),
                                                                  dense_output.bfloat16())}
            passed = untouched_exact and state_metrics["finite"] and output_metrics["finite"] and (
                state_metrics["max_head_relative_l2"] <= LIMITS[
                    "state_selected_max_head_relative_l2"]) and (
                output_metrics["max_head_relative_l2"] <= LIMITS[
                    "output_max_head_relative_l2"])
            data["passed"] = passed
            case["steps"].append(data); save()
            if not passed:
                retain_failure(report, save, {
                    "batch": batch, "step": step+1, "layout": layout_dict(layout),
                    "q": q, "k": k, "v": v, "g": g, "beta": beta, "indices": indices,
                    "expected_before": packed_dict(expected_before),
                    "actual_before": packed_dict(actual_before),
                    "expected_after": packed_dict(expected), "actual_after": packed_dict(actual),
                    "expected_output": output, "actual_output": actual_output})
                raise AssertionError("packed reference recurrence parity failed")
        case["status"] = "passed"; save()
    except BaseException as error:
        case.update(status="failed", error=repr(error),
                    failed_step=step+1 if "step" in locals() else None)
        try:
            if "q" in locals():
                retain_failure(report, save, {
                    "batch": batch, "step": case["failed_step"],
                    "layout": layout_dict(layout), "q": q, "k": k, "v": v,
                    "g": g, "beta": beta, "indices": indices,
                    "expected_before": packed_dict(expected_before),
                    "actual_before": packed_dict(actual_before),
                    "expected_after": packed_dict(expected)})
            save()
        except BaseException as report_error:
            report["case_failure_save_error"] = repr(report_error)
        raise


def operator_schema_and_meta(check, report):
    decode_schema = torch.ops.qwen36_damp.decode.default._schema
    prepare_schema = torch.ops.qwen36_damp.prepare.default._schema
    report["operator_schemas"] = {"decode": str(decode_schema),
                                  "prepare": str(prepare_schema)}
    writes = [index for index, argument in enumerate(decode_schema.arguments)
              if argument.alias_info is not None and argument.alias_info.is_write]
    no_return_alias = all(return_value.alias_info is None
                          for return_value in decode_schema.returns)
    check("decode_mutable_alias_contract",
          {"mutable_argument_indices": writes, "output_does_not_alias": no_return_alias},
          len(decode_schema.arguments) == 14 and writes == [5, 6, 7] and no_return_alias)
    check("prepare_void_immutable_contract", {},
          len(prepare_schema.arguments) == 6 and len(prepare_schema.returns) == 0 and
          all(argument.alias_info is None or not argument.alias_info.is_write
              for argument in prepare_schema.arguments))
    for batch in (1, 16):
        slots = batch+3
        tensors = [
            torch.empty(batch, HQ, DK, device="meta", dtype=torch.bfloat16),
            torch.empty(batch, HQ, DK, device="meta", dtype=torch.bfloat16),
            torch.empty(batch, HV, DV, device="meta", dtype=torch.bfloat16),
            torch.empty(batch, HV, device="meta", dtype=torch.float32),
            torch.empty(batch, HV, device="meta", dtype=torch.bfloat16),
            torch.empty(slots, HV, DV, 16, device="meta", dtype=torch.float16),
            torch.empty(slots, HV, DV, 112, device="meta", dtype=torch.int8),
            torch.empty(slots, HV, 4, 112, device="meta", dtype=torch.float32),
            torch.empty(HV, DK, device="meta", dtype=torch.int32),
            torch.empty(HV, DV, device="meta", dtype=torch.int32),
            torch.empty(HV, DV, device="meta", dtype=torch.int32),
            torch.empty(HV, DV, device="meta", dtype=torch.float32),
            torch.empty(batch+1, device="meta", dtype=torch.int32),
            torch.empty(batch, device="meta", dtype=torch.int32)]
        prepared = torch.ops.qwen36_damp.prepare(
            tensors[0], tensors[5], tensors[8], tensors[9], tensors[10], tensors[11])
        result = torch.ops.qwen36_damp.decode(*tensors)
        check("operator_meta_batch_"+str(batch), {"shape": list(result.shape),
              "dtype": str(result.dtype), "device": str(result.device)},
              prepared is None and result.device.type == "meta" and
              result.dtype == torch.bfloat16 and result.shape == (batch, HV, DV))
        invalid_pk = torch.empty(HV, DK, device="meta", dtype=torch.int64)
        try:
            torch.ops.qwen36_damp.prepare(
                tensors[0], tensors[5], invalid_pk, tensors[9], tensors[10], tensors[11])
        except RuntimeError as error:
            check("meta_rejects_plan_int64_batch_"+str(batch), {"error": str(error)}, True)
        else:
            check("meta_rejects_plan_int64_batch_"+str(batch), {}, False)


def eager_prepare_and_rejections(device, query, high, pk, pv, inverse_pv, sr,
                                  check):
    """Prepare is eager-only; validate malformed static plans before decode."""
    good = [query, high, pk, pv, inverse_pv, sr]
    before = [x.cpu().clone() for x in good]
    prepared = torch.ops.qwen36_damp.prepare(*good)
    torch.npu.synchronize()
    check("eager_prepare_valid_batch_"+str(query.shape[0]), {},
          prepared is None and all(exact(a, b) for a, b in zip(good, before)))
    malformed = []
    bad = pk.clone(); bad[0, 1] = bad[0, 0]
    malformed.append(("pk_duplicate", 2, bad))
    bad = pk.clone(); bad[0, 0] = DK
    malformed.append(("pk_out_of_range", 2, bad))
    malformed.append(("pk_wrong_dtype", 2, pk.long()))
    malformed.append(("pv_wrong_shape", 3, pv[:, :-1].contiguous()))
    bad = pv.clone(); bad[0, 1] = bad[0, 0]
    malformed.append(("pv_duplicate", 3, bad))
    malformed.append(("inverse_pv_wrong_relation", 4, inverse_pv.roll(1, 1)))
    for label, value in (("sr_zero", 0.0), ("sr_negative", -1.0), ("sr_inf", math.inf),
                         ("sr_nan", math.nan)):
        bad = sr.clone(); bad[0, 0] = value
        malformed.append((label, 5, bad))
    malformed.append(("query_wrong_dtype", 0, query.float()))
    malformed.append(("high_wrong_shape", 1, high[..., :-1].contiguous()))
    for label, index, replacement in malformed:
        bad_args = list(good); bad_args[index] = replacement
        try:
            torch.ops.qwen36_damp.prepare(*bad_args)
        except RuntimeError as error:
            check("prepare_rejects_"+label+"_batch_"+str(query.shape[0]),
                  {"error": str(error)}, True)
        else:
            check("prepare_rejects_"+label+"_batch_"+str(query.shape[0]), {}, False)
    # Restore valid tiling/plans explicitly after negative prepare calls.
    torch.ops.qwen36_damp.prepare(*good)
    torch.npu.synchronize()
    check("prepare_negative_cases_do_not_mutate_inputs_batch_"+str(query.shape[0]), {},
          all(exact(a, b) for a, b in zip(good, before)))


def invalid_dynamic_metadata(device, query, high, low, scales, pk, pv, inverse_pv,
                             sr, check):
    """Unsupported metadata must reject atomically in kernel, not partly update."""
    batch, slots = query.shape[0], high.shape[0]
    key = query.clone()
    value = torch.zeros(batch, HV, DV, dtype=torch.bfloat16, device=device)
    log_decay = torch.zeros(batch, HV, dtype=torch.float32, device=device)
    beta = torch.zeros(batch, HV, dtype=torch.bfloat16, device=device)
    lengths = torch.cat((torch.zeros(1, dtype=torch.int32),
                         torch.ones(batch, dtype=torch.int32)))
    indices = torch.arange(batch, dtype=torch.int32)
    invalid = []
    for label, replacement in (("zero_length", 0), ("multi_token_length", 2)):
        bad = lengths.clone(); bad[-1] = replacement
        invalid.append((label, bad, indices.clone()))
    for label, replacement in (("negative_slot", -1), ("out_of_range_slot", slots)):
        bad = indices.clone(); bad[-1] = replacement
        invalid.append((label, lengths.clone(), bad))
    if batch > 1:
        bad = indices.clone(); bad[1] = bad[0]
        invalid.append(("duplicate_slots", lengths.clone(), bad))
    before = [x.cpu().clone() for x in (high, low, scales)]
    for label, cpu_lengths, cpu_indices in invalid:
        device_lengths, device_indices = cpu_lengths.to(device), cpu_indices.to(device)
        output = torch.ops.qwen36_damp.decode(
            query, key, value, log_decay, beta, high, low, scales, pk, pv,
            inverse_pv, sr, device_lengths, device_indices)
        torch.npu.synchronize()
        guards = {"all_output_nan": bool(torch.isnan(output.cpu()).all()),
                  "every_state_region_bitwise_unchanged": all(exact(x, y)
                      for x, y in zip((high, low, scales), before)),
                  "metadata_inputs_unchanged": exact(device_lengths, cpu_lengths) and
                      exact(device_indices, cpu_indices)}
        check("reject_dynamic_"+label+"_batch_"+str(batch), guards, all(guards.values()))


def operator_case(device, batch, steps, check, report, save):
    generator = torch.Generator().manual_seed(SEED+batch)
    slots, layout = batch+3, random_layout(generator)
    original = torch.randn(slots, HV, DV, DK, generator=generator)*0.005
    expected = pack_value_major(transform_state(original, layout), layout)
    dense = original.clone()
    high, low, scales = [x.to(device) for x in
                         (expected.high, expected.low, expected.scales)]
    pk, pv, inverse_pv = [x.to(dtype=torch.int32, device=device).contiguous()
                         for x in (layout.pk, layout.pv, layout.pv.argsort(1))]
    sr = layout.c.to(device).contiguous()
    lengths = torch.cat((torch.zeros(1, dtype=torch.int32),
                         torch.ones(batch, dtype=torch.int32))).to(device)
    immutable = [pk, pv, inverse_pv, sr, lengths]
    immutable_cpu = [x.cpu().clone() for x in immutable]
    pointers = [x.data_ptr() for x in (high, low, scales)]
    # The explicit prepare operation is outside capture and first decode.
    # It validates INT32 logical plans and positive finite original-coordinate SR.
    prepare_query = torch.zeros((batch, HQ, DK), dtype=torch.bfloat16, device=device)
    eager_prepare_and_rejections(device, prepare_query, high, pk, pv, inverse_pv,
                                 sr, check)
    invalid_dynamic_metadata(device, prepare_query, high, low, scales, pk, pv,
                             inverse_pv, sr, check)
    decode = torch.ops.qwen36_damp.decode
    case = {"mode": "value-major-custom-operator", "batch": batch,
            "steps": [], "status": "running", "abi": ABI}
    report["recurrence_cases"].append(case); save()
    try:
        for step in range(steps):
            q, k, v, g, beta, indices = make_turn(batch, slots, step, generator)
            untouched = [i for i in range(slots) if i not in indices.tolist()]
            expected_before = expected.clone()
            actual_before = ValueMajorPacked(high.cpu().clone(), low.cpu().clone(), scales.cpu().clone())
            before = [x[untouched].cpu().clone() for x in (high, low, scales)]
            expected, output, _ = compressed_step(expected, layout, q, k, v, g, beta, indices)
            dense, dense_output = uncompressed_step(dense, q, k, v, g, beta, indices)
            inputs = [x.to(device).contiguous() for x in (q, k, v, g, beta)]
            input_cpu = [x.cpu().clone() for x in inputs]
            device_indices = indices.to(device)
            output_actual = decode(*inputs, high, low, scales, pk, pv, inverse_pv,
                                   sr, lengths, device_indices)
            torch.npu.synchronize()
            if not isinstance(output_actual, torch.Tensor):
                raise TypeError("decode must return one output Tensor")
            if output_actual.shape != (batch, HV, DV) or output_actual.dtype != torch.bfloat16:
                raise TypeError("decode output must be BF16[B,12,128]")
            actual = ValueMajorPacked(high.cpu(), low.cpu(), scales.cpu())
            state_metrics = errors(restore_state(unpack_value_major(actual, layout), layout
                ).index_select(0, indices.long()), restore_state(unpack_value_major(
                    expected, layout), layout).index_select(0, indices.long()))
            output_metrics = errors(output_actual, output.bfloat16())
            guards = {
                "untouched_regions_bitwise": all(exact(x[untouched], y)
                    for x, y in zip((high, low, scales), before)),
                "storage_pointers_stable": pointers == [x.data_ptr() for x in (high, low, scales)],
                "static_inputs_unchanged": all(exact(x, y)
                    for x, y in zip(immutable, immutable_cpu)),
                "turn_inputs_unchanged": all(exact(x, y)
                    for x, y in zip(inputs, input_cpu)),
                "indices_unchanged": exact(device_indices, indices),
            }
            passed = all(guards.values()) and state_metrics["finite"] and output_metrics[
                "finite"] and state_metrics["max_head_relative_l2"] <= LIMITS[
                    "state_selected_max_head_relative_l2"] and output_metrics[
                    "max_head_relative_l2"] <= LIMITS["output_max_head_relative_l2"]
            case["steps"].append({
                "step": step+1, "indices": indices.tolist(), "passed": passed,
                "implementation_state": state_metrics, "implementation_output": output_metrics,
                "guards": guards,
                "quantized_vs_dense_state_diagnostic": original_coordinate_errors(
                    expected, layout, dense, indices),
                "quantized_vs_dense_output_diagnostic": errors(output.bfloat16(),
                                                               dense_output.bfloat16())})
            save()
            if not passed:
                retain_failure(report, save, {
                    "batch": batch, "step": step+1, "layout": layout_dict(layout),
                    "q": q, "k": k, "v": v, "g": g, "beta": beta, "indices": indices,
                    "expected_before": packed_dict(expected_before),
                    "actual_before": packed_dict(actual_before),
                    "expected_after": packed_dict(expected), "actual_after": packed_dict(actual),
                    "expected_output": output, "actual_output": output_actual,
                    "pk": pk, "pv": pv, "inverse_pv": inverse_pv, "sr": sr,
                    "actual_seq_lengths": lengths})
                raise AssertionError("custom packed recurrence parity/slot guard failed")
        case["status"] = "passed"; save()
    except BaseException as error:
        case.update(status="failed", error=repr(error),
                    failed_step=step+1 if "step" in locals() else None)
        try:
            if "q" in locals():
                retain_failure(report, save, {
                    "batch": batch, "step": case["failed_step"],
                    "layout": layout_dict(layout), "q": q, "k": k, "v": v,
                    "g": g, "beta": beta, "indices": indices,
                    "expected_before": packed_dict(expected_before),
                    "actual_before": packed_dict(actual_before),
                    "actual_after": {"high": high, "low": low, "scales": scales}})
            save()
        except BaseException as report_error:
            report["case_failure_save_error"] = repr(report_error)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("cpu", "npu-reference", "npu-operator"), required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--operator-library", type=Path)
    parser.add_argument("--device-proof", type=Path,
                        help="parent-captured fresh device/container manifest; retained by hash")
    parser.add_argument("--steps", type=int, default=STEPS,
                        help="smaller runs are smoke only, not the 160-step matrix")
    args = parser.parse_args()
    out = args.output_dir.resolve()
    if out.exists() or out == REPO or REPO in out.parents:
        parser.error("require NEW output directory outside repository")
    if args.steps < 1 or args.steps > STEPS:
        parser.error("steps must be in [1,160]")
    is_npu = args.mode.startswith("npu")
    if is_npu and os.environ.get("ASCEND_RT_VISIBLE_DEVICES") != "0":
        parser.error("NPU gate requires externally proven physical4 -> logical0 and visible=0")
    if is_npu and (args.device_proof is None or not args.device_proof.is_file()):
        parser.error("NPU gate requires a fresh external --device-proof manifest")
    if args.mode == "npu-operator" and (args.operator_library is None or not
                                       args.operator_library.is_file()):
        parser.error("npu-operator requires explicit existing --operator-library")
    out.mkdir(parents=True)
    report = {"schema": "damp-independent-packed-oracle/v1", "status": "running",
              "artifact_root": str(out),
              "created_ns": time.time_ns(), "mode": args.mode, "steps": args.steps,
              "matrix_class": "complete-160-step" if args.steps == STEPS else "smoke-only",
              "abi": ABI, "limits": LIMITS,
              "arithmetic": {"scale_reciprocal_fp32_bits": hex(RECIPROCAL_BITS),
                             "zero_group_scale": 1.0,
                             "code": "RNE32(x/scale), nearest-even integer, clamp[-127,127]"},
              "checks": [], "recurrence_cases": [],
              "script_sha256": sha(__file__),
              "oracle_sha256": sha(HERE/"independent_oracle.py"),
              "candidate_reference_sha256": sha(PROJECT/"reference.py"),
              "versions": {"torch": torch.__version__},
              "evidence_scope": "CPU/NPU numerical oracle and packed recurrence only; "
                  "NOT calibrated model, batchmix, graph, service, performance or task accuracy"}
    def save():
        # Sanitization cannot throw a secondary NaN/Inf JSON exception.
        (out/"report.json").write_text(
            json.dumps(safe_json(report), indent=2, allow_nan=False)+"\n")
    def check(name, data, passed, fixture=None):
        report["checks"].append({"name": name, "passed": bool(passed), **data})
        save()
        if not passed:
            if fixture is not None:
                retain_failure(report, save, fixture)
            raise AssertionError(name)
    save()
    try:
        torch.set_num_threads(1)
        selftests(check)
        device = "cpu"
        if is_npu:
            import torch_npu
            torch_npu.npu.set_compile_mode(jit_compile=False)
            torch.npu.set_device(0)
            device = "npu:0"
            report["versions"]["torch_npu"] = torch_npu.__version__
            report["external_device_proof"] = {"path": str(args.device_proof),
                                              "sha256": sha(args.device_proof)}
            report["physical_binding_authority"] = "fresh external parent launcher manifest; "
            report["physical_binding_authority"] += "file presence alone is not mapping proof"
        candidate = load_candidate()
        packing_parity(candidate, device, check)
        if args.operator_library is not None:
            report["operator_library"] = {"path": str(args.operator_library.resolve()),
                                          "sha256": sha(args.operator_library)}
            torch.ops.load_library(str(args.operator_library.resolve()))
            operator_schema_and_meta(check, report)
        if args.mode == "npu-operator":
            for batch in (1, 16):
                operator_case(device, batch, args.steps, check, report, save)
        else:
            for batch in (1, 16):
                compressed_reference_case(candidate, device, batch, args.steps,
                                          check, report, save)
        report["status"] = "numerical_pass"
    except BaseException as error:
        report.update(status="failed", error_type=type(error).__name__, error=repr(error),
                      traceback=traceback.format_exc())
        report["completed_ns"] = time.time_ns()
        try:
            save()
        except BaseException as save_error:
            # Keep original failure as process exception; print bounded fallback JSON.
            print(json.dumps(safe_json({"original_error": repr(error),
                                       "report_save_error": repr(save_error)})), file=sys.stderr)
        raise
    report["completed_ns"] = time.time_ns()
    save()
    print(json.dumps({"status": report["status"], "report": str(out/"report.json")}))


if __name__ == "__main__":
    main()
