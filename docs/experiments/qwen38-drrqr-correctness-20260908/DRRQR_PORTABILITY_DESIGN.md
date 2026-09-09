# DRRQR portability: design-time admission for beta compensation and layerwise rank

Date: 2026-09-09. Design review, not a new numerical, performance or accuracy result.

This document serves two concrete DRRQR candidates: fixed retained-key beta
compensation of the current energy64 selector, and a layerwise logical-rank
budget. It does not introduce another acceleration algorithm or a general
runtime framework. Current teacher capture/replay remains the deciding experiment;
this design review accompanies it, not replaces it.

The primary acceptance remains reproducible >=10% same-stack end-to-end output
throughput gain and no LongBench-v2/GSM8K accuracy decline. Portability additionally
requires measured positive throughput gain against each admitted environment's own
contemporaneous dense control. A second environment/workload matrix is not yet
specified; no arbitrary-environment or universal-speedup claim is supported.

## 1. Preserve algorithm semantics before selecting a backend

The portable plan should describe logical per-layer/head coordinates and their
order, logical Dk, Q/K-to-V head association, selection objective, calibration
identity, coefficient definition, normalization/scale convention, state-coordinate
representation and prefill/decode policy. Current energy-kernel selection is an
experimental DRRQR-family variant, not exact official StrongRRQR reproduction.

An adapter may lower that plan to physical layouts and kernels, but must not
silently change coordinate selection, r, mathematical scale or state meaning.
Keep an independent recurrence reference across backends. BF16/FP32 rounding and
backend arithmetic must be tested against declared tolerances, not hidden as a
change in the algorithm.

### Fixed retained-key beta compensation

For the projected recurrence with omitted coordinates deliberately excluded,
let k_ret = sqrt(rk) * u and T = sqrt(rk) * S_ret, with rk positive and constant
for that head over time. Then:

```text
S_ret_next = alpha*S_ret + beta*(v - alpha*S_ret@k_ret)*k_ret^T
T_next     = alpha*T     + (rk*beta)*(v - alpha*T@u)*u^T
```

This motivates beta' = rk*beta, not a proof of dense recovery. The real dense
residual also contains alpha*S_dropped@k_dropped. Time-varying rk additionally
changes the coordinate transform: the decay becomes
alpha*sqrt(rk_t/rk_previous). Beta-only compensation does not implement that term.
Existing real calibration already shows within-head retention variation.

The current candidate freezes **train_k_mean from old calibration rows 0..11**.
It must not substitute the all-row/held-out mean or fit the new teacher prompts.
The local TP4 mapping is four Q/K heads to twelve V heads, with three consecutive
V heads per Q/K head; repeat_interleave(3) is this model's mapping, not a universal
constant. Other models require an explicit validated head association.

The executed change is beta BF16 -> FP32 multiply by r -> BF16, in both candidate
prefill and every decode. Each trajectory starts from its own zero-state prefill.
Reusing dense/noncompensated nonzero state requires the correct coordinate
conversion; changing a plan/r must never silently reuse an old cache.

For q_ret = sqrt(rq)*q_unit the ideal projected output has a
sqrt(rq/rk) factor, plus the logical attention-scale convention. Such an ideal
diagnostic is separate from the actual candidate output. Actual gated RMS uses
finite epsilon, observed weights, BF16 rounding and norm-before-gate order.
Positive per-head scale cancellation is exact only in the relevant ideal
zero-epsilon arithmetic; it cannot justify deleting these actual checks.

### Layerwise logical rank

Choose each layer's logical Dk and its coordinates under an explicit global
budget. Equal sum(Dk) is only a logical payload budget, not proof of equal runtime
allocation or speed. Layer sensitivity and cross-layer/autoregressive feedback
must determine whether a redistributed budget preserves accuracy. Retained energy
is a selection diagnostic, not LongBench-v2/GSM8K accuracy.

