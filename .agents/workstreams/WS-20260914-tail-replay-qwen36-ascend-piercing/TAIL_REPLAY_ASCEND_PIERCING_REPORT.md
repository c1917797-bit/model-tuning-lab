# Tail-Replay on Qwen3.6-27B Ascend: piercing report

Date: 2026-09-15

## Executive decision

The tested Tail-Replay mechanism is **not admitted** to cache-hit TTFT,
performance, or task-quality evaluation on this Ascend environment.

The architecture match is strong: Qwen3.6-27B has 48 GDN layers arranged as
16 three-GDN groups, matching the paper's target family. The native Ascend
execution path was reached on every TP rank and every GDN group. However,
zero-initial-state replay of the final 5% or 10% of a 650-token prompt did not
reconstruct state closely enough to pass the numerical mechanism gate.

This is a rejection of the tested 5%/10% zero-state suffix-replay candidates,
not a claim that the paper is false on its reported hardware or that every
possible Tail-Replay adaptation is impossible.

## Frozen question

Can a 5% or 10% suffix replay reconstruct the Qwen3.6-27B GDN cache on Ascend
accurately enough to justify implementing and benchmarking prefix-cache-hit
TTFT?

The evidence ladder was frozen as:

1. prove architecture and runtime-path fit;
2. prove recurrence-only arithmetic with an exact-split control;
3. prove a complete three-GDN group with an exact functional control;
4. compare the first real decode token using reconstructed versus dense state;
5. only then admit a candidate to paired cache-hit TTFT and quality testing.

## Environment

- Model: `/cache/efim/Qwen3.6-27B`
- Image: `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`
- vLLM / vLLM-Ascend line: 0.23.0
- Hardware: Ascend 910B4, physical NPU4-7 only
- Mapping: host 4,5,6,7 to container 0,1,2,3
- Tensor parallelism: 4
- Prefix caching: disabled
- Graph mode: disabled (`--enforce-eager`) for numerical diagnosis
- Prompt: 650 tokens
- Replay ratios: 5% and 10%
- Exact-control relative-L2 ceiling: 0.01

## Activation and harness validation

An early TP2 attempt failed at KV-cache capacity initialization. A later TP2
request completed but produced no oracle events. Source audit showed that the
plugin had wrapped `Qwen3_5DecoderLayer.forward` before vLLM-Ascend replaced
that function. The plugin was corrected to wrap the final Ascend-patched
forward path. This failure is retained as an activation lesson, not algorithm
evidence.

After correction:

- the pinned-image software suite passed 42/42;
- the focused Tail-Replay suite passed 21/21;
- TP4 activation was observed on all four ranks and all 16 groups per rank;
- all live-cache preservation checks were bitwise equal.

## Numerical evidence

### Recurrence-only oracle

Coverage was 48 GDN layers x 4 ranks x 2 ratios = 384 rows.

| Replay ratio | Exact-control max relative L2 | Replayed-state mean relative L2 | Replayed-state max relative L2 |
|---|---:|---:|---:|
| 5% | 0.003025 | 0.518888 | 0.886842 |
| 10% | 0.003491 | 0.494324 | 0.877730 |

The exact control passed, while suffix-only recurrence retained roughly half a
state norm of error on average.

### Full three-GDN-group prefill oracle

All 64 exact controls passed and all 64 live caches were bitwise preserved.

| Replay ratio | Group-output relative L2 mean / max | Recurrent-state relative L2 mean / max |
|---|---:|---:|
| 5% | 0.174475 / 0.268407 | 0.529680 / 0.891113 |
| 10% | 0.164604 / 0.259969 | 0.503038 / 0.883130 |

This showed that the recurrence discrepancy propagated through convolution,
normalization, gating, projections, residuals, and MLPs.

### First real decode token

One TP4 request generated two tokens, so one actual decode step ran after the
650-token prefill. For each rank and each of 16 GDN groups, the functional
decode path was first checked using the real dense pre-decode state.

- exact controls: 64/64 passed;
- candidate results: 64 per ratio, 128 total;
- cache preservation: 64/64 bitwise preserved;
- all candidate tensors were finite;
- every candidate group-output relative-L2 value exceeded 0.01.

| Replay ratio | Output relative L2 mean / min / max | Output cosine mean / min | Recurrent-state relative L2 mean / max |
|---|---:|---:|---:|
| 5% | 0.053577 / 0.023782 / 0.127720 | 0.998283 / 0.991815 | 0.502004 / 0.871819 |
| 10% | 0.051287 / 0.022978 / 0.121431 | 0.998450 / 0.992601 | 0.476821 / 0.865451 |

The exact functional-decode output error was only 0.003815 on average and
0.006212 at worst, below the frozen 0.01 ceiling. The candidate gap therefore
cannot be attributed to the functional harness alone.

## HYPIC-style gate result

| Gate | Result | Consequence |
|---|---|---|
| Architecture fit | Pass | Continue |
| Real Ascend hot-path activation | Pass | Continue |
| Exact recurrence control | Pass | Continue |
| Exact full-group control | Pass | Continue |
| Exact first-decode control | Pass | Candidate comparison is admissible |
| 5% suffix replay numerical signal | Fail | Do not benchmark |
| 10% suffix replay numerical signal | Fail | Do not benchmark |
| Paired cache-hit TTFT | Not run | Candidate was not admitted |
| Task quality | Not run | Candidate was not admitted |

Request latency from this diagnostic is not a performance result: the oracle
deliberately executes dense and multiple candidate paths and synchronizes for
evidence.

## Decision and next use of effort

Stop the current Tail-Replay 5%/10% zero-state suffix-replay implementation.
Do not spend NPU time on paired TTFT or downstream accuracy for these
candidates.

A future Tail-Replay research branch would need a materially different
reconstruction method, such as a non-zero boundary-state estimator, a learned
correction, or a substantially longer/adaptive replay window. Those are new
algorithmic variants and must restart at the same exact-controlled NPU gates;
they should not be presented as reproduction of the tested paper setting.

## Evidence locations and identities

First-decode artifact root:
`/cache/cch/tail-replay-qwen36-ascend-tp4-20260915/first-decode-oracle/v1`

- request SHA256: `f46d6a6881abecd33795be53404ed9d8b1b4a64d44b7d2b423b7c06c1b1e26a1`
- response SHA256: `43daed79794836a35eb832a2077419ab8ddc98afc64baa39304c4c3403a0dba6`
- runtime SHA256: `4ed3e0c392c93eb7ed4a250d4722433b533f7fc732e7841c463b586721a15c87`
- probe source SHA256: `3a04a73497f3da47b74b7ead46a7024ed9565ef031e1fa5cdcbcd0c282739078`

After the run, the owned container was stopped and NPU4-7 were confirmed to
have no running processes.

## Allowed and forbidden claims

Allowed: the tested 5%/10% zero-state Tail-Replay mechanism executed through
the native Ascend Qwen3.6 TP4 path with complete rank/group coverage and valid
exact controls, but produced material reconstructed-state and first-decode
group-output deviations and was not admitted to performance or quality tests.

Forbidden:

- Tail-Replay improves or regresses Ascend TTFT; no admissible TTFT test ran.
- Tail-Replay preserves or degrades task accuracy; no admissible task test ran.
- The diagnostic request time is an end-to-end performance measurement.
- These results disprove every Tail-Replay variant or the paper's reported
  results on other hardware and software stacks.
