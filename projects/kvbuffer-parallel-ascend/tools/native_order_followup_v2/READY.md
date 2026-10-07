# Native-order v2 follow-up: true middle batches and raw report consumer

This NEW six-source plus manifest packet is default OFF, source preparation only. It neither changes the frozen v1/49, v2/64 sources nor signs resource authority or a new formal clock. MAIN owns Docker, all NPU4–7 admission and execution. NPU0–3 remain protected. No old failure/receipt becomes PASS.

## Actual inputs checked during preparation

- v2 source manifest:
  /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/split_gate_v2/SOURCE_MANIFEST.json
  SHA 508ff442ede945b8fb5930f79ee597ec1dba07e5d4e778d9abc85aafda6ce9c9.
- actual compiled7 build:
  /cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924/build-receipt.json
  SHA ff4c4a22ccf3e03d57baf08d59d6494e0f1435c74fbd132bbba1e98850e30dd8.
- actual candidate library:
  same root /build/libqwen36_gdn_kvbuffer_native_order_v2_ops.so
  SHA 77b4d61f94b4a8747bd08d2223b11d87702b43186acfd2f1b2e220f7b64a065c.
- current refreshed no-device Meta:
  same root /meta-report-format-v2.json
  SHA fb765a5389ad97464597f16a43915440a46b654b3419d86a9894692d487592ee.
- old consumer closure audit:
  /opt/host/vnf/austinov/model-tuning-lab/projects/kvbuffer-parallel-ascend/tools/middle_service_bridge_v1/PACKET.json
  SHA 3b985866bec8a4deaf30899ac8b4df0cf8c5bbf7943b67f97897eede056c2755.

The build happened before an oracle EOF-format-only repair; compiled7 sources are byte-identical and the original build receipt is not rewritten. The refreshed actual Meta binds current source64. No stale Meta32bd is used. MAIN reported saved-step MA09d4 completed exit0; that isolated diagnostic is NOT this full matrix, middle-T, service or performance evidence.

## Exact retained numerical protocol

NEW namespace is qwen36_kvbuffer_native_order_v2.
middle_run.py explicitly binds the frozen v2 oracle module and calls its original run_case without replacing global torch.ops. Real T2–15 is never padded to16. Groups are:

- physical4: T2,14,15;
- physical5: T7,11,13;
- physical6: T3,4,9,12;
- physical7: T5,6,8,10.

Each T runs eager trial0 and graph trials0–2, 160 own-feedback steps each, S=T+3. This preserves64 total B1–16 cases/10240 steps (middle alone56/8960), original slot rotation, reset steps64/112, flush/nonflush/base/log/untouched guards and complete raw checkpoint fields. Output bound .00303; full/per-head materialized state relative L2 2e-6. B16's original graph active schedule remains in the B16 split gate; intermediate T uses actual all-active T as in the original generic oracle.

Native expected output finite checks are restricted ONLY to native-defined active rows. All candidate outputs, all materialized state, all log buffers and native state retain complete finite checks. No candidate NaN, threshold relaxation, clipping or native-padding rewriting is admitted.

Passed step raw files are hash-recorded and removed only by frozen oracle.run_case; first failing raw file is retained. Thus cumulative D2H and disk writes are NOT resident disk footprint. The same oracle can still incur cumulative report rewrites; this packet deliberately does not change evidence/math/timeout to optimize IO. All shapes, guards, pointers and arithmetic remain the frozen implementation.

## After MAIN landing/review: default-OFF and stdlib tests

From this NEW directory:

    /usr/bin/python3 -B -m unittest test_followup -v
    /usr/bin/python3 -B consumer.py
    /usr/bin/python3 -B middle_run.py
    /usr/bin/python3 -B middle_meta.py

SYNTHETIC tests exercise full64-case producer-shaped structures, not genuine operation/device authority. No Torch/load/NPU/Docker is called by these tests.

