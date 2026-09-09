# Parameter provenance and reference classification

Latest objective: >=2x TTFT and TPOT acceleration, lossless accuracy, no
quantization/retraining, physical NPU0-3 only. User supplied tuning bundle is
optimization experience, NOT authority to label that bundle original baseline.

The completed tp4dp1-npu03-ref-v1 is a CURRENT-CONFIGURATION REFERENCE.
It is not a faithful reconstruction of a fully specified original baseline.
Keep its raw files and measured numbers immutable. Current MTP k1 control
isolates MTP against this reference; no claim that inherited tuning gains have
been measured separately or that the overall original-baseline goal is met.

| Parameter | User original engine-log evidence | Current four-card reference | Classification |
|---|---|---|---|
| Parallelism | TP8/DP1 | TP4/DP1 | Latest resource adaptation, not speedup |
| Dtype / quantization | BF16 / none | BF16 / none | Required invariant |
| Seed / context | 1024 / 133000 | 1024 / 133000 | Preserved |
| Graph mode | FULL_DECODE_ONLY | FULL_DECODE_ONLY | Preserved |
| Capture sizes | 1,2,4,8,16,24,32 | Same | Preserved |
| Prefix caching | Enabled | Enabled | Present in original log, not automatically contamination |
| MMAR env + additional config | Not established by engine log | Enabled / true | Inherited candidate; original unknown |
| Async scheduling | Not established by engine log | Enabled | Inherited candidate; original unknown |
| CPU binding | Not established by engine log | Enabled | Inherited candidate; original unknown |
| HCCL_BUFFSIZE / OMP / task queue | Not established by engine log | 512 / false,1 / 1 | Inherited candidate; original unknown |
| Mamba cache mode and dtypes | Not established by supplied log | align / BF16 / BF16 | Explicit current config; original unknown |
| Max seqs / batched tokens | Not established by supplied engine log | 16 / 32768 | Explicit current config; original unknown |
| FULL_AND_PIECEWISE | Not original graph mode | Not active | Candidate experience |
| PTO_CHUNK_GDN | Not established by engine log | Not explicitly set by current role | Not proof disabled; verify runtime default |
| DEBUG / Triton dumps | Not established by engine log | Explicitly enabled | Measurement overhead candidate; original unknown |

Do not turn unknown into false/default or disable everything and call it original.
Framework defaults and runtime image identity must be inspected before defining
a reproducible reconstructed control. Do not manufacture a slow denominator.

Historical screening: original wide FULL_AND_PIECEWISE capture failed with
stream limits; bounded capture started but mixed TTFT/TPOT results. MMAR-off
screen did not establish stable incremental benefit. These are conditional
observations, not universal conclusions or current four-card acceptance.

Next: complete active MTP comparison unchanged, freeze actual runtime identities,
resolve omitted original settings from archived launch evidence if available;
otherwise explicitly label a reconstructed control and retain the current
reference as another denominator. Validate lossless correctness before accepting
E2E gains; report each gain against its named, same-topology reference.

Source inspection05f8: scripts/run_qwen35_tp8_user_baseline_service.sh.
