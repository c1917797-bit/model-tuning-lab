#!/usr/bin/env python3
"""CPU-only attribution of an immutable real-NPU restricted-golden failure.

No candidate/native library load, no torch_npu import, no recurrence rerun,
no threshold changes, no feedback resynchronization. CPU reduction variants
are hypotheses, NOT the actual 910B WholeReduceSum/Exp execution contract.
"""
import argparse
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from independent_oracle import (OracleLayout, ValueMajorPacked, RECIPROCAL,
    errors, f32_bits, pack_value_major, restore_state, scalar_div_f32,
    scalar_scale_f32, unpack_value_major)

FIELD_NAMES = ("high", "low", "scales")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite_json(x):
    if isinstance(x, dict): return {str(k): finite_json(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [finite_json(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x): return {"nonfinite": repr(x)}
    return x


def exact(a, b):
    a, b = a.detach().cpu().contiguous(), b.detach().cpu().contiguous()
    return a.shape == b.shape and a.dtype == b.dtype and torch.equal(
        a.view(torch.uint8), b.view(torch.uint8))


def packed(d):
    if set(d) != set(FIELD_NAMES): raise ValueError("unexpected packed fields")
    return ValueMajorPacked(*(d[n] for n in FIELD_NAMES))


def subset(p, ids):
    return ValueMajorPacked(*(getattr(p, n).index_select(0, ids) for n in FIELD_NAMES))


def summary(a, e):
    result = {}
    for n in FIELD_NAMES:
        x, y = getattr(a, n), getattr(e, n)
        if x.shape != y.shape or x.dtype != y.dtype: raise ValueError("packed ABI differs")
        result[n] = {"bitwise": exact(x, y),
                     "numeric_differences": int((x != y).sum()),
                     "max_absolute": float((x.double()-y.double()).abs().max())}
        if n == "scales":
            result[n]["max_positive_scale_ulp"] = int((
                x.contiguous().view(torch.int32).long() -
                y.contiguous().view(torch.int32).long()).abs().max())
    return result


def inventory(x):
    if isinstance(x, torch.Tensor):
        return {"shape": list(x.shape), "dtype": str(x.dtype), "device": str(x.device),
                "finite": bool(torch.isfinite(x.float()).all())}
    if isinstance(x, dict): return {k: inventory(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [inventory(v) for v in x]
    return x


def rounded_code(x, scale):
    return max(-127, min(127, round(scalar_div_f32(x, scale))))


def division_details(x, scale):
    x, scale = float(x), float(scale)
    rational = Fraction.from_float(x)/Fraction.from_float(scale)
    ieee = scalar_div_f32(x, scale)
    cpu = float((torch.tensor(x, dtype=torch.float32) /
                 torch.tensor(scale, dtype=torch.float32)).item())
    reciprocal_quotient = float((torch.tensor(x, dtype=torch.float32) *
        (torch.tensor(1.0, dtype=torch.float32)/torch.tensor(scale, dtype=torch.float32))).item())
    half = math.floor(float(rational))+0.5
    margin = rational-Fraction.from_float(half)
    f = torch.tensor(ieee, dtype=torch.float32)
    q_ulp = abs(float(torch.nextafter(f, torch.tensor(float("inf"))).item())-ieee)
    return {"x": x, "x_bits": hex(f32_bits(x)), "scale": scale,
        "scale_bits": hex(f32_bits(scale)), "exact_rational_quotient": str(rational),
        "ieee_rne_fp32_quotient": ieee, "ieee_quotient_bits": hex(f32_bits(ieee)),
        "cpu_tensor_div_quotient": cpu, "cpu_quotient_bits": hex(f32_bits(cpu)),
        "reciprocal_multiply_quotient": reciprocal_quotient,
        "reciprocal_quotient_bits": hex(f32_bits(reciprocal_quotient)),
        "ieee_code": rounded_code(x, scale), "cpu_tensor_code": round(cpu),
        "reciprocal_multiply_code": round(reciprocal_quotient),
        "nearest_half": half, "exact_rational_minus_half": str(margin),
        "exact_rational_minus_half_float": float(margin),
        "rounded_fp32_minus_half": ieee-half, "quotient_ulp_at_ieee": q_ulp,
        "exact_margin_in_quotient_ulp": float(margin)/q_ulp if q_ulp else None,
        "fp32_half_tie": ieee == half, "half_tie_even_code": round(half)}


def minimal_x_ulp_for_code(x, scale, target, budget=64):
    # Conditional sensitivity only: candidate FP32 x was not saved.
    current = torch.tensor(float(x), dtype=torch.float32)
    if rounded_code(float(current), scale) == target:
        return {"ulp_steps": 0, "x": float(current),
                "x_bits": hex(f32_bits(float(current))), "x_delta": 0.0}
    direction = float("inf") if target > rounded_code(float(current), scale) else float("-inf")
    destination = torch.tensor(direction, dtype=torch.float32)
    for distance in range(1, budget+1):
        current = torch.nextafter(current, destination)
        value = float(current)
        if rounded_code(value, scale) == target:
            return {"ulp_steps": distance, "x": value,
                    "x_bits": hex(f32_bits(value)), "x_delta": value-float(x)}
    return {"not_found_within": budget, "direction": repr(direction)}


def reduce_products(products, mode):
    if mode == "torch_sum128":
        return products.sum(-1)
    folded = products[..., :64]+products[..., 64:]
    if mode == "fold64_torch_sum":
        return folded.sum(-1)
    if mode == "fold64_sequential":
        value = folded[..., 0].clone()
        for i in range(1, 64): value = value+folded[..., i]
        return value
    if mode == "fold64_balanced_adjacent":
        value = folded
        while value.shape[-1] > 1:
            value = value[..., 0::2]+value[..., 1::2]
        return value[..., 0]
    raise ValueError(mode)


def arithmetic_variant(before_selected, layout, q, k, v, g, beta, mode, update_mode, exp_mode):
    b = q.shape[0]
    pk = layout.pk.long()[None].expand(b, -1, -1)
    pv = layout.pv.long()[None].expand(b, -1, -1)
    qh = q.float().repeat_interleave(3, 1).gather(2, pk)
    kh = k.float().repeat_interleave(3, 1).gather(2, pk)
    vh = (v.float()/layout.c[None]).gather(2, pv)
    decay = g.exp() if exp_mode == "cpu_exp_f32" else g.double().exp().float()
    decayed = before_selected*decay[..., None, None]
    if mode == "torch_mv128":
        dot = torch.empty(b, 12, 128)
        for row in range(b):
            for head in range(12): dot[row, head] = torch.mv(decayed[row, head], kh[row, head])
    else:
        dot = reduce_products(decayed*kh[..., None, :], mode)
    residual = (vh-dot)*beta.float()[..., None]
    outer = residual[..., None]*kh[..., None, :]
    if update_mode == "separate_mul_add":
        updated = decayed+outer
    elif update_mode == "fp64_mul_add_round_f32":
        # Diagnostic FMA approximation; no claim that CPU double establishes
        # the hardware instruction's internal rounding for every input.
        updated = (decayed.double()+residual.double()[..., None] *
                   kh.double()[..., None, :]).float()
    else:
        raise ValueError(update_mode)
    qs = qh*torch.tensor(128**-0.5, dtype=torch.float32)
    if mode == "torch_mv128":
        readout = torch.empty(b, 12, 128)
        for row in range(b):
            for head in range(12): readout[row, head] = torch.mv(updated[row, head], qs[row, head])
    else:
        readout = reduce_products(updated*qs[..., None, :], mode)
    output = (readout.gather(2, pv.argsort(-1))*layout.c[None]).bfloat16()
    return updated, output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--fixture-sha256", required=True)
    parser.add_argument("--source-report", type=Path, required=True)
    parser.add_argument("--source-report-sha256", required=True)
    parser.add_argument("--oracle-sha256", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-boundaries", type=int, default=64)
    args = parser.parse_args()
    out = args.output_dir.resolve()
    repo = HERE.parents[2]
    if out.exists() or out == repo or repo in out.parents:
        parser.error("require NEW output root outside repository")
    if not 1 <= args.max_boundaries <= 256: parser.error("max-boundaries must be 1..256")
    for path, expected in ((args.fixture, args.fixture_sha256),
        (args.source_report, args.source_report_sha256), (HERE/"independent_oracle.py", args.oracle_sha256)):
        if not path.is_file() or sha(path) != expected:
            parser.error("frozen input identity mismatch: "+str(path))
    out.mkdir(parents=True)
    result = {"schema": "damp-restricted-native-failure-cpu-diagnostic/v1",
        "status": "running", "created_ns": time.time_ns(),
        "fixture_sha256": args.fixture_sha256,
        "source_report_sha256": args.source_report_sha256,
        "oracle_sha256": args.oracle_sha256, "script_sha256": sha(__file__),
        "scope": "CPU-only attribution of saved real-NPU fixture; no gate relaxation, "
                 "no NPU execution, no generalSR/graph/service/performance/quality claim",
        "missing_evidence": ["candidate updated FP32 before packing",
                             "candidate Div quotient before CAST_RINT"]}
    def save():
        (out/"report.json").write_text(json.dumps(finite_json(result), indent=2, allow_nan=False)+"\n")
    save()
    try:
        torch.set_num_threads(1)
        f = torch.load(args.fixture, map_location="cpu", weights_only=True)
        source_report = json.loads(args.source_report.read_text())
        if source_report.get("schema") != "damp-restricted-native-compressed-golden/v1":
            raise ValueError("unexpected source gate schema")
        if source_report.get("first_failure_fixture", {}).get("sha256") != args.fixture_sha256:
            raise ValueError("source report does not bind this failure fixture")
        if source_report.get("source_hashes", {}).get("independent_oracle.py") != args.oracle_sha256:
            raise ValueError("oracle differs from failing experiment")
        if f.get("stage") != "closed_loop": raise ValueError("fixture is not a recurrence failure")
        result["source_gate_status"] = source_report["status"]
        result["source_operator_library"] = source_report.get("operator_library")
        result["source_native_provenance"] = source_report.get("native_source_manifest")
        result["fixture_inventory"] = inventory(f)
        result["fixture_step"] = f["step"]
        result["batch"] = f["batch"]
        result["variant"] = f["variant"]
        ld = f["layout"]
        layout = OracleLayout(ld["c"], ld["pv"], ld["pk"], ld["khi"], ld["group"])
        gb, ab = packed(f["golden_before"]), packed(f["actual_before"])
        ga, aa = packed(f["golden_after"]), packed(f["actual_after"])
        ids = f["indices"].long()
        untouched = torch.tensor([s for s in range(gb.high.shape[0]) if s not in ids.tolist()], dtype=torch.long)
        result["indices"] = ids.tolist()
        result["same_before_all_slots"] = summary(ab, gb)
        result["same_before_selected"] = summary(subset(ab, ids), subset(gb, ids))
        result["golden_untouched"] = summary(subset(ga, untouched), subset(gb, untouched))
        result["candidate_untouched"] = summary(subset(aa, untouched), subset(ab, untouched))
        result["selected_after"] = summary(subset(aa, ids), subset(ga, ids))
        result["saved_output"] = errors(f["actual_output"], f["native_evidence"]["original_output_bf16"])
        result["saved_state_original_coordinates"] = errors(
            restore_state(unpack_value_major(aa, layout), layout).index_select(0, ids),
            restore_state(unpack_value_major(ga, layout), layout).index_select(0, ids))
        native_update = f["native_evidence"]["native_updated_selected_fp32"]
        if native_update.shape != (len(ids), 12, 128, 128) or native_update.dtype != torch.float32:
            raise ValueError("native updated FP32 evidence ABI mismatch")
        selected_repack = pack_value_major(native_update, layout)
        replay = gb.clone()
        for n in FIELD_NAMES: getattr(replay, n).index_copy_(0, ids, getattr(selected_repack, n))
        result["native_updated_independent_repack_vs_saved_golden_after"] = summary(replay, ga)
        result["fixed_native_updated_pack_vs_candidate_after"] = summary(subset(aa, ids), selected_repack)
        result["native_update_is_finite"] = bool(torch.isfinite(native_update).all())
        code_mask = subset(aa, ids).low != subset(ga, ids).low
        differences = code_mask.nonzero(as_tuple=False)
        result["low_code_differences"] = {"total": len(differences),
            "reported_limit": args.max_boundaries, "truncated": len(differences) > args.max_boundaries}
        boundaries = []
        for row, head, value, low_key in differences[:args.max_boundaries].tolist():
            slot, key = int(ids[row]), low_key+layout.khi
            group = value//layout.group
            x = float(native_update[row, head, value, key])
            sg = float(ga.scales[slot, head, group, low_key])
            sa = float(aa.scales[slot, head, group, low_key])
            maximum = float(native_update[row, head, group*32:(group+1)*32, key].abs().max())
            scale_expected = 1.0 if maximum == 0 else scalar_scale_f32(maximum)
            cg, ca = int(ga.low[slot, head, value, low_key]), int(aa.low[slot, head, value, low_key])
            entry = {"index_selected_head_value_lowkey": [row, head, value, low_key],
                "slot": slot, "group": group, "full_key": key,
                "original_value_index": int(layout.pv[head, value]),
                "original_key_index": int(layout.pk[head, key]),
                "golden_code": cg, "candidate_code": ca,
                "group_maximum_native_update": maximum,
                "group_maximum_bits": hex(f32_bits(maximum)),
                "scalar_rne_scale": scale_expected,
                "scalar_rne_scale_bits": hex(f32_bits(scale_expected)),
                "golden_scale_matches_scalar_rne": f32_bits(sg) == f32_bits(scale_expected),
                "candidate_scale_equal_golden_bits": f32_bits(sa) == f32_bits(sg),
                "fixed_native_update_division": division_details(x, sg),
                "conditional_minimum_native_x_ulp_to_candidate_code":
                    minimal_x_ulp_for_code(x, sg, ca)}
            col = ga.low[slot, head, group*32:(group+1)*32, low_key]
            col_a = aa.low[slot, head, group*32:(group+1)*32, low_key]
            entry["same_group_column_code_differences"] = int((col != col_a).sum())
            entry["native_x_neighbor_codes"] = [
                {"direction": direction, "x": float(torch.nextafter(
                    torch.tensor(x), torch.tensor(destination))),
                 "code": rounded_code(float(torch.nextafter(torch.tensor(x), torch.tensor(destination))), sg)}
                for direction, destination in (("minus1ulp", float("-inf")), ("plus1ulp", float("inf")))]
            boundaries.append(entry)
        result["boundary_details"] = boundaries
        result["source_native_arithmetic_cpu_hypotheses"] = []
        selected_before = unpack_value_major(gb, layout).index_select(0, ids)
        modes = ("torch_mv128", "torch_sum128", "fold64_torch_sum",
                 "fold64_balanced_adjacent", "fold64_sequential")
        for exp_mode in ("cpu_exp_f32", "cpu_exp_fp64_rounded"):
            for mode in modes:
                for update_mode in ("separate_mul_add", "fp64_mul_add_round_f32"):
                    updated, output = arithmetic_variant(selected_before, layout,
                        *[f[n] for n in ("q", "k", "v", "g", "beta")],
                        mode, update_mode, exp_mode)
                    candidate_pack = pack_value_major(updated, layout)
                    result["source_native_arithmetic_cpu_hypotheses"].append({
                        "reduction": mode, "outer_update": update_mode, "decay": exp_mode,
                        "arithmetic_contract": "CPU sensitivity model, not actual 910B execution",
                        "updated_fp32_vs_saved_native": errors(updated, native_update),
                        "packed_vs_saved_golden": summary(candidate_pack, subset(ga, ids)),
                        "packed_vs_saved_candidate": summary(candidate_pack, subset(aa, ids)),
                        "bf16_output_vs_saved_native": errors(output, f["native_evidence"]["original_output_bf16"])})
        result["attribution_constraints"] = [
            "Exact before excludes feedback/untouched-slot drift at this step if checks confirm it.",
            "Repacking saved native update validates oracle lifecycle independently of candidate.",
            "Equal FP16 payload/scales does not prove all candidate updated FP32 elements equal.",
            "CPU quotient/tie or ULP sensitivity can locate a boundary but cannot identify actual NPU Div.",
            "No candidate prepack/quotient evidence was retained: update-vs-pack attribution stays unresolved.",
            "CPU fold/tree/FMA/Exp variants are diagnostic hypotheses, never acceptance or source-execution proof."]
        result["status"] = "diagnostic_complete"
    except BaseException as error:
        result.update(status="failed", error=repr(error), error_type=type(error).__name__,
                      traceback=traceback.format_exc())
        try: save()
        except BaseException as secondary: print("secondary save failure: "+repr(secondary), file=sys.stderr)
        raise
    finally:
        result["completed_ns"] = time.time_ns()
        try: save()
        except BaseException as secondary: print("secondary final save failure: "+repr(secondary), file=sys.stderr)
    print(json.dumps({"status": result["status"], "report": str(out/"report.json")}))


if __name__ == "__main__":
    main()
