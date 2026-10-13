# Skill repairs integration
## Status
Started/not-ready. Target main at ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Owning branch work/skill-repairs-20261013; no repair files imported yet.
This is a selective integration workstream, not a HYPIC rerun.

## Objective and boundaries
Integrate the planning-schema example repair and five-file main runtime-template
repair already validated in the published experiment branch. Use task.json
path/commit/blob bindings. Do not merge the whole experiment branch or add the
native-plugin/observer source. No device allocation, quality or performance work.

## Evidence
Source archive c03604ad184a154c90757ef805445b997ddbad92 on the remote experiment
work branch retains PLANNING_SELECTIVE_INTEGRATION_20261013.md,
RUNTIME_SELECTIVE_INTEGRATION_20261013.md and their hashed receipts.
Read them through Git; they are not copied wholesale into main.

## Next
Publish this start checkpoint and verify upstream equality; then import only
the declared six files, add narrow self-contained validation, validate and push.
Before integration fetch the target, attest exact validated source/target,
prepare target-owned merged state in the no-ff merge tree, validate that final
tree, and push/verify main. No unvalidated state commit after the merge.

## Claims and recovery
One current-thread integrator owns the lock recorded in task.json. Existing
experiment worktree/drafts stay untouched. Three registered worktrees are below
the repository budget8. Never recreate an existing worktree after tool timeout.
Retain original base and checkpoint provenance; stop on remote drift/failed gates.
