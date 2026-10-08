# Prospective cache10r2 matched performance ruler (2026-10-08)

Historical, unexecuted r2 preregistration. Its r2 quality entry gate never
passed, and the named controller was retargeted before device execution to
the separately frozen `HOTPATH_CACHE10R13_MATCHED_PERFORMANCE_PLAN.md`.
Do not run from the r2 instructions below or treat them as current.

This ruler is for the HYPIC 0.85/cache10 serving identity. The completed
0.9/4-segment binding-off performance pair is valid historical evidence but
not a control for this identity. Do not pool or directly compare its raw
latencies with this campaign.

## Entry gate and frozen pair

- First complete and independently audit both cache10r2 127-sample quality
  arms, including 381 scored rows per arm and exact owned release. A failed or
  interfered arm prevents an unqualified paired performance decision.
- Only physical chicaihong01 NPU0-3; never touch NPU4-7 or unrelated
  containers. Check actual NPU processes, the existing Docker claims, and
  port 8223 before each phase. A 10-second lane guard runs throughout each
  measured phase; any foreign PID or probe error invalidates that phase and
  aborts only the exact owned service.
- Pin the same image, source commit, model shards, benchmark bytes, TP4,
  cpuset 112-191, context 41,984, CPU-binding-off flag, GPU utilization
  0.85, 3,584 MiB HYPIC material cache, and 10 materialized segments as the
  audited cache10r2 quality service. Normalize only arm-specific evidence
  paths and HYPIC enablement when comparing service specifications. Never
  mutate the shared image, source checkout, host settings, or foreign service.
- Fresh exact-owned service for each of six phases. Alternate order:
  no-cache/hypic-only screen; hypic-only/no-cache repeat2;
  no-cache/hypic-only repeat3. Each phase uses a new root and refuses to
  overwrite or silently resume partial evidence.

## Measured workload and validity

- Reuse frozen `tools/benchmark_shared_prefix.py` with two concurrent
  one-token priming requests, then 40 measured requests at concurrency 16,
  32,768 prompt tokens with a 16,384-token shared prefix and explicit
  `[16384, 32768]` segment ends, fixed 1,024 output tokens, temperature 0,
  seed 0, and ignore-EOS. This keeps the prior C16 workload protocol while
  changing only the declared service identity.
- Every phase must yield 40 distinct successful rows, no failures, all
  exactly 1,024 output tokens and `finish_reason=length`; recompute weighted
  TPOT, nearest-rank P95 TPOT/TTFT, throughput, and hashes from raw rows.
  Require candidate measured hot-path evidence and no baseline worker-hot
  events, four physical workers in the exact container, clean lane samples,
  and exact container/worker/port release. Controller exit zero alone is not
  an audit pass.

## Declared decisions

Report all six phase metrics, three paired deltas, medians, and variation.
Classify performance as matched-valid only if all six phase contracts and
isolation/release checks pass. Separately report whether median HYPIC minus
baseline weighted TPOT is at most -10 ms/token and median baseline minus
HYPIC TTFT P95 is at least 10 s, the existing paper-effect thresholds.
Also report TPOT percentage reduction and throughput ratio without replacing
the declared gates. A valid but unfavorable effect is a negative result, not
a reason to change the ruler. Even a favorable result is limited to this
model/workload/service identity; it does not prove full-paper C3 or validate
all archived Skills.

## Execution handoff

The work-branch controller is
`hotpath_cache10_matched_performance.py`; its default invocation is an
offline frozen-spec/pair-seam inspection. The `--run` entry requires the
independent `hotpath-quality-cache10r2-full-audit.json` receipt, refuses an
existing attempt root, enforces the preceding phase's clean result, and then
checks physical NPU0-3 before creating its exact-owned service. Invoke each
phase in the order listed above with `--arm`, `--phase`, and `--run` in
separate bounded operations. Do not invoke any `--run` while the current
quality candidate/control is live. On interruption, inspect its operation
handle and preserved root; never resume a partial phase in place.

After all six phases, run
`audit_hotpath_cache10_matched_performance.py`. It independently checks
raw rows, recomputes metrics, reconciles contracts/hashes, guard/worker/
release receipts, normalized service specifications, and the declared
effects. The executable and audit were checked offline against the frozen
0.9 performance data format; that check is not a cache10 NPU result.
