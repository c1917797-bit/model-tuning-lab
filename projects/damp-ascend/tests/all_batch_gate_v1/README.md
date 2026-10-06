# DAMP real-T1..16 shared-arena numerical gate v1 (prepared, not executed)

This NEW packet tests only `torch.ops.qwen36_damp_all_batch_v3` / the independently
built `libqwen36_gdn_damp_all_batch_v3_decode_ops.so`. It does not activate the
service adapter or rewrite old B1/B16/shared/graph/native oracles. The v3 change
admits actual T1..16; the numerical update and exact RN32-division-then-RNE
quantizer are unchanged. Source preparation/stdlib success is not NPU proof.

## Frozen preregistration

- Deadline remains **2026-10-07T08:48:03Z**, not restarted by this packet.
- Actual T1..16: q/k[T,4,128] BF16, v[T,12,128] BF16, g[T,12] FP32,
  beta[T,12] BF16; lengths INT32[T+1]=[0,1,...,1], indices INT32[T].
  No padded fake T16 rows or fake slot. S=T+3 and real changing slots over160 turns.
- Original-coordinate selected **and complete** state max-head-relative-L2<=1e-5;
  output<=0.00303; finite all. Untouched typed slots bitwise, immutable inputs
  bitwise, all raw/view/input/output pointers stable, complete conv and outer/
  inter-region guards bitwise. No loosening to the user's task-level1% allowance.
- Per-T SR1/power2 with independent per-Hv permutations × adjacent/guard_gaps:
  four cases. Full queue64 cases,10240 changing feedback turns; each has two
  independently captured graphs + a separate eager arena and independent native
  compressed golden. Three warmups; eight identical reset/replay checks;160
  changing-input closed-loop turns without candidate state resynchronization.
- Static buffers copy/synchronize outside capture. prepare is explicit and outside
  capture for every new T/plan/shape key. A different T is a different graph,
  not a proved scheduler transition or graph-pool lifecycle.
- Native HQ12 golden uses the unchanged helper/signature contract, independent
  CPU group-loop packing, selected-only updates and independent feedback.
  SR1/power2 dyadic V/c fixtures avoid unproved BF16 double-cast rounding.
  This restricted oracle does **not** prove general FP32 SR, final192 calibrated
  plans, full model cache, scheduler, throughput or LongBench-v2/GSM8K.
- Real dynamic metadata negatives: prefix, last active length, negative/out-of-range
  INT32 slots, duplicate slots, cumulative lengths. Extra active tokens0/7/8
  where present target align-to8 copies, including T2/7/8/9/15. Every invalid
  eager/graph call must output allNaN and leave every input and complete raw
  arena unchanged; valid recovery occurs only after no-write was proved.
- Fifteen actual DATA overlap cases per case: partial32B/exact-start mutable pairs
  and each ofeleven readonly inputs vs high region. Only synchronous DATA-interval
  rejection plus entire arena/every-input no-write passes. Internal numerical
  or device failure terminates; never recover/resync/retry the same failure.

## Source/runtime identity and failure retention

`runtime_manifest.json` pins this packet and every imported unchanged protocol.
The wrapper source manifest SHA is
`a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958`.
Only a real MAIN build receipt schema `damp_all_batch_wrapper_build_v3`,
compiled_no_device/new9 sources/new namespace/library hash, actual defined
launcher audit, CANN9.1 identity and configure/build logs is admitted. Old v2
library/receipt/Meta results cannot fill this contract.

Each execution requires a fresh parent device-proof with exactly one physical
card mapped to logical0, nonprivileged and exclusive-resource gate. Only MAIN
may create/run containers or loads. The current TP4 ON-only reference capture
exec-0000000000000455 retains physical4–7; do not start this queue before release.

The process-local glue replaces allocation/observation/DATA nonalias and only
the metadata *fixture generator*. Frozen graph_case, numerical native helper,
pack/restore and thresholds remain byte-identical. It never reassigns torch.ops.
Raw-before and original exceptions are recorded before assertion; nullable
copy errors cannot overwrite the original failure. Fresh output only; first
failure .pt+SHA and finiteJSON retained. No automatic retry.

## Four distinct physical shards

| Physical→logical | Actual T | Cases |
| --- | --- | --- |
| 4→0 | 1,2,3,4 | 16 |
| 5→0 | 5,6,7,8 | 16 |
| 6→0 | 9,10,11,12 | 16 |
| 7→0 | 13,14,15,16 | 16 |

All four successful receipts are needed for the full restricted allT coverage.
One shard success is only that four-T shard, not allT, general-SR or serving.
MAIN may run distinct shards concurrently only after fresh resource/mapping
checks; no competing load in the TP4 capture. No repetition merely to occupy cards.

Stdlib preparation (no Torch import or NPU):

```text
/usr/bin/python3 -B projects/damp-ascend/tests/all_batch_gate_v1/test_software_contract.py
```

Ready NPU command template, executed only by MAIN in a freshly proven single-card
same immutable v0.23/CANN9.1 image with Python3.12.13. Every uppercase placeholder
must be replaced by an actual path/hash; output root must not exist:

```text
DAMP_RUN_ALL_BATCH_GATE_V1=1 DAMP_ENABLE_ALL_BATCH_WRAPPER_V3=1 ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1
/usr/local/python3.12.13/bin/python3 -B projects/damp-ascend/tests/all_batch_gate_v1/run_all_batch_gate.py
  --physical-card 4
  --library ACTUAL_V3_SO --library-sha256 ACTUAL_V3_SO_SHA256
  --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/all_batch_wrapper_v3/source_manifest.json
  --source-manifest-sha256 a115f00eb371476ad96c440fca53db2c383e2f5f11c9b62e80214543754c1958
  --runtime-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tests/all_batch_gate_v1/runtime_manifest.json
  --runtime-manifest-sha256 ACTUAL_PACKET_MANIFEST_SHA256
  --build-receipt ACTUAL_V3_BUILD_RECEIPT --build-receipt-sha256 ACTUAL_RECEIPT_SHA256
  --device-proof FRESH_PHYSICAL4_ONLY_PROOF --device-proof-sha256 ACTUAL_PROOF_SHA256
  --native-source-manifest ACTUAL_NATIVE_SOURCE_MANIFEST --native-source-manifest-sha256 ACTUAL_NATIVE_MANIFEST_SHA256
  --output-dir /drrqr-results/all-batch-shard-physical4-v1
```

For other shards use physical5/6/7, matching fresh proof and distinct nonexistent
outputs. This is a multiline argument template, not a ready shell heredoc.
`--audit-only` runs source/build admission without Torch, no output creation and
no device execution. Successful no-device admission is not a numerical pass.

For aggregation MAIN reads/checks hashes of four report.json artifacts and calls
`contract.validate_shards` in stdlib. This checks all64 exact T/SR/layout cases,
source/runtime/SO equality and completed guards, not authenticity by filename.
Raw-report hashes, build/library/source/device receipts remain mandatory.

## Explicit limits

No arbitrary FP32 SR, calibrated model plan, graph invalid static plan mutation,
graph-pool eviction/functionalization, simultaneous streams/service, cache
manager/prefix reuse, performance or final task accuracy is proved by this
synthetic packet. Actual scheduler integration needs separate source-bound
model admission and matched dense E2E. All untouched old failures remain retained.
