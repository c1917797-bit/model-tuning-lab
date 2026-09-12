# T20 bounded-prefill runtime-monkeypatch findings

## Decision

Retain bounded-prefill decomposition as a TTFT component, but do not promote
T20 as the final candidate. The c1 fail-fast gate passed TTFT and failed TPOT,
so the next candidate must stack an independently measured decode treatment.

## Exact runtime evidence

- Artifact root:
  `/cache/austinov/qwen35-t20-candidate-prefill-20260911`.
- Official image:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Runtime form: removable Python monkeypatch; no vLLM/vLLM-Ascend source
  overlay, no custom image, no custom operator OPP mount.
- Devices: physical NPU0-3 only, TP4 BF16. Physical NPU4-7 were not mounted.
- Activation report SHA256:
  `8f8e6ec88ae7423892b2708c2f3bcbfaa5f285486e656896a2b40a3009e0f850`.
- Smoke SHA256:
  `38ba686f2db194ebbf4b545969b37b8097085ecaa18c25648ddfc74e8c4ec0c7`.
- Warmup c1/32 SHA256:
  `afea58cc2a470f8517aa65c0838a8f7439d1b9d31288fcc3ab129dfd558a42b8`.
- Measured c1/32 SHA256:
  `25567805ce1916ac8184f81c1eadb3b8485d235a279ee4f26730b28fd9fbe00a`.
- Pair-decision SHA256:
  `adcdf1b5aff9d490a333a1a393b909c3aab4df960dbd1089ed79975dc2fa5b2e`.

The measured candidate completed 32/32 requests with zero errors and natural
EOS. Its TTFT P95 was 808.224 ms and TPOT P95 was 28.282 ms. Against the
identity-matched control at 6310.576 ms and 29.107 ms, TTFT improved 87.193%
and TPOT improved 2.835%. The standardized decision is `iterate`: TTFT meets
the corrected >=20% gate; TPOT misses the corrected >=10% gate. Response hashes matched 14/32, so
the required all-357 paired semantic gate remains outstanding for any final
stack.

The 32-request warmup completed with zero errors and natural EOS. Its TTFT
P95 was 5828.262 ms because previously unseen prefill shapes still compiled;
it is stabilization evidence, not a performance claim. The separate measured
run used a new cache salt after this warmup.

## Upstream-first decode boundary

The upstream audit is pinned to:

- vLLM-Ascend main
  `1b1709b9227ad3e0db2d82b9231c4962919b86f5`;
- CANN ops-transformer master
  `d967eeb08ceef7c394d0d5e27767e5b08b77aa58`.

ops-transformer already provides
`experimental/ffn/swiglu_gated_mlp`, which computes
`gate_up MatMul -> SwiGLU -> down MatMul`, supports BF16 and Atlas A2/910B,
and therefore is the required starting point for the dense decode candidate.
Do not independently implement that chain.

This upstream operator does not include TP AllReduce. The upstream
`aclnnMatmulAllReduceV3` supports Atlas A2 and TP sizes 1/2/4/8, but A2
restricts `commMode` to `ai_cpu`. The next admission must measure the
composition of the upstream fused MLP compute path with the existing TP
collective, and must not claim a single upstream full-chain operator exists.

The unchanged vLLM-Ascend v0.23.0 image does not contain
`aclnnSwigluGatedMlp`. If the exact upstream operator is evaluated, build it
from the pinned ops-transformer source into a minimal read-only OPP bundle and
load it only through the runtime monkeypatch launcher. Do not use the earlier
diagnostic bundle containing `libopapi_math.so`; that extra runtime library
previously shadowed packaged dependencies.

## Next gate

Before service integration, benchmark exact Qwen3.5 TP4 BF16 decode shapes and
require correctness plus enough dense-tail critical-path reduction to cover
the remaining c1 TPOT gap. Reuse the upstream SwiGLU gated MLP source and the
existing collective path; add only a compatibility adapter in the runtime
monkeypatch. A result below the preregistered whole-chain threshold is rejected
without another service matrix.
