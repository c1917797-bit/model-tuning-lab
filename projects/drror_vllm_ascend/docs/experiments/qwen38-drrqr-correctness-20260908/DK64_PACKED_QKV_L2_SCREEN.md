# Dk64 packed-QKV plus L2 screen

Date: 2026-09-11  
Status: numerical and operator-composition gates passed; rejected at the
single fixed-protocol service screen.

## Scope

This is a DRRQR energy-Dk64 decode-path adapter. It consumes the packed
causal-convolution Q/K/V tensor, writes the existing contiguous Q/K/V layout,
normalizes Q and K with FP32 square/sum/rsqrt at eps=1e-6, and preserves the
BF16 materialization boundary before the unchanged native recurrent operator.
It is not a new selector, an accuracy result, an endpoint result, or a
cross-environment performance proof.

The plugin implementation is explicitly opt-in. It admits only pure
non-speculative TP4 Dk64 decode with local geometry H_QK=4, H_V=12, Dk=64 and
Dv=128. Dense layers, prefill, mixed prefill/decode and speculative decode keep
the audited v0.23 path.

## Preserved compile failure and bounded correction

The first NPU launch failed before arithmetic execution because Ascend Triton
could not merge branch-local vectors of length 64 and 256 in one kernel. The
failure is preserved at:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-packed-qkv-l2-v1/parity-v1

The one predeclared build correction separated Q/K normalization and V copying
into two kernels without changing the formula, output layout, tolerance or
fallback. Corrected kernel SHA256:

b1f0b641c8f57648ee6cb3dffccd3b4d2bba4a0c162d9cb69728244bcf64fdae

## Exact NPU gate

The corrected run passed on container logical NPU0, externally verified as
physical NPU4. Batch 1 and 16 each ran eight changing inputs. Candidate eager
and NPUGraph Q/K/V were bitwise equal to torch.split + torch.cat + two
l2norm_fwd reference outputs, all outputs were finite and contiguous, and
graph output pointers remained stable.

Report:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-packed-qkv-l2-v1/parity-v1-fix1/report.json

Report SHA256:

2fd4133dfa00edd9f639c1d6215707656d32b88ed03eb86c128cc3ee734feaac

## Fresh-process ABBA micro screen

Two reference and two candidate processes ran in ABBA order. Each case used 20
warmups followed by seven blocks of 100 calls. Values below are the mean of the
two run-level median device-event times.

| Batch | Path | Reference ms | Candidate ms | Candidate change |
|---:|---|---:|---:|---:|
| 1 | eager | 0.569006 | 0.372724 | -34.495580% |
| 1 | NPUGraph | 0.019783 | 0.012900 | -34.794169% |
| 16 | eager | 0.665309 | 0.377429 | -43.270169% |
| 16 | NPUGraph | 0.031334 | 0.018919 | -39.620349% |

Run report SHA256 values in order:

- reference 01: 464b56a8881bde6969b67efda08aabdcfb3b398b39e84f82e2fa2ebf7d9b7c69
- candidate 02: 031c67b5c58c1a5dec8fcb4ecbee4980eb1d75991337406681f4c8c47d1f0917
- candidate 03: f8e06bb425774bfcd65788c669750621390137fd10c9b04c952140203709b49d
- reference 04: 1e810abcdbaf83c296f7a2e01d4a5dbccdaf26e6a0c8001138edf6c211aa7a4a

These percentages apply only to the isolated rearrangement-plus-normalization
composition. They must not be projected onto endpoint throughput.

## Fixed-protocol endpoint screen

The opt-in path was exercised by all four TP workers. Each worker recorded both
patch installation and execution of the
packed_qkv_l2+npu_recurrent_gated_delta_rule decode backend. The screen used
40 requests, concurrency 16, input length 32768, shared prefix 16384, fixed
output length 1024 and no profiler. All 40 requests completed with 40960 output
tokens.

| Metric | Frozen dense | Prior energy-Dk64 | Packed-QKV/L2 |
|---|---:|---:|---:|
| Output throughput (tok/s) | 135.142470 | 141.564496 | 140.583188 |
| Mean TTFT (ms) | 34693.578 | 33468.964 | 34414.993 |
| Mean TPOT (ms) | 69.436227 | 66.689384 | 66.538082 |

The candidate is 4.025913 percent above the frozen dense baseline but 0.693188
percent below the prior comparable energy-Dk64 screen. Its TPOT is 0.226875
percent better than the prior Dk64 result, while TTFT is 2.826587 percent worse;
the net endpoint result therefore does not promote. It remains 8.073529 tok/s,
or 5.742883 percent relative, below the fixed 148.656717 tok/s acceptance
target.

Performance report:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/dk64-packed-qkv-l2-v1/service-candidate-v2/performance.run1.json

Performance report SHA256:

8b22c609f1470ef6e62d8c3397143740e8eea0be374a1bad994335d2dc51edb8

The new and prior Dk64 service logs both contain the same message about
skipping the persistent npugraph_ex cache for graphs containing Triton
kernels. It is therefore not candidate-specific evidence and does not explain
the regression. The supported interpretation is narrower: the isolated
composition improved substantially, but its endpoint cost share was too small
to overcome TTFT and whole-service costs.

After measurement the exact service process group was terminated. The
dedicated container retained only its idle shell, and npu-smi reported no
running processes on NPU0-7.

## Decision

Reject this packed-QKV/L2 implementation at the single endpoint screen and do
not spend repeats, profiling or accuracy budget on it. This rejects the tested
implementation, not DRRQR. The next loop must target a materially larger native
Ascend seam spanning packed QKV normalization, gating and recurrent state
traffic, and must establish a static endpoint-share case before implementation.
Final accuracy remains deferred until a performance candidate is promoted.