Projection/conv row slicing, per-layer normalization and scale, state shape,
cache identity and prefill/decode dispatch must all use that same layer plan.
A global maximum-Dk envelope is a backend allocation choice, not the logical
dimension for every layer. Unchanged mathematical intent across environments
does not require every backend to use the same physical envelope.

## 2. Minimal saved-versus-added cost model

Let hq/hv be local Q/K and V head counts, dv the V width, H the model hidden
width, T executed tokens, Lc the convolution history length, and bs/bc/bw the
state/conv/weight element sizes. For one layer, useful logical payloads are:

```text
recurrent state per live sequence: hv * dv * Dk * bs
conv history per live sequence:   Lc * (2*hq*Dk + hv*dv) * bc
reducible Q/K projection weights: 2*hq*Dk * H * bw
Q/K projection FLOPs:             approximately 4*T*hq*Dk*H
recurrent arithmetic/traffic:     proportional to T*hv*dv*Dk
```

These are payload/scaling relationships, not measured DRAM traffic, allocated
pool capacity, critical-path time or throughput. Actual allocation must count
unique backing storage and legal simultaneous occupancy; do not sum aliased
cache views or assume shared-pool reuse is free.

For the observed local TP4 geometry hq=4, hv=12, dv=128, FP32 recurrent state,
BF16 conv state and Lc=3, the unpadded state+conv payload per layer/live slot is:

```text
S(Dk) = 6144*Dk bytes
C(Dk) = 48*Dk + 9216 bytes
S+C   = 6192*Dk + 9216 bytes
Dk64: 405504 bytes; Dk128: 801792 bytes
```

This explicitly uses the real service's FP32 state, not a hypothetical BF16
budget. Physical padding, pool pages, reserved slots and fragmentation are extra.
The external cache dtype does not specify internal arithmetic precision;
workspace/intermediate storage and its traffic must be budgeted separately.
Full-attention KV, V/output projections, MLP and many TP collective payloads do
not shrink merely because GDN Dk shrinks.

| Candidate | Hardware-independent opportunity | Added costs and ways benefit disappears |
| --- | --- | --- |
| Fixed beta compensation | Does not itself reduce state or projection work. It attempts to recover fidelity at a reduced DRRQR rank, preserving the rank reduction's opportunity. | FP32 conversion/multiply/BF16 conversion, intermediate reads/writes and possibly extra launches. A small state kernel or low batch can make launch cost dominate. Fusion may amortize this but is a separate implementation, not assumed. Accuracy can worsen if constant-retention or dropped-term approximations are poor. |
| Layerwise rank | Smaller per-layer Q/K projection, recurrent state and state movement; budget redistribution may spend rank where needed for fidelity. | Gather/pad/scatter, additional graph/layout groups, arena bookkeeping, allocation fragmentation and worse tiling. Max-Dk allocation may erase state savings. Rank imbalance/extra communication can lengthen the TP critical path; unchanged hidden-width all-reduces are not automatically smaller. |

For design screening, estimate each affected stage with its **physical** bytes,
FLOPs, launch count, effective parallelism and expected overlap. A bounded model
such as max(F/compute_rate, B/bandwidth) + launch_count*launch_latency can expose a
candidate's break-even assumptions. It is not a prediction to certify throughput:
rates depend on shapes, residency, tiling and concurrency, and kernels can overlap.

End-to-end saving must exceed the added work on the actual critical path.
Kernel-time sums, CPU timing and a state-only microbenchmark cannot supply that
inequality or a strict impossibility bound. TTFT and TPOT can move differently.
A beta candidate may improve local fidelity yet add unacceptable TPOT; a rank
plan may reduce payload yet lose throughput to padding or scheduling.

## 3. Logical Dk is not physical width, stride or alignment

Represent logical Dk separately from physical row width and byte strides.
Physical width may be align_up(Dk, a), but the alignment a and supported layout
are backend capabilities, not algorithm parameters. Zero padding must preserve
logical normalization, explicit logical scale, coordinate order and state
updates; a changed reduction order still needs arithmetic validation.

