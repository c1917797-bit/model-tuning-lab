# True P2–15 native continuation: source-only readiness

Default OFF. MAIN alone owns all containers, NPU loads, scheduling and Git.
This NEW packet never modifies legacy gate, oracle, reference wrapper, production
kernel, parser globals, Torch ops or deadline (2026-10-07T08:48:03Z).

## Admission and matrix

Each complete shard first executes an actual B16 full-reference call versus
16 individual B1 reference calls. All three returned tensors must be bitwise
equal before any P2–15 candidate work. The frozen reference remains B1/B16 only.
The reference source has no cross-request reduction: task/token/head dispatch
L96–98, QK/V offsets L131–135, gating row L158/165, state/output L332–345.

Candidate native chunk, selected pack and compressed decode always receive
true P, never PAD16. Golden uses its own packed feedback, selects the same
ordered slots, invokes existing B1 reference per request, concatenates its three
CPU returns in row order, packs independently, and updates only selected slots.
The NEW RowwiseReference is an explicit callable argument to frozen feedback;
no candidate state is copied into golden. B1 slices are cloned into physical
ND32 buffers (g row48B / beta row24B); original static plans remain immutable.

- Shard P2-8: P=2,3,4,5,6,7,8; 28 native cases, 4480 decode turns.
- Shard P9-15: P=9,10,11,12,13,14,15; 28 cases, 4480 decode turns.
- Every P: adjacent and guard-gaps arena, fresh then own-feedback continuation,
  160 changing decode turns after each native chunk->pack. Full typed state,
  nonselected slots, conv/FA/padding bytes, actual pointers, input guards and
  original-output metrics use unchanged state1e-5/output0.00303.
- Native sequences use lengths65/66/67, actual cu[P+1], initial[P,12,K128,V128].
  Native final is transposed to value-major before exact x/c, Pv/Pk packing.
- Zero/PAD/range/duplicate failure classes retain the frozen kernel semantics;
  this NEW positive native matrix does not claim to rerun legacy negative suites.

The actual gdn_attn_builder.py direct import now has a separately bound stopped-
image snapshot SHA42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16,
manifest b05d03335c10dfb3b0e7ed5f8b691ac0e95529d424cac39f85c1d31b1d710b46.
This does not retroactively enlarge the frozen 23-source identity claim.
Execution additionally checks the actual image-local builder bytes.

## Evidence, timing and failure scope

Before CPU Fraction golden work, every actual native final, original native
fixture, whole raw arena, own golden, indices and bindings are durably saved in
a fresh per-case .pt file with SHA. No old result directory is overwritten.
Each B1 reference call gets an individual JSONL record: original error, nullable
copy errors, actual pointer pairs, input/output hashes, executed flag, ABI/ND/
finite/immutable/nonalias/BF16-cast guards and elapsed process time. Complete
row tensor records stay in the current CPU fixture through the whole turn.
Positive full tensor payloads are not permanently saved per row. JSONL is
fsynced at each completed turn, and on failure; a sudden kill between rows can
lose the uncommitted trailing rows. Native pre-golden checkpoints have their
own fsync boundary. No claim of full pre-dispatch crash recovery.

Original reference dispatch/async errors are captured before frozen after-copy
queries and re-raised even if a later pointer query or evidence write also fails.
First legacy failure is retained; NEW intermediate_row_failure/intermediate_failure
artifacts supplement it without overwriting. Failures never retry or resync;
partially written native-pack calls retire the whole active case.
Admission/CLI errors before the output root exists have only original stderr/
exit evidence; MAIN must preserve its launch command and streams. Startup
import errors after mkdir have finite report.json when writing is possible.

Process timing fields include oracle/copies/synchronization and are diagnostic,
NOT kernel latency or E2E throughput. Full matrix needs 93,585,408 Fraction
transform decisions and 76,160 B1 feedback calls; the 65536-entry cache cannot
hold even random P1 final. P9-15 has ~2.4x more scalar work. No completion-time
promise, no weakened gates to hide CPU wait. Actual cache hits/misses and phase
wall times are recorded. The deadline is checked before native case, every
reference row and every candidate dispatch.

## Commands (prepared only; no future proof fabricated)

Pure stdlib source/behavior checks on host:
`/usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/native_prefill_intermediate_v1/test_runner.py`
`/usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/native_prefill_intermediate_v1/runner.py --check-sources`

Future same-image gate argv (MAIN supplies actual PACKET_SHA, fresh proof and
new external OUT, not template fake admission):
`/usr/local/python3.12.13/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tools/native_prefill_intermediate_v1/runner.py --execute --shard P2-8 --physical-card 4 --preflight FRESH_SINGLE_CARD_PROOF --packet-sha256 PACKET_SHA --legacy-runtime-manifest-sha256 7ea60a45ea46f28811c16455885eab46dbd78bce5586a8914f06a701dbcd4ed1 --build-receipt /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build-receipt.json --library /cache/cch/qwen36-damp-20261006/selected-prefill-build-v1/build/libqwen36_damp_selected_prefill_v1_ops.so --decode-build-receipt /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/build-receipt.json --decode-library /cache/cch/qwen36-damp-20261006/all-batch-wrapper-v3-build-v1/cmake/libqwen36_gdn_damp_all_batch_v3_decode_ops.so --decode-library-sha256 a802d2584f6342acd198406a94c4a4cb3dd0e9cd6cc360569e58f3f117ac0ade --native-anchor-report /cache/cch/qwen36-damp-20261006/production-integer-compaction-general-v1/gate/report.json --reference-library /cache/cch/qwen36-damp-20261006/native-sr-reference-build-v1/libqwen36_damp_native_reference_ops.so --reference-library-sha256 853f655c45c11cb5de5a1b0810c9a8850c0b66aea4c9aa049e01ac89f1aeccc8 --out OUT`
Second disjoint card: same exact argv, shard P9-15, actual authorized card7
(or another freshly authorized4..7) and separate proof/OUT.

Required env DAMP_ENABLE_NATIVE_REFERENCE=1, TORCH_DEVICE_BACKEND_AUTOLOAD=0,
PYTHONDONTWRITEBYTECODE=1, ASCEND_RT_VISIBLE_DEVICES=0. Parent actual launcher
must ensure MA0455 terminal/exact owned TP4 stopped, fresh idle/mapping/canary,
nonprivileged one card->logical0, no physical0–3, actual CPU/RAM/mount/disk
headroom, RO repo/build/source/old evidence and only own new results RW.
Suggested correctness budget per shard1CPU/8GiB; two shards +8GiB ordinary RAM
reserve=24GiB. Formal performance must not overlap these diagnostics. This
packet is not a new controller and does not create or clean containers.

Scope: PCP1 standalone eager operation. prebuilt_meta=None, all P rows fresh
or all continuing; injected service-unpack body is not model/cache authority.
Graph, mixed fresh/continuation, actual prebuilt native metadata, conv/GDN/FA
service scheduling, 192 calibrated plans, full model and E2E/accuracy remain
separate pending gates. Software mocks/source admission never count as NPU.

## Final authority is not connected

This source packet and any future two shard reports are not an all-P assembly
or service admission. `allP_assembly_ready=false`. Final authority still needs
a NEW source-bound all-P validator consuming original terminal records/streams,
the exact per-shard reports and hashes, preserved B1/B16 evidence, and the
actual B16-split bitwise anchors. Its execution, output path and hash have not
been created here; current assembly wiring remains pending. A synthetic
validator record or a future filename must not stand in for original terminal
bytes. Per-shard PASS alone must never set model-cache/service/graph/performance
ready. MAIN must review and bind that separate actual authority before use.
