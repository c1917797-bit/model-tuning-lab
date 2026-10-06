# Independent integer-certificate NPU probe — NPU NOT RUN
This directory alone is NEW. Frozen5 certificate files, frozen16 exact probe,
production/trace/reference/cache code are unchanged. MAIN owns Docker/build/
NPU/Git. Reuse of the previously compiled exact-bits queued ASC wrapper is
source provenance, NOT proof this new target compiles or is numerically correct.

## Contract
Explicit torch.ops.load_library(libqwen36_damp_integer_probe_ops.so) registers
qwen36_damp_integer_probe.prepare(x_bits,scale_bits,proposal_magnitude) -> (),
and certify_bits(same3 INT32 vectors) -> seven fresh INT32[N+16] full buffers:
accepted, lowerFloor, upperFloor, lowerDomain, upperDomain, finalSignedCode,
finalValid. Only N64/896. Separate namespace/SO; no automatic fallback or global
native replacement. The7 output sentinels are in op_kernel/probe_plan.h.

Inputs require same910B4 device, contiguous1D physicalND,32B alignment, equal
shape and disjoint COMPLETE backing storage byte intervals (including guards).
Each prepare/certify synchronously copies proposal to CPU and rejects every
value<0 or>127 BEFORE any Gather/dispatch. This is deliberately diagnostic:
not a performance implementation and not graph-compatible. Meta cannot inspect
proposal values, physicalND or pointer aliasing; those gates are device-only.
Synchronous D2H on capture must not be relabeled graph support.

prepare validates then publishes immutable C/F LUTs and tiling by(device,N).
First H2D occurs only in explicit prepare. Cached prepare checks inputs again;
no first-use H2D in certify. Cold preparation flushes queue outside the launch
lambda and completes ACL memcpy before publication. The ASC compiled wrapper
uses stream(false)+OpCommand::RunOpApi+triple-chevron inside lambda, NOT direct
C++ kernel launch stream(true). The deployed public get_npu_format and
npu_format_cast are kept for physicalND inputs, outputs and plans.

C/F LUT128 signed INT32 elements are internal constexpr tables, logicalj
converted to UINT32 BYTE offsets inside frozen helper. Slot127 duplicates126.
SHA256 of little-endian INT32 arrays:
C 7c6e8dbfe3ea2a3dcaf62ab2ef14936d2d9252a36738eb6b78ba4b1d37c7c708
F 2df58f09be50ce6051418c229acf641a37c9596f1826884ee02d7a02b1581a83
C||F c58fdd435e302b9209203dcbdd38b7e456bed8f0d425d9f7339ca5b46e3582c8
Software asserts exact digests; kernel receives only cached internally madeLUT.
Plan mutation malformed-LUT public negative is not applicable: no table input.

Exported lower/upperDomain is POSITIVE NORMAL FINITE originalscale AND normal
endpoint exponent. Frozen EndpointFloor w7 alone expresses only exponentdomain;
the probe explicitly combines originalscale validity. Floors are safe normal
synthetic placeholders when domain0; they have NO threshold authority.
The software model retains exact placeholder bits, while independent Fraction
multiplication/floor independently checks every domain1 endpoint.
Only accepted0/1 can bypass ExactCode; its original x raw sign restores signedn.
Rejected lanes use frozen exact_quantizer_bits.h EXACT target
clip(RNE_integer(RN32(x/s))). Invalid x/scale must return valid0/code0.
No epsilon, half-tie snap, scale floor, oracle/tolerance change or FP32 sidecar.

## Kernel/dataflow/UB
Sole AIV writes7 whole N*4 output interiors, offset8ints=32B; guards untouched.
TQue input/LUT DataCopy->EnQue/DeQue makes MTE2->V readiness.
Frozen Certify135 vectorAPI/fence calls is unchanged. Two EXTRA EndpointFloor
calls plus output copies export diagnostic endpoints; probe cost is not a
production speed number. Explicit V_S Fetch/Set/Wait precedes scalar reads.
The scalar loop visits all lanes but calls ExactCode only rejected lanes.
Explicit S_V precedes VECOUT queues' V->MTE3 output handshake.

