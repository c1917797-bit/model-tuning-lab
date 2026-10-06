# Test-only independent native-derived general-SR golden (prepared, unvalidated)

This is a separately built/loaded reference, not a production operator, cache
manager feature, performance candidate, or evidence that DAMP has passed.
No Docker, build, library-load or NPU run was performed by this preparation agent.
The parent owns the only build/load/NPU launch. Keep every output directory new.

## Frozen source and license

Native recurrent source: `/cache/austinov/src/vllm-ascend`, commit
`5cb98caaadeff42b5b62b996e34bb2aaa29d20fd`.
Ordinary DAV2201 header:
`csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h`,
SHA256 `96e6d9667af1e3457316ffce92a8a983fcb90096df08e3efd13ec0b35b8b1c5b`.
Original Huawei notices are retained; Apache-2.0 text is copied from that root
LICENSE (source SHA256 `c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4`).
Build/PTA infrastructure derives from the Cannbot direct-invoke template under
CANN Open Software License v2; retain LICENSE-CANN and its source notices.
No arch35/950 arithmetic is used.

The sibling production operator's build metadata discovery and exported
`at_npu::native::custom_ops::get_npu_format` are infrastructure reuse only.
No production header, compressed load, quantizer, trace or arithmetic helper is
included/linked. Independent Python CPU pack/unpack belongs to the test harness,
not to this kernel.

## Exact test ABI

```text
torch.ops.qwen36_damp_reference.decode(
  q, k, v, g, beta, state_selected, pk, pv, inv_pv, sr
) -> (updated_fp32, original_output_fp32, original_output_bf16)
```

- q/k: BF16 [T,4,128], native normalized input, no second normalization.
- v: original-coordinate BF16 [T,12,128], NOT BF16 v/c.
- g: FP32 [T,12]; beta: BF16 [T,12].
- state_selected: readonly transformed-coordinate FP32 [T,12,128,128], value
  major [T,Hv,reorderedV,reorderedK]. Test-side independently unpacks and selects
  the active slots. This operator does not receive any hi/lo/scales.
- pk/pv/inv_pv: INT32 [12,128], logical indices, each complete permutation.
  pv maps reordered V -> original V; inv_pv maps original V -> reordered V.
  Pk is per value-head; source q/k head is h//3.
- sr: positive finite FP32 [12,128], c[h,v] in ORIGINAL value coordinates.
- outputs: [T,12,128,128] FP32 updated transformed state; [T,12,128] FP32 restored
  readout BEFORE rounding; [T,12,128] BF16 restored readout with one final cast.
- T exactly 1 or 16, pure one-token selected-state test ABI. No mixed/MTP/PAD,
  slot leases, prefix lifecycle, graph capture or production dispatch is claimed.
- Inputs are not mutated and outputs are newly allocated with no schema aliases.
  All inputs must be contiguous physical ND, same NPU; plans synchronously
  validate on CPU. This eager test-only validation must not enter a graph.

The immutable selected-state input intentionally separates numerical reference
from slot lifecycle testing. The parent harness must still validate ALL candidate
slots, untouched slots, indices, pointer stability, guards and full 160-step
coverage; this reference does not waive those gates.

## Source mapping (not a candidate self-oracle)

The reference copies ALL native MatVecMul and ReduceSum* methods verbatim
(newline normalized) plus the full native Compute prefix through final FP32
readout reduction, before native Cast/store. `check_source_contract.py` checks
these exact spans against the pinned source.

| Native method | Reference mapping / allowed change |
| --- | --- |
| CopyInQKV | BF16->FP32 native casts preserved. Additional FP32 Div(v,c), then Pv; q/k Pk; native q scaling before dot. |
| CopyInGamaBeta | Native beta Cast of padded 16 entries; Exp of complete Nv=12 g row, then scalar head access. |
| LoadPrefetchedState FP32 branch | Plain independently supplied dense FP32 input copied into stateInUb, no decompression. |
| MatVecMul | Exact native Mul and MulAddDst mask/repeat/stride code. |
| ReduceSumAddFoldK128 | Exact multi-repeat lower+upper Add into UPPER half, PIPE_V, WholeReduceSum. No replacement per-row sum/mv. |
| Compute | Exact native `deltaInUb = vInUb[curVOffset] - deltaInUb;`; native decay, beta, Broadcast, MulAddDst, q-readout order retained. gk branch remains textually but false by ABI. |
| Native pre-Cast seam | Updated FP32 copied to new output; independently exposes full readout. |
| Output | Inverse Pv, multiply ORIGINAL-coordinate c in FP32, expose FP32, then sole CAST_RINT to BF16. |

