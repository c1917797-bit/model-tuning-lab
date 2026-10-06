#!/usr/bin/env python3
"""One-shot CPU diagnosis of an immutable packed-recurrence failure fixture.

This does not relax gates, rerun the original experiment, or execute NPU.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import time
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from independent_oracle import (
    OracleLayout, ValueMajorPacked, compressed_step, errors, f32_bits,
    pack_value_major, restore_state, unpack_value_major)


def exact(a, b):
    return (a.shape == b.shape and a.dtype == b.dtype and
            torch.equal(a.contiguous().view(torch.uint8),
                        b.contiguous().view(torch.uint8)))


def packed(d):
    return ValueMajorPacked(d["high"], d["low"], d["scales"])


def summary(actual, expected):
    result = {}
    for field in ("high", "low", "scales"):
        a, e = getattr(actual, field), getattr(expected, field)
        mask = a != e
        result[field] = {
            "bitwise": exact(a, e),
            "numeric_differences": int(mask.sum()),
            "max_absolute": float((a.double()-e.double()).abs().max()),
        }
        if field == "scales":
            result[field]["max_ulp_positive_scales"] = int((
                a.contiguous().view(torch.int32).long()-
                e.contiguous().view(torch.int32).long()).abs().max())
    return result


def subset(p, ids):
    return ValueMajorPacked(*(getattr(p, name).index_select(0, ids)
                              for name in ("high", "low", "scales")))


def same_before_sum_step(before, layout, q, k, v, g, beta, ids, pack_all):
    state = unpack_value_major(before, layout)
    updated = state.clone()
    batch, hq, dk = q.shape
    hv, dv = state.shape[1:3]
    ratio = hv//hq
    outputs = torch.empty(batch, hv, dv, dtype=torch.float32)
    for row, slot in enumerate(ids.tolist()):
        for head in range(hv):
            pv, pk = layout.pv[head].long(), layout.pk[head].long()
            qh = q[row, head//ratio].float().index_select(0, pk)
            kh = k[row, head//ratio].float().index_select(0, pk)
            vh = (v[row, head].float()/layout.c[head]).index_select(0, pv)
            decayed = state[slot, head] * g[row, head].float().exp()
            residual = vh - (decayed*kh[None, :]).sum(-1)
            current = decayed + (beta[row, head].float()*residual)[:, None]*kh[None, :]
            updated[slot, head] = current
            output = (current*qh[None, :]).sum(-1)*(dk**-0.5)
            outputs[row, head] = (output*layout.c[head].index_select(
                0, pv)).index_select(0, pv.argsort())
    if pack_all:
        result = pack_value_major(updated, layout)
    else:
        selected = pack_value_major(updated.index_select(0, ids), layout)
        result = before.clone()
        for name in ("high", "low", "scales"):
            getattr(result, name).index_copy_(0, ids, getattr(selected, name))
    return result, outputs, updated


def batched_candidate_replay(before, layout, q, k, v, g, beta, ids, candidate):
    """Exact provider replay, explicitly NOT an independent mathematical oracle."""
    cp = candidate.Packed(before.high.transpose(-1, -2).contiguous(),
                          before.low.transpose(-1, -2).contiguous(),
                          before.scales.transpose(-1, -2).contiguous())
    cl = candidate.Layout(layout.c, layout.pv, layout.pk, layout.khi, layout.group)
    state = candidate.unpack(cp, cl)
    qe, ke = q.float().repeat_interleave(3, 1), k.float().repeat_interleave(3, 1)
    qp, kp, vp = candidate.transformed_inputs(qe, ke, v, cl)
    selected = state.index_select(0, ids)
    updated, output = candidate.gdn_step(selected, qp, kp, vp, g, beta, 128**-0.5)
    selected_packed = candidate.pack(updated, cl)
    for name in ("high", "codes", "scales"):
        getattr(cp, name).index_copy_(0, ids, getattr(selected_packed, name))
    result = ValueMajorPacked(cp.high.transpose(-1, -2).contiguous(),
                             cp.codes.transpose(-1, -2).contiguous(),
                             cp.scales.transpose(-1, -2).contiguous())
    full_updated = state.clone(); full_updated.index_copy_(0, ids, updated)
    output_original = candidate.restore_output(output, cl).bfloat16()
    return result, output_original, full_updated, (selected, qp, kp, vp)


def reduction_stages(before_selected, qp, kp, vp, g, beta):
    """Compare reducer alone on identical FP32 operands; report exp separately."""
    decay_batched = g.float().exp()
    decay_scalar = torch.empty_like(decay_batched)
    for row in range(g.shape[0]):
        for head in range(g.shape[1]):
            decay_scalar[row, head] = g[row, head].float().exp()
    decayed = before_selected.float()*decay_batched[..., None, None]
    sum_dot = (decayed*kp[..., None, :]).sum(-1)
    mv_dot = torch.empty_like(sum_dot)
    for row in range(g.shape[0]):
        for head in range(g.shape[1]):
            mv_dot[row, head] = torch.mv(decayed[row, head], kp[row, head])
    dot_fp64 = (decayed.double()*kp.double()[..., None, :]).sum(-1)
    residual_sum = vp-sum_dot
    residual_mv = vp-mv_dot
    updated_sum = decayed + (beta.float()[..., None]*residual_sum)[..., None]*kp[..., None, :]
    updated_mv = decayed + (beta.float()[..., None]*residual_mv)[..., None]*kp[..., None, :]
    # Do not cast FP64 mathematical diagnostic down to FP32 before measuring.
    def full_precision_metrics(a, e):
        a, e = a.double(), e.double()
        d = a-e
        return {"relative_l2": math.sqrt(float(d.square().sum())/
                      max(float(e.square().sum()), 1e-30)),
                "max_absolute": float(d.abs().max()),
                "numeric_differences": int((a != e).sum())}
    return {
        "exp_batched_vs_scalar": {"bitwise": exact(decay_batched, decay_scalar),
            **full_precision_metrics(decay_batched, decay_scalar)},
        "same_decayed_operand_sum_vs_mv_dot": full_precision_metrics(sum_dot, mv_dot),
        "sum_dot_vs_fp64_diagnostic": full_precision_metrics(sum_dot, dot_fp64),
        "mv_dot_vs_fp64_diagnostic": full_precision_metrics(mv_dot, dot_fp64),
        "sum_vs_mv_residual": full_precision_metrics(residual_sum, residual_mv),
        "sum_vs_mv_updated_before_pack": errors(updated_sum, updated_mv),
        "reduction_contract_note": "torch.mv may use fused accumulation; "
            "torch elementwise multiply then sum is a different FP32 operation order. "
            "Neither is evidence of the unbuilt Ascend kernel."
    }


def boundary_details(mv_updated, sum_updated, mv_packed, sum_packed, layout, ids):
    changed = (mv_packed.low != sum_packed.low).nonzero()
    details = []
    id_set = set(ids.tolist())
    for slot, head, value_row, low_key in changed.tolist():
        if slot not in id_set or len(details) >= 32:
            continue
        group = value_row//layout.group
        key = low_key+layout.khi
        data = {"slot": slot, "head": head, "reordered_value": value_row,
                "original_value": int(layout.pv[head, value_row]),
                "reordered_key": key, "original_key": int(layout.pk[head, key]),
                "group": group}
        for label, updated, p in (("mv", mv_updated, mv_packed),
                                   ("sum", sum_updated, sum_packed)):
            value = float(updated[slot, head, value_row, key])
            scale = float(p.scales[slot, head, group, low_key])
            quotient = float(torch.tensor(value, dtype=torch.float32)/
                             torch.tensor(scale, dtype=torch.float32))
            half = math.floor(quotient)+0.5
            data[label] = {"updated_value": value, "value_bits": hex(f32_bits(value)),
                           "scale": scale, "scale_bits": hex(f32_bits(scale)),
                           "quotient": quotient, "quotient_bits": hex(f32_bits(quotient)),
                           "nearest_half": half, "distance_to_half": quotient-half,
                           "code": int(p.low[slot, head, value_row, low_key])}
        details.append(data)
    return {"changed_low_codes_total": int(changed.shape[0]),
            "selected_boundary_details_first32": details}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--reference-sha256", required=True,
                        help="reference identity from the retained failure report")
    args = parser.parse_args()
    reference_path = HERE.parent / "reference.py"
    if hashlib.sha256(reference_path.read_bytes()).hexdigest() != args.reference_sha256:
        parser.error("candidate reference identity differs from failure report")
    spec = importlib.util.spec_from_file_location("damp_failure_provider", reference_path)
    candidate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = candidate
    spec.loader.exec_module(candidate)
    out = args.output_dir.resolve()
    repo = HERE.parents[2]
    if out.exists() or out == repo or repo in out.parents:
        parser.error("require NEW external output root")
    torch.set_num_threads(1)
    # Fixture contains only CPU tensor dictionaries/scalars, no candidate classes.
    f = torch.load(args.fixture, map_location="cpu", weights_only=True)
    layout = OracleLayout(**f["layout"])
    before_expected, before_actual = packed(f["expected_before"]), packed(f["actual_before"])
    after_expected, after_actual = packed(f["expected_after"]), packed(f["actual_after"])
    q, k, v, g, beta = [f[name] for name in ("q", "k", "v", "g", "beta")]
    ids = f["indices"].long()
    untouched = torch.tensor([i for i in range(before_expected.high.shape[0])
                              if i not in ids.tolist()], dtype=torch.long)
    out.mkdir(parents=True)
    result = {"schema": "damp-exact-fixture-diagnostic/v1", "created_ns": time.time_ns(),
              "fixture_sha256": hashlib.sha256(args.fixture.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "fixture_step": f["step"], "indices": ids.tolist(),
              "candidate_reference_sha256": args.reference_sha256,
              "status": "running", "evidence_scope": "CPU failure attribution only; "
              "no gate relaxation, NPU, performance or task accuracy"}
    def save():
        # Inputs are checked finite by oracle; retain failure without NaN JSON loops.
        def clean(x):
            if isinstance(x, dict): return {key: clean(value) for key, value in x.items()}
            if isinstance(x, list): return [clean(value) for value in x]
            if isinstance(x, float) and not math.isfinite(x): return {"nonfinite": repr(x)}
            return x
        (out/"report.json").write_text(json.dumps(clean(result), indent=2, allow_nan=False)+"\n")
    save()
    try:
        result["before_selected"] = summary(subset(before_actual, ids), subset(before_expected, ids))
        result["before_untouched"] = summary(subset(before_actual, untouched),
                                             subset(before_expected, untouched))
        mv_expected, mv_output, mv_update = compressed_step(
            before_expected, layout, q, k, v, g, beta, ids)
        sum_expected, sum_output, sum_update = same_before_sum_step(
            before_expected, layout, q, k, v, g, beta, ids, False)
        mv_actual, _, _ = compressed_step(before_actual, layout, q, k, v, g, beta, ids)
        sum_selected, sum_actual_output, _ = same_before_sum_step(
            before_actual, layout, q, k, v, g, beta, ids, False)
        sum_all, _, _ = same_before_sum_step(
            before_actual, layout, q, k, v, g, beta, ids, True)
        result["oracle_replays_saved_expected_after"] = summary(mv_expected, after_expected)
        result["legacy_full_repack_replays_actual_after"] = summary(sum_all, after_actual)
        result["same_before_mv_vs_sum_prepack"] = errors(
            restore_state(sum_update, layout).index_select(0, ids),
            restore_state(mv_update, layout).index_select(0, ids))
        result["same_before_mv_vs_sum_output_fp32"] = errors(sum_output, mv_output)
        result["same_before_mv_vs_sum_output_bf16"] = errors(sum_output.bfloat16(),
                                                            mv_output.bfloat16())
        result["same_before_mv_vs_sum_packed"] = summary(sum_expected, mv_expected)
        result["same_before_quantization_boundary"] = boundary_details(
            mv_update, sum_update, mv_expected, sum_expected, layout, ids)
        result["input_drift_only_mv_actual_vs_mv_expected"] = summary(mv_actual, mv_expected)
        result["only_selected_repack_vs_legacy_all_repack"] = summary(sum_selected, sum_all)
        result["legacy_untouched_changed"] = summary(subset(sum_all, untouched),
                                                     subset(before_actual, untouched))
        result["selected_repack_untouched_unchanged"] = summary(subset(sum_selected, untouched),
                                                               subset(before_actual, untouched))
        result["selected_repack_vs_saved_actual_selected"] = summary(
            subset(sum_selected, ids), subset(after_actual, ids))
        result["saved_actual_output_vs_sum_replay"] = errors(f["actual_output"],
                                                             sum_actual_output.bfloat16())
        # Factorial isolation: O(E), O(A), C(E), C(A), with O independent mv oracle
        # and C exact batched provider. This also covers the corrected v2 harness.
        batched_expected, batched_expected_output, batched_expected_updated, stage_inputs = (
            batched_candidate_replay(before_expected, layout, q, k, v, g, beta,
                                     ids, candidate))
        batched_actual, batched_actual_output, _, _ = batched_candidate_replay(
            before_actual, layout, q, k, v, g, beta, ids, candidate)
        result["batched_provider_selected_repack_replays_saved_actual_after"] = summary(
            batched_actual, after_actual)
        result["batched_provider_replays_saved_actual_output"] = errors(
            batched_actual_output, f["actual_output"])
        result["same_expected_before_oracle_vs_batched_provider_prepack"] = errors(
            restore_state(batched_expected_updated, layout).index_select(0, ids),
            restore_state(mv_update, layout).index_select(0, ids))
        result["same_expected_before_oracle_vs_batched_provider_packed"] = summary(
            batched_expected, mv_expected)
        result["same_expected_before_batched_quantization_boundary"] = boundary_details(
            mv_update, batched_expected_updated, mv_expected, batched_expected,
            layout, ids)
        result["same_before_reduction_stages"] = reduction_stages(
            *stage_inputs, g, beta)
        result["candidate_batched_vs_perhead_sum_output"] = errors(
            batched_expected_output, sum_output.bfloat16())
        result["v2_untouched_saved_actual_after_vs_before"] = summary(
            subset(after_actual, untouched), subset(before_actual, untouched))
        result["status"] = "diagnostic_complete"
    except BaseException as error:
        result.update(status="failed", error=repr(error), error_type=type(error).__name__)
        try: save()
        except BaseException as save_error: print("secondary report error: "+repr(save_error), file=sys.stderr)
        raise
    result["completed_ns"] = time.time_ns()
    save()
    print(json.dumps({"status": result["status"], "report": str(out/"report.json")}))


if __name__ == "__main__":
    main()