Explicit UB max:
3inputs*896*4=10,752B;2LUT*128*4=1024B;7outputs*896*4=25,088B;
16scratch*896*4=57,344B; total94,208B. Add CANN/compiler stack and alignment
overhead during build/device review; this is not allocator proof.
No GatherMask compaction is implemented. An exact isolated pass CANNOT enable
a deployable fast path: sparse compaction and production costs remain gaps.
No graph, packed feedback, cache-manager, E2E or task-accuracy pass is claimed.

## Provenance and audit
CMake/queued wrapper are adapted from source-frozen exact_bits target; it
previously compiled with deployed CANN9.1/Torch2.10.0+cpu/TorchNPU2.10.0.post4.
CMake binds frozen AscendC helper SHA e96cbd... and ExactCode f5d380... exactly.
Runner separately binds9 actual compiled dependencies to the compiled manifest
and successful build receipt, and all16 runtime dependencies to a separate
runtime manifest. Its compiled9 subset must match runtime16, with6 frozen
dependencies also checked explicitly. It hashes the actual loaded .so
and relevant /proc/self/maps libraries, all raw artifacts and fresh physical
NPU4–7 preflight. The registered Meta layer is only shape/schema evidence.

Reviewed maintainer Paper-to-Ascend, loop/evidence/environment/host skills and
Cannbot direct-invoke/PTA+anti-pattern/sync/API/precision references. PTA route
A applies because ASC file embeds triple-chevron; plain C++ stream(true)
recommendation does not replace the queued architecture. Generic claim that
TORCH_LIBRARY/Meta implies graph support is not used. OriginalCannbot/source
repos are read-only; scanner side effects must be checked before execution.
All reported static candidates are retained, not erased to make code look green.

## Preparation commands — MAIN only, no devices for build
Use exact immutable-image no-device build setup that successfully compiled
exact_bits, verifying Python/compiler paths first. Do not start extra NPU.
Fresh nonoverwriting build root:
```sh
set -euo pipefail
test ! -e /cache/cch/qwen36-damp-20261006/integer-certificate-build-v2
source /usr/local/Ascend/cann-9.1.0/set_env.sh
cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/quantizer/fast_integer_certificate/probe -B /cache/cch/qwen36-damp-20261006/integer-certificate-build-v2 -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3 -DCMAKE_BUILD_TYPE=Release
cmake --build /cache/cch/qwen36-damp-20261006/integer-certificate-build-v2 --target qwen36_damp_integer_probe_ops -j2
```
SO is libqwen36_damp_integer_probe_ops.so. Source/build receipts must reflect
actual hashes and terminal successful compilation, not these instructions.
Do not delete/overwrite old build targets or erase failed logs.

Pure-software check (no torch import):
```sh
PYTHONDONTWRITEBYTECODE=1 python3 projects/damp-ascend/operator/quantizer/fast_integer_certificate/probe/run_certificate_gate.py --software-only
```

Receipt contracts required before same-image Meta and then MAIN device run:
--source-manifest uses the actual compiler document with NO schema:
sources=exact COMPILED_NAMES9 relativepath->SHA map (7new+2 frozen headers).
--runtime-manifest is SEPARATE, schema=damp_integer_certificate_runtime_sources_v1,
sources=exact SOURCE_NAMES16 relativepath->SHA map.
compiled9 must equal the runtime16 subset; unknown/drift/missing bindings reject.
build_receipt.schema=damp_integer_certificate_build_v1,
status=compiled_no_device,npu_executed=false,physical_soc_runtime_observed=false,
sources=compiled9,commands configuration/build each exit_code0 plus log hashes,
library_sha256=actualSO,npu_arch=dav-2201,image_id=frozen660ce23a... identity.
cann_identity={version:"9.1.0",component:"opp",
version_info_path:"/usr/local/Ascend/cann-9.1.0/opp/version.info",
version_info_sha256:actual841279757459d4eabc1c8cfea69d3e1dc0fc9db3eb0c18100294cd5c1301b9e6}.
Meta/NPU phases read actual OPP file, check hash and Version=9.1.0 line, plus
configured ASCEND_HOME_PATH. This proves OPP component identity, NOT every
SDK package. No-device target dav-2201 is NOT runtime SoC proof; NPU separately
checks actual Ascend910B4. version.cfg paths were actually absent; do not invent them.
preflight.schema=damp_integer_certificate_preflight_v1,passed=true,
mapping_proven=true,no_external_npu_processes=true,physical_devices=[oneof4–7],
logical_device=actualmapping,soc=Ascend910B4,checked_at_utc=fresh<=300seconds.
Parent must release its TP4 capture before this single-NPU probe; source/receipt
checks cannot grant competing execution permission.

