# HYPIC r20 serial three-sample diagnostic — terminal audit

This is a **post-hoc, bounded mechanism diagnostic**, not a replacement for
the r19 full LongBench-v2/c32/max-2048 quality verdict. The selected sample
indexes were frozen before r20 device work in
`HYPIC_R20_SERIAL_DIAGNOSTIC_PREREGISTRATION_20261011.json` (SHA256
`480b415761be8eeee69b1bd75479b60c37e75c642127034ec4b1728b00f76098`).

Both arms used physical NPU0–3, Qwen3.6-27B TP4, repaired plugin source
`4429e35177979c874bf053ab29789e4773f39b22`, explicit segment
boundaries, max output 2048, two one-token warm requests and three scored
requests for each of indexes 059, 082 and 126. Requests were serial (`c1`).
The independent auditor replayed request hashes, responses, scoring,
source attestation, physical-process isolation and exact owned release.
The two serving specifications differ only in `VLLM_ASCEND_HYPIC_ENABLE`
and their arm-specific evidence path. Short canary request and response
hashes match across arms.

| Arm | Controller | Scored correct | Length-limit finishes | Four-worker hot proof | Clean isolation samples | Immutable arm-result SHA256 |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| no-cache | `exec-0000000000000675`, exit 0 | 9/9 | 0/9 | not applicable | 149 | `07890fbb4c423aff06afe6036b7c5080da3babddf96d29cd899df9ab68944a54` |
| HYPIC-only | `exec-0000000000000690`, exit 0 | 9/9 | 0/9 | 9/9 | 149 | `8cbdddb9284177dd6d020670af7af1b2e23ea31941fdf2df81e256a8a97640ce` |

All nine paired responses stopped naturally and were scored correct in both
arms. Index 059, which was 3/3 correct with natural stops in the r19 control
but 0/3 correct with length caps in its c32 HYPIC arm, is 3/3 correct with
natural stops and proven hot in r20 serial HYPIC. Indexes 082 and 126 are
also 3/3 correct in both r20 arms. This serial/c32 contrast is consistent
with a load-, scheduling- or cache-state-dependent failure, but does **not**
isolate which mechanism caused r19's loss. It does not prove HYPIC safe for
the full population or make r19's `REJECT_OR_QUALIFY` verdict pass.

Frozen independent paired-audit artifact:
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hypic-r20-serial-diagnostic-paired-audit.json`
SHA256 `44bd68b877f941af24422160941ca5006b8deabe5b3396f8e038fc3d6f41ae15`.
Baseline and candidate roots are respectively
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r20-serial-baseline`
and
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r20-serial-hypic`.
Both roots are terminal and immutable; never rerun into them.

Next, use existing r19 per-request events and output records to test whether
the quality losses and caps cluster with unproved-hot requests, cache
evictions or scheduling phase. If that evidence cannot distinguish causes,
freeze one new bounded c32 intervention with a fresh control and one
declared switch before further device work. A corrected full matched pair,
not this diagnostic, is required to change the adoption decision.
