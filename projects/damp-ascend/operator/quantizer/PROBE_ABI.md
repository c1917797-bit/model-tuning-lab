# Exact-bits isolated operator / gate (prepared, not executed)

This is NEW qwen36_damp_quantizer only. No production integration, scalarstate
sidecar, service, graph support, fast certificate, GatherMask or performance
acceptance is implied. Main agent controls builds and physical NPU4-7.

## ABI

- prepare(INT32 x_bits[N], INT32 scale_bits[N]) -> ().
- exact_bits(same) -> (INT32 codes_with_guards[N+16],
                       INT32 valid_with_guards[N+16]).
- N=64..1792, multiple64. Inputs are raw binary32 bits carried in signed INT32;
  negative signed integer values preserve their uint32 bit pattern in the kernel.
- Actual inputs: same NPU, physical ND, contiguous, 32B aligned, disjoint.
  Shape/dtype/count admission precedes upload and dispatch. Invalid float-domain
  values are legal probe fixtures: code0/valid0; they do not become valid numbers.
- Full returned backing buffers are fresh/disjoint from all inputs and eachother.
  Codes first/last8 ints=0x13579bdf, valid first/last8=0x2468ace0. Only middle N
  entries are written by the single AIV owner. No view-base assumptions.
- Meta outputs match N+16/dtype and shape/dtype/count/offset checks. No physical
  ND, SoC, memoryalias or graph guarantee follows from a Meta pass.
- prepare caches an 8-byte tiling blob by device/count, not inputs/state. It does
  synchronous H2D outside capture. cold exact_bits rejects instead of implicitly
  preparing. Exact kernel arithmetic has no floating operations, except that
  the scalar clz instruction and uint64 multiply/shift lowering require real
  compiler/NPU verification.
- Compiled for dav-2201; runtime uses aclrtGetSocName()=="Ascend910B4".
  This specific string/API must be confirmed by main's actual same-image build
  and runtime gate, not guessed from device declaration alone.

## Reused verified deployment path

The ASC wrapper includes the .asc kernel and is LANGUAGE ASC. Its launch runs
inside OpCommand::RunOpApi on getCurrentNPUStream().stream(false), matching
operator/diagnostic's actual successful queued path. Do not switch to C++ direct
stream(true). ND queries/allocation use this same TorchNPU version's public
custom_ops::get_npu_format and npu_format_cast, not unexported FormatHelper ABI.
The CMake donor retains error-checked marked metadata extraction, preventing
torch's stdout npu-smi warning from corrupting TorchConfig discovery.

License for reused CANN build scaffold is ../LICENSE-CANN. Original quantizer
bit algorithm / probe is Apache-2.0 (../LICENSE-APACHE). No upstream/image edits.

Declared probe UB: 4 queues *1792*4B =28,672B, one buffer each. No Select or
float fast path is included in this compiled probe. All raw inputs/outputs use
whole 32B-aligned regions. MTE2_S pair precedes scalar reads; S_V pair precedes
VECOUT EnQue/DeQue's V_MTE3 handshake. Main must audit actual queue/event lowering,
compile logs, and NPU guards; this description is not a hardware pass.

## Main-owned commands

Use absent external build and output directories, preserving old logs/so:

 cmake -S projects/damp-ascend/operator/quantizer \
   -B /cache/cch/qwen36-damp-20261006/quantizer-build-v1 \
   -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
 cmake --build /cache/cch/qwen36-damp-20261006/quantizer-build-v1 -j2

These commands assume the actual CANN9.1/ASC environment is loaded. Do not run
them from an unproved SDK environment or let CMake output touch the repo.

Software fixture gate, no torch import/device/build:

 PYTHONDONTWRITEBYTECODE=1 python3 \
   projects/damp-ascend/operator/quantizer/run_exact_bits_gate.py --software-only

The NPU runner requires three external main-authored receipts plus explicit SO:

- source manifest: {"schema":"damp_quantizer_sources_v1","sources":{...}}.
  Exact relative source-name list is SOURCE_NAMES in run_exact_bits_gate.py,
  each value SHA256. This includes oracle, fixture builder and runner, not just
  the compiled header.
- build receipt: {"schema":"damp_quantizer_build_v1","sources":same_map,
  "library_sha256":tested_SO_SHA,"npu_arch":"dav-2201","soc":"Ascend910B4",
  "cann_version":"9.1.0", ...actual compiler/environment/log identities...}.
  Main generates this after verifying the real compile artifacts. A self-written
  source manifest alone does not prove which source was compiled.
- fresh preflight: {"schema":"damp_quantizer_preflight_v1","passed":true,
  "mapping_proven":true,"no_external_npu_processes":true,
  "physical_devices":[4],"logical_device":0,"soc":"Ascend910B4",
  "checked_at_utc":"...timezone timestamp...", ...actual command evidence...}.
  Exactly one physical4-7, proved logicalmapping, at most5 minutes before launch.
  Mere container device declarations do not constitute mapping/idle proof.

After main reviews/source-freezes/builds, run --meta-only with library,
library-sha256, source-manifest, build-receipt, absent output-dir; no preflight is
needed for no-device Meta. For actual gate add --preflight, --logical-device0.
--repeats defaults20 and cannot be lowered below20. The exhaustive raw-bit matrix
is run in N1792 chunks; N64 uses a mixed lifecycle smoke. Both counts repeat20
times, full inputs and fresh output guards checked. No performance timing claim.

Runner captures each full raw return and full input-after via torch.save before
asserting code/valid/guard invariants. Negative prepare/exact count/dtype/contiguity/
alignment/alias/CPU admission also preserves inputs/error before assertions.
All artifacts live in a new external directory; no overwrite and no results in Git.
The final report binds source/build/SO/fixtures/SoC/Torch/TorchNPU plus loaded
library hashes. CPU/Meta phases do not constitute NPU or graph acceptance.

