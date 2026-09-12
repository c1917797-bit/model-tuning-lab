# Round0 performance breakdown: Qwen3.5-27B TP4 on Ascend 910B4

## Status and evidence boundary

This is a bounded, analysis-only CANNBot profile-analyzer report. It uses the
already captured four-rank native msprof data and frozen operator artifacts;
it did not start or modify containers and did not use an NPU.

Evidence:

- Control profile:
  `/cache/austinov/qwen35-cannbot-round0-msprof-control-20260909T092151Z`
- Official MMAR component artifact:
  `/cache/austinov/qwen35-mmar-components-official-20260909T103515Z/components.json`
- Fresh GDN microbenchmark:
  `/cache/austinov/qwen35-gdn-projection-fusion-fresh-20260909T104335Z/gdn_projection_fusion.json`
- Component artifacts identify the official image as
  `quay.io/ascend/vllm-ascend:v0.23.0`, image ID
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
  BF16 TP4 on physical NPU0-3, with runtime patch disabled.

The profile directory itself has no complete provenance/SHA manifest, so it
must not yet be promoted as a final current-control denominator. This report
also does not claim a full interactive CANNBot structure-decomposition run;
the user supplied a fixed bounded breakdown scope.

## Method

The two non-unit MMAR shapes delimit prefill: `M=1536` and `M=274`.
After the second prefill interval, the capture contains 104 steady decode
tokens. Each token has 64 calls of each decode MMAR shape, or 128 MMAR calls
in total.

Device intervals were unioned by rank, stream, shape, and phase. Percentages
below are overlap views and are **not additive**. In particular, the AICPU
MMAR interval contains the AI Core MMAR interval; adding the two would double
count the same wall time. Host API entries were kept separate from device
execution.

## Decode breakdown

The rank-0 steady decode window is 3072.556 ms for 104 tokens
(29.54 ms/token). Other ranks have comparable wall windows; max-rank values
are used where a single value is needed.

| Overlapping category | Rank-0 interval union | Decode-window share | Approx. per token |
|---|---:|---:|---:|
| MMAR AICPU envelope | 2.915 s | 94.8% | 28.0 ms |
| Other MatMul | 1.457 s | 47.4% | 14.0 ms |
| MMAR AI Core | 0.975 s | 31.7% | 9.38 ms |
| Other device work | 0.373 s | 12.1% | 3.59 ms |
| GDN-labelled recurrent kernels | 0.0915 s | 3.0% | 0.88 ms |
| Attention | 0.0366 s | 1.2% | 0.35 ms |

The largest named rank-0 decode tracks are MMAR AICPU (stream 72,
2.913 s/13,312 calls), MatMulV2 (stream 71, 1.365 s/18,302 calls), and
MMAR AI Core (stream 71, 0.975 s/13,312 calls). These overlap substantially.

### Decode MMAR by rank and shape

| Shape | AICPU median across ranks | AI Core median across ranks | p95 AI Core range | Median launch offset | Effective envelope |
|---|---:|---:|---:|---:|---:|
| M1 K1536 N5120 BF16 | 203.0-204.5 us | 51.25-53.5 us | 57.75-60.25 us | 145.5-148 us | 203.0-204.5 us |
| M1 K4352 N5120 BF16 | 236.75-238.0 us | 92.0-92.5 us | 95.75-98.5 us | 140.25-140.75 us | 236.75-238.0 us |

The AI Core interval is fully contained in the AICPU interval for these
paired calls. Cold maxima inflate whole-capture means (up to 2.153 ms), so
steady medians/p95 are the useful decode measures.

Internal metrics support a lifecycle/data-movement diagnosis rather than a
compute-bound diagnosis. For K1536 the median MAC time is about 1.56 us
(3.4-3.5% of reported AI Core time); for K4352 it is about 4.41 us
(5.1-5.2%). MTE/scalar and collective lifecycle dominate. The reported
`cube_utilization` is not a theoretical-efficiency result.

## Prefill breakdown and rank skew

The most important TTFT finding is a severe rank/shape asymmetry.

| Prefill shape | Rank 0 AI Core median | Rank 1 | Rank 2 | Rank 3 |
|---|---:|---:|---:|---:|
| M1536 K1536 | 7131 us | 552.5 us | 7040.6 us | 7118.8 us |
| M1536 K4352 | about 660 us | about 660 us | about 660 us | about 662 us |
| M274 K1536 | 8101 us | 153.1 us | 8083 us | 8090 us |
| M274 K4352 | 568.6 us | 233.25 us | 577.0 us | 578.6 us |

