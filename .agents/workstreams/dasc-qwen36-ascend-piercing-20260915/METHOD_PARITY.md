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
| GDN static decay | `g=-exp(A_log)*softplus(a+dt_bias)`, `a=-0.3` | Same formula in `selector.head_horizons` | Independent scalar/tensor reference tests required | Implemented, reference gate incomplete |
| Retention horizon | `H_s=ln(epsilon)/g`, `epsilon=1e-3` | Same formula and default constants | Boundary and dtype tests required | Implemented, reference gate incomplete |
| GDN selection | Retain full head state when `H_s>W_max` | `retained_head_indices` | Existing selector tests plus model count manifest | Implemented |
| DASC-NR load | Restore retained units; omitted units start at zero only on cache-hit Load, then accumulate normally while the request remains active | v12r6 is superseded; the plugin now assigns stable request-owned dense slots, exposes compact tensors to scheduler copy outside the native call, and preserves omitted units across synthetic decode/block transitions | Pinned-image lifecycle tests pass; multi-step NPU equality/finite-state gate remains | Framework integration implemented; NPU gate incomplete |
| Physical checkpoint | Ragged flat-pack with per-layer offsets | Heterogeneous per-layer Mamba specs aggregated into one vLLM physical group | Physical bytes and cache-capacity verifier | Different representation; graph capture failing |
| TP compute placement | Model-load permutation of coupled tensors | No weight/head permutation | Exact permutation and output-equivalence test | Missing |
| TP storage balance | Shared TP pool with variable-split all-to-all on Store and inverse on Load | Per-layer MAX retained count; each rank pads with its next-longest heads | Rank payload and communication trace | Not equivalent |
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

## Required closure gates

1. Add an independent reference implementation for equations 2-3 and threshold
   boundaries; compare retained indices bit-for-bit on synthetic and real
   layer snapshots.
2. Decide explicitly whether exact paper TP balancing is required. If adapted,
   quantify its capacity loss relative to ragged shared-pool placement and
   label the variant.
3. Prove full-attention KV metadata is unchanged despite the mixed physical
   group before another service launch.
4. Integrate request-owned dense active slots so DASC-NR zero-fill occurs only
   at a true prefix-checkpoint Load. Prove omitted-unit continuity across
   decode steps and scheduler block transitions, then pass Ascend graph
   capture, strict prefix-hit canary, multi-step recurrent-state checks, and
   physical-byte verification.
5. Only then run matched dense/candidate performance and final E2E quality
   evaluation.