Set MANIFEST to this directory/SOURCE_MANIFEST.json and its actual new SHA; this is a MAIN reviewed source Ref, not runtime authorization:

    /usr/bin/python3 -B consumer.py --source-audit --manifest MANIFEST --manifest-sha256 SHA
    /usr/bin/python3 -B middle_run.py --audit-only --batches 2 14 15 --physical-device 4 --followup-manifest MANIFEST --followup-manifest-sha256 SHA

Repeat the audit command with the three exact groups above. It imports no Torch and creates no output. A current real v2 Meta14 is required before numerical middle execution; old v1 Meta14 cannot stand in for the new SO.

## No-device actual v2 Meta14 command template

The immutable image must expose canonical repo, exact build/meta/library paths read-only and ONLY the fresh output file parent writable. CANN/driver libraries and environment use MAIN's already proved no-device Meta bootstrap; no davinci compute node, no native enable_custom_op or Triton architecture call. Env TORCH_DEVICE_BACKEND_AUTOLOAD=0, PYTHONDONTWRITEBYTECODE=1:

    /usr/local/python3.12.13/bin/python3 -B middle_meta.py --execute \
      --followup-manifest MANIFEST --followup-manifest-sha256 SHA \
      --library /cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924/build/libqwen36_gdn_kvbuffer_native_order_v2_ops.so --library-sha256 77b4d61f94b4a8747bd08d2223b11d87702b43186acfd2f1b2e220f7b64a065c \
      --build-receipt /cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924/build-receipt.json --build-receipt-sha256 ff4c4a22ccf3e03d57baf08d59d6494e0f1435c74fbd132bbba1e98850e30dd8 \
      --meta-receipt /cache/cch/qwen36-kvbuffer-parallel-20261006/build-native-order-v2-20261007-0924/meta-report-format-v2.json --meta-receipt-sha256 fb765a5389ad97464597f16a43915440a46b654b3419d86a9894692d487592ee \
      --output FRESH_ABSOLUTE_OUTPUT

meta_inputs is AST-identical to frozen v2 meta_probe.meta_inputs. It now evaluates all fourteen actual T. Its actual report has Torch schema strings, new source70 before/after, maps/SO hash, nonalias output and prepare-return-None; Meta has no numerical/physical-ND/graph/service claim.

## NPU middle entry (MAIN ONLY, pending actual admission)

The single-card worker must be nonprivileged, memory.max8GiB, physical card→logical0, exact owned label/source canary/actual gate PID continuity. MAIN does fresh host fail-closed inspection immediately before launch. Unknown active owners cannot be relabelled to pass a monitor. Cross-paper NPU remains serial. Release and independent components use actual terminal/stopped/proof bytes, not a fabricated SUCCESS.

    /usr/local/python3.12.13/bin/python3 -B middle_run.py --execute \
      --batches 2 14 15 --physical-device 4 \
      --followup-manifest MANIFEST --followup-manifest-sha256 SHA \
      --identity MAIN_GENERATED_RO_IDENTITY --output-dir /kvbuffer-results/FRESH_GATE \
      --library ACTUAL_LIBRARY --library-sha256 ACTUAL_LIBRARY_SHA \
      --build-receipt ACTUAL_BUILD --build-receipt-sha256 ACTUAL_BUILD_SHA \
      --meta-receipt ACTUAL_META --meta-receipt-sha256 ACTUAL_META_SHA \
      --middle-meta ACTUAL_NEW_META14 --middle-meta-sha256 ACTUAL_NEW_META14_SHA

Execution env KVBUFFER_NATIVE_ORDER_MIDDLE_EXECUTE=1, ASCEND_RT_VISIBLE_DEVICES=0, PYTHONDONTWRITEBYTECODE=1. Import native custom operators only in this NPU path; each docker exec needs the real CANN bootstrap, not assumptions about container startup shell environment. All evidence inputs RO; only this stage output RW. Identity kvbp.native-order-middle-launch/v2 binds exact protocol, gate/followup source Refs, source70, three artifacts, new Meta14, original proof refs and preflight<=600s. MAIN registers phase budget/deadline once; this source cannot issue or extend either.

