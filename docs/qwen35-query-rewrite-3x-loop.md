# Qwen3.5-27B query_rewrite 2x E2E Loop

The optimization target is the complete serving path, not an isolated kernel.
The final candidate may combine core operators, inference algorithms and
runtime parameters. Each addition is first measured as one attributable
treatment, then retained or removed before the next treatment is added.

```text
orient
-> freeze original DP2/TP4 baseline
-> profile TTFT/TPOT critical paths
-> optimize and integrate a core operator
-> add an inference algorithm
-> tune runtime parameters
-> combine accepted treatments
-> run ablations
-> verify concurrency 1/5/8/16 against the immutable original baseline
```

An operator result is not complete until the operator is selected at runtime
inside Qwen3.5-27B on vLLM-Ascend and produces a valid improvement on
`/cache/cch/query_rewrite.jsonl`.

Final success requires TTFT and TPOT at or below one half of the original
baseline for concurrency 1, 5, 8 and 16, with correct business outputs, zero
request errors, safe HBM, and acceptable tail latency.
