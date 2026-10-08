# Exact-main ascend-source-map: HYPIC retrospective case (2026-10-09)

Status: **partial-evidence**. This is an offline source-seam replay, not a new NPU run or a paper-complete verdict. Exact-main Skill is `7aac2fc220ef5191b0de224615fc2cb17de347ce` at `ead80810`; this branch has the same blob. The target is the 64-layer Qwen3.5-architecture BF16 checkpoint (48 linear/16 full-attention layers) served as one TP4 replica on physical NPU0–3.

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

However, the removed r12 container did **not** retain a separate raw `docker inspect` bind receipt or an in-container source-tree hash. The controller's checks and runtime import path support the source selection, but the original bind bytes cannot be independently reconstructed now. A future full pair should persist Docker inspect binds plus an in-container tree/commit digest at start. The r12 startup log itself is not a complete source-to-binary attestation.

## Next bounded implementation and rollback

Before a new test, freeze the decision rule and paired no-cache/HYPIC contract. The first candidate remains at the scheduler/cache materialization seam: explain and unit-test the five r12 cold requests, then change one admission/eviction rule with a failing-to-passing CPU regression. Keep `c12060c` as rollback and retain the disabled-control path; new source needs a real-weight canary and a same-identity 0.85 no-cache control before scored quality or performance. Run only when physical NPU0–3 have no real foreign processes; the active-idle guard must fail closed. Never use NPU4–7 or stop another workload. For a genuinely lower-level bottleneck, hand off to `ascend-cannbot-profiler` first.

Replay: `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_ascend_source_map_case.py`. It checks frozen source symbols, source identity, raw start/log hashes, C3 gap, case boundaries, and current main blobs; it does not prove a full-quality pair or independently replay a removed container.
