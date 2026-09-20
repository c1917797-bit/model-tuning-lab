# Ten-paper Ascend piercing summary

## Acceptance contract

All papers were judged against the same project goal: Qwen3.6-27B on Ascend,
delivered as a vLLM-Ascend plugin/monkeypatch, at least 10% end-to-end
output-throughput gain, separately reported TTFT/TPOT, and no LongBench-v2 or
GSM8K regression. Operator microbenchmarks, CPU results, theoretical bounds,
and paper-reported numbers are not substitutes for this contract.

## Ordered result

| Rank | Paper / mechanism | Terminal result | Decisive evidence |
|---:|---|---|---|
| 1 | Fast and Stable Triangular Inversion | No-go for the current 10% E2E target; retain operator work | Numerical gate and deterministic replay passed. The triangular primitive reached about 3.14-3.16x, and full-GDN candidates reached about 1.18-2.01x locally, but the measured affected fraction was insufficient for 10% E2E. |
| 2 | DeltaLog | No-go at opportunity gate | Recurrent fraction was 4.52-4.84%; even perfect deletion bounded speedup to 1.047-1.051x, while the paper-local bound was about 1.021-1.023x. |
| 3 | When Good Enough Is Optimal | No-go at opportunity gate | The reported 5.2x local inversion speedup bounded measured prefill improvement to about 1.024x; decode coverage was zero. |
| 4 | KVBuffer | No-go at opportunity gate | Faithful scope covered only 4.52-4.84% of the measured path. Perfect deletion was still below 1.051x. An aggressive derivative would need to remove over 90% of a much broader, no-longer-faithful scope. |
| 5 | HYPIC | Performance reproduction passed for the shared-prefix workload; strict joint acceptance not passed | Three-run means: throughput +36.07%, TTFT -43.63%, TPOT -18.99%. LongBench-v2 changed by -0.2625 percentage points and GSM8K by -0.1516 percentage points, so the literal no-regression gate remains unmet. User directed that HYPIC not be rerun. |
| 6 | Sparse Prefix Caching | No-go for a thin v0.23 adapter | The real scheduler hook was reached on NPU, but native prefix caching and the HYPIC/GDN state lifecycle conflict. A faithful implementation needs an atomic runtime seam rather than a thin monkeypatch. |
| 7 | Scaling State-Space Models with Tensor Parallelism | No-go as incremental work | Current vLLM/vLLM-Ascend already shards the relevant projections and recurrent state. BF16-to-FP16 does not reduce bytes. Existing communication headroom was below the 10% target. |
| 8 | EPD-Serve | No-go for the fixed text-only, four-card contract | The encoder path is bypassed by the accepted workload. Faithful PD disaggregation needs two TP4 model instances (eight cards), outside the authorized topology. |
| 9 | DASC | No-go at deterministic replay gate | Structural cache-copy checks passed across all TP workers and GDN layers, but identical fixed decode requests produced three different outputs. The dense eager control was deterministic. Performance and GSM8K claims are therefore invalid. |
| 10 | DUET | No-go at intervention-layer gate | DUET relies on separate custom prefill/decode silicon packages and package-level transfer. A vLLM-Ascend plugin cannot change fixed Ascend silicon; the official artifact is an architecture simulator, not a CANN implementation. |

## Core conclusion

The ordered piercing queue is complete, but the general project acceptance is
still open:

- HYPIC is the only candidate that crossed the 10% end-to-end performance line,
  and only for its intended shared-prefix workload.
- HYPIC did not satisfy the literal zero-regression quality rule in the recorded
  formal reproduction.
- None of the other nine papers yielded a valid general-purpose, end-to-end
  candidate under the current Qwen3.6-27B/v0.23/four-NPU contract.
- MXR/stable triangular inversion is the strongest reusable operator artifact,
  but its local gain cannot be promoted to an end-to-end claim.

Therefore it would be incorrect to claim a universal Ascend improvement of at
least 10% from this portfolio. Any next campaign should begin with a fresh
profile proving at least roughly 10% removable critical-path headroom, or with a
pre-declared composition of orthogonal, already-correct mechanisms. It should
not automatically repeat any deterministic failure or already-insufficient
opportunity gate.

## Reusable migration lessons

1. Prove workload reachability and intervention-layer compatibility before
   implementing a paper.
2. Subtract functionality already present in the target runtime; score only
   incremental headroom.
3. Convert local speedups to an Amdahl bound before operator engineering.
4. Separate numerical correctness, deterministic replay, structural cache
   correctness, and task-level accuracy. Passing one does not imply another.
5. Keep dense and candidate controls on the same eager/graph mode and common
   optimizations.
6. Treat prefix/state lifecycle changes as atomic runtime work, including
   scheduler identity, allocation, graph keys, rollback, and cache ownership.
7. Preserve negative results with exact evidence so a later version change can
   trigger a targeted re-audit rather than a full rerun.
