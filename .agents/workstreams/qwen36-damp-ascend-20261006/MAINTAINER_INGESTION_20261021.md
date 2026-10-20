# Maintainer ingestion — 2026-10-21

Scope: the user's request to summarize successful and failed practice into
maintainer skills. This stage edits documentation only; no experiment, NPU
lease, authorization extension, algorithm or numerical threshold changed.

## Reviewed evidence and confidence

Read the current remote tuning-loop skill and its complete causal-recovery and
portfolio-admission references, then the BOLE continuation HANDOFF and these
actual repository audit records under `bole_resume_20261020T154710Z/`:

- R20_CONSUMER_REPAIR.json
- NATIVE_AR_FA256_DECISION.json
- SERVICE_MODEL_V6_AUDIT.json
- G1_MODEL_V2_AUDIT.json
- GDN_REPLAY_V2_AUDIT.json
- GDN_TIMING_V1_FAILURE.json
- GDN_TIMING_CPU_V2_AUDIT.json
- TASK_SCOPE_RECONCILIATION.json

These records include exact source/result paths, byte counts and SHA256 values.
The new lesson is based on these read records; it is not a fresh independent
re-adjudication of raw tensors. Additional raw-result hash commands encountered
transport errors with no confirmed result. Their hashes are therefore retained
as recorded references, NOT claimed reverified in this maintenance turn.
The branch continued advancing during review; the first guarded patch correctly
refused a changed HEAD. The target skill was reread unchanged, and the scoped
patch applied against 50eb592790559c9b6645d76cb4b042c2bc106a29.

## Durable change

Existing skill: `ascend-inference-tuning-loop`; no new top-level skill.
Reference: `references/bole-saved-input-and-service-qualification.md`.

The old model131repair12 case is preserved as historical material in that
reference. The main skill now routes to the specific lesson instead of repeating
the detailed case. Other dirty skills, global/workstream handoffs, source trees
and experiment data were not staged by this maintenance task.

## Decisions retained

- Saved-input precision controls can localize a boundary error; private AR is
  not untouched production dense.
- Reader defects can be repaired against qualified original capture without
  changing original math/tensors or rewriting the failed parent.
- Short TP4 service and two sequential requests are useful positive milestones;
  unobserved slot reuse, cross-step events and long decode remain pending.
- GDN 192 x 2 component replay PASS is not service timing or whole-model benefit.
- Hook order, dynamic reflection, CPU-affinity and reader allocations belong to
  preparation/runtime attribution; they do not establish a paper limitation.
- Task prompts and scorers must share the frozen contract; new scope supersedes
  old scope prospectively, never by silently unioning task lists.

## Verification and limits

`scripts/validate-mst.sh` completed with exit0:
`PASS: Maintainer Skill Tree structure is valid (20 skills)`.
Six trigger/action/forbidden-promotion scenarios are documented for regression
review. They are not six newly executed software or NPU tests.

No new formal performance or task-accuracy result is claimed. Commit/push status
must be verified from Git, not inferred from this document.
