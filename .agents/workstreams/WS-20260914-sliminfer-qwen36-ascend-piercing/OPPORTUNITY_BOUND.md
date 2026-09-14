# Opportunity and mechanism admission

## Evidence available now

The HYPIC-equivalent Qwen3.6 performance ruler has a completed dense historical
control with mean TTFT 40.358 seconds, TPOT 74.507 ms/token and output
throughput 123.765 token/s. These historical values define the comparison
contract but are not a SlimInfer result.

A Qwen3.6 TP4 profile from the same model and pinned image was reused from
`/cache/cch/hypic-qwen36-piercing-20260904/profiles/pdc-baseline`. Its workload
was input 32,768, output 128, concurrency 4 and four requests, so it is
contextual opportunity evidence rather than the formal c16/output1024 ruler.
The raw evidence was copied to a new derived directory before analysis; the
HYPIC evidence was not mutated.

Offline CANN parsing produced an operator summary and SQLite database, but the
log also contains step-trace database warnings and unknown-key errors. The
usable subset shows large-row work in `MatMulV3`, `MatMulV2`,
`FusedInferAttentionScore`, GDN chunk/recurrent kernels, normalization, slicing
and `hcom_allReduce`. Summed task time exceeds the trace span because tasks
overlap. These totals rank affected mechanisms only; they are not removable
wall time and cannot be converted into a throughput claim.

For the proposed 20/40/60 pruning boundaries, the token-linear row-work proxy is
`(20 + 20*0.375 + 20*0.1875 + 4*0.125) / 64 = 49.609375%` of dense. This is an
optimistic shape proxy for token-linear work after pruning, not a measured
speedup. Full-attention quadratic work may increase the opportunity, while
selection, gather/scatter, metadata, TP synchronization and hybrid GDN state
handling reduce it.

## Admission decision

- The faithful cross-hybrid route remains admitted for one bounded canary
  because pruning after layer 19 can affect most later GDN, MLP and
  full-attention token work, not only the full-attention operator.
- A full-attention-only derivative is **not** admitted as a likely 10% service
  gain from the existing trace. Perfect removal of the identified attention
  sum alone is below 10% of the diagnostic envelope, and gather/scatter plus
  selection adds cost.
- The available Qwen3.6 profile is sufficient to admit the identity and
  semantics canaries. A new formal profile is justified only after a real
  pruning path exists and must separate prefill/decode and preserve the raw
  trace.

## Stop/redirect rule

Reject the current route if the pinned vLLM hybrid cache cannot express
layer-specific token/state counts without changing global scheduler identity, or
if the corrected optimistic end-to-end bound is below the next useful
milestone. A successor must materially change the hypothesis and use a separate
experiment ID.
