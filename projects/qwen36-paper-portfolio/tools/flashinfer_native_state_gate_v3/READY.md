# FlashInfer native-state gate v3 — SOFTWARE ONLY / DEFAULT OFF

This independent packet adapts FlashInfer Eq.1–3 normalized output + natural-log
LSE composition to the deployed CANN old-FIA and npu_attention_update.
It does not install FlashInfer, substitute its scheduler, or claim new tiling/
service benefit because vLLM-Ascend already uses native merge. Public source
proves an API family, not actual BNSD/BF16/empty-domain/graph support.

Primary sources:
https://arxiv.org/html/2501.01005v1
https://raw.githubusercontent.com/vllm-project/vllm-ascend/v0.23.0/vllm_ascend/attention/context_parallel/attention_cp.py
https://raw.githubusercontent.com/vllm-project/vllm-ascend/v0.23.0/vllm_ascend/attention/context_parallel/common_cp.py
https://www.hiascend.com/doc_center/source/zh/Pytorch/600/apiref/apilist/ptaoplist_000837.html
https://raw.githubusercontent.com/Ascend/op-plugin/7.3.0/op_plugin/config/op_plugin_functions.yaml

## One default-OFF entry, independent consumer

MAIN reviews/applies canonical.patch only to the independent new
projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3/ directory,
then independently checks every source and manifest SHA. No H8/shared source,
algorithm, Docker image or global schema is patched.

Default OFF:
  /usr/bin/python3 -B .../flashinfer_native_state_gate_v3/main.py

Source audit (no Torch/Docker/NPU):
  /usr/bin/python3 -B .../flashinfer_native_state_gate_v3/main.py --source-audit-only --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_SOURCE_MANIFEST_SHA

The one MAIN-only device CLI, NOT executed by the preparation agent:
  /usr/bin/python3 -B /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3/main.py --host-execute --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/flashinfer_native_state_gate_v3/SOURCE_MANIFEST.json --source-manifest-sha256 ACTUAL_SOURCE_MANIFEST_SHA --output-dir /cache/cch/flashinfer-native-state-v3-UNIQUE_NEW_LEAF

Only that exact command/order is admitted. A shell/taskset/timeout wrapper is
not equivalent original authority. MAIN serializes physical6 with other jobs.
The parent directory must exist; the leaf must be new. The controller itself
creates a unique exact owned CID and invokes its source-bound canary/numerical
child. A prior leaf/CID/result is never reused.

After completion MAIN saves the ORIGINAL AWMCP envelope including targetPeerId,
routeDecision and original terminal record from its actual terminal operation.
The producer cannot invent that terminal Ref before return. Independent consumer:
  /usr/bin/python3 -B .../flashinfer_native_state_gate_v3/main.py --consume --source-manifest CANONICAL_SOURCE_MANIFEST --source-manifest-sha256 ACTUAL_SOURCE_MANIFEST_SHA --launch-proof NEW_OUTPUT/launch.json --launch-proof-sha256 ACTUAL_LAUNCH_SHA --terminal ORIGINAL_AWMCP_ENVELOPE --terminal-sha256 ACTUAL_ORIGINAL_ENVELOPE_SHA --execution-authority NEW_OUTPUT/RESULT.json --execution-authority-sha256 ACTUAL_RESULT_SHA --report NEW_OUTPUT/gate/report.json --report-sha256 ACTUAL_REPORT_SHA --expected-peer lgw_a6109c51076a4a2c9d2674ca5a8704a0

The terminal's unique host marker binds exact immutable RESULT bytes. RESULT
binds launch, numerical child/marker/report, real process/protection/cleanup
evidence. --inspect-abi/partial/failed/timeout/cancel/wrong-peer/old-H8 records
cannot satisfy numeric consumer. Software fixtures are never numerical PASS.

## Frozen source and launch closure

Nine own files + three exact reviewed generic host dependencies =12 sources.
H8 host SHA4ddd75...e5e20 is imported without global mutation. Only generic
hardware/process/effective CPU/resource/cleanup mechanics are inherited.
Owner, create/inspect, mounts, cutoff and pipeline are independent overrides.
The frozen host helper and old exec/parser SHAs are also bound. No H8 launch,
source manifest, algorithm or numeric authority is reused.

