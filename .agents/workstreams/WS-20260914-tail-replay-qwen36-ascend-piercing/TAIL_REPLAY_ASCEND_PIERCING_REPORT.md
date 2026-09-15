# Tail-Replay on Qwen3.6-27B Ascend: piercing report

Date: 2026-09-15

## Executive decision

The tested Tail-Replay mechanism remains **open for end-to-end validation**.
The earlier use of a 0.01 intermediate relative-L2 threshold as a candidate
acceptance gate was incorrect and is withdrawn.

The architecture match is strong: Qwen3.6-27B has 48 GDN layers arranged as
16 three-GDN groups, matching the paper's target family. The native Ascend
execution path was reached on every TP rank and every GDN group. However,
zero-initial-state replay of the final 5% or 10% of a 650-token prompt produced
measurable intermediate-state and first-decode group-output deviations. These
are diagnostic signals, not an end-to-end accuracy decision.

The 0.01 threshold applies only to the exact dense functional control used to
prove that the probe follows the real Ascend operator path. The user's 1%
acceptance limit applies to end-to-end GSM8K accuracy loss, not to an
intermediate tensor.

## Frozen question

Can a 5% or 10% suffix replay reconstruct the Qwen3.6-27B GDN cache on Ascend
accurately enough to justify implementing and benchmarking prefix-cache-hit
TTFT?

The evidence ladder was frozen as:

1. prove architecture and runtime-path fit;
2. prove recurrence-only arithmetic with an exact-split control;
3. prove a complete three-GDN group with an exact functional control;
4. compare the first real decode token using reconstructed versus dense state;
5. integrate the approximate candidates into the real cache-hit path;
6. decide them using paired cache-hit TTFT and end-to-end GSM8K, with at most
   1% GSM8K accuracy loss.

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
- every candidate group-output relative-L2 value exceeded 0.01, but 0.01 is
  not a valid acceptance threshold for an approximate Tail-Replay candidate.

| Replay ratio | Output relative L2 mean / min / max | Output cosine mean / min | Recurrent-state relative L2 mean / max |
|---|---:|---:|---:|
| 5% | 0.053577 / 0.023782 / 0.127720 | 0.998283 / 0.991815 | 0.502004 / 0.871819 |
| 10% | 0.051287 / 0.022978 / 0.121431 | 0.998450 / 0.992601 | 0.476821 / 0.865451 |

The exact functional-decode output error was only 0.003815 on average and
0.006212 at worst, below the frozen 0.01 harness ceiling. The candidate gap
therefore appears to be a real property of suffix replay rather than a probe
artifact, but its effect on logits and GSM8K remains unmeasured.

## HYPIC-style gate result

| Gate | Result | Consequence |
|---|---|---|
| Architecture fit | Pass | Continue |
| Real Ascend hot-path activation | Pass | Continue |
| Exact recurrence control | Pass | Continue |
| Exact full-group control | Pass | Continue |
| Exact first-decode control | Pass | Candidate comparison is admissible |
| 5% suffix replay numerical signal | Diagnostic only | Continue to E2E |
| 10% suffix replay numerical signal | Diagnostic only | Continue to E2E |
| Paired cache-hit TTFT | Not run yet | Required |
| End-to-end GSM8K | Not run yet | Required; loss must be at most 1% |

Request latency from this diagnostic is not a performance result: the oracle
deliberately executes dense and multiple candidate paths and synchronizes for
evidence.

## Decision and next use of effort

Continue the current 5%/10% candidates into a real, opt-in cache-hit
integration. First verify candidate activation and output/logit plumbing, then
run paired cache-hit TTFT and end-to-end GSM8K. The final quality gate is the
user-defined GSM8K accuracy loss of at most 1%; the report should show both
absolute percentage-point and relative-percent deltas to avoid ambiguity.

The intermediate error suggests that 10% is the more promising of the two
tested ratios, but it does not authorize selecting a winner before E2E results.

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

Allowed: the tested 5%/10% zero-state Tail-Replay diagnostic executed through
the native Ascend Qwen3.6 TP4 path with complete rank/group coverage and valid
exact controls, and produced measurable reconstructed-state and first-decode
group-output deviations whose E2E impact remains unknown.

Forbidden:

- Tail-Replay improves or regresses Ascend TTFT; no paired TTFT test has run.
- Tail-Replay passes or fails the 1% GSM8K gate; no E2E GSM8K test has run.
- The diagnostic request time is an end-to-end performance measurement.
- These results disprove every Tail-Replay variant or the paper's reported
  results on other hardware and software stacks.
