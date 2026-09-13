# Qwen3.8-27B DRRQR on Ascend: bounded program conclusion

Date: 2026-09-13

## Decision

The bounded DRRQR program is **joint-target-not-met**.

The best comparable endpoint screen remains energy-Dk64 at 141.564496153
output tokens/s, 4.752041 percent above the frozen dense baseline of
135.142469917 output tokens/s. The fixed 10 percent target is 148.656716909
output tokens/s, leaving 7.092220756 output tokens/s or about 5.009887 percent
additional improvement relative to energy-Dk64.

No later DRRQR algorithm/operator route passed its predeclared evidence gate
strongly enough to justify another endpoint run. The final same-stack,
thinking-off, max_tokens=2048 LongBench-v2 and GSM8K pair was therefore not
run. Quality is unaccepted under the final protocol, not proven to have
declined under that protocol.

This decision stops the tested program. It is not a theorem that every future
DRRQR formulation is impossible.

## Final value/state-width decision

The last material route extended frozen energy-Dk64 with aligned layer-shared
value/state widths Dv64 and Dv48. It used:

- the independently audited 16-sequence Ascend teacher corpus;
- fit indices 0-11 and untouched indices 12-15;
- one layer-shared coordinate set per representative layer;
- one bounded foldable scalar per layer;
- exact checkpoint out-projection weights;
- energy-Dk64/Dv128 as the comparator.

The fit lock was published before held-out data was loaded. Dense post-RMS
formula calibration passed on fit and heldout at relative-L2 0.001660 and
0.001683.

| Width | Aggregate projected-error ratio | Worst-layer ratio | Retained post-RMS ratio | Head-layer fraction <=1.10 | Result |
|---|---:|---:|---:|---:|---|
| Dv64 | 3.711740 | 84.740126 | 2.422295 | 52.78% | rejected |
| Dv48 | 4.072586 | 75.822537 | 2.602293 | 43.40% | rejected |

Both widths passed identity, split, coordinate-count, scalar-bound and dense
formula checks. Both failed aggregate projected output, worst-layer projected
output, aggregate retained post-RMS, head-layer robustness fraction and
worst-head robustness gates. This is a large fidelity miss, so the complete
nearby layer-shared coordinate-and-scalar value-width family is closed before
NPU implementation.

Artifact:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/drrqr-two-sided-value-width-heldout-v1

- started SHA256: ac14d2af87aef66acc07f1ec3734d63fb766bd69ac01822898bd6e8a8ccfdb7c
- fit-lock SHA256: ac7f65e52e3805d0f6debfa17721223b2ffe1703f0648d4bbef85f5dc26477a8
- report SHA256: 44a7ca586e52a72ff42e4ed2f7d3b064158fa6c261875791b24fadd9b2ca6528
- tool SHA256: 8d56fbe4fa992acd2384cd736045c1c28d2914e8d23f8e720e6f5c71833725c8

## Per-head value-coordinate closure

The layer-shared screen reported per-head robustness but did not itself test
one coordinate set per head. That selector-granularity distinction received
one final bounded screen. It changed only the coordinate scope to one static
set for each of 48 global value heads and retained exactly one scalar per
layer. The proposed serving implementation remained statically foldable:
matching V/Z projection rows, convolution channels, state rows, RMS gamma
entries and out-projection columns would be packed before serving, with no
per-token gather.

The same fit indices 0-11, untouched indices 12-15, checkpoint projections and
predeclared gates were used. The fit lock was published before held-out load.
Dense post-RMS formula calibration again passed at 0.001683 relative-L2.

| Width | Fit projected ratio | Held-out projected ratio | Retained post-RMS ratio | Head-layer fraction <=1.10 | Result |
|---|---:|---:|---:|---:|---|
| Dv64 | 4.256534 | 4.164589 | 3.098033 | 55.21% | rejected |
| Dv48 | 4.138284 | 4.177106 | 3.203223 | 49.65% | rejected |

