# Scope and status

This is an unexecuted advisory proposal. It does not modify the completed
`gdn_kernel` proposal, the model, a Git worktree, the host, a container, a
service, or a device. Local validation is limited to Python parsing/bytecode,
stdlib source checks, default-OFF/help behavior and codec algebra. There is no
Torch installation in the local validation environment. No NPU compilation,
actual replay, numerical qualification or timing result is claimed.

`replay_gdn.py` is the opt-in MAIN-owned singleton producer.
`consume_gdn.py` is a separate opt-in Devices[] CPU consumer.
`replay_common.py` imports only the standard library. Both CLI default-OFF and
`--help` paths import neither this helper nor Torch/Triton/vLLM. The producer
has no Docker, process admission, physical device selection, Git, model
instantiation, scheduler or cache publication implementation.

MAIN alone creates/admit/launches the exact owned singleton same-image stage.
The explicit producer CLI may initialize logical `npu:0` only after verifying
the MAIN admission and current container identity. Its public `run(...,
initialize_logical0=False)` also supports an already initialized owner.
Neither entry can establish resource admission independently. The driver does
not release or stop its owner; MAIN must preserve the normal stop/cleanup chain.

# Inputs and manifest

Fill `MANIFEST_TEMPLATE.json` with actual deployed absolute Ref3 values. The
template contains null placeholders and is deliberately not an executable
ticket. Hash the final file to obtain the CLI `--manifest-ref` JSON Ref3.

The immutable manifest binds:

* All three driver files; the completed candidate wrapper and private kernel.
* Exact original `core112.py`, `oracle112.py`, `independent_model.py`,
  `model_entry.py`, `sourceio.py`, `diagnostic_export.py`, and `consume_model.py`.
  Every original Ref3 must equal its entry in the actual r23 source manifest.
* The actual r23 `SOURCE_BOUND.json` Ref3 and four ordered rank receipt Ref3s.
  The original `.pt` file Ref3 comes from each receipt, never from a guessed path.
* MAIN's real admission Ref3, described below.
* Exactly forward32, commit32x32, one CPU tensor thread, and no microtiming.

Source hashes are checked before importing any source-bound module or loading
any tensor file. The complete input closure is checked before importing Torch.
The helper loads modules by checked absolute file path. Original
`independent_model.py` imports `model_entry`; the exact checked original is
registered under that dependency name first. The candidate kernel is imported
by its existing wrapper only after actual admitted logical0 initialization.

Each rank is loaded sequentially with `torch.load(..., map_location='cpu',
weights_only=True)`. Failure of this safe loader is retained as a failure; there
is no `weights_only=False` fallback or custom class allowlist. The producer and
consumer recalculate the original primitive envelope's logical tensor bytes,
validate all64 traversal entries, all48 GDN layers, actual native input tokens,
the C1/131 request/tree ownership, and independent native-prefill physical-slot
anchors. Canonical `[B,H,Dk,Dv]` state must equal the actual native
`[H,Dv,Dk]` anchor after transpose/unsqueeze. All four ranks must share the exact
request and three tokens. Original receipts must have distinct captured worker
PIDs and raw hashes, one captured container cgroup and no primary failure.

The locally provided rank0 receipt is actual r23 evidence:
`BOLE-TREE-RANK-0.pt` has bytes776504853 and SHA256
`9c967f8cc208a9720f5d81c5d0c2a58227205a1e30b9a00e002b101fc3107b22`.
Its source Ref3 has bytes78768 and SHA256
`3b0843d87ced4cdfa3ee0f2ab753a1c1193e71ffdea15f64809098d8df3dac09`.
Do not substitute the local copied receipt's path for the actual owned-stage
receipt/raw/source paths when filling the real ticket.

# MAIN admission and release schemas

`ADMISSION_TEMPLATE.json` must be filled from actual controller/container
inspection, not assertion alone. The producer accepts raw Docker `inspect`
objects or a one-element inspect list as the inspection payload. It checks:

* Replay inspect `Id` and `Image` equal the admission container ID/image digest;
  its saved observed `State.Running` is True.
* Exactly one numbered NPU mapping exists: host `/dev/davinci4` to guest
  `/dev/davinci0`. Non-numbered management devices are not counted as compute
  devices. After import, Torch must report exactly one logical NPU.
* Original retained r23 inspect `Id` occurs in all four actual captured worker
  cgroups, and its `Image` equals the replay image.
* The current process's `/proc/self/cgroup` contains the replay container ID;
  every environment key declared in the admission matches exactly.
* Physical devices `[4]`, logical devices `[0]`, guest device path, actual source
  Ref3, MAIN authority, and common HF32-OFF policy are fixed.

The admission carries observed image/container evidence, not permission to
create a stage. If a different controller inspection format or cgroup namespace
is required, review and source-pin an explicit adapter before execution. Do not
weaken an identity gate after observing results.

After producer exit, MAIN stops its actual device owner and creates a release
JSON with schema `bole.gdn3-replay-owner-released/v1`, authority `MAIN`, the
exact `replay_result` Ref3, original `admission` Ref3,
`owner_stop_completed: true`, and `controller_inspection` Ref3. That last actual
inspection must join the same container ID/image and have `State.Running: false`.
The CPU consumer requires this release and runs in a separate Devices[] stage,
with empty `ASCEND_RT_VISIBLE_DEVICES`, `TORCH_DEVICE_BACKEND_AUTOLOAD=0`, no
numbered NPU device nodes, and no Torch NPU import. It performs no device cleanup.

