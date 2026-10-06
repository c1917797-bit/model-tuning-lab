# KVBuffer parallel FP32 — P1 review packet

Status: **BUILT + LOAD/META / NPU-UNVERIFIED**. New parallel candidate, not a renamed v5 rerun.
Only this directory is new. No vendor/reference/runtime/image edits. No NPU,
Docker start, build or Git mutation was performed by the preparer. MAIN later
performed the actual isolated NO-device build/load/Meta actions described below;
that new evidence does not change the preparer's historical action scope.

## MAIN actual NO-device evidence

MAIN compiled the unchanged seven operator files for dav-2201 in image
sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
Build receipt /cache/cch/qwen36-kvbuffer-parallel-20261006/build-p1-v1/build-receipt.json
SHA25db2cee4f6e6020e476b2c92e15fa8321655bd22e371e35c4d27b0db16dd0d4:
both CMake commands exit0, npu_executed=false, physical_soc_runtime_observed=false.
Library SHA0e7c64b53314f1e822a27b5f373376d82d3f73c01264a384cf58ee4bc6e3477b.
Loading and exact mutable schema/prepare schema plus positive Meta B1/B16 passed:
meta-p1-v1/report.json SHA2765f4bbcbf1d935e260b4d6cfa3b5401257aaf125fca0ae4c149193566dc727.
The NO-device software suite also passed25 tests. This proves compilation,
loading/registration and the positive Meta shapes, not real NPU execution.
Meta negative validation is not implemented by this Meta kernel.
physical_nd_proven=false and graph_proven=false. Actual UB/device ordering,
native numerical recurrence, model lifecycle, E2E and task accuracy remain pending.
Use the existing artifact once after a fresh MAIN launch identity; do not rebuild
or run the already-completed NO-device stages under the same output names.

## Sole algorithm change

Retain cap16, FP32 base/U-log, BF16 K-log and the original native numerical gates.
Batch all16 K-log dot products, weighted U contractions and boundary rank-one
folds using vector operations and a four-level pairwise tree. No data-dependent
per-entry GetValue/ExpScalar/Dot/Add loop. Flush uses16×8×64 tiles, not serial
one-entry materialization. V/K tiling and the fixed four-level tree are not
per-log serial recurrence.

