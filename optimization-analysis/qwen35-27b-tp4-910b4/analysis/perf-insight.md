# Qwen3.5-27B TP4/910B4 performance candidate insight

## 1. Decision boundary

This is a CANNBot candidate-source record, not a passed Plan and not a
performance claim. It was produced from existing, read-only evidence; no NPU or
container was used and no product/plugin code was changed.

The applicable target is the unchanged official vLLM-Ascend 0.23.0 image,
Qwen3.5-27B BF16, TP4/DP1 on physical NPU0-3. A deliverable must remain an
independent pip-installable runtime plugin, injected from a read-only mount
through `PYTHONPATH`; an optional custom OPP may only be mounted read-only and
selected through process environment set before workers start. The plugin may
not replace vLLM/vLLM-Ascend source or site-packages in the image.

The currently verified round0 timeline and component evidence is sufficient to
exclude several ideas, but `progress.md` and `scenario.md` still describe
the formal `model-infer-perf-breakdown` as pending. Therefore every candidate
below is provisional until that breakdown is recorded. No
`plan-dashboard.md` should be initialized from this file alone.

## 2. Evidence used

- Workstream HANDOFF:
  `.agents/workstreams/exp-20260904-qwen35-query-rewrite-3x-e2e/HANDOFF.md`.
- Round0 four-rank timeline:
  `/cache/austinov/qwen35-cannbot-round0-timeline-20260909-v1.json`,
  SHA256 `32239a5d4e40a3541012015b921e213f12e5c77903c340b581245404946a2e77`.
- Official MMAR component breakdown:
  `/cache/austinov/qwen35-mmar-components-official-20260909T103515Z/components.json`,
  SHA256 `69fab79b24cc607c52129a1948ef03c49b7227174d3a335ed559b4502ff8d117`.
- Fresh GDN projection microbenchmark:
  `/cache/austinov/qwen35-gdn-projection-fusion-fresh-20260909T104335Z/gdn_projection_fusion.json`.
- t12 standalone control/candidate:
  `/cache/austinov/qwen35-gdn-runtime-t12-control-standalone-20260909T110844Z`
  and
  `/cache/austinov/qwen35-gdn-runtime-t12-candidate-standalone-20260909T1127Z`.
- Runtime source contract:
  `qwen35-performance-optimization/runtime-monkeypatch/check_official_image_source_contract.py`.
- CANNBot instructions:
  `model-infer-fusion/SKILL.md` and
  `model-infer-parallel-analysis/SKILL.md`.

The material observations are:

1. Decode M=1 row-parallel shapes are exactly K1536/N5120 and
   K4352/N5120. Their cross-rank launch-start p95 is only 12.120 us and
   8.050 us respectively.
2. Official fused MMAR takes 85.66455 us (K1536) and 87.1936 us (K4352),
   while ordinary matmul plus all-reduce takes 186.5505 us and 179.7428 us.
   Decomposing the official op is therefore closed.
3. Prefill K1536 MMAR shows millisecond-scale arrival skew: p95 6929.155 us
   for M1536 and 8163.175 us for M274, while ranks finish within roughly
   4-6 us. This points upstream of the collective, not to decode launch skew.
4. Fusing GDN qkvz and ba projections is still a valid primitive:
   2.950886x geometric-mean speedup over M1/M5/M8/M16 with zero or tiny
   max-absolute difference.
5. That primitive did not translate into the current service target. t12
   c1/32 changed TTFT P95 6502.636 -> 5697.694 ms (-12.38%) and TPOT P95
   31.754 -> 31.641 ms (-0.36%). It also produced only 16/32 byte-identical
   response hashes, so it is neither a performance nor a quality promotion.

## 3. Current runtime patch: real coverage and gaps

The t12 runtime plugin currently patches these exact seams:

- `vllm/model_executor/layers/mamba/gdn/qwen_gdn_linear_attn.py::
  QwenGatedDeltaNetAttention.__init__`: constructs
  `MergedColumnParallelLinear(...in_proj_qkvzba)`.
