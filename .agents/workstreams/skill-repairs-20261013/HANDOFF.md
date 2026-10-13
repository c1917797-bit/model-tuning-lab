# Skill repairs integration
## Status
In-progress/not-ready. Six selected repair files imported and CPU validated.
Target parent ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
No NPU allocation, no HYPIC code imported, no main update yet.

## Evidence
Start3194848e remotely verified inmc00c2; source archivec03604ad is published.
See task.json immutable source-byte bindings and separate executable-bit override.
REPAIR_SCOPE.md records evidence, limits and ingestion destinations.
validate_selected_repairs.py checks byte/mode/scope/constraints, registry,
instantiated planning examples and direct executable CLI.
Nine runtime subprocess tests cover switch controls and worker-local abort.

## Next
Content94851c0b passed tests; push00d4 timed out, remote unknown.
Finish registry checks, then bind the exact content commit in completed
evals,ready task and integration evidence,then validate/push that ledger.
Fetch target and source again; validate the target-owned merged state in the
final no-ff merge tree BEFORE committing/pushing main. Do not merge whole HYPIC.

## Recovery and retention
Original experiment and two untracked observer drafts remain untouched.
One current-thread integrator retains its declared lock. Reclaim this worktree
only after exact-source main integration,pushed reachability and released claims.
Remote work branch retained. Do not discard original source bindings or base.