For base B, cumulative log-decay c and entry timestamps lambda,
r[l]=exp(c-lambda[l]) only on live entries. Retrieval is
exp(c)*B*z + U^T*(r*(K*z)). u=beta*(v-exp(g)*retrieval(k)).
Append or fold at16; non-boundary base is bitwise unchanged.
Dead coefficients are zero before exponentiation; stale lambda is never exp'ed.
This preserves the paper mechanism algebraically, not bitwise FP32 arithmetic.
It is an equation-derived project implementation, not verified author source.
[Paper](https://arxiv.org/abs/2605.19049v1), source hashes in PROVENANCE.json.

## Files and scope

- operator/: independently named TORCH_LIBRARY qwen36_kvbuffer_parallel_fp32;
  prepare uploads tiling outside capture, decode rejects cold geometry.
  Strict same-device, physical ND, dtypes, shapes and nonaliasing mutable ranges.
- plugin/: explicit QWEN36_KVBP_ENABLE=1 only. Source-hash-pinned v0.23 adapter,
  donor+actual Qwen receiver binding and actual48 instances each TP4 rank.
- tools/native_oracle_probe.py: fresh output matrix, eager B1/16×160steps then
  three independent graph captures B1/16, changing slots, capacity boundaries,
  reset/reuse, complete state/per-head limits, all log/metadata footprints,
  guard/pointers/input immutability, zero-length dummy slot0 and output-zero.
- tests/: stdlib admission/AST/equation contracts. CPU PASS is not NPU evidence.

The model adapter is deliberately **P1 eager-only**. Its kernel graph probe is
not proof that the model/cache/scheduler graph lifecycle is integrated. Enforce
eager on BOTH screen arms. Prefix off, mamba cache none, no chunked prefill,
no speculation/PCP/DCP/multimodal/prompt-embeds/cache migration. It proves all48
real receivers before mutation and rejects a pure-decode unsupported ABI rather
than silently falling back. Native prefill and mixed fallback remain; mixed
decode materializes selected decode slots before the original native call.
P2 branch-elimination/mixed lane serving is documented separately, not implemented.

## Admission and storage

Kernel launch requires CPU-value admission of [initial_offset, per-sequence
lengths], not cumulative offsets. Prefix ones followed by zero dummy lengths;
only live slots are unique/in range. The kernel checks length before any state
or slot read and never writes dummy state. Runtime data admission is the caller's
responsibility; C++ wrapper performs static device/storage/schema checks without
a graph-time CPU sync. Invalid live metadata is outside the admitted operator
contract, never a supported native fallback.

Native base [S,12,128,128] FP32 is the original pool, no persistent state sidecar.
K [S,4,16,128] BF16, U [S,12,16,128] FP32, three32-wide metadata rows:
119296 bytes/layer/slot; 5726208 bytes/slot/rank across48 layers.
For455 slots this is2605424640 bytes/rank. Budget must be reserved before ANY
of the48 allocations; native KV plus explicit auxiliary allowance cannot exceed
the common total budget. Dense gets that same total. Actual observed slots must
fit the preregistered allowance; failure must not silently grow memory.
UB data slices use126336 bytes plus an explicit4096-byte Broadcast temporary,
130432 bytes within the existing128KiB reservation. Every Broadcast uses the
public five-argument ABI, avoiding its implicit LCM stack-buffer allocation.
Queues use37664 bytes; total reserved remains168736 <192KiB on source-bound
dav_c220 / NPU_ARCH2201. Seven prelaunch V-pipe RAW/WAR barriers are included after q-log reduction,
delta-log reduction, scalar initialization, local flush-tile copies, dummy output
initialization, merge output reduction, and K-log input conversion.
The public five-argument API compiled in MAIN's actual NO-device build; that is
not runtime UB/resource or synchronization proof. Actual NPU storage/ordering,
physical ND and changed-input graph behavior remain unverified. Source definitions and old frozen hashes are in PROVENANCE.json.

GPU metadata copies in the first eager adapter are deduplicated by pointer and
are read-only; their safety overhead is not hidden from E2E measurement.
The pinned CachedRequestState prompt_is_token_ids field is list[bool] | None,
not a boolean: None means all-token-ID text, while a supplied mask must match
the complete prompt length and contain only True booleans. Prompt embeddings
and multimodal features remain rejected.
All original runner/outer-forward arguments are passed unchanged. First actual
request enumerates the receiver owning functions; donor source hashes alone
are insufficient. At every turn all48 cores must execute exactly once.

## Required order after review

1. MAIN has read the source and built/loaded the existing artifact in the exact
   immutable image. Verify its receipt/source/library hashes before use; do not
   repeat the completed build. Runtime physical ND, tiling, UB and synchronization
   still need the actual NPU gate. Any future changed build uses a NEW directory.
   Do not modify reference sources or the original image.
2. Parent records fresh device-idle/host RAM/disk/container mapping, image,
   source and library hashes. Create kvbp.launch-identity/v1 externally;
   the probe must not issue its own successful launch/source identity.
3. One native-oracle NPU matrix. Limits are output normalized max0.00303 and
   complete AND per-head state relativeL2 2e-6, not final1% task tolerance.
   Before ANY logical reconstruction/check/metric, persist an independent raw-step
   CPU tensor file: complete before/after/native, original inputs/input-before,
   raw outputs, complete guards and all pointers. Failed raw is never deleted.
   Only this run's individually passed, hash-checked temporary step may be removed;
   prior results are never cleaned. NaN/Inf metrics serialize as null with finite=false,
   while original nonfinite tensor values remain in raw evidence. Diagnostic FP64
   conversion is CPU-first, never an assumed NPU FP64 capability. No auto-retry.
4. Real eager native-off/on output preservation and cache lifecycle gate:
   mixed/prefill/decode, reset/reuse,48 layers×4ranks, native output IDs.
   Prefix-copy/export/eviction/migration/model-graph remain NOT admitted.
5. Profiler OFF matched dense/candidate E2E screen:40 requests/C16,
   input32768/prefix16384/forced1024out (=40960outputs). Same current model,
   image, TP4, eager/general optimizations, scheduler and total memory budget.
   No reuse of the historic108.996204 baseline as contemporaneous evidence.
6. If hopeful:3 balanced paired repetitions, then final nonthinking normal-EOS
   max2048 GSM8K and LongBench-v2. Report TTFT/TPOT, task pp and relative loss.
   User's1% task loss tolerance is separate from the unchanged tensor gates.

No final performance, accuracy, cross-environment portability or deployment
success is claimed. Formal24h clock starts only when parent activates the reviewed
hypothesis. Global deadline remains2026-10-09T11:17:31Z.

Software-only command (no Docker/NPU):
python3 -B -m unittest discover -s projects/kvbuffer-parallel-ascend/tests -v