- `vllm/model_executor/models/qwen3_5.py::Qwen3_5Model.load_weights`:
  maps six checkpoint shards into the fused projection.
- `vllm_ascend/ops/gdn.py::AscendGatedDeltaNetAttention.forward`:
  consumes the fused qkvzba output.
- `vllm_ascend/ops/weight_prefetch.py::WeightPrefetchMethod.
  _maybe_prefetch_mlp_gate_up_weight_preprocess` and
  `vllm_ascend/ops/layernorm.py::AscendGemmaRMSNorm.forward_oot`:
  linear-attention gate/up prefetch lifecycle.
- Optional diagnostics wrap
  `vllm.v1.core.sched.scheduler.Scheduler.schedule` and
  `vllm_ascend.core.dyntra_lb_scheduler.DyntraLBScheduler.schedule`.

It does **not** change
`vllm_ascend/ops/linear.py::AscendRowParallelLinear.forward`,
`vllm_ascend/ops/linear_op.py::_get_row_parallel_op`, or
`MatmulAllreduceRowParallelOp.apply_impl`; both K1536 and K4352 still call
the official `torch_npu.npu_mm_all_reduce_base`. It also does not fuse the
GDN post-core norm/gate with the output projection, the dense SwiGLU with
down projection, or the GDN prefill core. These are the only remaining seams
considered below.

## 4. Parallel-strategy conclusion

Keep TP4/DP1 with the same four-rank HCCL group. Qwen3.5-27B is dense; its
64-layer row-parallel hot path contains approximately 64 K1536 projections
(48 GDN output projections plus 16 full-attention output projections) and
64 K4352 dense down projections per decode token. Reducing TP degree would
increase per-rank weight/capacity pressure and changes sharding and boundary
communication.

TP2/DP2 and TP2/PP2 have already failed capacity or c1 gates in this
workstream. A module-specific TP/CP/KVP change would require weight/group
repartitioning outside the removable runtime-plugin boundary. Therefore no
parallel-config change is a candidate for this round.

## 5. Mandatory attribution before implementation

Before generating an operator, augment the existing privacy-safe diagnostics
only enough to correlate one c1 and one c16 control profile:

- scheduler wall time and prefill/decode scheduled-token counts from the two
  `schedule` seams above;
- begin/end device timestamps around GDN core, GDN terminal norm+projection,
  dense activation+down projection, and row MMAR, tagged by M/K but never by
  prompt text;
- graph capture/compile miss counts and first-token-only markers.

The decision rule is causal: prefill MMAR arrival skew must correlate with one
upstream interval on the late rank, and a decode candidate must occupy enough
non-overlapped critical-path wall time to make a 20% TPOT reduction plausible.
Instrumentation is a prerequisite, not a candidate and not a PR deliverable.

## 6. Candidate A — GDN terminal fusion (highest-priority TPOT candidate)

### Exact execution seam

Patch
`/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py::
AscendGatedDeltaNetAttention.forward` at the terminal sequence:

```python
core_attn_out = self.norm(core_attn_out, z)
...
out, _ = self.out_proj(core_attn_out)
```

The runtime plugin dispatches only unquantized BF16 Qwen3.5 GDN layers with
TP=4 and local shape `[..., 12, 128]` (flattened K1536) to a custom
`rmsnorm_gated_mmar` wrapper. All other shapes/models fall back to the
original method. The custom operator must compute the current fused
RMSNorm-gate semantics followed by the row-parallel
K1536/N5120 matmul-allreduce. There is no verified current `torch_npu` API
that fuses this whole subchain; the existing `self.norm` already fuses
normalization and gate, so replacing only that call is not a candidate.
CANNBot/ops-transformer generation is justified only for the full terminal
subchain.

### Causal impact

This removes the materialization/readback of the 1536-element normalized
activation and one Python/operator boundary before each of 48 GDN output
MMARs per generated token. Decode directly targets TPOT. The same seam occurs
for prefill and may reduce TTFT, but TTFT credit must be measured separately;
it must not be inferred from M=1 results.

