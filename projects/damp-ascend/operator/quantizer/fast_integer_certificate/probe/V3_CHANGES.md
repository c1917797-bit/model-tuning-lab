# V3 launcher correction — no load or NPU pass promised

MAIN actual v2 MA02dc compiled CXX/ASC/linked a shared library, SHA
4fd87e85a0ecf97b4613477f9d52517e80e90c3bb9931f378d5d37238ce21b53.
MAIN actual no-device Meta MA02f1 FAILED at ctypes dlopen:
undefined symbol qwen36_damp_integer_certify_bits_kernel.
MA02f6 and exact extraction02f7 proved that both the SO and
certificate_torch.cpp.o have this sole U; readelf lists GLOBAL DEFAULT UND.
Raw evidence is /cache/cch/qwen36-damp-20261006/integer-certificate-symbol-audit-v1/output.log.
Shared-object link success allowed the unresolved symbol and was NOT load proof.
Original v2 build/Meta receipts, runtime manifest and source archive are untouched.

audit/kernel-source-v2.asc.txt exactly preserves the actual v2 source:
SHA e623bb047aad35a972f2c49e40260297cc5853a5fe703bb0764a773bd0954dd3.
v1 archive SHA0c845f2e4bf237ff2e5b08cf7dfe0d932dc65de38b8dc28d89c0b74278b7e00c
also remains untouched.

Minimal NEW compile-source change is only certificate_probe_kernel.asc:
the annotated global DEFINITION (same13 GM arguments, braces) is visible in
both ASC passes. Only certificate_probe.h include and device body are guarded
by defined(__NPU_ARCH__). The frozen parent's non2201 #error remains unchanged.
Original device body is preserved byte-for-byte; no arithmetic, dataflow,
allocation, input admission, quantizer/oracle/tolerance change. Wrapper/CMake
and the other6 compile sources plus2 frozen headers are unchanged.
The successful isolated exact_bits and KVBuffer sources likewise expose an
unconditional global definition in the ASC-compiled wrapper translation unit.
Their queued stream(false)/RunOpApi ABI is not changed to plain-C++ stream(true).

Source-only software test now rejects a declaration-only host projection and
verifies the archived v2 device body is unchanged. This is NOT a compiler or
host-launcher proof. New runtime16 manifest binds the changed kernel and test;
old audit/runtime-source-manifest-v2.json is preserved as the old identity.
Runner and its9-compiled/16-runtime receipt contract are unchanged.

MAIN must use a new nonoverwriting integer-certificate-build-v3 directory.
After successful configure/build, nm/readelf must show the same global kernel
as a defined exported host symbol rather than U/UND. Only then perform a new
same-image dlopen/schema/Meta observation. Any failure remains saved; no
unchanged rerun and no NPU correctness inference from compilation or Meta.
Physical SoC must still be observed independently on NPU; OPP9.1 identity,
immutable image, source/SO receipts and all numerical gates remain unchanged.
Production/GatherMask/graph are still unproven and disabled. DAMP deadline
remains 2026-10-07T08:48:03Z.

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
