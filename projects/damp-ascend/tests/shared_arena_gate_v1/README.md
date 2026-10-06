# NEW shared-arena gate v1 — preparation only, default OFF

This packet is NOT an executed NPU result. MAIN alone builds, loads, launches,
collects receipts and commits. Frozen production9/runtime13/graph6/collector,
wrapper5/service12 are unchanged. DAMP's original24h deadline is not reset.

## Exact scope and reuse

The NEW candidate is only torch.ops.qwen36_damp_arena_v2, with its exact9-source
manifest and actual no-device successful build receipt. No old torch.ops registry
is reassigned. The graph arithmetic protocol35df04… and native compressed golden
95d11c… stay byte-frozen. This runner injects only allocation, full-raw evidence
observation and contiguous actual DATA-span nonalias glue into imported modules
in this one process. No file or mathematical/oracle/update/packing change occurs.

General-SR source dependencies are pinned because the frozen protocols import
them, but this restricted graph gate does NOT execute or admit general SR.
The independent general-SR native-anchored oracle remains available for a later
NEW shared-allocation eager/general graph extension. No fabricated general pass.

Per --batch1 (physical4) or --batch16 (physical7), one logical0 shard:

- SR1/per-Hv permutation and power2/per-Hv permutation.
- Each in adjacent SoA or explicit32/64/96/32B guard-gap layout.
- Raw INT8 backing: nonzero96B outer prefix, convBF16[S,3,2560],
  hiFP16[S,12,128,16], loINT8[S,12,128,112], scalesFP32[S,12,4,112],
  then128B tail. Per slot conv15360 + hi49152 + lo172032 + scale21504B.
- Exactly three separate raw arenas (two captured graphs and one eager feedback)
  plus separate resettable warmup arena. Retain raw AND typed views throughout.
  Typed views must share the backing, be physicalND themselves, be contiguous,
  have nonzero offsets/32B pointers. A typed format_cast that silently creates
  independent backing is forbidden.
- Cold prepare outside capture;3 numerical warmups;2 actual NPUGraph captures;
 8 identical resets;160 changed Q/K/V/g/beta/slot turns. Synchronize inputs before
 replay. The candidate, both graphs and independent golden carry their OWN
 feedback. State resets occur only at explicitly registered phase boundaries,
 never between changing turns to conceal errors.
- Selected and COMPLETE restored-state relativeL2<=1e-5, output<=0.00303,
  finite tensors, bitwise untouched slots/inputs/pointers, graph-eager bitwise
  equality. Entire conv/padding/prefix/tail raw bytes are invariant at every
  relevant prepare/capture/reset/replay/eager observation.
- Original9(B1)/11(B16) dynamic metadata negatives replay on the same graphs,
  allNaN output/no-state-write, exact all-byte/pointer invariance then legal
  recovery.15 eager actual-overlap cases/graph case: three partial32B state pairs,
  one shared-start state pair, all11 readonly kinds overlap high. Valid
  shape/dtype/alignment/bounds, exact host DATA-overlap rejection and entire raw
  no-write required. Malformed eager pointer arguments are not graph replay tests.

Actual data spans are independently checked from pointer/count/width/backing/
storage_offset. Merely different Storage objects or shared-base presence cannot
prove nonalias or overlap. Cross-layer ownership/sharing and actual vLLM allocator
execution are NOT proved by this synthetic same-storage gate.

Meta checks remain inherited LIMITED structural checks. Meta success is not
physicalND, pointer/values, graph or service admission. T2..15, mixed scheduling,
general-SR graph, arbitrary slot geometry, final192 calibrated plans, TP4 model,
functionalization/torch.compile, E2E throughput/TTFT/TPOT and task quality are
explicitly outside this receipt. No persistent FP32 production sidecar is used.

## Failures and source lock

Runner accepts only a NEW external output directory. It retains raw-before,
CPU golden and original dispatch exception separately from nullable CPU-after
copies before assertions/first_failure.pt. JSON is finite via frozen safe_json.
No automatic rerun, threshold relaxation or post-failure resync. A poisoned
context is never replaced by another unguarded copy in final cleanup.
Source/runtime/library/receipt are hash-checked before load and after completion.
Actual /proc/self/maps library identities are recorded.

## MAIN-only commands

First preflight (no Torch, no build/load/NPU):
  /usr/bin/python3 -B -m unittest discover -s projects/damp-ascend/tests/shared_arena_gate_v1 -p test_software_contract.py -v

No-device source receipt admission:
  /usr/bin/python3 -B projects/damp-ascend/tests/shared_arena_gate_v1/run_shared_arena_gate.py --audit-only --batch 1 [all identities below] --output-dir /cache/cch/qwen36-damp-20261006/shared-arena-audit-v1

Actual single-shard command in MAIN's nonprivileged one-card SAME immutable image:
  /usr/local/python3.12.13/bin/python3 -B projects/damp-ascend/tests/shared_arena_gate_v1/run_shared_arena_gate.py --batch 1 --library /cache/cch/qwen36-damp-20261006/arena-wrapper-v2-build-v1/cmake/libqwen36_gdn_damp_arena_v2_decode_ops.so --library-sha256 ACTUAL_SO_SHA --source-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/arena_wrapper_v2/source_manifest.json --source-manifest-sha256 c05354c54175bcaa15c1637ff335febcc2500b0c0489e37db5354d65d4a5001f --runtime-manifest /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/tests/shared_arena_gate_v1/runtime_manifest.json --runtime-manifest-sha256 ACTUAL_RUNTIME_SHA --build-receipt /cache/cch/qwen36-damp-20261006/arena-wrapper-v2-build-v1/build-receipt.json --build-receipt-sha256 ACTUAL_RECEIPT_SHA --device-proof ACTUAL_FRESH_PHYSICAL4_PROOF --device-proof-sha256 ACTUAL_PROOF_SHA --native-source-manifest ACTUAL_NATIVE_MANIFEST --native-source-manifest-sha256 ACTUAL_NATIVE_MANIFEST_SHA --output-dir /cache/cch/qwen36-damp-20261006/shared-arena-b1-v1

Environment: DAMP_RUN_SHARED_ARENA_GATE_V1=1,
DAMP_ENABLE_ARENA_WRAPPER_V2=1, ASCEND_RT_VISIBLE_DEVICES=0,
PYTHONDONTWRITEBYTECODE=1; SAME native/bootstrap library/OPP paths as the accepted
production gate. For B16 change --batch16, parent physical7 proof, NEW output
shared-arena-b16-v1. Literal proof requires only [4] or [7] and {"0":physical};
not an old physical4 proof relabelled as7. TTL30min applies before set_device.

The command's ACTUAL_* identities deliberately cannot be invented before MAIN's
build/launch. Source compile receipt schema damp_arena_wrapper_build_v2 records
exact9 sources, source manifestSHA, librarySHA, imageSHA, npu_arch=dav-2201,
actual successful command/log hashes, nm-defined T/W symbol audit and actual OPP9.1
identity. No CANN/device reuse inferred from a README.
