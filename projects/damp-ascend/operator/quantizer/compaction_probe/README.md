# Independent DAMP packed-mask/compaction/scatter seam probe

This NEW target diagnoses a necessary DAMP quantization dataflow seam. It is NOT a
production performance implementation or evidence that DAMP has passed recurrence,
graph, serving, throughput or task-accuracy acceptance. Existing production v4,
failed gates, certificate5/quantizer16/certificate-probe9 and collector remain unchanged.

## ABI and mechanisms

`torch.ops.qwen36_damp_compaction_probe.prepare(accepted,x_bits,scale_bits,magnitude)->()`
then `compact(...)->(codes_guard,indices_guard,retained_guard,valid_guard)`.
Four disjoint contiguous physical-ND2 INT32[N] inputs, N64/448/896, aligned32B.
Flags are actual0/1 and proposal magnitudes actual0..127, synchronously checked on
EVERY call before dispatch. Diagnostics only: these CPU admissions exclude graph.
Accepted magnitudes are supplied mathematically valid fixture inputs; this probe
does not validate the integer certificate itself or run approximate Div.

Kernel transforms flags to exact FP32 bits by **INT32** Muls(0x3f800000), then
**actual CompareScalar EQ0** writes packed bits. A lane0/1 vector is never passed
directly as a tensor bit mask. CreateVecIndex + GatherMask compacts rejected indices.
Only retained rejects enter frozen ExactCode, then code/valid scatter to original
lanes. Original raw x sign restores vector accepted codes; no FP32-to-integer
sign inference, no floating quotient golden, no scale floor. ExactCode identity:
`f5d380534d34d6e4148d94fcfec35b294ca8ca38d09316d98b11e7f645ff6169`.
Independent golden imports ONLY hash-bound Fraction->IEEE RN32->integer RNE oracle
`test_exact_quantizer.py` SHA
`b1c9d10bf9e24e095fe048235693e426f5437be27a9e21b39503bd7825a50c3d`.

Each output is a distinct complete INT32[N+16] backing root:32B guard before and
after, actual kernel writes middleN only. Codes/valid cover every lane. Indices
contains retained ordered positions then INDEX_FILL=-777777. Retained interior
starts with count and all remaining entries COUNT_FILL=-888888. Separate sentinels
per output. Full inputs include external32B guards. Kernel uses one AIV only,
prevents bad count/index from reading outside UB, and does not write any input.

## Actual UB reservation and synchronization

At MAX_N896: single packed VECIN4*896*4=14336B; single packed VECOUT
4*(896+16)*4=14592B; VECCALC six INT32 planes6*896*4+256B packed mask=21760B.
**Total50688B**, no double buffers,2TQue only. Tiling32B is read directly from GM
and is not another UB queue. Compare source/mask relative offsets are multiples256B;
actual compiler allocator/CompareScalar constraints remain build/NPU checks.
There are no per-lane Tensor allocations or unbudgeted persistent table planes.
Queue DeQue provides MTE2->V; Compare/Gather vector dependencies use PIPE_V;
V_S precedes count/index/raw scalar reads; S_V precedes scalar-scattered vector
consumers; VECOUT EnQue/DeQue precedes MTE3. CANN CreateVecIndex internal S_V is
source-inspected. A zero **retained** count is allowed; GatherMask input count is
always N>0, never0. Returned count/order still require actual910B4 validation.

## Source provenance and deliberate adaptations

Reuse public CANN9.1 API and queued ASC-compiled wrapper from this repository;
CANN template-derived CMake retains its original CANN-2.0 notice.
`compaction_probe_kernel.asc` global DEFINITION/braces remain visible to ASC host
pass, while device body alone is guarded. A declaration alone previously produced
a successfully linked but unresolved launcher in another target; compilation
alone does not establish dlopen or kernel execution. Explicit runtime SoC910B4,
ND and whole backing-disjoint gates remain fail-closed.
Public API only in includes (`kernel_operator.h`); internal snapshots were read
for evidence, never included/modified:
- `/cache/cch/qwen36-damp-20261006/sdk-div-audit-v1/include-basic_api/kernel_operator_vec_gather_mask_intf.h`;
  c220 implementation and CreateVecIndex implementation from same SDK snapshot.
- `/cache/cch/ops-transformer/moe/moe_token_unpermute_with_routing_map/op_kernel/masked_select.h`
  GenerateMask/GatherResult actual CompareScalar packed-mask use.
