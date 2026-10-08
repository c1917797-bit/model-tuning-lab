# HYPIC 穿刺中的 Maintainer Skill 验证账本

2026-10-08 14:56 UTC version attribution audit: V11/P14/N4 are bounded
**work-branch campaign** codes, not proof that exact `origin/main` Skill
bytes passed. Seven branch `SKILL.md` bodies differ from current main;
two are V rows: `chicaihong01-host-maintenance` and
`ascend-benchmark-evidence`. Branch registry routing also differs.
`verify_skill_matrix.py` now reports these mismatches automatically.
Read `MAIN_SKILL_VERSION_BOUNDARY.md` before promoting or citing a
main-version behavior claim. No existing HYPIC result was discarded and
no V/P/N row was silently changed; exact-version attribution remains
an explicit long-term acceptance gate.

2026-10-08 14:38 UTC: independently inspected the preserved cache10r2
candidate event schema against
`.agents/skills/ascend-model-quality-evaluation/references/quality-test-contract.md`.
The clean-set audit receipt SHA256 is
`99f2578adddd041f7a84fe441a1ac02b754b2c1a8217054e80e855b67e7f55bd`;
the original event JSONL SHA256 is
`7a577889eda32df5d2f5e33906bd8337d2b94126d31190a224a132dbb21cadf0`.
All 168 scored request IDs join a pre-intrusion
`explicit_segment_boundary_active` event, but the
`worker_hot_path` and `complete_hybrid_repair` events lack request IDs.
Thus the existing Skill contract correctly restricts this evidence to
request-level admission plus aggregate worker activity, with a separately
serialized sentinel. Per-scored-request worker coverage is not proven.
This is a successful application of one existing evidence-boundary rule,
not a full quality evaluation, a new Skill edit, or a V reclassification;
`ascend-model-quality-evaluation` remains P and totals stay V11/P14/N4.

2026-10-08 14:13 UTC: cache10r2 full candidate
`exec-00000000000013ec` ended isolation-invalid at 56/127 samples after
`cannbench_ds` entered physical NPU0. All 56 files predated the first
observed intrusion and passed a bounded independent row/scorer/explicit-
boundary audit; exact owned release and guard detection passed. This
adds evidence for host-maintenance and benchmark-boundary behavior, but
does not move the 29-Skill behavioral ledger beyond V11/P14/N4. It is not
a full model-quality or paper reproduction pass. See
`HOTPATH_CACHE10_REPAIR.md` for preserved hashes, the partial-evidence
limit, and the pending explicitly revised protocol choice.

2026-10-08 13:06 UTC: fresh cache10r1 full candidate
`exec-00000000000013cc` was isolation-invalid at 0/127 samples. The guard
detected physical NPU3 PID 3551181 from `cannbench_ds`; the new in-flight
fail-fast path stopped only the identity-proven owned service about 34
seconds after first detection. Owned container, workers and port were
released; the foreign lane remained busy. This verifies the bounded guard
repair but supplies no quality score or whole-paper acceptance. The ledger
remains V11/P14/N4; do not count this as a new model-quality verification.

2026-10-08 11:51 UTC: the prospectively declared cache10 stress completed
9/9 samples, 27/27 scored rows, 58 clean physical-lane observations, and
exact release; independent audit `exec-0000000000001375` passed. See
`HOTPATH_CACHE10_REPAIR.md`. This verifies a bounded concurrent replay gate,
not the 127-sample paired quality or every scored request's worker-hot path.
The 29-Skill ledger remains V11/P14/N4 pending full quality and performance.