Both widths failed aggregate projected output, worst-layer projected output,
aggregate retained post-RMS, head-layer robustness fraction and worst-head
robustness. Dv64 also worsened from the layer-shared projected/retained ratios
of 3.711740/2.422295; Dv48 worsened from 4.072586/2.602293. The failure is
already large on fit and persists on held-out, so it is not a marginal split
effect. No NPU, endpoint or task-accuracy run followed.

Artifact:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/drrqr-per-head-value-width-heldout-v1

- started SHA256: f0841fd65fa43350e67726255866910cdde34b6a8eb8683ded928af209eb9bc2
- fit-lock SHA256: 50c50cd274c67d658ee1c0d14daf2f41679b4522ba26ad90a2e0463eeab4680e
- report SHA256: 000c174f2b45f4e8cee1700d577201ae14199b87f29f8fede6dbfcbe17c9fcf4
- tool SHA256: 007156a0ffd374cd7130c9ae4ed842b85ec2e3bc5f3cfe312e4af216c10184a0

This closes the nearby static value-coordinate family at both layer-shared and
per-head granularities. It does not prove every possible learned or newly
derived value-state representation impossible.

## Complete value-head scalar-merge closure

A later bounded reopen preserved a retained head's complete Dv128 coordinates
and original RMS denominator, while reducing global Nv48 to Nv16 by keeping one
of every three complete value heads. For each key-head group it selected the
retained head and fit three bounded scalars on fit-only data, then folded the
three original output-projection blocks into the retained block. The frozen
source audit confirmed local Nv4/Nk4 satisfies the native recurrent
divisibility contract and that the serving cut points can be static.

The optimistic profile ledger put this Nv16 design at 152.694978 output tok/s,
or +12.988151 percent versus frozen dense, so it had sufficient paper
headroom. Fidelity did not survive three predeclared cross-validation folds
over reused calibration indices 0-11:

| Metric | Result | Gate |
|---|---:|---:|
| Aggregate projected-error ratio | 3.887735 | <=1.10 |
| Aggregate feature-error ratio | 3.451611 | <=1.10 |
| Worst fold projected-error ratio | 4.062477 | <=1.20 |
| Layer-fold fraction <=1.10 | 0/18 | >=75% |
| Worst layer-fold ratio | 10.294326 | <=1.50 |
| Dense formula relative-L2 | 0.001660 | <=0.01 |

All three fit locks were published before their validation indices were loaded
and their hashes matched. The failure is consistent across every layer-fold,
not a marginal split or formula defect. No fresh teacher capture, NPU,
implementation, endpoint or accuracy run followed. Nearby head choices,
scalar ranges and select-one-and-fold variants are closed; a future Nv
reduction must change the recurrent state/dynamics representation.

Artifact:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/drrqr-value-head-scalar-merge-cv-v1

- started SHA256: fc844da3440267ee15a9ab906fa3b8c17f67e43e998fe8f363a4c8a8d2b2661c
- fold-0 lock SHA256: c5938ffd3c32167515bce38460bbead616868e366f91d08faa8f195e78bf6f34
- fold-1 lock SHA256: b721674d72b7ef9634148b08a2bfb97b2972a66d77ebd1ddfefc60ab28797d38
- fold-2 lock SHA256: 12d86db57b11b3fc790fa5539c560dcfdac2f53d6909057daa09348629bcee65
- report SHA256: d61cd9619f95a2e83fc5a51027974ae9720b81fe24ac9f7a3da6846456b49c10
- tool SHA256: c7f3e44ca94dc9c794081f7626b89c61b6e06bf1886e0d911c9762402d0ecb16

## Rank-1 shared value-state oracle closure

The select-one result was followed by a stronger necessary-capacity oracle.
For every key head and fold it fit the best orthogonal rank-1 direction across
the three complete energy-Dk64 operator outputs. On validation it was allowed
to form that latent from all three already-computed states, expand back to all
three heads, retain the original three Z gates and RMS applications, and use
the exact checkpoint output projection. A real Nv16 recurrence would have
strictly less information and additional dynamics/folding error.

