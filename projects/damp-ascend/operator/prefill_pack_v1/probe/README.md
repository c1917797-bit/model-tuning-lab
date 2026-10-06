# Isolated DAMP prefill FP32 SR divide probe — default OFF

This diagnostic has no production state writes and is NOT prefill-pack, graph,
service or performance acceptance. New7 compiled sources include frozen exact
FLOAT helper bca2ab98... and existing scalar BitLength/DecodePositive helper
f5d38053...; old operators/receipts remain untouched.

Actual API is qwen36_damp_prefill_float_probe:
prepare(x_bits,sr_bits,proposal_bits,use_candidate=False)->()
divide_bits(...,use_candidate=False)->(quotient_bits,valid,finite,certified).

Inputs are disjoint physical-ND32B INT32 raw-bit vectors, N64 or896 only.
proposal_bits means nonnegative FP32 magnitude, not an integer quantization
code; arbitrary/invalid proposals cannot index a table and fail certificate.
Default FALSE uses exact25-iteration scalar restoring divide on every lane.
TRUE diagnostically checks exact scalar midpoints then exact fallback, never
trusts vector Div. Four outputs are fresh complete N+16 INT32 buffers; front
and tail8 ints each are32B guards, with distinct fixed sentinels. Invalid input
returns bits/valid/finite/certified all0. Valid-input quotient Infinity has
valid1/finite0 and exact signedInf bits; it must not be silently clipped.

The CMake wrapper compiles as ASC, queued stream(false)+RunOpApi, not ordinary
CXX direct stream(false). Host-visible annotated global definition emits the
launcher; only device include/body are hidden, retaining2201 guard. Require
actual nm T/W non-UND launcher before dlopen. Cold prepare uploads only16B
tiling and never runs in capture. Meta registration proves only shape/schema.

Explicit UB is3 input queues+4 output queues, each1x896x4 =25088B. No LUT,
Broadcast or hidden high-level scratch. MTE2_S fences scalar input GetValue;
S_V plus output EnQue/DeQue precedes MTE3 whole32B transfers. Scalar arithmetic
and binary shifts need actual compiler/NPU validation. CANN snapshot actually
contains MTE2_S/S_V enum at sdk-div-audit-v1/impl-basic_api/kernel_event.h;
this source evidence alone does not prove synchronization correctness.

## MAIN-owned no-device build (commands, NOT performed by this agent)

From exact same image with no NPU devices, preserved new external build dir,
CANN environment sourced and real Python executable verified:

    cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/prefill_pack_v1/probe \
      -B /cache/cch/qwen36-damp-20261006/prefill-float-build-v1/build \
      -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
    cmake --build /cache/cch/qwen36-damp-20261006/prefill-float-build-v1/build -j2

NEW outputs must not exist. CMake metadata marker/error/path guards reuse the
successful certificate-v3 scaffold, public same-version ND query/cast APIs.
Record compiled9 manifest, image ID, successful command/log hashes, exact
library SHA, npu_arch=dav-2201, actual OPP version.info SHA and non-UND exported
qwen36_damp_prefill_float_div_bits_kernel audit before Meta/load.

run_float_gate.py binds actual build sources/library/image/arch/export/logs
and OPP9.1 identity. It does not invent a passed build receipt or actual SoC
from the compilation target. MAIN must provide real matching evidence.

## MAIN-owned actual gate command (all SHA arguments are actual receipts)

    python3 -B run_float_gate.py --mode meta --execute \
      --source-manifest /ABS/source_manifest.json --source-manifest-sha256 ACTUAL \
      --runtime-manifest /ABS/runtime_manifest.json --runtime-manifest-sha256 ACTUAL \
      --build-receipt /ABS/build-receipt.json --build-receipt-sha256 ACTUAL \
      --library /ABS/libqwen36_damp_prefill_float_probe_ops.so --library-sha256 ACTUAL \
      --output-dir /drrqr-results/prefill-float-meta-v1

For NPU add --mode npu and --preflight/--preflight-sha256/--physical-card4,
using fresh MAIN-approved restricted-device proof and exclusive execution.
No unchanged retry, no output overwrite. Gate records actual SoC, full raw
bits/status/guards before asserts and nullable D2H on poisoned context;
CPU rows/golden/before are saved BEFORE H2D. Input values/complete backing
guards/storage pointers are immutable, outputs all fresh/nonalias.

Matrix: signedzero, subnormals, minnormal boundary, power2 lower/upper
midpoints and neighboring representable preimages, max/overflow, general
scales including subnormal,6000 seeded rawbit ratios, invalid inputs.
Run exact and scalar-certificate modes independently. Every positive has8
identical executions on fixed input/storage; N64/N896 each have20 additional
changing-input fixtures (fresh buffers between fixtures, not a graph/static
address proof). Negative0/63/65/897/1792/wrongdtype/noncontiguous/unaligned
offset/alias/CPU inputs must reject unchanged. Load/Meta has4 positives and
5 count negatives. Other Meta dtype/layout negatives remain an explicit gap.

Full scalar all-lane paths may be too slow to deploy. A numerical probe
pass cannot prove fast prefill-pack. Actual transformed native state high/low
pack, selected slots/FA+conv/padding guards, pack->decode, final192plans,
real mixed/continuation/admission and matched E2E remain separate gates.