For rank 0, the M1536 prefill wall/device-union is 556.870/556.866 ms:
MMAR AICPU unions to 554.436 ms, MMAR AI Core to 407.643 ms, and other
MatMul to 69.072 ms. For M274 the corresponding wall/device-union is
531.492/531.492 ms, with MMAR AICPU 531.484 ms and MMAR AI Core 465.852 ms.
These are overlapping unions.

Rank 1's device union is only about 273.9 ms for M1536 and 93.6 ms for M274
inside comparable phase wall windows. On the slow K1536 ranks, MAC time is
only about 91 us (M1536) or 18 us (M274) while the reported AI Core interval
is 7-8 ms. The long interval is therefore synchronization/communication
waiting, not useful MatMul compute. This rank skew is the primary TTFT
diagnostic and should be explained before changing a kernel.

## Isolated component evidence

The official component protocol used 40 warmups, 200 measured iterations,
seven repeats, and the max-rank median.

| Shape | MatMul-only | MatMul + standalone AllReduce | Official fused MMAR | Fused saving vs serial |
|---|---:|---:|---:|---:|
| M1 K1536 N5120 | 25.0362 us | 186.5505 us | 85.6646 us | 100.886 us (54.1%) |
| M1 K4352 N5120 | 22.6590 us | 179.7428 us | 87.1936 us | 92.5492 us (51.5%) |

Correctness against the serial reference was bounded by max absolute error
2.0 and relative L2 0.00303/0.00362 for the two shapes.

The fresh GDN projection-fusion microbenchmark measured separate versus
fused BF16 projections at M=1/5/8/16. Speedups were
2.9645x/2.9465x/2.9318x/2.9609x (geometric mean 2.9509x), with max absolute
error no greater than 0.0002442. At M=1 it saves about 67.44 us per GDN
layer. With 48 GDN layers per decode token, 3.24 ms/token is an empirical
upper-level estimate, not guaranteed end-to-end savings. It must not be
extrapolated to prefill M274/M1536.

## Measured and theoretical gaps

| Comparison | K1536 | K4352 | Interpretation |
|---|---:|---:|---|
| Full-model decode envelope / isolated official fused | 2.387x | 2.730x | Full model adds 118.84/150.81 us per call |
| Full-model decode envelope / isolated MatMul-only | 8.17x | 10.50x | Empirical lower reference, not theory |
| Official fused / isolated MatMul-only | 3.42x | 3.85x | Collective/lifecycle cost remains |
| Measured / theoretical | missing | missing | No supported theoretical artifact |

A reliable roofline/theoretical gap cannot be calculated from this capture.
`operator_analysis.csv`, a supported chip-configuration output, and a
reliable HCCL topology/bandwidth model are missing. No BF16 peak or bandwidth
number is inferred. Timeline `hcom_allReduce_` events are nonstationary
initialization/explicit collectives and are not shape-linked decode
AllReduce-only measurements; the frozen component artifact is used instead.
Host `aclnnMatmulAllReduce` API entries occur only for the 256 prefill
calls, while decode is task-queue/replay, so host API totals are not charged
per decode token.

## Conclusions and minimum next gates

1. **P0 TTFT diagnosis:** instrument phase/rank/topology/algorithm selection
   around prefill K1536 and explain why ranks 0/2/3 spend 7-8 ms while rank 1
   spends 0.15-0.55 ms. Require a matched four-rank profile and reduction of
   the max-rank envelope before any promotion.
2. **P0 TPOT candidate:** target the full-model MMAR AICPU
   init/finalize/IPC/queue lifecycle, not just the AI Core kernel. Keep the
   official registered MMAR path and compare paired per-shape envelopes.
3. **P1 GDN candidate:** projection fusion is strongly validated as an
   isolated small-M operator optimization, but its estimated 3.24 ms/token
   alone does not prove the 20% TPOT target and does not address prefill.
4. Run exact-image control/candidate profiles with identical requests and
   four-rank phase markers. Gate first on correctness and M=1 component
   envelopes, then c1/c16 fail-fast, then the complete c1/c5/c8/c16
   three-repeat P95 matrix. Never sum overlapping timeline categories.
5. Add a profile provenance/SHA manifest and supported theoretical-analysis
   artifacts before treating round0 as final or reporting a theoretical gap.

No product/plugin code change is recommended from profile evidence alone.