| Metric | Result | Gate |
|---|---:|---:|
| Aggregate projected-error ratio | 5.410002 | <=1.10 |
| Aggregate feature-error ratio | 5.012867 | <=1.10 |
| Operator-state reconstruction relative-L2 | 0.553733 | diagnostic |
| Worst fold projected-error ratio | 5.712986 | <=1.20 |
| Layer-fold fraction <=1.10 | 0/18 | >=75% |
| Worst layer-fold ratio | 80.730378 | <=1.50 |
| Dense formula relative-L2 | 0.001660 | <=0.01 |

The three fold ratios were 5.408264, 5.712986 and 5.156480, so the result is
stable across splits. All fit locks were published before validation load and
matched their hashes. Separately, retaining dense value-source projection and
convolution while perfectly removing the proportional recurrent, RMS,
output-projection and packed-concat work credits only 2.645949 ms/token,
0.535715 ms/token short of the open gap. The Nv16 rank-1 family is therefore
closed before early-dynamics design, NPU, endpoint or accuracy work.

Artifact:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/drrqr-value-head-rank1-oracle-cv-v1

- started SHA256: ffb94184d52bccf883917c64b850b37da3829daf82d014c29481b369895d8bb8
- fold-0 lock SHA256: e51281827235ec6b1232464245ea06edacd5d87eb45c34ae88d7cd5e00e5f747
- fold-1 lock SHA256: a5acdc81c4b0811bf1c9a74189a57c405aece42fac4620644b4e724b87b4411c
- fold-2 lock SHA256: f873f9446ed253a2035ce8d5acd97dba1823ab2ca0660794eed1a9d8f1de7683
- report SHA256: 32f9295d84d613a2f8c458071a8ee6957ccd70018e924772b8a3b9701da666a0
- tool SHA256: fb57c1de16a7f3560b88e05cae1a900cb43a865ed2f044b39e942d6a2f172ff1

## Rank-2 shared value-state oracle and fusion closure

The final bounded representation check raised the favorable oracle from one to
two orthogonal latent states for every three-head key group, reducing global
Nv48 to Nv32. It still formed those states from all three real energy-Dk64
operator outputs on validation and retained the exact original Z gates, RMS
applications and checkpoint output projection. This is more informative than
any implementable two-state recurrence because it pays no formation,
foldability or dynamics penalty.

| Metric | Result | Gate |
|---|---:|---:|
| Aggregate projected-error ratio | 3.272293 | <=1.10 |
| Aggregate feature-error ratio | 3.210713 | <=1.10 |
| Operator-state reconstruction relative-L2 | 0.061391 | diagnostic |
| Worst fold projected-error ratio | 3.324044 | <=1.20 |
| Layer-fold fraction <=1.10 | 0/18 | >=75% |
| Worst layer-fold ratio | 3.868026 | <=1.50 |
| Dense formula relative-L2 | 0.001660 | <=0.01 |

The three fold ratios were 3.324044, 3.315541 and 3.185740, with all locks
published before validation load. Although rank two reconstructs most raw
operator-state energy, exact downstream gating, normalization and projection
still amplify its error to more than three times the energy-Dk64 reference.
This directly disproves raw-state reconstruction error as a sufficient
admission metric.

Nv32 structural reduction alone has an optimistic endpoint ceiling of
146.919230 output tok/s, or +8.714329 percent, below the fixed target. Retaining
dense value-source projection/convolution and reducing only proportional
recurrent and downstream work credits just 1.322975 ms/token, still 1.858690
ms/token short of the original gap. Because the fidelity gate failed, the
specific Nv32 plus corrected fused-recurrent combination is closed without an
overlap audit, Stage2 arithmetic repair, build, NPU, endpoint or accuracy run.

Artifact:

/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/drrqr-value-head-rank2-oracle-cv-v1

- operation: exec-0000000000000874, 357565 ms
- started SHA256: d1bc1c7865a3f9f9fa8b5f0cdc0a4dc77b1c851d499e9a5323fec436ff281332
- fold-0 lock SHA256: 3bbf9e670652ddbb19702dff81f5d09a9e5dfee72bec69c0ec905c319a0e238b
- fold-1 lock SHA256: 3d4d85ff32f547a08435e62542a9821d7037654355af024121a8bcc554435808
- fold-2 lock SHA256: 90b41c3fb52e4860b9cf008f8ae982c1c7c793186bc7ba70d84b6a0cc87cad2f
- report SHA256: 7a6a25e809bf4ba5f9b866137f2a3f4abea091d8f4fabc0344e0906d4e1f22b0
- tool SHA256: 062f64c1057f66f525bd0389bddaef5c5aa38ea0b5d50e08cf55b2f8adc60034

## What was established

- The real Ascend GDN execution path and loaded binaries were identified.
- Native recurrent correctness was separated from padded-state invalidity;
  Dk104/Dk88 historical decode results were invalidated while Dk128/Dk64
  controls remained valid.
- A reproducible dense denominator and fixed endpoint protocol were frozen.
- Energy-Dk64 produced a real but insufficient +4.752041 percent endpoint
  screen.
- A complete multi-step teacher corpus with state continuity, output, source,
  library and token identity was captured and independently audited.
- ABI/storage, eager/state/NPUGraph and arithmetic gates prevented invalid
  custom-operator results from reaching performance tests.
- Multiple Q/K-only, heterogeneous-width, subspace, phase-transition,
  compensation, packed-QKV, normalization-fusion, layer-shared value-width and
  per-head value-width, complete value-head scalar-merge, rank-1 and rank-2
  shared value-state routes were rejected at the cheapest faithful evidence
  layer.

## Why the program stops

The remaining throughput gap is larger than the optimistic perfect-removal
headroom of the measured small operator seams. Direct Dk64 projection and
convolution slicing are already active. The last structural routes with a cost
ceiling above the target failed exact downstream fidelity by multiples rather
than a tunable margin at both layer-shared and per-head selector granularities.
Opening another nearby selector, scalar, launch fusion, generic operator
optimization, MTP, speculation, quantization or training branch would violate
the declared DRRQR scope or repeat a stopped family.

## Post-conclusion FP32 state-cache admission audit

A subsequent source-only reopen check tested whether a plugin-owned FP32
in-place recurrent-state cache/update was materially different. It was
rejected before implementation:

- the active torch schema already declares recurrent state as mutable
  `Tensor(a!)`;
- pure decode passes `ssm_state` directly to the native recurrent operator,
  which updates it in place;
- the profiled Slice/ConcatD shapes bind to QKVZ split, Q/K/V split and packed
  QKV layout, not to the FP32 recurrent-state tensor;
- compact request-state allocation changes capacity/index ownership but does
  not remove the per-active-request recurrent state update.

The admissible new state-copy saving is therefore zero. Even the deliberately
incorrect perfect removal of every profiled Slice plus ConcatD kernel would
credit only 1.826091 ms/token against the 3.181665 ms/token open TPOT gap, and
kernel sums are not a critical-path forecast. No code, build, NPU, endpoint or
accuracy run was started. See
`.agents/evals/practice-iterations/drrqr-dk64-fp32-inplace-state-cache-admission-v1.yaml`.

## Post-conclusion fused-recurrent floor audit

The failed raw-packed-QKV Stage2 was re-read without modifying it. Its
first-step numerical failure has a concrete implementation cause: the
normalization routine squares Q/K in place, destroys the original signed
values, and then normalizes the squared values. A correct implementation would
square into separate scratch and multiply the preserved inputs.

That bug is not being fixed because an independent target-runtime floor rejects
the mechanism first. Under a deliberately favorable bound:

