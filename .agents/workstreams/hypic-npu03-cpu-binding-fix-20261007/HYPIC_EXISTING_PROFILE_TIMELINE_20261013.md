# HYPIC existing-profile timeline analysis

Recorded 2026-10-13. Post-hoc CPU-only analysis; no new NPU capture or runtime change.

## Identity and checks

Input: separate four-rank Prefill r2 and Decode r6-manager parsed copies under
/cache/cch/hypic-npu03-cpu-binding-fix-20261007. Original raw roots remain unchanged.
Source c12060cd47e7575ead059983d7a8bb4704165c98, not current4429e35.
CANN9.1.0/torch_npu2.10.0.post4. Raw independent Prefill and Decode audits
passed again in01a4, preserving the Prefill frozen47-column miss (46 observed).

analyze_hypic_profile_timeline.py uses integer-nanosecond interval merging.
Seven unit tests passed (overlap/nesting/duplicate/empty/touching/reversed ranges,
epoch precision and invalid timestamps). The analysis records hashes for each
input CSV and rank profiler config; it writes a distinct exclusive output:
 /cache/cch/hypic-npu03-cpu-binding-fix-20261007/profile-timeline-analysis-20261013.json
SHA25690385d77afe877b66758529d9272d0674b7d89d3798349577fd19b96b372bddd.

Independent verify_hypic_profile_timeline.py uses an event-count sweep, not
the analyzer's merge/intersection functions. Operation01af verified all8
phase/rank timelines, input identities and overlap totals.

## Measured exported-kernel windows

All values below are milliseconds. Window is first exported kernel start to
last exported kernel end; it is not service TTFT/TPOT, HTTP capture duration,
an entire request or the CANN Stage column. Compute includes AI_CORE,
AI_VECTOR_CORE, MIX_AIC and MIX_AIV. Other exported classes are retained in
the all-kernel union but not mislabeled compute.

| Phase/rank | Window | Compute union | Communication union | No exported kernel | Largest gap |
| --- | ---: | ---: | ---: | ---: | ---: |
| Prefill0 | 6594.113 | 2090.312 | 744.254 | 3751.614 | 3666.746 |
| Prefill1 | 6595.205 | 2089.330 | 554.739 | 3942.747 | 3861.327 |
| Prefill2 | 6594.180 | 2090.725 | 578.916 | 3916.683 | 3836.967 |
| Prefill3 | 6594.347 | 2090.486 | 601.769 | 3894.137 | 3810.704 |
| Decode0 | 1810.630 | 1672.265 | 77.380 | 60.984 | 3.516 |
| Decode1 | 1810.612 | 1674.404 | 75.833 | 60.376 | 3.443 |
| Decode2 | 1810.640 | 1671.020 | 74.089 | 65.531 | 3.955 |
| Decode3 | 1810.659 | 1676.785 | 69.594 | 64.280 | 3.578 |

Compute/communication interval overlap is0 in these exported rows on every rank.
This does not prove that no unexported activity or host work overlapped them.
A no-exported-kernel interval is not proof of hardware idleness or host root cause.

The communication sum demonstrates the double-counting risk: rank0 Prefill
hcom_allReduce rows sum to1488.429ms, versus744.254ms union across exported
COMMUNICATION tasks. Decode hcom_allReduce rows sum152.242ms versus77.380ms
communication union. Counts/sums are useful for ranking, not removable wall time.

Cross-rank first/last kernel timestamp spreads are1.094370/0.002685ms for
Prefill and0.046305/0.002575ms for Decode. Independent clock calibration and
causal dependencies are not proved; these are timestamp observations only.

## Hotspots, shapes and pipeline metrics

Rank0 Prefill summed compute hotspots include MatMulV3(256 calls,875.064ms),
ChunkGatedDeltaRuleFwdH(144,306.481ms), FusedInferAttentionScore(16,301.764ms),
AddRmsNormBias(128,145.585ms) and recompute_w_u_fwd_kernel(48,53.437ms).
These are existing integrated-HYPIC events, not standalone GDN experiments.

Rank0 Decode MatMulV2 has19,215 calls summing1272.726ms. RecurrentGatedDeltaRule
has3024 calls,46.711ms, with Q/K[1,4,128],V[1,12,128] and
state[393,12,128,128]. Prefill GDN exported Q[1,4,16392,128] and
V[1,12,16392,128]. These recorded TP-local head-group ratios are3, not2;
retain them as historical source/architecture evidence, not universal shapes.

Rank0 duration-weighted pipeline ratios:
Prefill AIC MAC0.6656,MTE2 0.7996,AIV vector0.2013;
Decode AIC MAC0.0782,MTE2 0.9357,AIV vector0.1283.
These ratios use eligible core-duration weights and may overlap; do not sum
them into a utilization partition or infer achieved HBM bandwidth from them.
They support inspecting the Decode linear/GEMM data path before assuming a
communication-dominated kernel window; they do not establish a causal fix.

Host API sums include Decode aclrtSynchronizeEvent1316.877ms and
aclrtSynchronizeStreamWithTimeout750.573ms, and Prefill launch1186.582ms,
aclrtLaunchKernelWithHostArgs1135.105ms. Synchronous waiting can contain device
work. These overlapping host/API aggregates cannot be added to device time.

## Explicit unresolved checks and routing

All8 step_trace_time.csv exports have blank Step fields. They do not prove
individual Decode-step latency; kernel counts and HTTP chunks cannot replace
step identity. CPU/NUMA causality, host gap-to-device dependency mapping and
cross-rank clock calibration remain unproved. The existing trace may permit
some host-event correlation; inspect it before proposing any new capture.

Exact-main profiler workflow8 now has replayable gap/overlap, operator/shape,
pipeline and cross-rank observations, but per-step and CPU/NUMA attribution
remain limited. Feed an inconclusive causal diagnosis to the tuning loop.
Do not modify HCCL, GDN, clocks or CPU binding from these unpaired old-source
profiles. No current4429e35 speed, quality fix or treatment adoption follows.

Architecture-fit/source-map supplements may cite the recorded TP-local shapes
and fixed author reference, but their original pre-implementation chronology
gaps cannot be repaired retrospectively. Their old current-quality-missing
statements are historical: r19 paired quality is complete, negative and immutable.
Do not rerun it to repair missing chronology or source documentation.

No Skill is promoted by this report. Counts remain9 bounded verified/20 partial.
Deadline2026-10-13T08:47:14Z, pending descriptive performance choice and remote
authentication boundary are unchanged. No NPU controller started.
