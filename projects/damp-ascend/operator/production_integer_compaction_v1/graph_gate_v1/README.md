# Restricted DAMP production graph + malformed metadata gate v1

Preparation only. MAIN owns device checks, Docker, builds, all NPU execution and
Git. This gate has not run on NPU. It does not repair/recompile production,
replace torch.ops, change numerical limits or claim service/performance/quality.

## Required actual eager admission

The exact same independent opt-in candidate
`qwen36_damp_integer_compaction_v1` has an actual restricted NPU receipt:
`/cache/cch/qwen36-damp-20261006/production-integer-compaction-restricted-v1/gate/report.json`,
SHA256 `47c6120134ba788ff3e4a40f949aba1de9ae052726745437482a0bcbc3a71444`.
Four B1/B16 x SR1/power2 per-Hv permutation cases each passed160 steps.
Library SHA `ad6d01068d8cb122abc58da874dad5c4bd0dbd90402d30b5feb0155a86c92c8b`.
These facts admit only the same source/SO into this NEW graph diagnostic.

The frozen nine compilation dependencies and old runtime13 remain untouched.
New runtime6 means these four executable/contract sources plus the pinned
DeltaLog NPUGraph API exemplar and original packed-gate metadata exemplar.
The old manifest/file identities, actual build/export receipt, runtime component
OPP9.1.0 bytes and complete eager receipt source bindings are verified separately.
Build target dav-2201 is not runtime SoC proof. Require fresh parent device proof
and actual Ascend910B4 at execution. No new build is needed for these Python gates.

## Matrix and independent feedback

All four admitted cases, no T2..15, no arbitrary positive SR/final192 plans:

1. Prepare static Pk/Pv/inversePv/c and immutable tiling OUTSIDE capture.
   Source wrapper cache key includes device/T/S/core-count, static plan pointers
   and their version counters. Dynamic query/slot values do not enter that key.
2. Three numerically checked warmups on a separate resettable typed arena.
   They do not consume or silently hide measured trajectory failures.
3. Two independently captured graphs via actual
   `torch.npu.NPUGraph(); with torch.npu.graph(graph): ...; graph.replay()`.
   Capture encloses candidate.decode only: no prepare, Python-created device
   constants, H2D copy, reference or native oracle. Save capture inputs/raw output
   and after-state before guards; reset arenas after capture explicitly.
4. Eight identical reset-to-initial replays, both graphs versus a separate eager
   arena bitwise for output and all three complete packed regions, plus frozen
   independent-native numerical checks. No warmup contributes to the eight.
5.160 changing Q/K/V/g/beta and slot-index turns. Input copies synchronize
   BEFORE replay, including the captured stream's visibility boundary learned
   from DeltaLog. Graph0/graph1/eager own their separate packed feedback; the
   source-frozen native golden owns its independent packed feedback. No step
   resynchronization from candidate to golden and no FP32 production sidecar.
6. On those SAME graphs and eager arena, nine B1/eleven B16 malformed
   length/index cases: nonzero/negative prefix, zero/multi-token/negative tail
   lengths, negative/out-of-range/INT32 extrema slots; B16 last-row duplicate
   slot and cumulative lengths mistaken for the pinned [0,1,...,1] ABI.
   All outputs must be BF16 NaNs, EVERY state byte and EVERY input/pointer
   unchanged. A host/capture error is a failed gate, not a substitute pass.
7. After every malformed replay, install valid changing inputs/indices on the
   SAME graphs. Check correct independent own-feedback continuation and exact
   graph/eager parity. This proves dynamic device metadata was read, not frozen
   at capture; only after complete pre-writer rejection was established.

Every valid step checks selected and complete original-coordinate state
max-head relativeL2<=1e-5, output<=0.00303, finite complete state/output, every
untouched packed slot bitwise, all immutable inputs, pointers, physical ND and
complete backing-storage nonalias. Both graphs and eager must agree bitwise;
bitwise against native packed data is separately recorded as diagnostic, not
a retroactive change to the old restricted numerical threshold.
The eight identical repeats also compare complete-state/output digests.

The native golden expands normalized HQ4 Q/K to Hv12 before EACH Hv's own Pk,
calls actual source-bound native recurrence on its own dequantized temporary
FP32 state and independently packs only selected slots. SR1/power2 dyadic V
makes its BF16 cast lossless, audited at every native call. This does NOT prove
general positive-FP32 SR; the separate independently anchored reference remains
necessary there. No test helper is substituted for actual candidate dispatch.