The frozen v0.23 Ascend decode path's Dk104/Dk88 CopyOutState padding defect is
runtime-invalid evidence. It does **not** show those DRRQR ranks are mathematically
bad. Keep the current non-16-aligned execution rejection. Do not reopen the old
results or lower the correctness gate.

A separately validated padded fallback could preserve logical semantics, but
its physical cost must be reported honestly: e.g. logical104 stored/executed at
physical128 may retain little/no state-kernel saving. Merely naming it Dk104 is
not a memory or speed result. A correct fallback is compatibility, not performance
acceptance.

For heterogeneous layers, prove allocation offsets, nonoverlap/lifetimes and
per-layer strides together with scheduler ownership. The existing shared hybrid
pool cannot be admitted just because standalone per-layer arenas passed. Grouping
by layout, or independent compact state pools, must account for page rounding,
block accounting, reserved/null identifiers and enough remaining attention
capacity. Reserve the actual physical state budget before deriving capacity;
do not fund it by accidentally reducing feasible request/context capacity.

## 4. Small explicit capability/dispatch boundary

No new generalized framework is required. For the candidate adapter, record and
validate only the capabilities it consumes:

- logical/physical Dk pairs; Q/K/V head mapping; supported state/input dtypes;
  layout, strides, padding and mutable-state alias contract;
- sequence-length and slot-index ABI, invalid-slot semantics, supported
  prefill/decode paths and graph modes;
- internal storage and accumulator/reduction dtypes, cast locations and rounding
  modes, chunk size/boundaries, and prefill/decode numerical execution policies;
- exact beta rounding pipeline, normalization/scale and gated-RMS semantics;
- cache group/page constraints and TP partition/collective requirements;
- implementation identity and the corresponding numerical qualification.

Dispatch only to a qualified implementation for that combination. If unavailable,
reject the candidate or use an explicitly labelled correct fallback; never
silently reinterpret Dk, dtype or padding. Keep the mathematical reference and
plan stable while backend adapters vary.

### Precision contract: external FP32 state is not all-FP32 execution

Frozen source for the current BF16-input/FP32-state Ascend chunk path specifies
64-token chunks, BF16 W/U intermediates, and BF16 non-final H between chunks.
The update epilogue promotes H for FP32 decay/addition, then uses CAST_RINT for
non-final H storage; the final-state FP32 branch writes its FP32 update directly.
The V-new epilogue forms U-WH in FP32, stores v_new in BF16, and separately forms
the decay-weighted value from the unrounded FP32 residual before another BF16
store. Therefore a 128-token all-FP32 unrolled recurrence is an independent
mathematical reference, not the same finite-precision implementation simply
because both expose FP32 final state.

The adapter contract must distinguish operand/intermediate storage from actual
accumulation precision, and record which operations round before reuse. State ABI
or a FP32 workspace alone cannot establish every dot-product's precision; leave
unspecified compiler/backend arithmetic explicitly unverified. Chunk boundaries,
rounding policies and cast placement are implementation properties separate from
logical DRRQR coordinates/rank and recurrence. A backend change to these properties
requires a new numerical qualification and corresponding dispatch/graph identity,
not an unnoticed change to the reference or beta-compensation semantics.

These source facts do not establish the cause or magnitude of all observed
numerical differences, resolve the executing device binary, or establish any
performance/accuracy benefit. The original failed gate, report, reference and
thresholds remain unchanged and failed; no post-hoc tolerance relaxation follows.
Use separate incremental controls for an algorithm transform on a fixed backend
and for a backend implementation change with a fixed logical plan. Such controls
can help attribution but cannot replace complete numerical qualification or final
paired task-accuracy acceptance. Any precision-aware diagnostic must be separately
named/versioned; it must not retroactively turn the original failed gate into a pass.

Plan/cache identity must distinguish selected coordinates/order, per-layer logical
ranks, head mapping, beta coefficients/state representation and normalization
policy. Graph identity must additionally respect physical shapes/strides, dtypes,
ABI and capture mode. Reuse with explicit persistent input buffers is permissible
only when semantics and lifetime rules remain valid. Current prefix caching is
off; this is a design obligation before enabling it, not evidence it is integrated.