### Risks

- BF16 RMS statistics, SiLU/gate order, and collective reduction order can
  change outputs.
- Fusing a collective into a compute op introduces stream, graph-capture,
  communicator-lifetime and failure-propagation risk.
- The op must never borrow v7 IPC state or its HCCL-window assumptions.
- A too-large fused kernel can lose overlap or regress M274/M1536 prefill.

### Required microbenchmark

Compare the entire stock chain `self.norm(x,z) -> official K1536 MMAR`
against the candidate, not MMAR alone. Test TP4 BF16 at M1/M5/M8/M16 and
prefill M274/M1536, alternate order, flush L2, warm up, use at least seven
repeats, and report median **max-rank** latency plus per-rank distributions.
Require at least 1.15x geometric-mean speedup on M1/M5/M8/M16, no tested cell
below 1.05x, and no prefill cell below 1.00x before service integration.

### Precision and service gates

Elementwise BF16 gate against the exact stock chain:
`abs(diff) <= 2^-6 + 2^-6 * abs(reference)` for at least 99% of elements,
max absolute error <=1.0, finite outputs, exact shapes, and a CPU-FP32
diagnostic oracle. Then require four-rank activation, natural-EOS smoke, a
candidate-specific 32-row paired canary with zero material regressions, and a
single-repetition c1/c16 screen where both
`TTFT ratio <=0.60` and `TPOT ratio <=0.80` in each cell. Only then enter
the full three-repeat matrix and all-357 paired gate.

### Composition

Stackable after the already verified qkvz/ba construction/mapping fusion.
Stackable with Candidate B after each passes alone. Mutually exclusive with
any alternative replacement of the GDN terminal row projection.

## 7. Candidate B — dense SwiGLU plus down-projection MMAR fusion

### Exact execution seam

Patch the official vLLM class used by Qwen3.5 dense layers,
`/vllm-workspace/vllm/vllm/model_executor/models/qwen3_next.py::
Qwen3NextMLP.forward`, at
`gate_up_proj -> act_fn (SwiGLU) -> down_proj`. The source-contract gate must
first prove this exact class/method and anchors in the pinned 0.23.0 image.
Dispatch only when `down_proj` is the unquantized TP4
`AscendRowParallelLinear` whose local input is K4352 and output is N5120.
Keep the official gate/up projection; fuse only its output activation
consumption with the K4352 row MMAR.

This is materially different from the closed dense-FFN/NZ route and the
A2 local-FFN microbenchmark: the measured unit here includes the final
four-rank collective and removes the intermediate SwiGLU tensor from the
critical path.

### Causal impact

All 64 layers execute this tail per decode token. Eliminating a separate
activation launch and intermediate HBM traffic before K4352 MMAR can lower
TPOT; prefill M274/M1536 may also lower TTFT if the fused path preserves
compute efficiency. It does not rely on faster ordinary all-reduce and does
not decompose the official MMAR.

### Risks

- SwiGLU half ordering and BF16 rounding are checkpoint-contract sensitive.
- The large gate/up output raises workspace and graph-capture risk.
- The earlier standalone dense local chain achieved only about 1.098x and did
  not pass its gate; this candidate must prove additional value from terminal
  fusion rather than reusing that result.
- K4352 online tiling, down-proj NZ, down-prefetch and MMAR core-count scans
  remain closed and may not be folded into this candidate.

### Required microbenchmark and gates

Compare `stock SwiGLU -> official K4352 MMAR` against the fused terminal op
at TP4 BF16 M1/M5/M8/M16/M274/M1536 with the same L2-flush,
alternating-order, seven-repeat, median-max-rank protocol as Candidate A.
Require M1/M5/M8/M16 geomean >=1.15x, every decode cell >=1.05x and no
prefill regression. Apply the same 2^-6 mixed-tolerance/99%/max-abs<=1.0
operator gate, exact SwiGLU half-order fixtures, four-rank smoke, 32-row
semantic canary, and c1/c16 ratios <=0.60/<=0.80 before advancement.

### Composition

