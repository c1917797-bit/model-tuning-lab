# HYPIC r19 versus prior success: protocol gap and next diagnostic

This is a read-only comparison of already frozen evidence. It does not change
the r19 LongBench-v2 quality decision or claim a causal root.

| Identity or procedure | Prior reported success | r19 full in-path pair |
| --- | --- | --- |
| Model and parallelism | Qwen3.5-27B, TP2, two accelerators | Qwen3.6-27B, TP4, physical NPU0-3 |
| Runtime source | Historical HYPIC 0.8.5 practice; current-repository prior source `3ad0967` is not proven byte-identical to the employee environment | Direct descendant `4429e35177979c874bf053ab29789e4773f39b22`; adds worker request evidence and a pending-materialization prefill gate |
| Quality request | Natural chat completion; no `vllm_xargs.hypic_segment_ends` | Explicit `hypic_segment_ends=[boundary,prompt_tokens]` in both arms |
| Quality output cap | 1024, natural EOS | 2048, natural EOS |
| Quality traffic | Three whole-dataset repetitions at concurrency 32 | Two one-token warm requests per sample, then three scored repetitions sequentially *within each sample*, while 32 samples may run concurrently |
| Hot-path interpretation | Natural quality requests did not establish explicit-segment HYPIC execution; the reported quality comparison is runtime-enabled safety | 134/381 scored requests have four-worker hot proof; the other 247 are unproved, not proven cold |

The prior reported performance gain remains a valid historical claim within its
own ruler. It is not an in-path LongBench-v2/2048 quality pass for the current
model and source. The additional per-request hot-evidence requirement restricts
the **mechanism-attribution claim**; it does not cause the independently audited
all-request quality score to fail.

The r19 matched, one-switch all-request result is no-cache 227/381 versus HYPIC
219/381 (-2.0997 percentage points). Length-limit finishes rose 49 to 67.
For sample 059, all three control responses stopped naturally and scored D,
while all three candidate responses hit 2048 tokens and scored A. This is a
repeatable observation for a post-hoc-selected sample, not proof that the
length cap or HYPIC arithmetic caused the population-level loss. The r19
candidate logged 126 materialization-ready events and 116 evictions with ten
materialized segments of capacity; churn is a hypothesis, not an identified
victim or causal mechanism.

The experimental question is therefore *not* whether to add a stricter
threshold to the old success. The new explicit-segment quality workload asks
whether the mechanism is safe when it actually participates. The old
off-path quality result cannot answer that question. Conversely, r19 does
not refute the prior natural-request result.

## Bounded next gate

1. Do not rerun r13-r19 roots or the full GSM8K suite. Keep r19 as a frozen
   negative deployment-quality result and incomplete universal-hot proof.
2. Before new device work, freeze a small, source-matched *diagnostic only*:
   same repaired source/image/model, explicit boundaries, cap 2048, natural
   EOS, two warm requests, control/treatment switch only, and a fixed set of
   preselected cap-loss and stable-control samples. Run serially first, with
   a fresh matching control; compare exact response prefix, finish reason,
   answer, worker-hot evidence, and materialization/eviction events.
3. If the serial pair still diverges, investigate source/position-state
   correctness before another c32 suite. If it converges but c32 diverges,
   investigate scheduler/cache pressure with one bounded c32 canary. Either
   outcome is diagnostic, not a 127x3 quality verdict; only a prospectively
   frozen full matched pair can replace r19 for adoption.
4. Admit that diagnostic only after fresh direct-route physical NPU0-3 and
   port 8223 idle proof, continuous isolation, and an explicit new artifact
   root. Do not touch NPU4-7 or foreign workloads.

Evidence: `hypic-previous-practice-reference.json`,
`hypic-historical-reproduction-contract.json`, the historical
`hypic_quality_eval.py`, current `hotpath_quality_full.py`,
`r19_repaired_c32_longbench_adapter.py`, r19 preregistration, and
`HYPIC_R19_REPAIRED_C32_LONGBENCH_TERMINAL_AUDIT_20261010.md`.
The r19 paired audit is SHA256
`40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`.
