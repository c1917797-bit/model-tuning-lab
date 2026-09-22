# Qwen3.6-27B Ascend 10-paper portfolio audit

## Current status

The fixed 10-paper queue has been pierced. HYPIC remains the prior successful
reference for segmented prefix reuse; it is not a new result from this
workstream. Every other queue entry has a scoped evidence-backed no-go or
inapplicability decision under the current Qwen3.6/v0.23/910B/plugin contract.

## Final acceptance boundary

The user now permits up to 1% end-to-end task-accuracy loss. Apply this to the
final, matched LongBench-v2 and GSM8K evaluations, not to a single operator
output, state element, or intermediate tensor. Report both percentage-point
and relative-percent deltas against the same-stack dense control; the user's
choice between these two interpretations of "1%" is pending. Until resolved,
do not declare a candidate accepted on accuracy alone. Keep the NPU
numerical/state/graph safety gates separate, and require the candidate to
meet the independent +10% end-to-end throughput target before spending a
final accuracy run.

The prior HYPIC three-run segmented-prefix result averaged +36.0663% output
throughput, with LongBench-v2 -0.2625 percentage points (-0.568% relative)
and GSM8K -0.1516 percentage points (-0.158% relative). Thus its historical
mean quality result is within either reading of the new 1% allowance. However,
those quality evaluations used `max_out_len=1024`; the Qwen3.6 final gate in
the GDN workstream specifies `max_tokens=2048`. This evidence cannot be
promoted to a 2048-output final accuracy pass, and HYPIC remains a prior
workload-conditional success rather than a new generic decode result.

## HYPIC portability audit (source-level, not a new hardware result)

The historical Qwen3.6 reproduction pins `hypic_vllm_ascend` commit
`3ad0967589304cd8fc4e7cff02f48ecc6125c89f`; the local source checkout
still resolves to that commit. It has unrelated dirty benchmark/test files,
which were not changed by this audit. A future thin version adapter must
re-prove these concrete seams before any new NPU claim:

- scheduler: vLLM `Scheduler`/`AsyncScheduler` and Ascend scheduler variants,
  patched at `add_request`, `schedule`, and `update_from_output`;
- worker: `vllm_ascend.worker.model_runner_v1.NPUModelRunner`, patched at
  initialization and `execute_model`, with import deferred until the Ascend
  custom-op bootstrap completes;
- full attention: `vllm_ascend.attention.attention_v1` implementation `forward`
  and Qwen attention geometry registration in `patch_qwen3_5`;
- linear attention: `vllm_ascend.ops.gdn.AscendGatedDeltaNetAttention._forward_core`
  plus its Qwen patch target, including state ownership and graph semantics.

These are version-sensitive private hooks, not proof that a newer runtime is
compatible. The official [v0.27.1rc1 feedback scope](https://github.com/vllm-project/vllm-ascend/issues/16014)
describes a model-restricted candidate centered on Kimi-K3/MiniMax-M3 and does
not declare Qwen3.6-27B on 910B4 validated. Do not spend a cross-version
performance run until that runtime first passes model startup, exact hook
dispatch, numerical replay, and matched dense control. Keep paper C3
distributed scatter/transfer distinct from the demonstrated single-instance
C1/C2 segmented hot reuse; the latter does not prove paper-complete C3.

## What cannot be added

- MXR and Good Enough optimize the same triangular-inversion scope.
- DeltaLog and KVBuffer optimize substantially the same recurrent-state decode
  scope.
- HYPIC and Sparse Prefix both rely on prefix reuse and cannot be presented as
  independent generic dense accelerators.

Using the most favorable measured shares, even perfect deletion of the direct
inversion scope and recurrent-state decode scope is below the 10% target. The
official six-stage MegaGDN candidate touches a larger scope, but its measured
local speedup was only 1.087x; a 10% Amdahl result at 10.87% share would require
more than 6x local speedup.

These are opportunity bounds, not end-to-end measurements. They reject
continued polishing of already-small scopes; they do not establish a new
performance result.

## Fresh current-stack profile

The bounded dense profile completed on physical NPU4-7 with one 32768-token
prefill request and 16-way decode. Prefill and decode each produced four rank
captures; decode coverage was exactly 30 worker iterations, including 1440
recurrent calls and 480 attention calls per rank. The profiler service was
stopped before any performance experiment.

The four-rank diagnostic means are:

- prefill direct triangular inversion: 3.61275%; perfect deletion is still
  below a 10% phase gain;
- prefill six-stage MegaGDN scope: 13.25425%; at least 3.18372x local speedup
  would be needed for a 10% phase gain;
- decode recurrent alone: 4.68675%; perfect deletion is still below 10%;
- decode shape-filtered GDN fusion seam: 14.15340%; at least 2.79680x local
  speedup would be needed for a 10% phase gain;
- decode attention: 27.40025%; decode matmul: 50.29700%.

The shape-filtered seam maps one source call chain: local Q/K/V concatenation,
convolution-weight transpose, causal convolution, mixed-QKV/gating slices,
fused gating, two Q/K normalizations, and recurrent state update. Unrelated
Slice and Transpose shapes were excluded. This is an upper-bound scope, not an
implemented mega-op or an end-to-end result.

Evidence:

- `/cache/cch/qwen36-paper-portfolio-synthesis-20260920/dense-profile-v1/profile-summary-v2.json`
- SHA256 `7d7554583eb202c26d51e946e8e3fd741e1a8578b1bba882f1af02104da06d81`
- export receipt SHA256 `87f13d128d8479b765bf97967e714718597411f835174ee4a91bdbab67a47103`

## Historical proposed self-evolution loop and closure

The paragraph below is the historical proposal at portfolio close, not an
unstarted action. The exact-semantics GDN decode mega-op was subsequently
built, passed real-NPU state/graph checks, and failed its fixed-output E2E
screen (118.455179 vs 125.819134 tok/s dense). DeltaLog v4c also passed
NPU/service gates but measured 112.424603 tok/s. Its targeted v0.2.2
selected-slot mixed-batch bridge then passed batch-1/16 eager/NPUGraph and
TP4 dispatch, yet measured 113.649628 tok/s on the same fixed-output screen.
The latter report is
`/cache/cch/qwen36-deltalog-20260920/performance-screen-v022/candidate.run1.json`
(SHA256 `5cb782eed695e56b27acd961690f4e446866be992f621f23d3e2487a3236e0d5`).
Neither implementation approaches the +10% gate; final accuracy was correctly
deferred. The fixed ten-paper queue is exhausted. HYPIC's prior +36.07%
result applies to the declared segmented shared-prefix workload and must not
be generalized to no-reuse traffic. Select any subsequent paper or cross-paper
loop only after a new workload/mechanism fit and measured opportunity gate;
first audit reusable deployed `vllm-ascend` and `ops-transformer` code.

Prototype an exact-semantics, explicit opt-in GDN decode mega-op through a
plugin monkeypatch. Before implementation, review the live `cannbot-skills`
operator-generation contract and `ops-transformer` examples. The first stop
gate is a shape/ABI feasibility audit: the candidate must cover the measured
shape-filtered seam and retain a credible route to at least 2.79680x local
speedup. Then require real-NPU multi-step state/output parity before any
profiler-disabled dense/candidate end-to-end comparison.

No new operator was generated in this synthesis stage, and cannbot was not
invoked to create one.
