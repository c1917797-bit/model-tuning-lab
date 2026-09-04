# Qwen3.5-27B query_rewrite 2x E2E Loop

The optimization target is the complete serving path, not an isolated kernel.
The final candidate may combine core operators, inference algorithms and
runtime parameters. Each addition is first measured as one attributable
treatment, then retained or removed before the next treatment is added.

```text
orient
-> lock original TP4 quick32-v3 baseline by SHA256
-> profile TTFT/TPOT critical paths
-> measure one parameter / algorithm / operator treatment
-> reject regressions or correctness failures
-> add an accepted treatment to the current best stack
-> measure the cumulative stack against the same original baseline
-> retain single-treatment and ablation evidence for attribution
-> repeat until both metrics reach 2x at concurrency 1/5/8/16
```

An operator result is not complete until the operator is selected at runtime
inside Qwen3.5-27B on vLLM-Ascend and produces a valid improvement on
`/cache/cch/query_rewrite.jsonl`.

Final success requires TTFT and TPOT at or below one half of the original
baseline for concurrency 1, 5, 8 and 16, with correct business outputs, zero
request errors, safe HBM, and acceptable tail latency.

The user-designated original denominator is the immutable TP4
`quick32-v3` run: first 32 records, one repetition, seed 1024 and natural EOS.
Every candidate uses exactly that request protocol and runs by itself; the
original service is not relaunched. The four original artifacts and their
SHA256 values are hard-coded into the decision analyzer. A candidate result is
invalid if any baseline hash, dataset identity, request count, termination
reason or response hash check fails.

The original ran on physical NPU0-3. Current candidates use the user-assigned
physical NPU4-7, mapped to logical devices 0-3 inside the container. Both sets
are Ascend 910B4; the decision artifact and container inspect preserve this
device-index caveat.

"One treatment" is an attribution rule, not a final-stack restriction. For
example, FlashComm1 and BF16 FRACTAL_NZ are first measured separately. If both
are accepted, `flashcomm1-bf16-nz` measures their cumulative effect. Later
accepted algorithms and feature-flagged operators are added to that best stack
the same way. Quantization is prohibited.

## Current durable decisions

- MTP is rejected: it changed 16-21 of 32 response hashes and regressed both
  metrics at every measured concurrency.
- FlashComm1 is failed at startup for the unchanged vLLM-Ascend 0.23.0
  Qwen3.5 TP4 path. Activation succeeded, but GDN graph construction mixed an
  unsplit symbolic sequence length with a sequence-parallel `ceil(s/4)`
  buffer. No E2E measurement exists, so this is not a claimed latency
  regression and not a rejection of the paper-level method.
- BF16 `weight_nz_mode=2` with MatMulAllReduce enabled also failed before
  readiness: the layout conversion activated, but `aclnnMatmulAllReduce`
  requires its `x2` input in ND rather than FRACTAL_NZ.
- The next isolated recovery is BF16 `weight_nz_mode=2` with
  MatMulAllReduce disabled on physical NPU4-7. That matches the actual fixed
  original setting and isolates the layout variable. Neither prior failed
  path is part of the current best stack.

The recovery launcher mode is `bf16-nz-mmar-off`; it explicitly sets
MatMulAllReduce false in both the environment and additional config, keeps the
model in BF16, and changes only `weight_nz_mode` relative to the original.

The real recovery run is rejected. It achieved about 2x TTFT at c1/c5 and
1.97x at c8, but c16 TTFT regressed, TPOT reached only 1.33-1.54x, and
15-19 response hashes changed in every cell. The next isolated treatment is
MatMulAllReduce enabled alone with NZ mode 1 and FlashComm1 disabled.

The isolated launcher mode is `mmar-on`. Relative to the real fixed original
it changes only MatMulAllReduce false to true and keeps the BF16 ND layout.

The same-device no-op control showed that the large fixed-original MMAR delta
was mostly run/device drift: net TPOT improvement was only 0-5.3% and c1-c8
TTFT improvement was only 2.4-8.6%. MMAR remains outside the accepted stack.

A full-model CANN dynamic profile then ranked the decode opportunity. In the
post-prefill window, MatMulV2 represented 70.702% of summed kernel duration,
AllReduce 10.530%, and recurrent GDN 2.406%. The dominant TP-sharded dense FFN
decode shapes were 1x5120 by 8704x5120 and 1x4352 by 5120x4352.

NPU Prompt Lookup Decoding was tested as the next training-free algorithm and
is rejected. Concurrency 1 TPOT was 4.82x slower. Concurrency 5 stalled after
25/32 requests and its observed TPOT was 7.67x slower; c8/c16 were not run.
Only 6.934% of draft tokens and 14.809% of first draft positions were accepted,
so retuning to a smaller draft window is not economically justified.

A partial matrix is now a terminal state, not an abandoned directory. The
runner preserves the candidate failure, captures logs and metrics, stops the
exact candidate container, classifies missing cells as not-run, emits
`reject-runtime-failure`, and hashes only artifacts that exist. The next loop
is a profile-ranked BF16 dense FFN operator with reference correctness,
repeated microbenchmarks, feature-flagged vLLM-Ascend integration and E2E
measurement on assigned physical NPU4-7.
