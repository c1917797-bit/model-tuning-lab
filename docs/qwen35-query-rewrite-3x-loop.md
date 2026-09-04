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
