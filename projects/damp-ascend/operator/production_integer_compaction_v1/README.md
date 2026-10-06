# DAMP production integer-compaction v1 — isolated, default OFF

This is a default-OFF **candidate**, not cache-manager integration or an end-to-end result. MAIN has now verified the actual build/export/load/Meta, isolated NPU certificate/compaction and the saved production step45 repair. See ACTUAL_GATES.md for exact scopes and hashes. Multi-step/general-SR, graph and real service acceptance remain separate gates. The original v4 operator, collector, trace, oracle and frozen quantizer headers are unchanged. This work does not reset the DAMP24h deadline.

## Scope and paper mechanism

The saved step45 diagnostic proved the production FP32 updated state and generated scale match native bitwise, but AscendC vector Div produced a quotient one ULP above -117.5 and therefore -117 rather than the required -118. This candidate repairs that **DAMP state requantization seam**, not unrelated attention/matmul fusion. Target remains clip(RNE_integer(RN32(x/scale))) with two distinct roundings.

All native recurrence, group32 RA-max scale generation, reciprocal FP32 bits 0x3c010204, value-major high16 FP16/low112 INT8/group32 FP32 scales, per-Hv Pk/Pv/SR, updated-state readout, original-coordinate inversePv*SR and single final BF16 cast are retained. There is no persistent FP32 state sidecar. One AIV retains ownership of a full token/Hv and its four groups.

New default-OFF namespace: `torch.ops.qwen36_damp_integer_compaction_v1`.
External schema remains prepare(query,hi,pk,pv,inv_pv,sr) and decode(query,key,value,g,beta,hi,lo,scales,pk,pv,inv_pv,sr,lengths,indices). Three mutable typed-state alias annotations remain. Only B1/B16, K128/Hq4/Hv12, one-token lengths [0,1,...,1], unique valid indices and physical ND are supported. Separate SO: `libqwen36_gdn_damp_integer_compaction_v1_decode_ops.so`.

Internal tiling is ABI2, padded 32B header + C128 + F128 = 1056B. Explicit cold prepare validates permutations/SR, synchronizes queued allocation outside RunOpApi, uploads immutable tiling/LUT once and retains plans. Every launched AIV loads the 1024B LUT once via the existing planIn queue. Hot decode has neither plan D2H nor cold H2D. Current wrapper additionally rejects non-32B pointers, overlapping complete backing storage and non-Ascend910B4 hardware; this is conservative correctness scope, not a claim of portable deployment or typed-arena support.

## Quantization

Raw FP32 lowFloat3584 is not overwritten. Eight chunks of 4V*112=N448 share the existing group32 scales. Vector Div only proposes a magnitude: its raw sign is cleared, positive bits capped at FP32 127, then RINT, so no NaN/Inf or unsafe index enters the cast/Gather. The frozen integer-only certificate does not rely on vmul rounding, Div error bounds, half-tie snapping, FTZ or epsilon.

Accepted magnitudes restore original x sign vectorially. CompareScalar creates the packed rejected mask, GatherMask compacts original lane indices, an explicit V_S pair precedes scalar consumption, and **only rank<retained** invokes frozen ExactCode on original raw x/scale. An explicit S_V pair precedes exact small-integer casts into INT8. Unused compact suffix is never observed. No all-lane scalar scan, float-Mul fast certificate, dense sidecar, floor or tolerance change is introduced.

An invalid original scalar/scale, unsafe retained count/index produces a failed current group and NaN output. It is **not** transactional rollback: earlier groups/tasks may already have stored state. Numerical/state-finiteness gates must reject such executions. Only malformed one-token metadata has the original pre-writer all-state-unchanged guarantee.

## Source binding and build prerequisites

`source_manifest.json` pins original seven files and all nine compilation dependencies (seven new files plus two unchanged shared helper headers). Native attribution/copyright headers are retained; licenses remain [Apache](../LICENSE-APACHE) and [CANN](../LICENSE-CANN). `ORIGINAL_TO_CANDIDATE.diff` preserves the initial source-preparation diff; current compiled bytes are pinned separately. Ten native method bodies remain byte-identical; UpdateReadout permits only the explicit existing-workspace substitution documented in BUILD_V2_REPAIR.md.

