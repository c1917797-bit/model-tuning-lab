# Isolated quantizer NPU preregistration (not executed)

Owner: main agent only; physical NPU4-7 after fresh route/device/namespace checks.
Every run uses a new absent external directory, explicit SO SHA/source manifest,
actual CANN/TorchNPU/device provenance, immutable fixture SHA, and no overwrite.
Old production v4 and trace v2 stay loadable unchanged.

1. Compile/load/schema are NOT numerical passes. New isolated test namespace
   and .so are explicit; no automatic production registration/monkeypatch.
2. Exact helper: finite FP32 x, all positive finite scales including subnormals;
   compare INT32 code BITWISE to independent Fraction->RN32->integerRNE.
   Use +0/-0, minimum/maximum subnormal and normal, maximum finite, scale=1,
   frozen scale max bits7c010203, scale bits39919209 and saved x bd05a10e.
   Invalid x NaN/Inf and scale 0/-0/negative/NaN/Inf must report invalid before
   any persistent mutation (isolated kernel has no persistent state at all).
3. Boundary fixtures: j=0..126, all seven/eight registered scale choices,
   RN32((j+.5)*s) and +/-1..4 raw-bit neighbors with both signs. Both integer
   parities; j0 binade corner; +/-127 saturation; quotient overflows and tiny
   quotients. Random FP32 raw-bit pairs supplement, never replace, boundaries.
   Code contract remains two-stage RN32->RNE, not exact-rational integer RNE.
4. Mul fast-domain gate: exact bitwise endpoint FP32 Mul against independent
   rational multiplication->RN32; normal domain, binade edges, minimum normal
   product, product overflow, maximum frozen scale. Detect subnormal/FTZ behavior.
   Until this gate PLUS documented domain assumptions are satisfied, run exact
   path only (rnMulReceipt=false). Bitwise sample agreement is evidence, not
   blanket proof of every ISA input; record any architecture contract limitation.
5. Fast certificate: counts64/1792, correct AND arbitrarily wrong proposed
   magnitudes0..127. All accepted lanes must match exact oracle BITWISE.
   Inject badly signed/NaN/Inf approximate q to test sanitation/sign restoration
   using a separate explicitly named fixture seam, not an undocumented operator
   parameter. No reliance on approximate Div ULP envelope.
   Zero magnitude must pass its upper certificate or fallback, never shortcut.
   Subnormal scales/products, infinities/NaNs and uncertain endpoints must fallback.
6. GatherMask: exact compact indices/count/order for no bits, every bit,
   alternating bits, first/last only, bits63/64/127/128/1791, sparse random masks.
   counts64/1792 (224B mask at max), repeat/counter contract, storage guards,
   source/rawX/scales/index input bitwise unchanged. Repeat >=20 to expose reuse
   hazards. Fail if any index omitted, duplicated, reordered or out of range.
   Positive normal finite results with +4-neighbor infinity must safely fallback.
7. Sync/DMA: no GM dense-state sidecar; one owner/head; typed output alignment;
   immutable source; canary guards; repeated invocation pointer/shape invariants.
   Caller inbound queue/MTE2 and outbound queue/MTE3 waits are part of probe,
   not inferred from helper success.
8. Measure exactLanes/total, isolated elapsed with profiling OFF, and compiler
   actual UB footprint. Record worst-case all-boundary fallback. Micro-latency
   cannot be promoted to service throughput.

Then integrate ONLY the proven quantizer into a NEW production identity:
- saved-step45 must reproduce updated-state/native equality and now oracle code;
- B1/B16 full160-step changing-state-index compressed feedback trajectory,
  selected complete hi/lo/scales/output, untouched slots, guards, plans and all
  immutable inputs, storage pointers. Keep frozen numerical thresholds;
- native SR1/power2 anchors and general positive FP32 SR independent reference;
- final192 calibrated plans, actual typed cache, scheduler, eager/graph gates;
- dense paired fixed output1024 end-to-end TTFT/TPOT/throughput;
- final LongBench-v2/GSM8K within latest user accuracy-loss allowance, reported
  separately from all intermediate numeric tolerances.

A new deterministic failure is saved and attributed. Do not retry unchanged,
relax half-tie code equality, add an undeclared scale floor, or claim paper no-go
from a single boundary implementation failure.