Example device phase (actual .soSHA/paths supplied by MAIN):
```sh
PYTHONDONTWRITEBYTECODE=1 python3 projects/damp-ascend/operator/quantizer/fast_integer_certificate/probe/run_certificate_gate.py --library /cache/cch/qwen36-damp-20261006/integer-certificate-build-v2/libqwen36_damp_integer_probe_ops.so --library-sha256 <actual-SO-SHA> --source-manifest <actual-compiled-source-manifest.json> --runtime-manifest <actual-runtime-source-manifest.json> --build-receipt <actual-build-receipt.json> --preflight <fresh-parent-preflight.json> --logical-device 0 --repeats 20 --output-dir /drrqr-results/integer-cert-npu-v1
```
For NO-device schema/Meta add --meta-only and omit --preflight; choose separate
new output directory. Unknown/path-mismatched/source-drift receipt fails closed.

## Actual matrix
N64 and89620 changed-input/lane-boundary calls with complete input-root and
pointer preservation; cold/cached prepare mutations saved and checked.
All127*254*12=387096 endpoint rows; all40,316 frozen labeledfixtures at proposals
true±1/0/127 plus all128 arbitrary proposals every257th fixture; savedstep45
wrong117 rejects/correct118 accepts, domain invalid/subnormal/extreme/signzero.
Seven complete guards/output bits and independent code/valid golden checked.
Raw returns and after-inputs saved BEFORE assertions, including faileddispatch.
Negative N0/63/65/897/1792, wrongdtype/shape/noncontiguous/misaligned,
alias/disjointviews-of-same-storage, CPUmixed/allCPU and proposal -1/128/129/
INTMIN/INTMAX, plus certify-before-prepare. Both entrypoints reject.
Physical other-format and cross-NPU-device negatives are NOT generated here;
wrapper rejects those shapes/formats but their actual negative test remains
unexecuted. Avoid unauthorized secondNPU just to manufacture that case.
Graph/GatherMask/productionstate are NOT validated; do not silently mark them.

## Actual build evidence and outcome
MAIN v1 build MA02be actually FAILED during ASC host pass. Its immutable
receipt/logs remain at /cache/cch/qwen36-damp-20261006/integer-certificate-build-v1/.
Original kernel source is preserved verbatim as audit/kernel-source-v1.asc.txt
with SHA0c845f2e4bf237ff2e5b08cf7dfe0d932dc65de38b8dc28d89c0b74278b7e00c.
Only NEW kernel.asc now exposes launcher declaration/plan to host and includes
device implementation under the SDK public defined(__NPU_ARCH__) boundary.
The frozen parent2201 gate is unchanged. MAIN v2 MA02dc actually compiled
CXX/ASC and linked successfully: receipt statuscompiled_no_device, both command
exit0, noNPU/physicalSoC observed. SO SHA
4fd87e85a0ecf97b4613477f9d52517e80e90c3bb9931f378d5d37238ce21b53.
Actual receipt is /cache/cch/qwen36-damp-20261006/integer-certificate-build-v2/build-receipt.json.
NO schema/Meta load or NPU pass has been reported at this documentation point.
Software v2 MA02e6 passed387096 endpoints/221676 proposals/unsafe0 plus3 failure
save simulations and13 receipt negatives; raw stdout is audit/software-v2.json.
Separate runtime16 manifest is audit/runtime-source-manifest-v2.json.
MAIN must load/test; a mathematical or NPU pass never
substitutes for real DAMP packed160step feedback and paired serving acceptance.
DAMP deadline remains2026-10-07T08:48:03Z; do not use prep to reset its timer.

