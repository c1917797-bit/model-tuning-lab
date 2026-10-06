# New production integer-compaction candidate gates — prepared only

Only this NEW tests directory is adapted. Original v4, original runners,
independent oracle/reference, collector and frozen helpers remain unchanged.
No build, dlopen, Meta or NPU execution is claimed by source preparation.
MAIN owns the sole build/load/NPU launch and all Git/container operations.

Namespace: qwen36_damp_integer_compaction_v1.
SO: libqwen36_gdn_damp_integer_compaction_v1_decode_ops.so.
External prepare6/decode14 packed-state ABI remains FP16 hi[S,12,128,16],
INT8 lo[S,12,128,112], FP32 scales[S,12,4,112]; per-Hv INT32 logical plans,
original-coordinate positive FP32 SR, model HQ4/HV12. B1/B16 one-token only.
There is NO assignment/monkeypatch to torch.ops.qwen36_damp.

## Exact reuse route and numerical boundaries

Fully read/pin original tests/restricted_native_golden_gate.py,
native_compressed_golden.py, native_call_contract.py, independent_oracle.py;
tests/general_sr_native_gate.py and general_sr_contract.py;
operator/diagnostic/run_saved_step45_trace.py. These seven files are immutable
runtime dependencies, with literal SHA in gate_contract.py. This is not reuse
of the candidate's quantizer as its own golden.

protocols.py imports original fixture generators/independent pack/unpack and
actual native helper. Copied general-SR anchor/general functions retain the
same transformations, arithmetic, fixtures, independent feedback and frozen
limits. Candidate is explicitly injected, not selected by an old namespace.
Only dispatch/evidence seams and complete-backing-storage nonalias are changed.
The software contract compares the numerical/guard AST and feedback statements.

Preregistered stages:

- step45: exact source-bound B1/SR1 failure fixture SHA59795dea...70598;
  re-establish its actual loaded native golden on the same immutable input.
  Require all THREE complete packed regions and BF16 output bitwise equal to
  saved native golden, plus immutable/pointer/untouched/ND/nonalias guards.
  This stronger single-case quantizer repair test is NOT a160step pass.
- restricted: original B1/B16 × SR1/power2 per-Hv permutations, changing
  Q/K/V/g/beta and indices for160steps, independent native compressed feedback.
  Original selected-head state<=1e-5 and output<=0.00303 remain; complete
  original-coordinate state is additionally checked<=1e-5.
- anchors: six independent reference/native cases B1/B16 × SR1 identity,
  SR1 per-Hv permutations, power2 per-Hv permutations,160steps; COMPLETE
  transformed FP32 state and restored BF16 output BITWISE. Native Q/K expand
  modelHQ4→NK12 before each Hv Pk; only dyadic/power2 V/c cast is legal.
- general: ALWAYS runs ALL six anchors first, then B1/B16 × general positive
  FP32 SR/random and near-half-cell stress,160steps. Reference receives
  ORIGINAL BF16 V, divides in FP32 and restores readout before its sole BF16
  cast; independently packs its OWN updated state, never candidate feedback.
  Selected and complete state<=1e-5, BF16 output<=0.00303; finite/immutable/
  untouched/full-storage/pointer guards mandatory. No resynchronization.
- all: step45, four restricted cases, six anchors, four general cases.
  <160steps receipts are smoke-only. No automatic retry or gate relaxation.

Candidate has only3 persistent typed buffers. FP32 reference arenas/updated
tensors are test-only diagnostics. Synthetic general SR does NOT cover final
192 calibrated plans, graph, mixed scheduler, lease/page copy, cache manager,
TP4 model serving, throughput, TTFT/TPOT or GSM8K/LongBench-v2 accuracy.

## Evidence/failure retention

Before a dispatch, CPU input/full-state/golden snapshots are retained. The
original dispatch/synchronize error is saved separately from nullable output/
input D2H errors; a poisoned context must not erase before/golden evidence.
Actual output and full packed-after bytes are retained before unpack/finite/
format/numerical assertions. On first failure first_failure.pt and its SHA
are saved; reports preserve original and secondary errors. Full successful
turn metrics/fixture hashes are recorded, not all160 large after arenas.
step45 always saves its actual fixture artifact. Never retry a partially
written production group or recycle a failed slot into serving.

## Provenance contracts (separate compilation and runtime sets)

source_manifest.json is the candidate's parent-owned source-preparation
manifest, containing EXACT nine repo-relative compiled_sources. MAIN's actual
NEW successful build receipt uses schema damp_production_integer_compaction_build_v1,
status compiled_no_device, same sources9, library_sha256, image_id frozen
660ce..., npu_arch dav-2201, configure/build commands with exit_code0 and
log_sha256, npu_executed:false, physical_soc_runtime_observed:false. It also
records actual exported_kernel={name: ...,defined:true,type:"T"/"W",
audit_sha256: actual nm/readelf log SHA}; UND/link-only must reject.
Failed build-v1 receipt is never edited into a success.

