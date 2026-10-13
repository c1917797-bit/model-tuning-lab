# Skill repairs integration
## Target-owned integration
Execution completed; integration merged after the validated merge is normally pushed.
Exact fetched source: 06365feb165898a86305296dc007b40ec4e09461.
Target parent: ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Validated repair content: f9af6d162b34ceaf96179ecbd963d8b90172693c.
This file is staged with the final integration tree, not a post-merge amendment.

## Scope and evidence
Six source-bound planning/runtime-template repair files, two completed evals and
task-owned acceptance/provenance are integrated; no HYPIC experimental code.
Source validationmc0102 and final-tree gates cover9 runtime subprocess tests,
3 planning controls,2 direct CLI controls,29 registry/structure entries and scope.
See integration-evidence.json, VALIDATION_CHECKPOINT.json and REPAIR_SCOPE.md.
Historical publication timeouts remain in checkpoint evidence; verified push/fetch
mc00e2/00e4 superseded them. No quality verdict or functional29-count promotion.
No new NPU work; lifecycle/Canary and full29 acceptance remain incomplete.

## Retention and recovery
Only after normal main push, exact-tip/ancestry/0-0 checks and no usage:
release this task's claims, reclaim its clean worktree and local merged branch,
then release its owned integration lock. Retain remote work branch.
Preserve original experiment and both untracked observer drafts.
If push is unknown or fails, keep worktrees/lock; inspect same merge before retry.
