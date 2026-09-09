# t13 dense-tail opportunity budget

This checkpoint narrows Candidate B from `T13_CANDIDATE_PLAN.md` using the
existing four-rank round0 msprof evidence. It is an offline feasibility result,
not a performance win and not authorization to start an NPU workload.

## Frozen task boundary

- Qwen3.5-27B, BF16, TP4/DP1, Ascend 910B4.
- MTP/speculation, quantization, and retraining remain forbidden.
- Final delivery remains a removable runtime plugin plus, only if justified, a
  read-only custom OPP.
- Acceptance remains TTFT P95 at least 40% lower and TPOT P95 at least 20%
  lower in every c1/c5/c8/c16 cell versus the frozen TP4 MTP-off
  `query_rewrite` denominator, with zero material quality regressions.

## Evidence

Input profile:

`/cache/austinov/qwen35-cannbot-round0-msprof-control-20260909T092151Z`

The analyzer intentionally counts only the non-overlapping top-level `SwiGlu`
and `MatmulAllReduce` rows. It excludes `MatmulAllReduceMc2AicpuKernel`, because
prior timeline analysis proved that its duration overlaps the top-level MMAR
interval and cannot be added as removable wall time.

Run:

```sh
python3 qwen35-performance-optimization/scripts/analyze_qwen35_dense_tail_budget.py \
  /cache/austinov/qwen35-cannbot-round0-msprof-control-20260909T092151Z \
  --required-chain-speedup 1.15
```

The profile contains exactly 6,720 M=1 K4352 MMAR calls per rank, which is
105 decode steps x 64 dense-layer tails. Across those steps:

- max-rank K4352 MMAR time is about 5.951 ms/decode step;
- max-rank standalone SwiGLU time is about 0.282 ms/decode step;
- the stock `SwiGLU -> K4352 MMAR` chain is about 6.232 ms/decode step on the
  slowest rank;
- completely deleting the standalone SwiGLU cost would improve that chain by
  only about 1.047x, below Candidate B's predeclared 1.15x microbenchmark gate;
- reaching 1.15x therefore requires roughly another 0.53 ms/decode step, or
  about 8.3 us per layer call, from the device-side activation-consumption /
  MMAR boundary in addition to eliminating the visible activation cost.

## Decision

**Do not implement an activation-only Python monkeypatch.** The official
vLLM-Ascend 0.23.0 path already dispatches `SiluAndMul` to
`torch_npu.npu_swiglu` and performs down-weight prefetch around it. Torch-NPU
does not expose an output/in-place form that would let the runtime plugin erase
the intermediate boundary without a device-side implementation.

The local `ops-transformer` 9.1.0 checkout contains an Ascend-910B CI-covered
`experimental/ffn/swiglu_gated_mlp`, but it fuses local matmuls and SwiGLU; it
does not fuse the TP4 final all-reduce. Substituting it and then doing a
separate all-reduce would repeat the already-rejected MMAR decomposition, where
the official fused MMAR was roughly 2x faster for the real M=1 shapes.

Follow-up timestamp pairing closes that boundary-only route. Every one of the
6,720 M=1 `SwiGlu` rows per rank was paired to the immediately following M=1
K4352 `MatmulAllReduce` row. The observed gap is only about 1.30-1.31 us/layer
on average, with p50 1.25 us, p95 about 1.5-1.75 us, and a maximum of 3.0 us.
Across 64 layers this is only about 83-84 us/decode step, far below the roughly
0.53 ms/decode step extra saving required by the 1.15x chain gate.

Therefore **reject a boundary-only custom OPP before implementation**. A future
dense-tail operator would have to materially reduce MMAR-side device work, not
just erase the activation-to-MMAR dispatch gap.

The previously measured local fused-FFN prototype is also insufficient as the
main money patch: 197.9728 -> 180.2859 us saves 17.6869 us/layer, or about
1.132 ms/token across 64 layers. Against the latest c1 control TPOT of 31.754
ms, a 20% target requires about 6.351 ms/token of saving, so that local fusion
covers only about 17.8% of the required reduction. It remains a possible
stackable micro-optimization, not the primary candidate.

Source inspection also closes the obvious HCCL-server shortcut: on A2/
Ascend 910B4, MatmulAllReduce V1/V2/V3 all select the AICPU HCCL server; CCU
selection is gated to the A5/dav-3510 path. V2 adds x3 and V3 adds commMode,
but neither supplies a different supported 910B4 server lifecycle. The x3
route was already rejected by measured evidence.

NPU0-3 were observed process-free during this checkpoint, but the workstream
handoff still requires a valid lease. No model service or NPU benchmark was
started from this evidence-only stage.
