# Qwen3.5 Performance Optimization

This directory is the reviewable home for the Qwen3.5-27B inference tuning
workstream on Ascend 910B4 and vLLM-Ascend 0.23.0.

## Current objective

- preserve paired semantic quality on the frozen query_rewrite workload;
- reduce TTFT P95 by at least 20% at c1/c5/c8/c16;
- reduce TPOT P95 by at least 10% at c1/c5/c8/c16;
- use BF16 TP4 on physical NPU0-3 only;
- do not use quantization, retraining, MTP, speculative decoding, vLLM source
  edits, final source overlays, or base-image mutation.
- never alter the host or image copy of vLLM-Ascend 0.23.0; load the patch from
  a read-only mount in a newly created disposable container, and roll back by
  recreating that container without the patch.

## Current candidate

The retained base is T32: an upstream fused-GDN prefill backport composed with
the Qwen3.5 projection monkeypatch. Its warmed c1/32 result reduced TTFT P95
from 841.073 ms to 617.432 ms (26.590 percent) with zero errors and natural
EOS. TPOT improved only 2.189 percent, from 28.909 to 28.276 ms/token, so this
is a TTFT component rather than a final candidate.

T33 zero-copy M=1 QKV views was rejected after TPOT regressed 2.147 percent.
T34 profiles the retained stack and proves that the remaining decode work is
dominated by MMAR/collective boundaries. The active search is therefore for an
upstream-derived, Qwen-specific MMAR/collective delta capable of closing the
remaining 2.2583 ms/token c1 gap without accuracy loss.

## Review map

- VALIDATION_PLAN.md: audited ordered plan and acceptance boundaries.
- T32_UPSTREAM_FUSED_GDN_PREFILL_FINDINGS.md: retained TTFT component.
- T33_DECODE_QKV_VIEW_ADMISSION.md: rejected zero-copy decode candidate.
- T34_RETAINED_STACK_PROFILE_FINDINGS.md: current decode/MMAR budget and next
  candidate admission boundary.
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