This is the FULL K128 native arithmetic seam, not a full copy of the unrelated
MTP/gk/buffer-depth/accepted-token scheduler. Copying the whole engine would add
unused slot/control machinery and large MAX_MTP buffers without improving
arithmetic independence. It is not an anchor until it matches the actual loaded
native op on SR=1/power2. A compiler lowering difference is a reference failure
to diagnose, not permission to select arithmetic that makes the candidate pass.

No INT8 rounding, scale, clamp or candidate packing code exists here. Never use
candidate trace as this reference's golden. CPU packing must consume this
reference's updated FP32 independently to create the REFERENCE feedback loop.

## UB / DMA / stream

Fixed per-AIV allocated bytes: 75,680.
Input queues: Q/K/V=768, beta=32, g=64, plans+SR=2048, state=16384.
Output queues: updated state=16384, full-head FP32=512, full-head BF16=256.
Work TBuf=39232: state16384 + matvec16384 + nine128-FP32 vectors4608 +
three128-INT32 Gather offsets1536 + delta128 + readout128 + beta64.
Host queries actual UB through PlatformAscendCManager; insufficient UB fails
closed. Build is dav-2201 and runtime Soc must be Ascend910B/Ascend910_93.
Core count is queried at runtime.

One task owns an entire (token,Hv), all four V32 tiles, the full updated head and
the full restored readout. Every GM output start/span is 32B aligned. There are
no original-coordinate output scatters sharing a DMA block and no GM scalar
writes. Input/output queues provide MTE2/V/MTE3 ordering; exact native PIPE_V
barriers retained, explicit V_S before scalar gamma/beta reads. Static sync
analyzer output must be preserved; regex results do not prove numerical safety.

This multi-TU C++ wrapper calls the generated kernel function with stream(true),
after empty-output allocation. It does NOT use stream(false), OpCommand or
ASC queued launch. Production sibling retains its distinct ASC queued route.
Meta registration only checks shape/type; it is not graph support.

## Parent build / source check commands (not run here)

Use the current serving image/CANN9.1 no-device build environment. New directory
must not exist. Source is readonly; build artifacts remain outside the repo.

```bash
python3 -B projects/damp-ascend/operator/reference/check_source_contract.py \
  --native-header /cache/austinov/src/vllm-ascend/csrc/attention/recurrent_gated_delta_rule/op_kernel/recurrent_gated_delta_rule.h
cmake -S projects/damp-ascend/operator/reference \
  -B /damp-results/native-reference-build-v1 \
  -DDAMP_BUILD_NATIVE_REFERENCE=ON \
  -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3
cmake --build /damp-results/native-reference-build-v1 -j4
```

Parent resolves CANN/ASC env and mount destination before running; no container
or workload is launched by these instructions alone. No changes to sibling
production CMake are required. Library:
`native-reference-build-v1/libqwen36_damp_native_reference_ops.so`.
Only explicit load is supported; NPU calls additionally require
`DAMP_ENABLE_NATIVE_REFERENCE=1`.

## Required next gates (ALL still pending)

1. Same-image no-device compile/load/schema/Meta B1/B16, reject malformed dtype,
   shape, blocked format, missing opt-in and invalid permutation/SR.
2. Anchor identity Pk/Pv, SR1 against actual native updated FP32 plus BF16 output,
   full B1/B16 160-step traces, not just last token. SR power2 restricted case:
   legal per-Hv Pk/Pv and original-coordinate SR transformation, no intermediate
   BF16 rounding loss. Compare complete native-derived states after consistent
   inverse transformations; preserve the rounding-order evidence.
3. Only after the anchor passes: general positive c and nonidentity Pk/Pv,
   cancellation/half-boundary stress, then all final calibrated layer/head plans.
   V/c must remain FP32; output restoration precedes BF16 cast. Do not compare
   against native BF16 V/c or native rounded BF16 output multiplied by c.
4. Two independent compressed trajectories: candidate actual packed state versus
   independently CPU-packed updated-reference state. Preserve prepack FP32 and
   pre-RINT boundary evidence for attribution; do not loosen frozen thresholds.
5. Only a validated general-SR receipt can authorize integration; restricted
   native / source contract / compile / Meta does not. No performance or E2E
   task-accuracy conclusion follows from this reference preparation.

Official API documentation cross-check: [DataCopy CANN9.1](https://www.hiascend.com/document/detail/zh/CANNCommunityEdition/910beta2/API/ascendcopapi/atlasascendc_api_07_00131.html)
and [aclrtGetSocName](https://www.hiascend.com/doc_center/source/en/canncommercial/5046/inferapplicationdev/aclcppdevg/aclcppdevg_03_0010.html).
Actual installed CANN9.1 compile/ABI remains the final authority.