- QKV split/concat, L2 and gating are all treated as perfectly removable;
- even the preceding QKVZ split is optionally credited;
- the recurrent part is reduced to 48 times the fastest single BF16 graph
  sample ever observed in the existing order-balanced micro-screen.

The resulting maximum credit is 3.004914 ms/token, still 0.176751 ms/token
short of the required 3.181665 ms/token. The real service uses FP32 recurrent
state, and a corrected fused kernel must still perform normalization, gating
and recurrence, so this bound already favors the candidate. No correction,
build, NPU, endpoint or accuracy run was started. See
`.agents/evals/practice-iterations/drrqr-dk64-fused-recurrent-floor-admission-v1.yaml`.

## Remaining mechanism-scale threshold

The validated Dk64 profile was also partitioned into every source-bound GDN
component: QKVZ/output projections, convolution, layout, L2, gating,
recurrent, and post-recurrent RMS. Their deliberately additive total is
8.950729 ms/token. Closing the 3.181665 ms/token gap therefore requires a new
mechanism to remove at least 35.55 percent of the whole optimistic GDN budget,
equivalent to about 17.1 of 48 uniformly costed GDN layers.

Perfect removal of the remaining key/state partition alone is only
2.927360 ms/token and still misses. Counting all packed layout work can make a
paper ceiling cross, but its surviving measured per-layer graph floor is what
the fused-recurrent audit already rejected. The broader value/output route had
enough paper headroom but failed the locked held-out fidelity gates by large
margins.

Consequently another coordinate selector, cache allocator, or per-layer launch
fusion cannot reopen the program. A future candidate must name a structurally
different DRRQR state representation affecting more than 35.55 percent of GDN
work, pass an untouched downstream-output gate, and retain physical margin for
its launches and added arithmetic. See
`.agents/evals/practice-iterations/drrqr-controllable-work-budget-v1.yaml`.

## Bimodal Dk0/Dk128 layer-rank audit

A final whole-layer interpretation was checked without launching NPU work:
retain critical GDN layers at the original Dk128 and assign other layers Dk0.
Here Dk0 does not preserve a smaller recurrent state; it makes the complete
GDN branch contribution zero and leaves only the residual bypass. It is
therefore generic branch pruning unless a new rank-zero recurrence is derived.

The exact dense Dk128 profile shapes bind a deliberately additive
9.543988 ms/token GDN budget. Under linear per-layer removal, zero bypass
overhead and inverse-TPOT conversion, an equal-state-budget plan with 24 Dk0
and 24 Dk128 layers reaches only 145.115511 tok/s, or +7.379650 percent.
Thirty-one bypasses remain below target. The first paper crossing requires
bypassing 32 of 48 GDN layers and retaining only 16; even then the projected
gain is only +10.087678 percent, with no physical-overhead margin.

The preserved all-48-layer teacher report closes the fidelity side
analytically. A zero branch has relative-L2 exactly one against each nonzero
dense branch output, versus 0.343918 global mean for energy-Dk64. Dk0 is
2.907668 times worse globally, violates 1145/1152 local windows under the
frozen five-percent regression gate, and has zero safe layers; even the best
layer violates 22/24 windows. The Dk0/Dk128 bypass family is therefore rejected
before code, build, NPU, endpoint or accuracy work. See
.agents/evals/practice-iterations/drrqr-bimodal-layer-rank-admission-v1.yaml.

## Reopen condition

Reopen only as a new bounded program around a materially different, named
DRRQR mechanism that provides both:

1. a full-path foldability and optimistic endpoint case that can materially
   close the current gap without dense reconstruction; and
2. a predeclared untouched downstream-output fidelity result that changes the
   current evidence, followed by target-NPU multi-step state and NPUGraph
   correctness.

Only a candidate that passes those gates should receive a fixed-1024-token
endpoint screen. Three-run performance and final LongBench-v2/GSM8K remain
reserved for a candidate that reaches the 10 percent performance gate.
