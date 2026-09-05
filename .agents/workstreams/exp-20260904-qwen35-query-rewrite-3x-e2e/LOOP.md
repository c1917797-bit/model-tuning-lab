# Approved inference performance loop

User approved protocol refinement on 2026-09-06. This contract supersedes older TP4-only and fixed-order tuning instructions in historical handoff sections.

## Baselines and objective
- Exactly two baseline groups: TP8/DP1 MTP OFF and TP8/DP1 MTP ON (k=1, local-argmax implementation explicitly identified).
- Physical NPU0-7; installed model and tokenizer fingerprints, BF16, no quantization; real /cache/cch/query_rewrite.jsonl.
- Fixed first 32 records, c1/c5/c8/c16, three repetitions, identical raw completion prompts, sampling and natural-EOS policy.
- Final requirement at EACH concurrency: TTFT p50 <= MTP OFF / 2 AND TPOT p50 <= MTP OFF / 2. Report the median of three per-run p50 values and each repetition separately.
- Preserve original v5 artifacts and denominator. Also report marginal change versus latest accepted stack and MTP ON reference.
- If a timing or comparability defect requires a revised protocol, retain original results; collect matched OFF and ON supplements under a new protocol version. Never compare revised measurements to old values as proof of speedup.

## Execution loop
Orient and freeze evidence -> finish both baseline groups -> audit measurement and quality -> profile bottleneck -> rank hypotheses -> implement bounded treatment -> correctness and activation -> E2E screening -> repeated full matrix -> decide -> stack or recover -> record and re-profile.
Choose parameters, algorithms, operators or their necessary integration from the measured bottleneck and attainable end-to-end benefit, implementation cost and risk. There is no mandatory parameters-first order.
Use one primary hypothesis per attribution run. A coupled algorithm/operator implementation may be one treatment if dependencies are declared; ablate components where practical.

## Measurement audit before promotion
- Separate service startup/compile, first request and steady-state serving. One warmup request alone does not prove every shape is warmed.
- Record prefix-cache state, hit counters, warmup prompts, reuse order and graph hit/miss. Current runner repeats prompts without a cache salt; call its results cache-policy-specific until audited.
- TTFT is request send to first generated token; empty protocol chunks must not count. EOS-only requests are valid requests but reported separately.
- TPOT is post-first-token generation time divided by generated tokens minus one. Exclude <=1-token completions from meaningful TPOT aggregation and report their count. Audit SSE multi-token chunks under MTP and terminal usage overhead; label client TPOT as an estimate when token timestamps are unavailable.
- Record output-length distribution and token counts; shorter or empty output cannot by itself prove acceleration.
- Report p50, p95, p99, per-repeat values, sample counts and variability. Tail estimates from 32 requests are descriptive and weak; use additional validation for tail claims.
- Fixed concurrency is a closed-loop workload. Record client-side waiting separately from service latency; do not describe it as a fixed-arrival-rate capacity test.
- Benchmark without profiling. Profile representative prefill and decode separately; account for overlap and do not sum kernel durations into wall latency.

## Correctness and feature activation
- Zero request errors and natural EOS are transport/runtime gates, not proof of business correctness.
- Validate operator numerical agreement against reference with declared tolerances and actual shapes/dtypes.
- Validate task quality against a meaningful nonempty reference set; audit empty references and empty outputs. String similarity and output hashes are diagnostics, not sufficient semantic approval.
- Prove installed patch hashes and actual runtime dispatch; feature flags alone are insufficient.
- For MTP: record accepted/drafted tokens, acceptance ratio with exact denominator, accepted tokens per verification step, draft and verification cost, memory, output lengths. Mark unavailable metrics as unavailable.

## Decisions and accumulated stack
- Predeclare per-candidate gain and non-regression thresholds before measuring.
- Accept a candidate with meaningful improvement in its targeted metric and no unacceptable regression elsewhere. It need not improve TTFT and TPOT simultaneously in every intermediate step; the final stack must satisfy both 2x goals at all four concurrencies.
- Use inconclusive when noise, cache drift, quality or activation evidence is insufficient; reject valid unhelpful treatments; mark startup/runtime failures failed.
- Operators from /cache/cch or generation tools must enter the actual vLLM-Ascend E2E path before promotion. Standalone microbench is candidate selection evidence.
- Record configuration, code commits, data and artifact hashes, raw evidence paths, profiling, decision, rollback and resource ownership after each stage.

## Baseline table destination
- Workstream: BASELINE_COMPARISON.md, with MTP OFF/ON rows per concurrency, TTFT/TPOT/E2E, request and token throughput, validity and protocol caveats, source hashes and paths.
- Machine-readable companion: baseline-comparison.csv under the experiment evidence root; raw JSON remains immutable.
- Add optimization rows or a separate cumulative table only after full verification.

## User-provided cumulative parameter candidate
- Preserve the 2026-09-06 user report that TP4/DP2, CPU binding, async scheduling and FULL_AND_PIECEWISE with the supplied capture-size list may have produced useful gains on this model family.
- Evaluate it after the active TP8 MTP-depth experiment as a complete BF16/no-quantization E2E candidate on physical NPU0-7 with the same query_rewrite records and c1/c5/c8/c16 protocol.
- Compare every result to the immutable TP8/DP1 MTP-OFF denominator; also report capacity/throughput separately because DP2 changes replica topology.
- Attribute cautiously: MatMulAllReduce is already active in the denominator; TASK_QUEUE_ENABLE=1, HCCL_BUFFSIZE=512, OMP settings, prefix caching, mamba cache dtypes and async scheduling are retained context, not automatically new gains.
- Source inspection of installed vLLM-Ascend 0.23.0 found no reader for VLLM_ASCEND_PTO_CHUNK_GDN. Preserve it as provenance, but do not claim activation or credit without a real reader/dispatch proof.
- FULL_AND_PIECEWISE previously encountered startup/graph failures in related combinations. Apply readiness and graph-activation gates before traffic, preserve any failure log, and do not silently fall back.
