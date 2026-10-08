# HYPIC 穿刺中的 Maintainer Skill 验证账本

2026-10-08 prospective update: the frozen clean2 natural-task quality
failure below remains unchanged. A separate explicit-boundary pilot-2
(`HOTPATH_PILOT2_RESULT.md`) passed three scored hot-path requests and
exact NPU0–3 release after repairing an audit ID join; this verifies a
limited protocol/activation step, not 127-sample quality or all-Skill
behavior. Full matched no-cache baseline `exec-0000000000001293` is now
running; HYPIC treatment, independent paired audit, and Skill status
reclassification are pending. A separate resume-session onboarding check
now moves only `mst-repo-onboarding` from N to P; fresh-clone acceptance
remains open. Thus bounded V10/P15/N4 is the current classification, not a
completed long-term goal.

Final clean2 note (2026-10-07 21:58 UTC): three formal 40/40 paired performance runs passed the bounded hot-path gate. The first 41984-context quality attempt (`exec-0000000000000c6d`) failed shared-host isolation and is not pooled. Fresh `clean2` (`exec-0000000000000e15`) completed all 12 paired quality units, exact input/row/scorer/hash audit, 752/754 clean guard samples and both releases. The original strict quality auditor failed because no natural request activated any worker hot path; the separate scoped audit preserved valid but inconclusive natural-task scores without formal acceptance. See `FINAL_EVIDENCE_DECISION.md`. A completed negative protocol verdict validates some bounded evidence/maintenance/reporting workflows, but not the hot-path quality workflow, whole-paper reproduction, or all 29 Skills.

Scope: origin/main at f1f37a39bd86f7db5fd3ee3dea358ae6868275c6 has 29 registered Skills and 29 SKILL.md files. This is a behavioral evidence ledger, not a claim that all 29 should be exercised by one paper. The old 2026-10-06 skill-validation.json is historical evidence and must be independently rechecked before promotion.

Current branch has ingested three verified performance/tooling lessons, one paper-derivative coverage lesson, one shared-host quality-isolation failure lesson, one source-grounded quality hot-path coverage-preflight lesson, and one aggregate-score floating-point/classification lesson into existing Skills, without adding a new Skill. A 29-Skill structural validator pass, the six-unit performance artifact audit and 12-unit scoped quality audit confirm tree integrity and bounded evidence handling; they do not establish hot-path quality or validate unrelated Skills.

Historical vocabulary: completed = a defined workflow produced a traceable positive or negative result; partial = the workflow has a documented evidence gap; unassessed = no behavioral acceptance recorded in the old HYPIC ledger. A structural validator pass is not behavioral validation.

Current-campaign codes as of 2026-10-07: **V** = this campaign exercised a bounded workflow with direct evidence, including an honest negative result; **P** = some steps/evidence exist but its relevant acceptance is open; **N** = not exercised here or not applicable. V is not a universal guarantee for every future use of that Skill. Ten V entries now include the previously verified environment/canary, experience/governance, Git and boundary workflows plus completed exact host release, 18-unit benchmark evidence accounting, bounded result reporting and final handoff. `PAPER_ARCHITECTURE_FIT.md` is retrospective, so paper-ingestion and architecture-fit remain P; their pre-implementation timing gate cannot be retroactively satisfied and C3/quality boundaries remain open. The model-quality Skill remains P because this frozen request/configuration pair never exercised its required worker-hot path, despite a complete natural-score audit. `BOUNDARY_AUDIT.md` explains why runtime-skill separation is N/not applicable rather than a synthetic pass. Run `python3 .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_matrix.py` to check that all 29 pinned main IDs occur exactly once and declared V/P/N counts match the table.

