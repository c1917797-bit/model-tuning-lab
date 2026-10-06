# Quantizer draft static audit / preparation receipt

Prepared on 2026-10-06. No Docker, CANN build, NPU or Git mutation by this agent.

Original mathematics test exec01cc terminal PASS:
116,015 raw FP32 pairs, 100,000 random; exact-bin model vs independent
Fraction->RN32->integerRNE oracle zero mismatches; 99,593 accepted arbitrary
magnitude proposals, zero unsafe certificates in an assumed RN32-Mul model.
Saved-step45 code -118. C++ harness not compiled. Old production header/wrapper
remain ecc24fada002dafbca962de5265f1bddc27a03d1e723070d9b317b415e3ca856 /
0329433adda1821600026df9b8449b64aa9b3d48c4bdcfec82ad07b8f3a94ed4.

New NPU-fixture mathematical check exec0212 terminal PASS:
40,316 labeled fixtures, 24 cases (N64 lifecycle + 23 N1792 full-matrix chunks),
fixture SHA 1c10a0a47fd9edd1c862d05bb55e39ae2dc06526c4cdbbf70f415b58e6d80e32.
New labels include original-coordinate raw saved cell, +/-0/extreme crossproduct,
all j=0..126 halves, both RN32 preimage midpoints and their neighbors,
normal/subnormal scale1/2, min-normal next neighbor, scale1.1 raw3f8ccccd,
invalid flags/code0 and 2,048 random pairs. This is stdlib math only.

## Complete red/high candidate history (none dismissed)

1. Original sync_audit exec01d9:
   SYNC-02 [red], quantizer_ascendc.h original line195.
   Message: "疑似 V 计算后未同步即 Scalar 读: Scalar@195 (计算@189)".
   Detail: "候选：Vector 计算（如 ReduceSum）后、GetValue 前需 V→S 同步
   （PipeBarrier<PIPE_V> 或 SetFlag/WaitFlag<V_S>） | 历史 case:
   cann/ops-nn PR#1678 (flag_pair) | 修复提示: 补齐缺失的 SetFlag 或
   WaitFlag，确保所有路径都触发 SetFlag | diff证据: @@ -166,12 +166,12 @@
   private: PipeBarrier<PIPE_V>(); Cast(xLocal, x1Fp32,...".
   Main approved expanding the existing post-Gather V_S helper into explicit
   same-site Fetch/Set/Wait. Original helper was read and contains exactly that
   pair. No arithmetic change, no upstream/scanner edits.

2. After that change, exec01e3, full-dir exec0213, and full-header exec021a:
   SYNC-08 [red], quantizer_ascendc.h line196.
   Message: "SetFlag 前存在提前退出（可能跳过 Set → 死锁）:
   SetFlag<HardEvent::V_S>".
   Detail: "同函数 Or 内未被兜底的 return/break: [67, 80]；确认所有路径都
   触发 SetFlag | 历史 case: cann/ops-transformer PR#6996 (flag_pair) |
   修复提示: 补齐缺失的 SetFlag 或 WaitFlag，确保所有路径都触发 SetFlag |
   diff证据: @@ -262,6 +262,7 @@ public:
   auto layoutUbBias = LayoutBias::template MakeLayoutInUb...".
   Submitted to main without source repair or dismissal. The isolated compiled
   exact-bits operator does not include this optional float fast helper, but this
   candidate remains relevant before any future integration.

3. New compiled probe header included in full exec021a scan:
   SYNC-08 [red], op_kernel/quantizer_probe.h line45.
   Message: "SetFlag 前存在提前退出（可能跳过 Set → 死锁）:
   SetFlag<HardEvent::MTE2_S>".
   Detail: "同函数 __aicore__ inline void Process 内未被兜底的 return/break:
   [33]；确认所有路径都触发 SetFlag | 历史 case: cann/ops-transformer
   PR#3921 (flag_pair) | 修复提示: 补齐缺失的 SetFlag 或 WaitFlag，确保
   所有路径都触发 SetFlag | diff证据: @@ -595,6 +595,7 @@
   __aicore__ inline void MlaPrologVecS1CubS2<MLAPT>::VectorBufferInit() {
   // ...".
   Submitted for main actual-path review. No blind patch to remove a regex warning.
   A possible reviewable restructuring, if main approves: put the complete
   producer/consumer/Set/Wait computation under if(validTiling_) instead of an
   early return, preserving no writes for invalid tiling. This is a proposal,
   NOT a repair already applied.

Performance-only suggestions retained:
SYNC-09 line47, "同一文件 PipeBarrier<PIPE_V> 过多: 30 个";
SYNC-09 line86, "同一函数连续 PipeBarrier 过多: 28 个 in Or".
Do not remove correctness barriers merely to reduce the count.

## Frontend coverage and side effects

Directory scanner did not include .asc by its extension filter. The compute class
was organized into a normal .h plus a thin .asc entrypoint, mirroring native style;
this exposes the actual class to the scanner without changing computation.
Final full scan included exact header, ops/register/wrapper, compute .h, optional
fast helper and host harness. The thin .asc launch entry remains manual-review
coverage; it only declares GM arguments, AIV task, TPipe and calls Init/Process.

Flow exec01db/01e5 had empty operation/access/dependency lists; no semantic pass.
After compute-header organization, flow exec021c found 4 operations, 2 accesses,
0 dependencies and no findings. Those limits are explicit; NPU queues/flags/DMA
and repeated guards still need actual verification.

Before executing scanner, checked case DB already existed, retriever SQL is SELECT
only, and sync_logging uses stdout/stderr StreamHandler only. PYTHONDONTWRITEBYTECODE
was set. No missing-cache auto-regeneration, repository-cache deletion, SDK edit,
or external tool-source write was performed. Original docs/skills were read in
full before scoped actions. Main decides red/high candidate repairs; scripts are
not used to waive NPU correctness.

## Remaining evidence

Same-image ASC compilation, library dynamic symbols/load/Meta, physical4-7 exact
code/valid/guard/input NPU matrix, THEN actual packed recurrent feedback and
general SR/final plans/cache/service/eager-graph/performance/task accuracy.
Fast RNmul and GatherMask are separate future gates, disabled in this probe.