# Actual computation and unchanged gates

For each of192 actual frames, both layouts are run in the same declared variant:

* Contiguous canonical state, final strides `(128,1)`.
* Actual column-strided canonical state formed by
  `state.transpose(-1,-2).contiguous().transpose(-1,-2)`, final strides `(1,128)`.

Both paths use exact FP32 H2D copies of saved normalized q/k/v/beta/gamma/state.
The original device `core112.verify` and three `core112.commit` calls run
unchanged. The candidate produces actual O/P/U and three actual private
selected states through its default-OFF interfaces, explicitly enabled only
inside this admitted stage. No live model/cache object is available to the
driver. Every returned result storage must be disjoint from input storages.
Actual input identities and bitwise bytes are checked after the original and
candidate calls; final actual post-call inputs are exported too.

The independent reference remains the exact original CPU FP64 literal
`oracle112.sequential(..., parents=(-1,0,0), return_updates=True)`. P's independent
truth is the original `independent_model` gamma path-product expression. For
each O/P/U and each of three endpoint states, the untouched original
`independent_model.old112` is applied to:

* Candidate versus literal FP64 truth.
* Replayed original device core versus literal FP64 truth.
* Candidate versus actual replayed original device core.
* Source-bound r23 captured originals versus literal FP64 truth.

Every original gate requires BOTH
`peak_abs <= 2e-5 + 2e-4 * max_abs(reference)` and `relative_l2 <= 2e-4`.
Candidate P must additionally be bitwise equal to replayed original device P.
There is no epsilon change, reference substitution, low precision, HF32,
best-frame selection, skipped layout or component-timing success assertion.
Finite numerical gate failures are retained for all192 frames before the
producer returns failure. Runtime/source/codec/budget errors stop immediately
with an explicit primary failure; partial exports cannot pass the consumer.

# Lossless bounded export

Duplicating both layouts' original and candidate FP32 states would exceed the
total1GiB budget. The producer therefore exports all actual values losslessly:
each actual CPU FP32 byte stream is XORed bytewise against its exact source-bound
captured counterpart, then zlib-compressed. Final actual inputs use the original
captured input as anchor. This is a reversible byte codec, not numerical
reconstruction, delta rounding, quantization or compression tolerance. Even an
original result that differs from r23 is stored with its complete exact delta.

Per rank there is one streaming `.bin` plus a JSON index. Each segment binds its
offset, compressed size/hash, exact shape/dtype/byte count, actual decoded hash
and exact original anchor hash. The consumer checks sequential complete coverage,
no gaps/trailing bytes, bounded zlib decompression, exact hashes and finite FP32
outputs. It recomputes every gate from decoded actual original/candidate values;
it does not trust the producer's metrics or reconstruct candidate states with
an oracle. It also decodes and verifies actual final post-call input bytes.

The hard aggregate on-disk cap is1GiB, including every rank's both-layout
original/candidate/input byte streams, indexes, result, failure and independent
CPU metrics. The producer reserves32MiB before appending tensor blobs, at least
16MiB before normal metadata completion, and15MiB after a possible bounded
failure receipt for the CPU report. Compression adequacy is unproved until the
real tensors are replayed. Insufficient space is a visible failed run; no frame
is omitted, no threshold relaxed, and no lower precision fallback is used.

Only one original rank envelope is resident at once; frames are processed
sequentially. Tensor compression/decompression operates one tensor at a time.
Only one frame's device tensors, CPU FP64 truth and byte-codec temporaries are
needed beyond the rank envelope. CPU tensor intraop threads are fixed to1;
MAIN retains container CPU/RAM/time limits. The source raw rank0 file is about
741MiB; allow the original envelope plus Torch and small per-frame temporaries.
The driver does not duplicate immutable source inputs in new exports.

# Reviewed invocation interface

MAIN fills and hashes the deployed manifest/admission, creates an empty ordinary
output directory, and launches only inside its already admitted singleton.
The producer CLI is:

```
BOLE_GDN3_REPLAY_ENABLE=1 BOLE_GDN3_TRITON_ENABLE=1 \
  python replay_gdn.py --execute --manifest-ref '<exact JSON Ref3>' --output '<fresh output leaf>'
```

After normal actual owner stop/release, the separate owned Devices[] consumer is:

```
BOLE_GDN3_CONSUME_ENABLE=1 ASCEND_RT_VISIBLE_DEVICES='' TORCH_DEVICE_BACKEND_AUTOLOAD=0 \
  python consume_gdn.py --execute --manifest-ref '<same exact JSON Ref3>' \
  --result-ref '<REPLAY-RESULT.json Ref3>' --owner-release-ref '<actual release Ref3>' \
  --output '<fresh independent output leaf>'
```

These are CLI descriptions, not executed commands or container admission steps.
Default invocations and `--help` are safe without Torch or an actual manifest.

No microtiming is included in this correctness variant. Correctness performs
source hashing, finite/identity checks, H2D/D2H, CPU FP64 reference work and
lossless compression. Timing those guarded calls against an unguarded original
would not measure kernel speed. A separate immutable, independently qualified,
equally scoped warmed microbenchmark can be designed afterward. Component
timings cannot establish a model qualification or the required >=10% fixed1024
output-token HTTP E2E improvement. Every producer/consumer result keeps model,
whole-model, scheduler and formal-success flags False.