| Skill | 2026-10-06 historical ledger | Current | This campaign's remaining acceptance |
| --- | --- | --- | --- |
| chicaihong01-host-maintenance | completed | V | Direct peer, physical-lane/worker proof, continuous guard and exact final quality-container release passed. |
| ascend-npu-environment-orientation | completed | V | Pinned image/source/model/TP/device/cpuset and target-worker proof passed. |
| ascend-canary-implementation | completed | V | Binding-off HYPIC deterministic canary and formal hot path passed. |
| runtime-monkeypatch-delivery | completed for rejected candidate | N | Supported upstream switch is not a monkeypatch; no new monkeypatch delivered. |
| ascend-benchmark-evidence | completed negative | V | Six performance and 12 quality units independently accounted; strict activation failure retained, not relabeled as quality pass. |
| ascend-performance-optimization | completed negative | P | CPU repair and HYPIC within-lane performance effect pass; quality acceptance pending. |
| paper-to-ascend-reporting | completed negative | V | Final bounded report separates performance pass, natural-score inconclusive result, formal activation failure and C3 omission. |
| mst-maintainer-handoff | completed negative | V | Final evidence paths, hashes, release, negative gate and next experiment recorded on independent branch. |
| ascend-cannbot-profiler | partial | P | Existing Decode profile informed diagnosis; rank-2 offline-export limitation remains. |
| paper-to-ascend-reproduction | partial | P | One-switch performance proven; full quality and paper-level audit pending. |
| ascend-model-quality-evaluation | partial | P | Natural 12-unit 2048-token scores audited, but frozen request/config never reached worker-hot path; prospective in-path quality acceptance open. |
| ascend-architecture-fit | unassessed | P | Retrospective C1/C2 text fit recorded from checkpoint/tokenizer/runtime; prospective timing, C3 and final quality remain open. |
| ascend-inference-tuning-loop | unassessed | P | Planned/baselined/attempted/verified/measured checkpoints exist; final decision pending. |
| ascend-source-map | unassessed | P | Runtime seam and activation pinned; method-chain source map not independently closed. |
| paper-ingestion | unassessed | P | ArXiv v2 mechanism/C1-C3 map and source audits recorded retrospectively; upstream exact commit and pre-implementation gate remain open. |
| paper-to-ascend | unassessed | P | Performance portion passed; quality and complete method-chain decision pending. |
| mst-agentsmd-authoring | unassessed | N | No new AGENTS.md authoring workflow executed. |
| mst-experience-ingestion | unassessed | V | Seven bounded evidence/classification lessons ingested in existing Skills or their references. |
| mst-git-checkpoint-policy | unassessed | V | Confirmed commit-implies-push policy followed on clean tracked work branch. |
| mst-loop-engineering-framework | unassessed | P | Orient-to-measure sequence recorded; final decide/close transition pending. |
| mst-parallel-workstreams | unassessed | P | Independent clone/lane separation proven; full workstream lifecycle pending. |
| mst-practice-iteration-planning | unassessed | P | One-variable gates and resource limits predeclared; complete iteration pending. |
| mst-repo-onboarding | unassessed | P | `ONBOARDING_RESUME_CHECK_20261008.md` exercised the resume route: 29/29 registry-directory match, no orphan, validator PASS and structured report; fresh-clone entry from handoff remains untested independently. |
| mst-repo-transformation | unassessed | N | No repository transformation is claimed by this HYPIC run. |
| mst-runtime-skill-boundary | unassessed | N | Repository-source audit found no runtime/product Skill or publication tree; external deployment is out of scope. |
| mst-skill-governor | unassessed | V | Existing narrow Skills and registry updated, with reason and validator evidence. |
| mst-skill-tree-design | unassessed | P | `MAIN_SKILL_TREE_DIAGNOSTIC.md` found 0 exact duplicate triggers but 8 main Skills over its 120-line design limit and 14 generic registry entries without trigger/scope; repair and behavioral selection review remain open. |
| mst-tool-adapter-boundary | unassessed | V | Only tracked tool adapter is one-line `CLAUDE.md` → `AGENTS.md`; canonical policy remains in AGENTS/registry. |
| mst-transformation-verification | unassessed | P | Structural 29-Skill validator passes, but the independent main-tree design diagnostic finds metadata/length gaps; semantic heading and runtime boundary review remain open. |

Historical count, with duplicate rows excluded: 8 completed, 3 partial, 18 unassessed = 29. Current bounded-workflow status: 10 V, 15 P, 4 N = 29. The NPU0–3 campaign passed paired performance and independent row/release audit; its frozen natural-request formal worker-hot quality gate failed and natural scores are inconclusive. The new explicit-boundary full quality pair is still running. No whole-paper or whole-tree completion claim is made.
