# DASC paper-to-Ascend method parity

Status date: 2026-09-16

Paper: [arXiv:2608.30386v1](https://arxiv.org/abs/2608.30386)

## Provenance boundary

The arXiv record and paper do not link a first-party source repository. Exact
title, arXiv-id, and algorithm-term GitHub searches found no author release as
of the status date. The code under `projects/dasc_vllm_ascend` is an
independent implementation from the paper specification and the pinned
vLLM/vLLM-Ascend runtime. It is not official author code.

If author code appears, record its repository URL and immutable commit here,
then replace inference-based entries with file/function/output comparisons.

## Mechanism matrix

| Paper mechanism | Paper specification | Current Ascend implementation | Evidence/gate | Status |
| --- | --- | --- | --- | --- |
| GDN static decay | `g=-exp(A_log)*softplus(a+dt_bias)`, `a=-0.3` | Same formula in `selector.head_horizons` | Independent Python-scalar reference agrees for FP32 and BF16 source parameters | Synthetic reference gate passed |
| Retention horizon | `H_s=ln(epsilon)/g`, `epsilon=1e-3` | Same formula and default constants | Near-threshold selection is checked against the independent scalar result | Synthetic boundary/dtype gate passed |
| GDN selection | Retain full head state when `H_s>W_max` | `retained_head_indices` | All 48 raw checkpoint layers match the independent scalar indices and the architecture manifest at `W_max=64` | Real-weight gate passed |
| DASC-NR load | Restore retained units; omitted units start at zero only on cache-hit Load, then accumulate normally while the request remains active | v12r6 is superseded; the plugin now assigns stable request-owned dense slots, exposes compact tensors to scheduler copy outside the native call, and preserves omitted units across synthetic decode/block transitions | Pinned-image lifecycle tests pass; multi-step NPU equality/finite-state gate remains | Framework integration implemented; NPU gate incomplete |
| Physical checkpoint | Ragged flat-pack with per-layer offsets | Heterogeneous per-layer Mamba specs aggregated into one vLLM physical group | Physical bytes and cache-capacity verifier | Different representation; v12r7 NPU gate pending |
| TP compute placement | Model-load permutation of coupled tensors | No weight/head permutation | Exact permutation and output-equivalence test | Missing |
| TP storage balance | Shared TP pool with variable-split all-to-all on Store and inverse on Load | Per-layer MAX retained count; each rank pads with its next-longest heads | Raw TP4 audit: 1728 threshold-retained heads become 2084 physically stored heads; whole-GQA-group optimal placement would reduce that bound to 1828 | Not equivalent; measured capacity loss and quantified adaptation bound |
| Full-attention KV | Unchanged | Intended unchanged; synthetic mixed group currently affects runner metadata | Dense/candidate metadata and graph-capture comparison | Not yet proved |
| Convolution state | Stored uncompressed in BF16 | Kept dense with native lifecycle | Prefix copy/invalidation and byte accounting | Implemented |
| Temporal state | Stored in FP32 | Compact persistent FP32, dense active FP32 workspace | ABI, restore/checkpoint, and byte gates | Implemented, graph gate incomplete |
| DASC-WR | Replay bounded suffix and copy refreshed omitted units | Not implemented | Replay-length and accuracy/latency tests | Missing |
| Serving framework | SGLang radix-cache integration | vLLM/vLLM-Ascend plugin monkeypatch | Runtime source hashes and activation evidence | Intentional platform adaptation |

## Equivalence claims allowed now

- Allowed: paper-derived GDN horizon selector; DASC-NR-inspired Ascend
  adaptation; plugin activation and physical allocation evidence for named
  immutable attempts.
- Not allowed: official DASC implementation; exact paper reproduction;
  paper-equivalent TP balancing; paper performance reproduction; end-to-end
  accuracy equivalence.

## TP4 capacity audit

The immutable raw-weight audit at
`/cache/cch/dasc-qwen36-ascend-20260915/selector-manifest-v3.json`
passed all 48 GDN layers. Its SHA256 is
`c474ff65baef39c41944da0a6027eaf5ab69805a55d23db00e1dca3b2fff1f8d`.
An independent second run produced a byte-identical file and hash. Version 3
supersedes version 2 by adding the Qwen GQA coupling constraint; it does not
replace or erase the older immutable artifact.

A separate standard-library verifier used unlabeled-bin dynamic programming,
not the manifest generator's backtracking search, to recompute all 48 optima
and validate every assignment and aggregate. Its immutable output is
`/cache/cch/dasc-qwen36-ascend-20260915/selector-manifest-v3.verify.json`
with SHA256
`15fdf0745e425b16b6311a794a66734d25a3a82e780bf14216201cc345fe3aa0`.

At `W_max=64`, the paper threshold retains 1728 of 2304 global temporal
heads (1.33x temporal-only compression). The current layerwise TP-MAX padding
stores 2084 heads (about 1.11x), an overhead of 356 heads. It therefore
realizes only 220 of the 576 possible head removals. This is a measured
adaptation tax, not a paper limitation, and makes rank-balanced placement or
paper-equivalent variable-split storage a priority if v12r7 proves runtime
correct but shows weak capacity/performance benefit.

There are three distinct storage bounds:

- Paper variable-split Store/Load: 1728 heads, with no equal-rank-width
  padding in this accounting.
- Arbitrary per-head equal-rank placement: 1788 heads, a mathematical lower
  bound that ignores Qwen's three-V-heads-per-Q/K-group coupling.
- Whole-GQA-group TP4 placement: 1828 heads. The exact solver assigns all 16
  groups, four groups per rank, and minimizes the maximum retained V-head load
  independently in every layer.

The group-constrained result removes 476 heads and recovers 256 of the current
356 padded heads, for about 1.26x temporal-only compression. It is the relevant
model-load permutation bound for a design that keeps each Q/K head colocated
with its three V heads. It is not yet an implementation result: A_log,
dt_bias, Q/K/V/Z and B/A projection slices, convolution channels, and output
projection columns must be permuted consistently, then checked for dense-output
equivalence and runtime overhead.

## Required closure gates

1. Keep the completed independent equations 2-3 gates: FP32/BF16 synthetic
   threshold tests and the 48-layer raw-safetensor TP4 manifest audit.
2. After v12r7 passes, choose between the quantified whole-GQA-group
   permutation bound (1828 heads) and exact paper variable-split storage
   (1728 heads). Keep the per-head 1788 result labeled as an unattained lower
   bound, not an implementation target.
3. Prove full-attention KV metadata is unchanged despite the mixed physical
   group before another service launch.
4. Request-owned dense active slots and synthetic omitted-unit continuity are
   implemented. Next pass Ascend graph capture, strict prefix-hit canary,
   multi-step recurrent-state checks, and physical-byte verification.
5. Only then run matched dense/candidate performance and final E2E quality
   evaluation.
