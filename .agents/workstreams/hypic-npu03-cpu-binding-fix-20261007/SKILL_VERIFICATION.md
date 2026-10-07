# HYPIC 穿刺中的 Maintainer Skill 验证账本

Current campaign note: HYPIC-only binding-off smoke and three formal 40/40 performance runs passed bounded canary/hot-path checks, and the independent six-unit performance audit passed. The first 41984-context quality attempt (`exec-0000000000000c6d`) finished all six no-cache units with independently valid raw rows but failed the NPU0-3 isolation gate when an unrelated container used physical NPU3 near the last unit; no HYPIC quality arm started. These attempt-1 rows are not a final paired control. A new full clean2 12-unit paired attempt with runtime foreign-PID guard is prepared; final quality, release and whole-paper audit remain pending. Performance-component validation must not be counted as full-paper or all-29-skill validation. See `QUALITY_RESOURCE_CONFLICT.md`.

Scope: origin/main at f1f37a39bd86f7db5fd3ee3dea358ae6868275c6 has 29 registered Skills and 29 SKILL.md files. This is a behavioral evidence ledger, not a claim that all 29 should be exercised by one paper. The old 2026-10-06 skill-validation.json is historical evidence and must be independently rechecked before promotion.

Current branch has ingested three verified performance/tooling lessons and one paper-derivative coverage lesson into existing Skills and registry triggers, not added new Skills. A 29-Skill structural validator pass and the six-unit performance artifact audit confirm those edits did not break the tree or the measured effect; they do not validate the unfinished quality workflow or the other unassessed Skills.

Historical vocabulary: completed = a defined workflow produced a traceable positive or negative result; partial = the workflow has a documented evidence gap; unassessed = no behavioral acceptance recorded in the old HYPIC ledger. A structural validator pass is not behavioral validation.

Current-campaign codes as of 2026-10-07: **V** = this campaign exercised a bounded workflow with direct evidence; **P** = some steps/evidence exist but its relevant acceptance is open; **N** = not exercised here or not applicable. V is not a universal guarantee for every future use of that Skill. The six V entries are environment orientation and canary (frozen token-ID/hot-path plus six-run audit), experience ingestion and skill governance (four reusable edits plus registry/validator), Git checkpoint policy (confirmed policy, validated clean branch and pushed commits), and the one-adapter boundary audit. `PAPER_ARCHITECTURE_FIT.md` now records a retrospective paper/target applicability check, so paper-ingestion and architecture-fit move from N to P; neither is V because its pre-implementation timing gate cannot be retroactively satisfied and the broader method/quality boundary remains open. `BOUNDARY_AUDIT.md` records why runtime-skill separation is N/not applicable for this repository rather than a synthetic pass. The quality campaign remains live; no complete-paper verdict is counted. Run `python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_matrix.py` to check that all 29 pinned main IDs occur exactly once and that the declared V/P/N counts match the table.

| Skill | 2026-10-06 historical ledger | Current | This campaign's remaining acceptance |
| --- | --- | --- | --- |
| chicaihong01-host-maintenance | completed | P | Direct peer, lane and worker proof passed; final quality-container release pending. |
| ascend-npu-environment-orientation | completed | V | Pinned image/source/model/TP/device/cpuset and target-worker proof passed. |
| ascend-canary-implementation | completed | V | Binding-off HYPIC deterministic canary and formal hot path passed. |
| runtime-monkeypatch-delivery | completed for rejected candidate | N | Supported upstream switch is not a monkeypatch; no new monkeypatch delivered. |
| ascend-benchmark-evidence | completed negative | P | Six paired performance units audited; 12 quality units still running. |
| ascend-performance-optimization | completed negative | P | CPU repair and HYPIC within-lane performance effect pass; quality acceptance pending. |
| paper-to-ascend-reporting | completed negative | P | Performance deltas independently recomputed; final quality-integrated report pending. |
| mst-maintainer-handoff | completed negative | P | Live branch handoff records exist; final quality outcome/release pending. |
| ascend-cannbot-profiler | partial | P | Existing Decode profile informed diagnosis; rank-2 offline-export limitation remains. |
| paper-to-ascend-reproduction | partial | P | One-switch performance proven; full quality and paper-level audit pending. |
| ascend-model-quality-evaluation | partial | P | Matched 41984-context, 2048-token 12-unit campaign running; no final score. |
| ascend-architecture-fit | unassessed | P | Retrospective C1/C2 text fit recorded from checkpoint/tokenizer/runtime; prospective timing, C3 and final quality remain open. |
| ascend-inference-tuning-loop | unassessed | P | Planned/baselined/attempted/verified/measured checkpoints exist; final decision pending. |
| ascend-source-map | unassessed | P | Runtime seam and activation pinned; method-chain source map not independently closed. |
| paper-ingestion | unassessed | P | ArXiv v2 mechanism/C1-C3 map and source audits recorded retrospectively; upstream exact commit and pre-implementation gate remain open. |
| paper-to-ascend | unassessed | P | Performance portion passed; quality and complete method-chain decision pending. |
| mst-agentsmd-authoring | unassessed | N | No new AGENTS.md authoring workflow executed. |
| mst-experience-ingestion | unassessed | V | Four trigger/action/destination/verification lessons ingested in existing Skills. |
| mst-git-checkpoint-policy | unassessed | V | Confirmed commit-implies-push policy followed on clean tracked work branch. |
| mst-loop-engineering-framework | unassessed | P | Orient-to-measure sequence recorded; final decide/close transition pending. |
| mst-parallel-workstreams | unassessed | P | Independent clone/lane separation proven; full workstream lifecycle pending. |
| mst-practice-iteration-planning | unassessed | P | One-variable gates and resource limits predeclared; complete iteration pending. |
| mst-repo-onboarding | unassessed | N | Fresh-clone entry from handoff not tested independently. |
| mst-repo-transformation | unassessed | N | No repository transformation is claimed by this HYPIC run. |
| mst-runtime-skill-boundary | unassessed | N | Repository-source audit found no runtime/product Skill or publication tree; external deployment is out of scope. |
| mst-skill-governor | unassessed | V | Existing narrow Skills and registry updated, with reason and validator evidence. |
| mst-skill-tree-design | unassessed | P | No new Skill added; trigger overlap review remains open. |
| mst-tool-adapter-boundary | unassessed | V | Only tracked tool adapter is one-line `CLAUDE.md` → `AGENTS.md`; canonical policy remains in AGENTS/registry. |
| mst-transformation-verification | unassessed | P | Structural 29-Skill validator and performance behavior passed; full boundary audit pending. |

Historical count, with duplicate rows excluded: 8 completed, 3 partial, 18 unassessed = 29. Current bounded-workflow status: 6 V, 18 P, 5 N = 29. The NPU0-3 campaign has passed paired performance and independent artifact audit; paired quality is running, not complete. No whole-paper or whole-tree completion claim is made. Reconcile each row against raw quality artifacts before the final count.
