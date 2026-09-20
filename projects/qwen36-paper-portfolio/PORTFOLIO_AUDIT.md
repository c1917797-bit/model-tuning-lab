# Qwen3.6-27B Ascend 10-paper portfolio audit

## Current status

The fixed 10-paper queue has been pierced. HYPIC remains the prior successful
reference for segmented prefix reuse; it is not a new result from this
workstream. Every other queue entry has a scoped evidence-backed no-go or
inapplicability decision under the current Qwen3.6/v0.23/910B/plugin contract.

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

## Next bounded self-evolution loop

Prototype an exact-semantics, explicit opt-in GDN decode mega-op through a
plugin monkeypatch. Before implementation, review the live `cannbot-skills`
operator-generation contract and `ops-transformer` examples. The first stop
gate is a shape/ABI feasibility audit: the candidate must cover the measured
shape-filtered seam and retain a credible route to at least 2.79680x local
speedup. Then require real-NPU multi-step state/output parity before any
profiler-disabled dense/candidate end-to-end comparison.

No new operator was generated in this synthesis stage, and cannbot was not
invoked to create one.