Absolute paths, source SHA pins, four logical devices and exact v0.23 assertions in
the current probes deliberately freeze one experiment. They are reproducibility
receipts, not portable public APIs or a claim that another stack is unsupported
in principle. A future adapter selects verified capabilities; it must not remove
experiment identity checks from historical reproduction.

## 5. Admission now, measurements on each admitted environment later

Before selecting a new DRRQR implementation, require this bounded design record:

1. Name the logical algorithm delta, approximation and unchanged reference;
   freeze calibration/coefficients before evaluating new prompts.
2. List saved logical work and actual physical allocation/work, added operations
   and expected break-even conditions. Reject a proposal whose stated savings
   rely on unimplemented compact allocation or fictitious reduced communication.
3. Name required backend capabilities, dispatch/fallback and graph/state/cache
   identities; preserve existing invalid-layout gates.
4. Qualify NPU numerics for the change: candidate-owned prefill and multi-step
   state, dense replay/capture control, actual RMS, and required eager/graph mode.
   Storage-only changes use byte checks; arithmetic uses predeclared tolerances.
5. Only then admit a bounded same-stack model screen. Apply common optimizations
   equally to dense; measure fixed 1024-output throughput plus TTFT/TPOT. Promising
   candidates proceed to repeated performance and no-thinking 2048-cap normal-EOS
   LongBench-v2/GSM8K pairing.

The current beta replay's actual post-RMS local screen can only prioritize the
next model candidate. It neither validates upstream/closed-loop feedback nor
qualifies a backend/environment by itself.

The supported hardware/runtime/workload matrix must be agreed with the user.
Primary-host results do not transfer as measurements. Every additional admitted
environment needs its own NPU correctness, paired end-to-end gain and final
accuracy evidence; untested environments remain unverified. Absence of a second
machine does not block this design work or current-host experiments, and does not
authorize access to new devices.

## Evidence basis and limits

This review uses existing project mathematics/code, without a new paper search,
alternative-algorithm proposal, benchmark or NPU run:

- `RETAINED_KEY_BETA_HYPOTHESIS.md`: coordinate transform, dropped term,
  time-varying retention, finite-epsilon boundary and existing synthetic gate.
- `tools/retained_key_energy_stats.py::audit`: frozen train_k_mean and 12/4 split.
- `tools/replay_gdn_teacher.py`: independent three-variant prefill/state,
  pre-L2 selection, 4-to-12 mapping, actual RMS and bounded dense-first gates.
- `tools/gdn_golden_parity.py::_decode_golden`: independent FP32 recurrence.
- Frozen `vllm_ascend/ops/gdn.py` and `ops/layernorm.py`: actual Ascend
  normalization/recurrent dispatch and gated-RMS order/epsilon.
- Precision source audit: frozen `ops/triton/fla/chunk.py` (64-token path and
  BF16 W/U conversion), `wy_fast.py` (W/U stores), and
  `csrc/moe/chunk_gated_delta_rule_fwd_h/op_kernel/` entry plus
  `arch22/gemm/kernel/gdn_fwd_h_kernel.hpp` and `arch22/epilogue/block/`
  `block_epilogue_gdn_fwdh_{update,vnew}.hpp` (BF16 H/v_new and explicit casts).
  These are source-level contracts, not complete binary-resolution evidence.
- `FINDINGS.md`, `HETEROGENEOUS_HYBRID_POOL_AUDIT.md` and
  `HETEROGENEOUS_STATE_ABI_V5.md`: invalid padded decode history, hybrid-pool
  alias constraints, and the distinction between native storage qualification
  and real cache-manager integration.
- Actual FP32 state evidence is recorded in
  `/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/layerwise-model-control-v1/legacy64/worker-probe/rank{0,1,2,3}.cache.json`.

All implementation remains plugin-local. No original runtime, image, reference
repository or resource boundary is changed by this document.