Stackable with Candidate A and the retained GDN qkvz/ba fusion. Mutually
exclusive with any whole-MLP replacement, down-proj NZ, or down-prefetch
variant.

## 8. Candidate C — 910B4-specific GDN prefill-core fusion (TTFT-only tier)

### Exact execution seam

Patch
`vllm_ascend/ops/gdn.py::AscendGatedDeltaNetAttention._forward_core` /
the registered `torch.ops.vllm.qwen_gdn_attention_core` prefill branch,
leaving decode recurrence untouched. The operator boundary must accept the
same mixed-qkv, b, a, output/state buffers and sequence metadata, and it must
preserve the current state layout exactly.

The newer checkout contains an A5-oriented
`torch_npu.npu_chunk_gated_delta_rule` probe and explicitly states that the
official implementation is unavailable for that device route. It is not a
verified 910B4 API and must not be called or backported blindly. This
candidate therefore requires a new, explicitly dav-2201/910B4-supported
ops-transformer implementation, or it is rejected before coding.

### Causal impact

Round0 shows M274/M1536 K1536 collectives arriving 6.9-8.2 ms apart. If
device timestamps attribute that skew to the multi-kernel GDN prefill core,
a single shape-specialized core can reduce the late-rank critical path and
therefore TTFT before the following MMAR. It has no credible TPOT effect
because decode recurrence is deliberately unchanged; it can only be part of
a final stack with A or B.

### Risks and gates

Recurrent state is much more sensitive than a stateless projection. Validate
per-token outputs and final state against the exact stock branch across
sequence lengths 1, 63, 64, 65, 274 and 1536, multiple cumulative-sequence
layouts, zero/nonzero initial state, and rank-local head partitions. Require
the standard BF16 mixed tolerance plus relative-L2 reports for both output
and state; reject NaN/Inf or any state-layout difference. Performance must
use max-rank latency and demonstrate that the late-rank interval and the
subsequent MMAR start-spread both shrink. Then use the same smoke, 32-row
canary and c1/c16 dual-metric gates. Candidate C is stackable with A/B but
must pass alone first; do not start with a mega-fused GDN operator.

## 9. Explicitly excluded routes

The following are not candidates and must not be renamed or combined into a
new round without materially new evidence:

- IPC fullmesh v7 (diagnostic/rejected; lifecycle and safety defects);
- ordinary matmul plus all-reduce in place of official MMAR;
- blanket decode MMAR launch-parameter retuning;
- down-proj NZ;
- online HCCL tiling or K4352-only tiling;
- HCCL_BUFFSIZE 64/128/256/1024 scans;
- MMAR x3 residual;
- prefill AllReduce+RMSNorm;
- MMAR core-count scans;
- global, attention-only or down-proj MMAR-off;
- FlashComm1/FlashComm2 projection variants;
- gate/up-only or down-prefetch retests;
- broad bounded-MMAR t11 or async-finalize;
- ShortGPT/layer skipping, MTP/speculation, quantization or retraining;
- TP2/DP2, TP2/PP2, CP/KVP or other weight/group repartitioning.

## 10. Recommended order

1. Finish the formal perf-breakdown and the narrow timestamp attribution.
2. If GDN terminal wall time is large enough, microbenchmark Candidate A.
3. If dense MLP tail wall time is large enough, microbenchmark Candidate B.
4. Consider Candidate C only when the prefill late-rank interval is actually
   inside GDN core and the 910B4 operator route is documented as supportable.
5. Integrate only one candidate at a time into the existing t12 loader.
6. Do not combine passing candidates until each has independent operator,
   precision, 32-row and c1/c16 evidence.
7. Promote only after c1/c5/c8/c16 x3 meets both targets and the all-357
   paired review has zero material regressions.

The likely final commercial form remains small: a source-contract-checked
Python package, an optional read-only custom OPP artifact, activation markers,
and a launcher that installs the package with `--no-index --no-build-isolation
--no-deps -e` inside a disposable container. Small code size is expected;
the proof burden lives in the artifacts and gates rather than source volume.
