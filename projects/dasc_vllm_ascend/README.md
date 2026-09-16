# DASC vLLM-Ascend Plugin

This project is the plugin-owned implementation area for the DASC
Qwen-GDN/Ascend piercing workstream.

The first implementation is deliberately a **numerical canary**. On a genuine
Mamba/GDN prefix-cache restore, it keeps the convolution state dense and copies
only weight-selected long-horizon temporal heads into the new running-state
block. Omitted temporal heads are zero-filled (DASC-NR semantics).

It does not yet reduce the physical cache page size. Therefore this version
must not be used to claim cache-capacity, TTFT, throughput, or paper-level
performance gains.

## Opt-in contract

The plugin is disabled by default. The initial canary requires these environment
values: MST_DASC_ENABLE=1, MST_DASC_MODE=nr-numerical,
MST_DASC_W_MAX=64, an absolute MST_DASC_EVIDENCE_PATH, and
VLLM_PLUGINS=dasc_vllm_ascend.

The implementation fails closed on unsupported versions, source identity,
cache mode, state shape, or worker dispatch. Evidence is written outside Git.

## Ascend mechanism canary result (2026-09-15)

On Qwen3.6-27B, TP4, vLLM/vLLM-Ascend v0.23.0, and physical Ascend
NPU4-7, a 2,350-token shared-prefix pair produced one 1,536-token local cache
hit. All four TP workers executed the patched restore path for all 48 GDN
layers (192 `prefix_temporal_restore` events). The candidate and disabled
control produced identical sampled 16-token continuations.

The paired reuse request took 4.213 s with the numerical canary and 4.008 s
with the plugin disabled: the canary was 5.095% slower. This is an expected
negative result for a dense-storage implementation that adds restore masking.
It proves reachability, not performance. The next performance-bearing
milestone is compact retained-head checkpoint storage with dense active
workspace expansion at restore time, followed by capacity and steady-state
A/B measurements.

Raw runtime evidence remains outside Git under
`/cache/cch/dasc-qwen36-ascend-20260915/`.

An experimental `MST_DASC_MODE=physical-cache-eager` path is implemented.
It changes every loaded GDN layer's MambaSpec to its heterogeneous compact
temporal shape, keeps runner-owned compact tensors authoritative for block
copy and invalidation, and expands active blocks into fixed dense workspaces
around the native Ascend core. This mode is eager-only until graph capture has
its own pointer and replay gate. It has not yet passed NPU or end-to-end
validation and must not be used for a performance claim.

## Physical-cache integration status (2026-09-16)

A stopped same-configuration dense-control container was recovered and audited.
Its immutable metadata proves the pinned image, physical NPU4-7 mapping, exact
serve arguments, and absence of a DASC source/plugin mount. Its retained Docker
log proves completion of all five `FULL_DECODE_ONLY` graph captures, server
readiness, ACL-graph replay, and one successful HTTP 200 completion request.
The client response body was not retained, so the earlier exact-`OK` claim is
withdrawn as unverified. Physical attempt v12r4 also proved plugin discovery and real DASC
activation on all four TP ranks: the heterogeneous group, TP-aligned geometry,
worker dispatch, Mamba lifecycle, and twelve compact physical cache bindings
were recorded. It then failed during graph capture in Ascend FIAS's no-RoPE
TND path because head dimension 256 is unsupported.

This result disproves the earlier conclusion that merely preserving a
Mamba-first model order fixes the dispatch. vLLM-Ascend v0.23 treats a
`UniformTypeKVCacheSpecs` group as one type by inspecting its first inner
spec. A DASC aggregate is intentionally mixed, so neither globally
attention-first nor Mamba-first ordering is a correct execution contract.
The successor keeps the authoritative model/storage order and adapts only the
runner's input-batch initialization view so attention slot mapping is derived
from an `AttentionSpec`; Mamba copy/invalidation remains independently
filtered to Mamba layers. That successor passed 97 no-device tests, but v12r5
proved it was a no-op at runtime: the aggregate already had an attention layer
first on every rank, and the same FIAS failure remained. The adapter is retired
from the active tree; commit `373b448` and the immutable v12r5 artifacts retain
the negative result.

## Provenance and paper parity

No first-party implementation repository was linked from arXiv or the paper,
and exact-title/algorithm GitHub searches found no author release as of
2026-09-16. This plugin is therefore an independent, paper-derived
DASC-NR/Ascend adaptation, not the authors' official code.

The weight-only GDN horizon formula, constants, head-wise threshold selection,
and zero-fill load policy follow the paper. The current implementation is not
yet method-chain equivalent to the paper's SGLang prototype: it does not
implement model-load head permutation, variable-split all-to-all TP storage
balancing, the exact ragged flat-pack layout, or DASC-WR suffix refresh. See the
workstream `METHOD_PARITY.md` for the executable parity contract. Until those
gaps are closed or explicitly scoped out, results must be labeled as an
Ascend adaptation rather than an exact paper reproduction.
