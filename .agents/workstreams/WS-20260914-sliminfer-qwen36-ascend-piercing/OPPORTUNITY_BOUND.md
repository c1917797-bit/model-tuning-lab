# Opportunity and mechanism admission

## Evidence available now

The HYPIC-equivalent Qwen3.6 performance ruler has a completed dense historical
control with mean TTFT 40.358 seconds, TPOT 74.507 ms/token and output
throughput 123.765 token/s. It did not include a clean Qwen3.6 operator profile.

A separate Qwen3.8 DRRQR diagnostic used the same 32K input and TP4 shape. Its
dense prefill trace reported a 4143.450 ms kernel envelope and 401.944 ms
rank-mean `FusedInferAttentionScore` sum. The ratio is 9.70%. This is only
hotspot-ranking context: operator sums may overlap and the model/candidate
identity differs, so it is neither a Qwen3.6 baseline nor an end-to-end bound.

## Admission decision

- The faithful cross-hybrid route remains admitted for one bounded canary
  because pruning after layer 19 can affect most later GDN, MLP and
  full-attention token work, not only the full-attention operator.
- A full-attention-only derivative is **not** admitted as a likely 10% service
  gain from the existing trace. Perfect removal of the identified attention
  sum alone is below 10% of the diagnostic envelope, and gather/scatter plus
  selection adds cost.
- Before a broad implementation, collect one bounded Qwen3.6 prefill profile
  only if no comparable trace already exists. Attribute exclusive or
  non-overlapped wall time; do not sum overlapping kernels into a throughput
  forecast.

## Stop/redirect rule

Reject the current route if the pinned vLLM hybrid cache cannot express
layer-specific token/state counts without changing global scheduler identity, or
if the corrected optimistic end-to-end bound is below the next useful
milestone. A successor must materially change the hypothesis and use a separate
experiment ID.
