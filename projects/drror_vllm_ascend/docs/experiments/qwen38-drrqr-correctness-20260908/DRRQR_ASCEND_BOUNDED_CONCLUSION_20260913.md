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
  compensation, packed-QKV, normalization-fusion and value-width routes were
  rejected at the cheapest faithful evidence layer.

## Why the program stops

The remaining throughput gap is larger than the optimistic perfect-removal
headroom of the measured small operator seams. Direct Dk64 projection and
convolution slicing are already active. The last structural route with a cost
ceiling above the target failed exact downstream fidelity by multiples rather
than a tunable margin. Opening another nearby selector, scalar, launch fusion,
generic operator optimization, MTP, speculation, quantization or training
branch would violate the declared DRRQR scope or repeat a stopped family.

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