## Raw numerical consumer API and real producer requirements

API:
validate_complete(inputs, packet_ref, enabled=True, read=ordinary_absolute_reader).

inputs exact {b1,b16,middle:[four RunAuthority objects]}. Each MAIN-issued RunAuthority has the old raw fields report/identity/operation/stdout/stderr/child/peer_id/operation_id/command/args/cwd/producer_sources, PLUS expected {container_id,owner,run_id,physical_device,batches,runner_argv}. Its original successful AWMCP terminal must be completed/zero/notcancel/nottimeout/direct peer lgw_a6109c51076a4a2c9d2674ca5a8704a0; command/argv/cwd and inline or file producer bytes match the external expectation. No reconstructed RPC is accepted. Original stdout marker:

    MAIN_KVBUFFER_NATIVE_ORDER_V2_CHILD {"report":{"path":...,"sha256":...},"identity":{...},"child":{...}}

One unique marker per actual child. Four middle children may share a real outer operation with four unique markers; all six containers/reports must be distinct.

MAIN must actually produce child schema kvbp.native-order-child/v2. Mandatory sources/data, all from real execution (NOT prefilled PASS): original execution command/args/cwd/exit/error/cancel/timeout and raw streams; image identity/output paths; producer source hashes; source_before/after64(split) or70(middle); original live and stopped Docker inspect; device_proof; actual_gate_process and waiting_process; release npu-smi bytes; protected0_3 and two original protected_processes_before/after Refs; sampled resource_refs; real native binary Ref; exact cleanup stopped/PID0/retained/notdeleted. Child serving/performance flags false.

device proof schema kvbp.native-order-device-binding/v2 binds immutable CID/image/card→0/preflight, separate_canary_not_gate and original canary/mapping/host_processes/cgroup Refs. Actual gate observation retains original PID/start_ticks/NSpid/cgroup/argv and all-eight-card npu-smi table. Protected snapshots schema kvbp.native-order-protected-processes/v2 retain observed_ns and full processes0–3 (PID/start_ticks identity). Historical comparison uses those original bytes, not today's /proc for reused PIDs. Cleanup inspects the exact owned container and verifies own physical card has no process; 0–3 sets stay unchanged.

This packet does NOT include or pretend an already-run parent/shim. If these producer facts are absent, the consumer rejects. Sampled resource refs are retained/hash-bound, but independent semantic re-evaluation of sampled RAM/CPU/disk budgets is explicitly false; MAIN's resource producer/consumer protocol remains a separate requirement. Therefore this descriptor cannot replace the stronger old service admission or automatically execute a model.

Return schema kvbp.native-order-all-T-numerical-checked/v2 only. All serving/model-lifecycle/E2E/accuracy/formal-performance/graph-service flags remain false. The old v1 plugin has a hard-coded v1 op namespace; no old launcher reuse or fake legacy PASS is offered. A NEW explicit receiver/lifecycle adapter and source-bound service protocol must be reviewed after the actual v2 full matrix succeeds. B1 saved-step alone cannot authorize those steps.

## R2 source-loader boundary (MAIN source review)

R1 c680bb8836e705fdef53d7430a26ece14092db2740843b094f888578ea9305bf is retained unchanged. Its unconditional no-Torch check was incorrect for after-source validation following explicit runtime import in Meta/NPU execution. R2 only changes module() to snapshot all torch/torch_npu module identities before and after the source module itself executes. Pre-existing runtime is allowed unchanged; introducing, removing or replacing runtime roots/submodules fails closed. The source loader does not unload runtime or silently repair such failures. Default/audit software checks still run without importing Torch/TorchNPU. Two added source-bound SYNTHETIC sentinel regressions cover existing runtime and new/replaced/removed runtime; they load no real Torch or device. No oracle/compiled7/oldsource64/artifact/numerical protocol changes.