The copied annotated global definition and braces remain host-visible; only device include/body are guarded. This explicitly carries the proven certificate-v3 host-stub lesson forward. Device code uses neither std::array nor Duplicate<uint8>. ASC queued launch uses current stream(false) inside RunOpApi; stream(true) is cold preparation only. Meta is a shape/schema implementation, never graph support.

After MAIN's full source review, use the same **no-device** image/runtime/source-provenance process as successful certificate-v3. This preparation can precede the independent compaction NPU pass, but no production NPU dispatch may do so. In an already authorized, nonprivileged, device-less build container with the same CANN ASC environment:

```sh
cmake -S /opt/host/vnf/austinov/model-tuning-lab/projects/damp-ascend/operator/production_integer_compaction_v1 \
  -B /ABS/NEW/damp-integer-compaction-build \
  -DCMAKE_BUILD_TYPE=Release \
  -DPython3_EXECUTABLE=/usr/local/python3.12.13/bin/python3 \
  -DDAMP_BUILD_INTEGER_COMPACTION_V1=ON
cmake --build /ABS/NEW/damp-integer-compaction-build -j2
```

The example requires a NEW absolute output; do not overwrite any old receipt/build. Record image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1, actual OPP version.info identity separately from real SoC, full source before/after hashes, command exit statuses, raw logs, library SHA and DT_NEEDED. Inspect nm/readelf for **defined non-UND** qwen36_gdn_damp_integer_compaction_v1_decode_kernel before dlopen/schema/Meta. Actual build-v3 and no-device Meta have passed; compilation/link success alone remains insufficient.

## Software-only check and required NPU path

```sh
python3 -B projects/damp-ascend/operator/production_integer_compaction_v1/check_source_contract.py
```

This read-only source/geometry/LUT test is not ASC/API/runtime validation. It checks ten unchanged original method bodies, the exact UpdateReadout workspace-only substitution, quantization prefix/store suffix and ProcessTask's sole error control seam, complete new-buffer offsets, immutable original/helper hashes, safe proposer ordering, sparse scalar boundary, ABI/schema and host-projected global visibility. It cannot prove hardware ordering, compiler stack, rounded math, real cache lifecycle or throughput.

Future MAIN gates, in order:

1. Real independent integer certificate + compaction on physical NPU4–7; actual N448/N896 mask/order/retained/sign/invalid/input/guard evidence. No guessed tail contract.
2. Fresh build + exported host symbol + actual no-device load/schema/Meta and negatives.
3. Same saved production step45 fixture: repaired packed code/state/output compared to independent golden; retain raw failure outputs. Original recurrence/high/scales remain bitwise.
4. Restricted native anchor B1/B16, changing indices, full160step own-feedback compressed trajectories; current frozen 1e-5 state relative-L2 /0.00303 output gates unchanged, half-boundary differences preserved.
5. Independent general-SR native-derived anchor, then positive non-power-of-two SR and final192 calibrated plans. Restricted power2 pass is not generalSR pass.
6. Actual graph gate, typed cache lifecycle/admission/ownership integration without dense FP32 sidecar; eager-only prepare does not prove graph.
7. Same-configuration profiling-off dense paired fixed1024 output throughput/TTFT/TPOT. Certificate/fallback ratio is diagnostic only, not performance evidence. Instruction/barrier cost may outweigh memory savings; must measure.
8. Only credible E2E candidate proceeds to three paired performance repetitions and final normal-EOS no-think max2048 GSM8K/LongBench-v2, using the latest user accuracy acceptance rule.

No end-to-end result, portability proof, tuning-target acceptance or completion is claimed here. Source/preparation manifest statuses are frozen provenance, not live acceptance receipts.

Historical source-only check: MA036b terminal0/70ms after the initial const-correctness preparation fix (see CONST_CORRECTNESS_FIX.md). The first actual build subsequently failed on a mixed const/mutable pointer initializer list (MA0384); BUILD_V2_REPAIR.md records the minimal wrapper fix and independently reviewed explicit broadcast workspace. Build-v2 then failed its SDK-snapshot mount prerequisite before any compiler command. Fresh build-v3 passed; all failed directories/logs and original7/helper2 hashes are retained. Saved-step45 now passes actual NPU bitwise repair; this is not a160step, graph, service or performance receipt.
