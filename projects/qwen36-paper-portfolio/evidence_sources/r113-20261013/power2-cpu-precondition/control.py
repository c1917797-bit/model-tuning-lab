"""Source-only exact power-of-two precondition. No native call/authority here."""
from __future__ import annotations
import argparse, hashlib, json, os, sys, time
from pathlib import Path
START, CUT = 1791835594, 1791878794
FACTORS = {"query": 2.0, "key": .5, "value": 2.0}
RAW_REF = {"path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/run-adakv-paged-r108-numeric-main-002/component-002/first-failure.pt", "bytes": 26163299, "sha256": "b2c238938dccdcacb611f66728bae0fe3e2c13ce757d420d67fb85641f76b435"}
GOLDEN_REF = {"path": "/cache/cch/qwen36-paper-preparation-20261007/lowbit/_draft_damp_operator_reuse/R87/adakv-paged-numeric-bootstrap-v1-002/numeric.py", "bytes": 12739, "sha256": "035535ce19d6fd426d9f1fd94faad37a08e696be744df68cfbaf049c761153e3"}

def need(v, message):
    if not v: raise ValueError(message)

def exact(a, b, t):
    return a.dtype == b.dtype and tuple(a.shape) == tuple(b.shape) and t.equal(a.contiguous().view(t.uint8), b.contiguous().view(t.uint8))

def prepare_power2(raw, original_reference, t):
    """Whole32/1536/frame. A false result never permits native submission."""
    need(callable(original_reference), "immutable independent original reference")
    need(tuple(raw["q"].shape) == (1, 6, 256) and tuple(raw["reference"].shape) == (1, 6, 256), "exact original full1536")
    need(all(x.device.type == "cpu" and x.dtype == t.bfloat16 for x in raw.values()), "CPU original BF16 fields")
    source = {"query": raw["q"].float(), "key": raw["expected_key"].float(), "value": raw["expected_value"].float()}
    need(exact(raw["key"], raw["expected_key"], t) and exact(raw["value"], raw["expected_value"], t), "entire original physical state, not selected-only substitute")
    scaled = {n: x * FACTORS[n] for n, x in source.items()}
    need(all(x.dtype == t.float32 for x in scaled.values()), "explicit FP32 scaling before HALF conversion")
    half = {n: x.to(t.float16) for n, x in scaled.items()}
    checks = {}
    for n, x in source.items():
        y, h = scaled[n], half[n]
        checks[n] = {"elements": x.numel(), "original_finite": bool(t.isfinite(x).all()),
                     "scaled_FP32_finite": bool(t.isfinite(y).all()), "scaled_half_finite": bool(t.isfinite(h).all()),
                     "inverse_scale_restores_original_float_bits": exact(y / FACTORS[n], x, t),
                     "scaled_nonzero_inputs_not_zeroed": bool(((x == 0) | (y != 0)).all()),
                     "all_scaled_half_float_exact": exact(h.float(), y, t)}
    # Check the full selected readset explicitly as well as every guard/unused element.
    for n in ("key", "value"):
        checks["selected_" + n + "32"] = {"elements": source[n][32:64].numel(),
            "all_scaled_half_float_exact": exact(half[n][32:64].float(), scaled[n][32:64], t)}
    q, k, v = source["query"], source["key"][32:64], source["value"][32:64]
    q2, k2, v2 = scaled["query"], scaled["key"][32:64], scaled["value"][32:64]
    qkh, kvh = half["query"].float(), half["key"][32:64].float()
    products = q[0, :, None, :] * k[:, 0, :][None, :, :]
    scaled_products = q2[0, :, None, :] * k2[:, 0, :][None, :, :]
    score = q[0] @ k[:, 0].T
    score2 = q2[0] @ k2[:, 0].T
    half_score = qkh[0] @ kvh[:, 0].T
    old_fp32 = original_reference(q, k, v, .0625, t).unsqueeze(0)
    scaled_fp32 = original_reference(q2, k2, v2, .0625, t).unsqueeze(0)
    post = scaled_fp32 * .5
    original_final = original_reference(raw["q"], raw["expected_key"][32:64], raw["expected_value"][32:64], .0625, t).unsqueeze(0)
    ideal = {"all49152_FP32_products_bitwise_equal": exact(products, scaled_products, t),
             "full192_FP32_QK_bitwise_equal": exact(score, score2, t),
             "full192_FP32_half_roundtrip_QK_bitwise_equal": exact(score, half_score, t),
             "full192_scaled_scores_bitwise_equal": exact(score * .0625, score2 * .0625, t),
             "all_FP32_scores_and_ideal_outputs_finite": all(bool(t.isfinite(x).all()) for x in (products, scaled_products, score, score2, half_score, old_fp32, scaled_fp32, post)),
             "full1536_ideal_AV_inverse_scale_bitwise_equal": exact(post, old_fp32, t),
             "full1536_original_FP32_to_BF16_matches_saved_golden": exact(old_fp32.to(t.bfloat16), raw["reference"], t),
             "full1536_scaled_post_BF16_matches_saved_golden": exact(post.to(t.bfloat16), raw["reference"], t),
             "unmodified_original_reference_matches_saved_golden": exact(original_final, raw["reference"], t)}
    supported = all(v for row in checks.values() for k, v in row.items() if k != "elements") and all(ideal.values())
    evidence = {"original_float": source, "scaled_float": scaled, "scaled_half": half,
                "original_QK_FP32": score, "scaled_QK_FP32": score2, "half_roundtrip_QK_FP32": half_score,
                "original_ideal_FP32": old_fp32, "scaled_ideal_FP32": scaled_fp32,
                "scaled_ideal_FP32_post_half": post, "unchanged_original_final_golden": original_final}
    return supported, {"exactness": checks, "ideal_semantics": ideal}, evidence

