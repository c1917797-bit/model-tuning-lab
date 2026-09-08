# Qwen3.5 Performance Optimization

This directory is the reviewable home for the Qwen3.5-27B inference tuning
workstream on Ascend 910B4 and vLLM-Ascend 0.23.0.

## Current objective

- preserve paired semantic quality on the frozen query_rewrite workload;
- reduce TTFT P95 by at least 40% at c1/c5/c8/c16;
- reduce TPOT P95 by at least 20% at c1/c5/c8/c16;
- use BF16 TP4 on physical NPU0-3 only;
- do not use quantization, retraining, MTP, speculative decoding, vLLM source
  edits, final source overlays, or base-image mutation.

## Current candidate

The active t12 candidate is a standalone Python runtime monkeypatch under
runtime-monkeypatch/. It reconstructs the previously promising GDN qkvz/ba
projection fusion and gate/up-prefetch stack without replacing files from
vLLM or vLLM-Ascend.

Its code and offline deployment contracts are validated, including an
editable installation in the pinned official image with no network and no NPU
devices. It has not yet run on NPU because physical NPU0-3 currently have an
external owner. Consequently this directory makes no t12 performance or
quality-pass claim yet.

The earlier bounded-MMAR t11 result remains historical evidence:

- c1 TTFT P95: 966.3259 ms to 505.1956 ms, 47.7% lower;
- c1 TPOT P95: 39.0459 ms to 32.3098 ms, 17.3% lower.

t11 is not final because it missed the current 20% TPOT target.

## Review map

- VALIDATION_PLAN.md: audited ordered plan and acceptance boundaries.
- runtime-monkeypatch/: candidate code, offline installer, activation wrapper,
  digest manifest, and static fusion test.
- scripts/run_qwen35_gdn_runtime_t12_npu03.sh: full-lifetime NPU0-3 lease,
  image/patch/resource checks, and source-overlay-free service launch.
  VARIANT=control and VARIANT=candidate use the same command and differ only
  in the runtime patch enable switches.
- scripts/capture_qwen35_gdn_t12_activation.sh: live container, worker, NPU,
  model-readiness, and log evidence capture.
- scripts/check_qwen35_gdn_t12_activation.py: fail-closed four-rank activation
  decision.
- scripts/analyze_qwen35_current_targets.py: fresh-control versus candidate
  median-of-three P95 decision using independent 0.60 TTFT and 0.80 TPOT
  ratios.
- scripts/check_qwen35_full_quality.py: fail-closed exact/manual paired quality
  decision covering every frozen dataset row and verifying artifact digests.
- tests/: no-device unit and contract tests.

Generated datasets, model weights, raw responses, service logs, profiler
traces, credentials, and benchmark artifacts stay outside Git under /cache.
Only the exact patch bytes that pass activation, performance, provenance, and
all-357-row quality gates may be promoted to the standalone delivery PR.