## Current v3 preparation — v2 actual load FAILURE supersedes the paragraph above

MAIN's v2 no-device Meta MA02f1 actually failed at dlopen with undefined
qwen36_damp_integer_certify_bits_kernel; MA02f6/02f7 nm/readelf confirmed
U/UND in both SO and ASC object. V2 CXX/ASC/link success is not a usable library.
Original v2 source remains verbatim in audit/kernel-source-v2.asc.txt
(SHAe623bb047aad35a972f2c49e40260297cc5853a5fe703bb0764a773bd0954dd3).

V3 minimally exposes the annotated global DEFINITION and braces to host while
guarding only device include/body. Frozen parent2201 rejection and algorithm
body are unchanged. See V3_CHANGES.md; compiled9 changes only kernel.asc,
runtime16 changes kernel.asc and test_software_contract.py. The runner is
unchanged. Use NEW integer-certificate-build-v3 plus runtime-source-manifest-v3;
old manifests/builds/Meta artifacts must remain untouched. MAIN must first prove
the host kernel symbol is defined/exported, then actually dlopen/schema/Meta.
No v3 build/load/NPU result is inferred from these preparation changes.

## Actual MAIN v3 build and no-device load/Meta — NPU NOT RUN

MAIN MA0309 ended terminal0; CMake configure/build both exit0. Actual nm exports
00000000000ac800 T qwen36_damp_integer_certify_bits_kernel (defined, not U/UND).
SO SHA f21105e61577f938fb8e039d1481e912c22760061bcd38a11348af5ec4472619.
MAIN MA031e ended terminal0 with actual dlopen/schema/Meta status=pass:
 /cache/cch/qwen36-damp-20261006/integer-certificate-meta-v2/gate/report.json
Actual v3 receipt is embedded in that report, completed UTC
2026-10-06T12:58:52.431179+00:00; immutable image660ce23a... and actual OPP9.1
identity remain bound. Loaded library/proc-map identities are reported.

Two registered schemas were observed: prepare(three Tensor)->() and
certify_bits(three Tensor)->seven Tensor. Report explicitly records two positive
Meta geometries: N64 -> seven INT32[80], N896 -> seven INT32[912].
Both prepare and certify are invoked at each geometry: four positive operator
calls, fourteen output tensors total. The successful source-bound meta_gate
also executes ten negative fixtures at BOTH entrypoints: badN0/63/65/897/1792,
wrongdtype, mismatchedshape, noncontiguous, misalignedstorageoffset and mixed
Meta/CPU device. This is twenty expected RuntimeError rejections. The report
stores only the two positive records, not twenty separate negative records;
the negative count is audited from the executed runner hash7cbefd... control
flow, not invented as an additional raw field.

Runtime16 manifest SHA8498f834d9b1713446f1bd1c723bb24892063e511ed974fe952d1971fa2487a3
and the nine compiled-source hashes bind the actual loaded SO. MAIN verified
runtime sources before/after unchanged. All old archives/build/Meta failures
remain preserved. Only these two documentation files are appended now;
compiled9/runtime16, runner/tests, production/trace and frozen helpers are unchanged.

The report explicitly states npu_executed=false, production_integrated=false,
graph_supported=false and no physical SoC runtime observation. Meta proves
shape/dtype/count/offset admission only; NOT proposal values, physical ND,
alias safety, device math, sparse compaction, packed feedback, throughput or
task accuracy. Next necessary stage is MAIN's fresh authorized NPU numerical
gate after current TP4 work releases; this no-device pass cannot enable the
production path or reset the unchanged DAMP deadline2026-10-07T08:48:03Z.