MAIN's actual v3 receipt cann_identity fields are root:/usr/local/Ascend/cann-9.1.0,
opp_version_info_sha256:84127975...b9e6, version_info:actual full file content;
flat cann_version_info_sha256 must match. The NEW contract uses these actual
fields, not the earlier probe receipt's differently named fields. Runtime
checks root/opp/version.info hash, full content equality and Version=9.1.0
under configured ASCEND_HOME_PATH. This proves OPP component, not all SDK
package versions or physical runtime SoC. Older source/audit bytes are archived.

runtime_manifest.json separately binds the six NEW executable/support/test
files plus seven frozen protocol/helper files (13 runtime sources); it is not
a compilation manifest or old receipt. Every required input manifest/receipt/
SO/report is explicitly SHA-pinned. Output root must be NEW, absolute and
outside Git; parent directory must already exist.

NPU native-source-manifest is a NEW parent authority file, not an old rewritten
report: native_commit5cb98c..., native_header_sha25696e6d966..., image_id,
source_contract_passed:true, native_runtime_library_path +SHA. The runner
verifies real process mappings after dispatch. For anchors/general/all it
additionally requires exact frozen reference_source_hashes10 and
reference_library_path + reference_library_sha256 bound to command arguments.
The numerical native anchors, not source hashes alone, identify its arithmetic.

Device proof is original external-MAIN contract: unique physical_npu_ids4–7,
logical_to_physical["0"]=4, privileged:false,
exclusive_resource_check_passed:true, observed_at_unix_ns nonfuture<=30min.
The runner itself checks actual Ascend910B4 and frozen Torch/TorchNPU versions;
a no-device build's target declaration is not runtime observation.

## Parent-only commands — prepared, not executed

Stdlib source/receipt/error retention:

    /usr/bin/python3 -B projects/damp-ascend/operator/production_integer_compaction_v1/tests/test_software_contract.py

Actual same-image NO-device load/schema/Meta uses run_meta_gate.py with ALL
required identity flags:

    --library /ABS/NEW/libqwen36_gdn_damp_integer_compaction_v1_decode_ops.so
    --library-sha256 ACTUAL_SO_SHA
    --source-manifest /ABS/REPO/projects/damp-ascend/operator/production_integer_compaction_v1/source_manifest.json
    --source-manifest-sha256 ACTUAL_MANIFEST_SHA
    --runtime-manifest /ABS/REPO/projects/damp-ascend/operator/production_integer_compaction_v1/tests/runtime_manifest.json
    --runtime-manifest-sha256 ACTUAL_RUNTIME_MANIFEST_SHA
    --build-receipt /ABS/NEW/build-receipt.json
    --build-receipt-sha256 ACTUAL_RECEIPT_SHA
    --output-dir /ABS/NEW/meta-gate-v1

Meta calls use only checks actually implemented in new register.cpp; no
permutation/SR values, physical ND, real device/alias/slot/graph is claimed.
Eager prepare negative matrices, malformed dynamic metadata, blocked format
and expanded T2..15 support remain separate NPU gates. Not silently inherited
from original operator receipt.

Actual NPU command calls run_npu_gate.py with SAME identity flags PLUS:

    ASCEND_RT_VISIBLE_DEVICES=0 DAMP_ENABLE_INTEGER_COMPACTION_V1=1
    DAMP_ENABLE_NATIVE_REFERENCE=1 PYTHONDONTWRITEBYTECODE=1
    --stage all --steps 160
    --device-proof /ABS/FRESH/physical4-logical0.json
    --device-proof-sha256 ACTUAL_DEVICE_PROOF_SHA
    --native-source-manifest /ABS/NEW/native-source-manifest.json
    --native-source-manifest-sha256 ACTUAL_NATIVE_MANIFEST_SHA
    --reference-library /ABS/INDEPENDENT/libqwen36_damp_native_reference_ops.so
    --reference-sha256 ACTUAL_REFERENCE_SO_SHA
    --step45-fixture /ABS/ORIGINAL/first_failure.pt
    --step45-source-report /ABS/ORIGINAL/report.json
    --step45-source-report-sha256 ORIGINAL_REPORT_SHA
    --output-dir /ABS/NEW/npu-gate-v1

Use --stage step45/restricted/anchors/general in separate NEW roots for
risk-proportional single experiments. No stage auto-starts Docker, builds a SO,
collects profiling or claims E2E benefit. MAIN must wait for independent
compaction NPU/API gates, review the candidate and inspect physical4 before
dispatch; this source package does not authorize activation.