The future MAIN-owned tiny canary reads actual installed version/source and
mapped native library; exact CANN9.1.0 must come from install metadata, never a
directory-name inference. CP/native/CANN bytes are snapshotted into owned output.
Each dual Ref binds actual runtime_ref + same-SHA host-readable snapshot_ref.
Native resolver rechecks runtime bytes and actually mapped library. These
snapshots are produced only by that future canary, not preparation.

Launch has one sentinel only at --launch-proof-sha256 in its argv template.
Validator requires the actual immutable launch byte Ref (SHA never optional),
requires its actual bytes equal canonical JSON+newline, expands the actual
Ref SHA, then compares the ENTIRE child CLI. No cyclic self-hash, substring,
flag-only agreement, old canary or guessed schema can satisfy it.

## Unchanged complete matrix, not service authority

Batch1..16/query width1,4/eager once + graph trials0,1,2/160 changing steps:
128 cases and20480 actual numerical steps. BF16 BNSD/qheads6/KVhead1/D256;
384-token persistent rows split128×3. Heterogeneous lengths, inactive lanes,
all-empty domains, mixed prefill/decode, row permutation/generation/paused rows/
release/reuse/reset all participate. Stable guarded graph buffers are updated
outside capture.

Independent scalar oracle evaluates direct full attention in stdlib; MAIN
CPU-FP64 direct unsplit attention uses original BF16 inputs, not native/candidate
states. Native full control and partial/native-update candidate are gated per
request/query/head (never GQA mean), natural LSE and exact empty identities.
Invalid partial values are sanitized BEFORE multiplication to prevent0*NaN.
Original undefined native outputs are retained on failure, never rewritten to
manufacture agreement.

Thresholds remain relativeRMS<=.005/cosine>=.99998/maxAbs<=.00303/
naturalLSE maxAbs<=.00303. Zero reference requires exact zero. Every step checks
guards/pointers/cache/paused rows/reuse/masks/defined finite predicates.
Raw checkpoint is written before assertions; failed/pending raw is retained.
Only exact owned passed checkpoints are discarded. Case Refs stream into host
consumer to avoid a monolithic report. Schedule-only tests are not actual steps.

## Resource, admission and exact stop-retain

Only physical6→logical0 +3 control nodes. Guest8GiB/1CPU, host256MiB/1CPU,
ordinary reserve8GiB/2CPU. Initial ordinary floor16.25GiB; later8.25GiB.
Hugepages are not additive. Owned output5GiB (incl.snapshots) + disk reserve8GiB.
Actual host/daemon ancestor quota/cpuset/PID affinity and guest effective cgroup
CPU are checked. os.cpu_count is not admission. Docker CLI alone restores AS
to unlimited; host inherited hard AS must be unlimited and softAS stays256MiB.

Fixed cutoff2026-10-09T11:17:31Z; whole phase5400s incl90cleanup must fit.
Neither child nor per-step deadlines extend it. Foreign4–7 actual NPU process/
nonidle HBM or physical6 open-FD/UDA conflict fails closed. Devices declarations
alone are recorded, not blockers. Protected0–3 PID/start_ticks/cgroup/argv hashes
must remain identical. Actual numerical physical6 Python PID/namespace PID/
start time/argv/hash/cgroup is retained and distinct from canary.

Original primary and secondary cleanup/source errors are both retained.
Full exact CID/image/labels/mounts/devices/resources inspect precedes stop.
Only that CID is stopped and retained; never docker rm/global stop/delete.
Final stopped inspect, release idle and0–3 protection are mandatory.

## Honest pending status

Actual stdlib command/exit/stdout/stderr/source SHA receipts are delivered
separately. No preparation Torch/Docker/NPU/build/model execution occurs.
Actual canary/installed schema/out-workspace/LSE ABI,128-case graph matrix and
stop-retain/original terminal consumer remain pending.

Even complete numeric consumer success leaves ready/serving/model/FlashInfer
scheduler or tiling benefit/matched fixed1024 C16/final2048 tasks false.
No formal24h paper clock is started. Next independent authority requires a
real vLLM TP4/64-layer allocator+model consumer, matched frozen dense1024 and
final2048 tasks; existing native merge is not new E2E benefit.