def rescale_native_output(actual_half, t):
    """For a future qualified caller only; CPU preconditions do not call FIA."""
    need(actual_half.dtype == t.float16 and tuple(actual_half.shape) == (1, 6, 256), "complete actual HALF output")
    x = actual_half.float(); y = x * .5
    need(bool(t.isfinite(x).all()) and bool(t.isfinite(y).all()) and exact(y * 2.0, x, t), "finite lossless FP32 output inverse scale")
    return y.to(t.bfloat16)

def main(argv=None):
    p = argparse.ArgumentParser(); p.add_argument("--execute", action="store_true")
    for n in ("raw-ref", "reference-ref", "output"): p.add_argument("--" + n)
    a = p.parse_args(argv)
    if not a.execute:
        print(json.dumps({"enabled": False, "NPU": False, "numerical_qualified": False})); return 0
    # This cold CLI is CPU-only, pending MAIN source/owner/resource admission.
    need(os.environ.get("ADAKV_POWER2_CPU_PRECONDITION_ENABLE") == "1" and os.environ.get("TORCH_DEVICE_BACKEND_AUTOLOAD") == "0", "explicit CPU-only precondition")
    need(a.raw_ref and a.reference_ref and a.output and START <= time.time() < CUT and not list(Path("/dev").glob("davinci[0-9]*")), "MAIN complete refs, current shared clock, no devices")
    import ast
    def checked(r):
        need(type(r) is dict and set(r) == {"path", "bytes", "sha256"}, "exact Ref3")
        path = Path(r["path"]); need(path.is_absolute() and path.is_file() and not path.is_symlink(), "original ordinary file")
        data = path.read_bytes(); need(len(data) == r["bytes"] and hashlib.sha256(data).hexdigest() == r["sha256"], "whole original bytes")
        return data
    rr, gr = json.loads(a.raw_ref), json.loads(a.reference_ref)
    need(rr == RAW_REF and gr == GOLDEN_REF, "exact original Ma0248 raw and independent reference Ref3")
    raw_bytes = checked(rr); golden_text = checked(gr).decode("utf8")
    nodes = [n for n in ast.parse(golden_text).body if isinstance(n, ast.FunctionDef) and n.name == "reference"]
    need(len(nodes) == 1, "one full unchanged original reference")
    ns = {"__builtins__": __builtins__}; exec(compile(ast.get_source_segment(golden_text, nodes[0]), gr["path"], "exec"), ns)
    root = Path(a.output); need(root.is_absolute() and not root.exists() and root.parent.is_dir(), "absent sole RW output")
    root.mkdir(); start = time.monotonic()
    import torch as t
    need("torch_npu" not in sys.modules, "never import device backend")
    t.set_num_threads(1); t.set_num_interop_threads(1)
    raw = t.load(rr["path"], map_location="cpu", weights_only=True)
    need(set(raw) == {"q", "key", "value", "expected_key", "expected_value", "prior_key", "prior_value", "actual", "reference"}, "all original fields")
    supported, checks, evidence = prepare_power2(raw, ns["reference"], t)
    t.save(evidence, root / "CPU_POWER2_PRECONDITIONS.pt")
    need(checked(rr) == raw_bytes and checked(gr).decode("utf8") == golden_text, "original raw/source unchanged")
    need(time.monotonic() - start <= 120 and time.time() < CUT, "shared CPU120 bound")
    report = {"schema": "adakv.power2-FP16-CPU-precondition/v1", "raw_ref": rr, "reference_ref": gr,
              "input_factors": FACTORS, "output_inverse_FP32_factor": .5, "checks": checks,
              "supported_for_future_control_only": bool(supported), "NPU": False,
              "native_intermediates_observed": False, "numerical_qualified": False,
              "matrix96_qualified": False, "model_ready": False, "performance_ready": False,
              "task_ready": False, "limits_unchanged": {"relative_rms": .005, "cosine": .99998},
              "elapsed_seconds": time.monotonic() - start}
    with (root / "REPORT.json").open("xb") as f: f.write(json.dumps(report, sort_keys=True, allow_nan=False).encode() + b"\n")
    print("ADAKV_POWER2_CPU_PRECONDITION " + json.dumps(report)); return 0

if __name__ == "__main__": raise SystemExit(main())
