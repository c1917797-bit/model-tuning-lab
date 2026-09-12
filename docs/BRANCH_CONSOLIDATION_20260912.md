# Repository consolidation, 2026-09-12

User authorized safe integration and branch convergence. No runtime changes.

Integrated source: 4617c5e4ccd8f4dc1c996bfc9b64f3f44bb30b72.
Target parent: 80cf967c929dc40842f47a15f0601b0a9b7b686a.
Scope: paper-parity, source-selection, baseline evidence and related handoff.
Required final-tree gates: validate-mst.sh and git diff --check.

Retention policy for this cleanup: remove only origin work branches already
reachable from main, after pushing an immutable annotated archive tag at the
exact old tip. Exclude branches with attached worktrees. Do not force-delete
unmerged local branches or remove any container-backed worktree.

The inventory found nine worktrees, including two locked historical trees.
Keep runtime/task trees: Qwen3.5 delivery (five unpushed commits at inventory),
DRRQR objective (one unpushed commit and a modified YAML), Qwen38 evaluation
(sixteen unpushed commits), and sparse-prefix reproduction. Do not publish
these unfinished results as accepted product code. Keep Qwen3.5 experience
ingestion pending semantic reconciliation with the newly integrated skills.
The parity maintenance tree is now integrated; removal still requires a
path-consumer audit. No new worktree was created.

Historical completed remote maintenance branches may be archived under
archive/consolidated-20260912/<old-work-branch-suffix>. Their commits remain
on main and in the remote archive tags. Active and unmerged branches remain.