Malformed metadata protection is different from a quantizer internal failure:
LoadValidateMetadata checks the whole call before ProcessTask/state writers.
An internal PackStore failure can have written earlier groups. It requires slot
retirement/abort, never recovery/retry. This gate only recovers after the former
has proven full-state invariance.

## Evidence preservation and unsupported cases

Frozen CandidateAdapter.observe saves CPU before/golden, original dispatch
exception, raw nullable after/output and distinct poisoned-context D2H errors.
Numerical/guard failure preserves first_failure.pt before the next invocation.
CPU input-source copies remain available if installation or later D2H fails.
Output directories must be fresh absolute external paths, never overwritten.
No automatic retry/eager fallback, performance timing or device resource polling.

Static malformed-plan/schema/Meta checks are reused read-only from runtime13;
this NEW gate adds actual dynamic values, not new host static-plan validation.
Non-ND, misalignment, dtype/shape/alias rejection remains the production wrapper's
contract. No graph admissibility is inferred merely from registration/Meta.
New negatives do not add B2..15, pad slots, mixed prefill/decode, scheduler/page
leases, prefix identity, TP4 cache-manager or request-media support.

## MAIN-only commands

Canonical repository:
`/opt/host/vnf/austinov/model-tuning-lab`.
Pure stdlib test (no Torch/build/device):
```sh
/usr/bin/python3 -B projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/test_software_contract.py
```

MAIN fills actual absolute paths/SHA arguments. Keep the original image CANN
PYTHONPATH, native bootstrap environment, restricted nonprivileged mapping
physical4->logical0 and fresh device proof. Output parent must already exist.
No-device source admission:
```sh
/usr/local/python3.12.13/bin/python3 -B projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/run_graph_gate.py \
  --audit-only \
  --library /cache/cch/qwen36-damp-20261006/production-integer-compaction-build-v3/libqwen36_gdn_damp_integer_compaction_v1_decode_ops.so \
  --library-sha256 ad6d01068d8cb122abc58da874dad5c4bd0dbd90402d30b5feb0155a86c92c8b \
  --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/production_integer_compaction_v1/source_manifest.json \
  --source-manifest-sha256 0332694334b868a3359449cbab00bd2d3ec3f81816dcd3f16e6cdc74137a7593 \
  --runtime-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/production_integer_compaction_v1/tests/runtime_manifest.json \
  --runtime-manifest-sha256 e1cf89a658f389ff45f681ced2ff376a2ef4c66cbfbb61095194d9bc597a232a \
  --build-receipt /cache/cch/qwen36-damp-20261006/production-integer-compaction-build-v3/build-receipt.json \
  --build-receipt-sha256 7f2ef668a80a83c0e15fba1578eb8496f65a36e319e7efec5059895c9f33f961 \
  --graph-runtime-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/production_integer_compaction_v1/graph_gate_v1/runtime_manifest.json \
  --graph-runtime-manifest-sha256 305f8d04bca8fd9ed012324d2cdd22385eae577ef0fef9ea59c3536dc53a2bfc \
  --eager-report /cache/cch/qwen36-damp-20261006/production-integer-compaction-restricted-v1/gate/report.json \
  --eager-report-sha256 47c6120134ba788ff3e4a40f949aba1de9ae052726745437482a0bcbc3a71444 \
  --device-proof FRESH_ABSOLUTE_PROOF_JSON --device-proof-sha256 FRESH_PROOF_SHA \
  --native-source-manifest EXACT_NATIVE_MANIFEST --native-source-manifest-sha256 EXACT_NATIVE_MANIFEST_SHA \
  --output-dir /damp-results/production-integer-compaction-graph-v1
```

Actual NPU command uses identical arguments without --audit-only and adds
environment `ASCEND_RT_VISIBLE_DEVICES=0`,
`DAMP_ENABLE_INTEGER_COMPACTION_V1=1`, `DAMP_RUN_GRAPH_GATE_V1=1`.
MAIN alone runs it after new live isolation, no concurrent competing TP4 load.
Do not reuse the old eager device proof as a fresh graph resource observation.
Expected final scoped status is `restricted_graph_metadata_pass` only if every
check passes; graph_supported remains false on any failure. Serving/generalSR
remain false even after such a pass. Numerical graph success is not evidence of
>=10% E2E gain or final GSM8K/LongBench task loss allowance.
