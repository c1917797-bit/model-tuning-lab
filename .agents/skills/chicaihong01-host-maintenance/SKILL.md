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
- A process-free sample is not a lease. Shared-device occupancy can change
  between a standalone preflight and launch, including within seconds. Keep
  the authoritative final occupancy check in the launch controller after any
  cooperative lock and immediately before container creation or service
  mutation. The lock protects only cooperating repository workflows.
- When device-side PIDs change during inspection, resolve each live PID through
  `/proc/<pid>/cgroup` to its container and inspect the container's live
  process tree. A long-lived shell container may launch or restart a short-lived
  model service after the original parent disappears. Record the actual
  container, script, model/service command, and device memory; do not infer a
  human owner from a path or container name when no owner metadata exists.
- Report container device declarations together with container state. By
  default, running containers and live processes are active occupancy claims;
  exited containers are historical provenance that still requires owner and
  cleanup review but does not by itself prove current device use. If the user
  or experiment contract explicitly says any declaration blocks allocation,
  apply that stricter gate without reinterpretation.
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- When a foreign process wins the preflight-to-launch race, fail closed and
  record the event as `not_run/resource_race`. Attribute each new PID through
  cgroups, confirm that no owned container/result root was created, and do not
  treat the admission failure as numerical, performance, or quality evidence.
  A later attempt requires a fresh live audit and a new control-plane
  idempotency key; never reuse the completed key from the rejected admission.
- Give expensive launch controllers a preflight-only path whose rejection is
  observational and machine-readable. It may validate pinned files, hashes,
  ordered inventories, and live resource state, but it must not create the
  owned container or immutable result root, bind the service port, or start an
  accelerator process. Record exact blocker identities and verify the absence
  of those side effects before classifying the attempt as
  `not_run/preflight_blocked`.
- A running privileged Ascend-capable container with neither explicit Docker
  device mappings nor a valid visible-device declaration has
  `unknown_device_scope`; it is not claim-free. Under an exclusive-use
  contract, conservatively treat it as a wildcard NPU contender until its owner
  proves a narrower live scope or stops it. Absence of a device PID at one
  instant is not enough because the container can start workers later.
- Keep ownership monitoring active from the final prelaunch check through
  service readiness when any tolerated foreign container can activate without
  a new Docker mapping. If a foreign PID appears, stop only the owned launch,
  preserve both identities, and classify the attempt as
  `not_run/resource_race`. An HCCL bind collision during worker startup is
  resource-race evidence when the conflicting socket belongs to that foreign
  workload; it is not an algorithm or numerical result.
- Do not stop, restart, or replace a workload until its owning workstream and
  rollback instructions are identified.
- Inspect 1 GiB HugeTLB sysfs state and consumers before any memory-pool change.
  Free pages inside the pool are not ordinary free RAM or permission to release
  them.
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
- The launch record distinguishes admission failure from an experiment that
  crossed its owned start boundary.
- A rejected preflight records exact blockers and proves zero owned launch side
  effects: no result root, container, service-port listener, or accelerator
  process.
- Privileged containers without a provable device scope are recorded as
  wildcard contenders, and startup-window monitoring detects late activation
  before any experiment result is accepted.
- Container occupancy reports include state and identify whether the default
  active-claim rule or an explicitly stricter declaration rule was applied.
- No verification value or other credential appears in tracked files or diffs.
- `./scripts/validate-mst.sh` and `git diff --check` pass.

## Failure handling

Preserve exact AWMCP errors. Refresh topology after routing drift and retry only
when the response marks the failure retryable. A control-plane timeout is not
proof of host, command, container, or NPU failure; do not mutate the machine to
compensate for an unproven diagnosis.
