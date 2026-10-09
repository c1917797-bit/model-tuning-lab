# Exact-main ascend-source-map: HYPIC retrospective case (2026-10-09)

Status: **partial-evidence**. This is an offline source-seam replay, not a new NPU run or a paper-complete verdict. Exact-main Skill is `7aac2fc220ef5191b0de224615fc2cb17de347ce` at `ead80810`; this branch has the same blob. The target is the 64-layer Qwen3.5-architecture BF16 checkpoint (48 linear/16 full-attention layers) served as one TP4 replica on physical NPU0–3.

2026-10-09 addendum: the r12 limitations below are historical, not the latest
serving-source state. The later r13 full pair has a replayable actual-container
source attestation. This case stays partial because the mapping was reconstructed
after implementation; it does not prove that the Skill's prospective
source-map gate chose the seam before the patch.

## Mechanism, measured opportunity, and layer

HYPIC C1 composes position-independent linear-attention segment states; C2 reuses and relocates full-attention KV with seam repair; C3 scatters cold segment computation across independent replicas and combines results. The historical same-lane six-unit performance audit shows a bounded C1/C2 opportunity (weighted TPOT median 77.5641 to 60.2237 ms/token, 22.356% lower), but its quality decision is `not-measured`. The later explicit-segment r12 diagnostic reached four-worker hot proof on 52/57 scored responses, not a full pair. Neither result proves C3 or adoption.

The narrow target is the vLLM-Ascend **runtime plugin/scheduler/cache seam**, not an HCCL or CANN kernel change. Map:

| Concept | Pinned derivative source at `c12060cd47e7575ead059983d7a8bb4704165c98` | Test / switch |
| --- | --- | --- |
| Explicit boundaries and stable segment identity | `hypic_vllm_ascend/ingress.py:parse_segment_ends`; `segmenter.py:hash_segment` | request-boundary and segment/hash tests; `VLLM_ASCEND_HYPIC_ENABLE` |
| C1 linear state reuse | `transition.py:compose_state_torch`; `patches/gdn.py:_position_independent_gdn_core` | GDN transition tests; four-worker materialization telemetry |
| Scheduler admission, cache and eviction | `position_independent.py:_ready_segment_entry,_select_materializations,_commit_materializations,schedule_position_independent`; `cache.py:SegmentCache`; `material.py:MaterializedSegmentStore`; `patches/scheduler.py:_apply_materialization_report` | `tests/test_evicted_directory_rebuild.py`; cache limit 3584 MiB / max 10 segments in r12 |
| C2 KV seam and position repair | `seam.py:hit_seam_positions`; `patches/attention.py:_repair_position_independent_kv,_forward_position_independent_attention` | seam/position tests and exact-request worker evidence |
| C3 cross-replica scatter/combine | **No implemented serving seam in this single-replica TP4 plugin** | separate topology, transfer-plane and quality/performance gate needed |

The smallest prior change `c12060c` rebuilt an evicted scheduler-directory entry during `_commit_materializations`; its focused regression is `tests/test_evicted_directory_rebuild.py`. That fixes metadata accounting, not communication or the entire cold fallback population. r12's 52/57 hot count did not isolate its causal benefit versus r11's 53/57: the sampled requests and scheduling differ. Do not widen to `ops-transformer`, CANN, HCCL or physical card configuration without a profile showing that seam. The upstream paper's SGLang implementation and this vLLM-Ascend derivative are distinct; the downloaded 10-file upstream snapshot has aggregate SHA `9ed7595aee682d7461fa2058156d625962ac6b5fa82e9cedba80521fb06f02de`, but no exact upstream Git commit has been established.

## Serving-source proof and limits

The r12 start receipt names the clean host plugin root, `c12060c`, image digest and NPU0–3. The frozen controller `binding_off_quality.py` requires that selected plugin root be a clean checkout at the requested commit, replaces the exact `/source-hypic:ro` bind, and compares actual Docker-inspected binds/environment/command during ownership checks. The service log shows API process, engine and all four workers importing `/opt/hypic/hypic_vllm_ascend/__init__.py`, and reports C3.1–C3.6 missing. These are stronger than merely finding an upstream checkout.

However, the removed r12 container did **not** retain a separate raw `docker inspect` bind receipt or an in-container source-tree hash. The controller's checks and runtime import path support the source selection, but the original bind bytes cannot be independently reconstructed now. The r12 startup log itself is not a complete source-to-binary attestation.

The later r13 serving-source attestation *was* exercised on physical NPU0–3.
The HYPIC-only service-start receipt hashes the actual-container attestation
(`d2169d9b…a92a687`). It records the selected `c12060c` source commit,
image digest, actual read-only `/source-hypic` bind, copy/editable-install
command, `/opt/hypic/hypic_vllm_ascend/__init__.py` import path, and a
32-file container Python tree digest
`0c6e64ac…37e3633` matching the clean host checkout. The independent r13
auditor checks these against the source tree and start receipt. This retains
the controller-captured actual bind list, not the complete raw `docker inspect`
bytes. The same
identity no-cache/HYPIC 127×3, max-2048 pair is complete and evidence-valid,
but deployed quality is `REJECT_OR_QUALIFY` (230/381 versus 219/381);
strict four-worker hot coverage is 368/381 and C3 remains unimplemented.
Source identity proof is not proof of technical adoption, nor does a Python
tree digest attest every compiled binary or transitive runtime dependency.

## Next bounded implementation and rollback

The missing **prospective source-map gate** is a new, independently scoped
minimal change: freeze the measured bottleneck, exact source seam, one
falsifiable implementation hypothesis, canary, and rollback *before* editing;
then use a failing-to-passing focused regression and inspect the actual
serving-source identity. The r13 raw source proof can be reused as historical
evidence, but its quality pair is rejected and cannot certify any future
changed source. Do not rerun the completed r13 pair merely to validate a
source-map note. If a new candidate is eventually proposed, preregister its
own quality/performance decision and use only actually idle physical NPU0–3;
never use NPU4–7 or stop another workload. For a genuinely lower-level
bottleneck, hand off to `ascend-cannbot-profiler` first.

Replay: `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_ascend_source_map_case.py`. It checks frozen source symbols, r12 historical receipts, r13 immutable attestation/start/audit hashes and host Python digest, C3 gap, case boundaries, and current main blobs. It does not recreate the removed container or verify compiled binary identity.