- [CANN GatherMask API](https://www.hiascend.com/document/detail/en/CANNCommunityEdition/910/API/ascendcopapi/docs/en/api/SIMD-API/basic_api/memory_vector_compute/compare_and_select/GatherMask.md).
Counter GatherMask(1,1,8,1) matches upstream tensor-pattern use, not unvalidated
arch35 behavior. All order/count/stride assumptions stay explicit probe gates.

## Preregistered matrix and output retention

N64/448/896; all/none rejected, none after all, single0/31/32/63/64/last where in
range, odd/even, seeded sparse/dense random, invalid domains all rejected and none
after invalid. Same four physical buffers receive changing masks AND raw values;
H2D is synchronized before every call, no fresh-input allocation perturn. Wrong
rejected proposals must be overwritten by exact fallback. Fraction fixtures cover
saved step45 -118, parity half +/-1ULP, non-power-of-two scale, signs/±0,
normal/subnormal/extreme scales and invalid x/scales. Complete inputs, outputs,
previous output snapshots, byte-interval aliases and pointers checked bitwise.
Every raw-before CPU fixture is saved BEFORE dispatch. First failure preserved
with partial/nullable D2H copies and finite JSON; no automatic retry/threshold edit.
Input-value admission tested before prepare AND dispatch; graph deliberately absent.

MAIN alone runs all container/build/device actions, after fresh physical4 mapping
and ownership checks. No privileged container or parent ma handles via mb. DAMP's
deadline remains2026-10-07T08:48:03Z. New build/output directories must not exist.

### Commands for MAIN (inside the already selected same image; no device for build)

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 projects/damp-ascend/operator/quantizer/compaction_probe/test_software.py
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 projects/damp-ascend/operator/quantizer/compaction_probe/source_receipt.py
cmake -S projects/damp-ascend/operator/quantizer/compaction_probe -B /drrqr-results/compaction-build-v1 -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
cmake --build /drrqr-results/compaction-build-v1 -j4
```

BeforeNPU, MAIN saves source receipt stdout externally, build log and SO SHA;
nm/readelf must show actual defined launcher (noU/UND), and no-device Meta/dlopen
must pass. Do not print whole Torch stdout as CMake path; existing marked metadata
discovery retained. PublicCustomFunctions physical format APIs are explicitly used.

```bash
PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 projects/damp-ascend/operator/quantizer/compaction_probe/run_compaction_gate.py --meta-only --output-dir /drrqr-results/compaction-meta-v1 --library /drrqr-results/compaction-build-v1/libqwen36_damp_compaction_probe_ops.so --library-sha256 VERIFIED_SO_SHA --source-receipt /drrqr-results/compaction-source-v1.json
ASCEND_RT_VISIBLE_DEVICES=0 PYTHONDONTWRITEBYTECODE=1 /usr/local/python3.12.13/bin/python3 projects/damp-ascend/operator/quantizer/compaction_probe/run_compaction_gate.py --output-dir /drrqr-results/compaction-npu-v1 --library /drrqr-results/compaction-build-v1/libqwen36_damp_compaction_probe_ops.so --library-sha256 VERIFIED_SO_SHA --source-receipt /drrqr-results/compaction-source-v1.json --device-proof /drrqr-results/compaction-device-proof-v1.json --physical-device 4
```

Device-proof JSON created by MAIN's fresh host inspection must explicitly contain
physical_device4/logical_device0/privilegedfalse/container/image_id/checked_utc and
host_device_paths including /dev/davinci4. Runner rejects proof older900seconds.
This JSON records external mapping evidence, not an independent in-container
physical mapping detector. Full loaded SO/torch_npu paths/hashes are recorded.

After actual seam PASS, MAIN may review minimal production integration; this probe
does not prove acceptance ratio/speed, full B1/B16×160 feedback, generalSR/calibrated
192plans, graph, cache lifecycle, model outputs or end-to-end10% benefit.

## Actual compiler failure and minimal v2

The first real CANN9.1/dav2201 no-device build FAILED; it did not execute NPU.
Two actual compiler errors (host-only std::array::operator[] and unsupported
Duplicate<uint8_t>) are preserved with original byte-exact plan/kernel under
audit/. See [V2_CHANGES.md](V2_CHANGES.md) for evidence/log SHA and exact repair.
V2 uses the same guard values in a constexpr C-array and zeroes the same256B
mask region through64 UINT32 elements. No mathematics,fixture,runner,gates,
CompareScalar/GatherMask,dataflow or UB change. New source assertions are only
software checks; MAIN must build/load v2 in a new directory before any NPU gate.
