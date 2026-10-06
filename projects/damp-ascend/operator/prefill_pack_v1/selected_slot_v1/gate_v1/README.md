# Selected-prefill gate v1 — prepared only, default OFF

This NEW packet is an actual-loadable/NPU-executable correctness harness, not a
claim it has run. Parent MAIN owns build/load/Docker/NPU/Git. All old selected
11 sources and frozen numerical/reference kernels remain untouched.

Two separately labelled stages:

1. `isolated`: CPU FP32 operation fixture → REAL selected pack SO → same raw
   allocator-faithful conv/high/low/scales SoA. All selected packed bits compare
   with an independent Fraction-RN32 transform and frozen CPU packing oracle.
   P1/P16 each have two layouts, 20 changed-value/slot calls on SAME buffers,
   eight identical reset calls, PAD/range/duplicate pre-writer rejection,
   shape/dtype/layout/offset/CPU/static-plan negatives and numeric retirement.
   Optional `--batches 1 2 ... 16` adds actual intermediate-P shapes; no fake PAD.
   Neither a CPU seed nor this passing would prove native-prefill/service.
2. `native_feedback`: actual image's original chunk function, public VllmConfig,
   real world1 Gloo/PCP1 and public ForwardContext; no global replacement. Fresh
   and continuation variable-length synthetic BF16 operations call the real
   native chunk (prebuilt_meta=None), produce native FP32 final states, pack
   designated shared-arena slots, then run 160 own-feedback decode steps via
   explicit allbatch ops + independently native-anchored FP32 reference.
   Continuation additionally exercises frozen service selected-unpack body
   against independent packed restore. The injected tiny layer/resource is
   labelled an UNPACK operation probe, NOT actual model/cache admission.

The standalone chunk gate does not cover real native builder's prebuilt chunk
metadata, conv, mixed dispatch, 48 receivers/4 ranks, final calibrated192 plans,
FA/page leasing/zeroing, graph/service or C16 formal timing. Those remain separate
gates. All ready/performance flags stay false even if this packet later passes.
It does not use persistent FP32 production sidecars. The reference holds only
its own independent packed trajectory; selected FP32 scratch is transient.

## Identity and evidence

Actual selected build receipt schema `damp-selected-prefill-build/v1` is pinned
to SHA50f161e6…, source manifest5670a88c…, SO28684cb4… and dav-2201/image660… .
The current actual stage is compile/export/load/Meta PASS (32 positives,
44 negatives), NPU=false. The harness requires original raw command logs and
symbol audit hashes, actual OPP version.info identity841279… (not all-SDK proof),
fresh single-card physical4–7 mapping and actual runtime Ascend910B4.

All runtime dependencies are source-hashed BEFORE Torch/device/library loading,
and rechecked at exit. Plans in this test are externally source/fixture-bound
CPU-derived constants; static inference version−1 alone is NOT immutability.
Selected float proposal stays OFF; exact division is tested, not approximate Div.

Complete guarded status `P*96+16` is copied and checked before ANY feedback.
Metadata error1 must preserve entire raw state. Numeric error2/3 may follow
earlier writes, so ALL slots selected by that invocation permanently retire;
never retry, partial rollback or fallback into the modified state. All CPU input,
expected and raw-before evidence is captured before dispatch. Original errors,
nullable output/after copies and pointer/stride records are preserved before any
assertions, including poisoned context. After-pointer queries are nullable and
record their own error without replacing the original dispatch failure. Packed
feedback fixtures refer to the independently cloned BEFORE trajectory, not to a
later-mutated golden buffer. Expected negative artifacts are distinct.
Before snapshots are held in CPU memory; they are NOT a durable pre-dispatch disk
journal. A process kill before failure-save may still lose that in-memory record;
no crash-recovery/durable-before guarantee is claimed by this packet.
Output directories use mkdir(exist_ok=False); no existing experiment is overwritten.

## Commands (MAIN only; not executed here)

Standard-library source tests (no Torch/load/NPU):

```sh
python3 -B -m unittest discover -s projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/gate_v1/tests -p test_contract.py -v
```

Default CLI is disabled and imports no Torch. In same immutable image, with exact
external runtime-manifest SHA, explicit RO input roots/logs/proof and fresh output:

```sh
python3 -B projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/gate_v1/run.py --execute --stage isolated --physical-card 4 --preflight <fresh-single-card-proof.json> --runtime-manifest-sha256 <frozen-manifest-SHA> --build-receipt /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build-receipt.json --library /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build/libqwen36_damp_selected_prefill_v1_ops.so --out <NEW-output-directory>
```

Native stage (same fresh proof, new output, exact frozen runtime manifest authority):

```sh
DAMP_ENABLE_NATIVE_REFERENCE=1 python3 -B projects/damp-ascend/operator/prefill_pack_v1/selected_slot_v1/gate_v1/run.py --execute --stage native_feedback --physical-card 4 --batches 1 16 --preflight <fresh-single-card-proof.json> --runtime-manifest-sha256 <frozen-manifest-SHA> --build-receipt /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build-receipt.json --library /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build/libqwen36_damp_selected_prefill_v1_ops.so --decode-build-receipt /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/build-receipt.json --decode-library /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so --decode-library-sha256 a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade --native-anchor-report /cache/cch/qwen36-damp-20261006/production-integer-compaction-general-v1/gate/report.json --reference-library /cache/cch/qwen36-damp-20261006/native-sr-reference-build-v1/libqwen36_damp_native_reference_ops.so --reference-library-sha256 853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8 --out <NEW-output-directory>
```

Native CPU admission binds actual allbatch build SHAa9c8a682…, full nine
compiled sources, source manifest a115f00e…, defined host launcher, all three raw
logs, OPP identity and SOa802d258… BEFORE Torch/device/library acquisition.
No Meta/build receipt is relabelled numerical acceptance.
Only B1/B16 native feedback is admitted by this first packet. MAIN must review
the new context/config/group-init seam before execution. No standalone probe is
a substitute for real-model native prebuilt/mixed/continuation evidence.

## Cost boundary

Exact Float fallback is scalar 25-round restoring arithmetic per non-c1 lane;
this is a correctness baseline with potentially unacceptable prefill cost.
No claim of fast/performance deployment follows. The independent Fraction
oracle uses binary64 only to locate neighboring FP32, then exact distances and
LSB parity choose RN32; 3000 random + signed boundary standard-library tests
compare it to frozen independent full-search oracle. None are NPU results.
