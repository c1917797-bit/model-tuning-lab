---
name: chicaihong01-host-maintenance
description: Use before maintaining code, inspecting runtime state, or running Ascend experiments on chicaihong01; resolve the live AWMCP peer, prove the route and target, enter the canonical remote repository, and keep verification credentials out of Git.
---

# chicaihong01 Host Maintenance

## Purpose
Make a fresh clone sufficient to enter the real machine-bound maintenance
environment safely. The local clone carries governance and discovery knowledge;
the canonical target-host checkout and live machine state produce authoritative
code, runtime, and performance evidence.

## Canonical target
- AWMCP topology path: `chicaihong01/ma`.
- Canonical target repository:
  `/opt/host/vnf/austinov/model-tuning-lab`.
- Compatibility path:
  `/cache/austinov/model-tuning-lab`.
- Expected host baseline: EulerOS on aarch64, 8 Ascend 910B4 NPUs, about 2 TiB
  RAM, and a large 1 GiB HugeTLB pool.

Topology peer IDs, processes, containers, ports, free memory, NPU ownership, and
software versions are live facts. Resolve or measure them every session; never
copy an old snapshot forward as proof.

## Verification credential boundary
Obtain the AWMCP verification value from the operator or approved secret
environment at session start and pass it only in the connector's `verify`
field. Refer to it in instructions as `AWMCP_VERIFY`.

Never commit, print, log, echo, cache, or embed the literal verification value
in this repository, scripts, shell history, handoffs, examples, or command
arguments. A clone intentionally does not contain the credential.

## Fresh-clone connection workflow
1. Read `AGENTS.md`, `.agents/HANDOFF.md`, this skill, and the narrow task
   skills.
2. Confirm the AWMCP connector is available and obtain `AWMCP_VERIFY` through
   the approved runtime channel.
3. Call AWMCP topology `tree` with merged scope and select the exact
   `chicaihong01/ma` node.
4. Resolve its current concrete peer ID. Never hardcode a peer ID from an older
   session.
5. Load the AWMCP `host-development` skill contract before its first action.
6. Run `a_status` against the resolved peer.
7. Accept the target only when the response identifies the intended peer and
   `routeDecision` is `peer_direct` or `upstream_local_peer`.
8. Use `a_exec` or the narrow filesystem action against that same peer to
   enter the canonical repository. A local clone is not target-device proof.
9. If the canonical repository is missing or resolves unexpectedly, stop and
   report the mismatch; do not silently create a second authoritative checkout.

## Start-of-turn remote orientation

From the canonical target repository, capture at minimum:

```sh
git fetch origin
git status --short --branch
git log -8 --decorate --oneline
git worktree list --porcelain
hostname
uname -a
docker ps
npu-smi info
ss -lntp
grep -E '^(MemTotal|MemAvailable|Hugetlb):' /proc/meminfo
```

Read `.agents/HANDOFF.md`. For every relevant active `work/*` tree, read its
`task.json` and branch-local `HANDOFF.md` before touching claimed files,
containers, ports, processes, or NPUs.

Use `.agents/git-policy.yaml` as the repository override for workstream
lifecycle limits. The current active worktree budget is eight. Inventory first;
never reclaim a dirty, in-use, unpushed, unmerged, or unsuperseded worktree.

## Machine and experiment safety

- Re-prove physical NPU/process/container ownership in the same session as each
  action. HTTP health or container existence alone is insufficient.
- If `npu-smi` shows no process and baseline HBM but a non-privileged canary
  fails with ACL `Resource_Busy`, inspect device-node holders, container
  device mappings, and the kernel log for `uda_occupy_dev_by_ns`. On this
  host, an all-device container running only `sleep infinity` held the UDA
  namespace without a visible NPU process; stopping it without deleting it
  released the device. Treat this as a diagnostic signature, not permission to
  stop an unidentified workload: identify its owner and rollback first.
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- Do not stop, restart, or replace a workload until its owning workstream and
  rollback instructions are identified.
- Inspect 1 GiB HugeTLB sysfs state and consumers before any memory-pool change.
  Free pages inside the pool are not ordinary free RAM or permission to release
  them.
- For a capped one-time release, consult its original durable completion ledger
  before a repeated message or continuation. Completed GiB consume that cap;
  do not release it again. Recheck the exact consumer PID/start and NUMA pools,
  preserve its required capacity and distinguish later memory drift from the
  immediate release delta. The October7 release of32GiB is already SPENT.
- Keep datasets, weights, checkpoints, credentials, raw profiles, and large
  generated artifacts outside Git.

For performance work, also use `ascend-npu-environment-orientation`,
`ascend-inference-tuning-loop`, and `ascend-benchmark-evidence`.

## Editing and checkpoints

Route non-trivial work through one named remote `work/*` branch and independent
target-host worktree. Create and push the remote start checkpoint before
protected-path or product edits. Use AWMCP `a_apply_patch` for remote UTF-8
text edits where available, validate each coherent stage, commit, and push to
the workstream upstream. Serialized integration alone updates `main`.

## Verification

- Target topology path and current peer are resolved, not assumed.
- AWMCP response proves the intended direct target.
- Commands run from the canonical target repository.
- Live Git, container, port, memory, and NPU state are captured before mutation.
- No verification value or other credential appears in tracked files or diffs.
- `./scripts/validate-mst.sh` and `git diff --check` pass.

## Failure handling

Preserve exact AWMCP errors. Refresh topology after routing drift and retry only
when the response marks the failure retryable. A control-plane timeout is not
proof of host, command, container, or NPU failure; do not mutate the machine to
compensate for an unproven diagnosis.