2026-10-08 prospective update: the frozen clean2 natural-task quality
failure below remains unchanged. A separate explicit-boundary pilot-2
(`HOTPATH_PILOT2_RESULT.md`) passed three scored hot-path requests and
exact NPU0–3 release after repairing an audit ID join; this verifies a
limited protocol/activation step, not 127-sample quality or all-Skill
behavior. The prospective 0.9 no-cache arm `exec-0000000000001293`
completed 127/127 and passed independent row, guard and release audit
(226/381 correct). Its HYPIC counterpart `exec-00000000000012e3`
passed the hot-path sentinel but failed at sample 7: a GDN replay temporary
allocation would cross the preserved 1024 MiB NPU safety watermark.
Only 1/127 candidate samples was persisted; the lane guard and exact release
passed. This is `incomplete-fail-fast`, not a paired accuracy verdict.
`HOTPATH_CAPACITY_REPAIR.md` predeclares a 0.85 common-service reserve
stress gate and a fresh matched pair. Its first stress run was invalidated
by an unexpected PID on physical NPU0 before the sentinel completed; no
capacity or quality acceptance follows. HYPIC Skill reclassification
remains pending. A separate fresh GitHub/main clone completed the full
`mst-repo-onboarding` workflow; see
`ONBOARDING_FRESH_CLONE_ACCEPTANCE_20261008.md`. This moves only that
Skill from P to V. Bounded V11/P14/N4 is the current classification, not
a completed long-term goal.

Final clean2 note (2026-10-07 21:58 UTC): three formal 40/40 paired performance runs passed the bounded hot-path gate. The first 41984-context quality attempt (`exec-0000000000000c6d`) failed shared-host isolation and is not pooled. Fresh `clean2` (`exec-0000000000000e15`) completed all 12 paired quality units, exact input/row/scorer/hash audit, 752/754 clean guard samples and both releases. The original strict quality auditor failed because no natural request activated any worker hot path; the separate scoped audit preserved valid but inconclusive natural-task scores without formal acceptance. See `FINAL_EVIDENCE_DECISION.md`. A completed negative protocol verdict validates some bounded evidence/maintenance/reporting workflows, but not the hot-path quality workflow, whole-paper reproduction, or all 29 Skills.

Scope: origin/main at ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2 has 29 registered Skills and 29 SKILL.md files. The registry Git blob ID is unchanged from f1f37a39bd86f7db5fd3ee3dea358ae6868275c6 (both are `2611864bbcf719d57920aae03ff9eb85521526b4`), and the Skill tree plus AGENTS.md have no diff between those commits. This is a behavioral evidence ledger, not a claim that all 29 should be exercised by one paper. The old 2026-10-06 skill-validation.json is historical evidence and must be independently rechecked before promotion.

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
| mst-repo-onboarding | unassessed | V | Resume and independent fresh GitHub/main clone routes both produced structured reports; fresh clone proved 29/29 registry-directory and entrypoint match, no orphan, validator PASS. Does not prove host/NPU entry. |
| mst-repo-transformation | unassessed | N | No repository transformation is claimed by this HYPIC run. |
| mst-runtime-skill-boundary | unassessed | N | Repository-source audit found no runtime/product Skill or publication tree; external deployment is out of scope. |
| mst-skill-governor | unassessed | V | Existing narrow Skills and registry updated, with reason and validator evidence. |
| mst-skill-tree-design | unassessed | P | `MAIN_SKILL_TREE_DIAGNOSTIC.md` found 0 exact duplicate triggers but 8 main Skills over its 120-line design limit and 14 generic main-registry entries without trigger/scope. Branch-only metadata repair and static regression check pass; main promotion and behavioral selection remain open. |
| mst-tool-adapter-boundary | unassessed | V | Only tracked tool adapter is one-line `CLAUDE.md` → `AGENTS.md`; canonical policy remains in AGENTS/registry. |
| mst-transformation-verification | unassessed | P | Main structural 29-Skill validator passes; branch validator now enforces routing metadata. Main metadata/length gaps, semantic heading and runtime boundary review remain open. |

Historical count, with duplicate rows excluded: 8 completed, 3 partial, 18 unassessed = 29. Current bounded-workflow status: 11 V, 14 P, 4 N = 29. The NPU0–3 campaign passed paired performance and independent row/release audit; its frozen natural-request formal worker-hot quality gate failed and natural scores are inconclusive. The explicit-boundary 0.9 baseline passed, but its candidate was capacity-failed after one sample; the first 0.85 stress gate was invalidated by a foreign PID before completing a sample. A fresh 0.85 matched replacement is still unverified. No whole-paper or whole-tree completion claim is made.
