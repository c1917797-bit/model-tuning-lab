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
   session or infer the node role from a familiar peer prefix. A previously
   valid peer can remain reachable after it has moved from `ma` to `mc`.
5. Load the AWMCP `host-development` skill contract before its first action and
   again before every remote mutation. If the workstream requires a reload
   before each remote operation, apply it to read probes and operation polling
   as well. After a timeout, routing error, or long pause, refresh topology and
   re-prove that the peer still owns `chicaihong01/ma` before continuing.
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
ss -lntp
grep -E '^(MemTotal|MemAvailable|Hugetlb):' /proc/meminfo
```

For device-bound work, set the current authorized physical NPU scope before
checking occupancy. On this 910B4 host use a per-device query such as
`npu-smi info -t proc-mem -i <authorized-physical-id> -c 0` for each allowed
card. If a scope is restricted, avoid commands that read the whole fleet.
Skill-only edits need no device query.

Read `.agents/HANDOFF.md`. For every relevant active `work/*` tree, read its
`task.json` and branch-local `HANDOFF.md` before touching claimed files,
containers, ports, processes, or NPUs.

Use `.agents/git-policy.yaml` as the repository override for workstream
lifecycle limits. The current active worktree budget is eight. Inventory first;
never reclaim a dirty, in-use, unpushed, unmerged, or unsuperseded worktree.

## Machine and experiment safety

- Re-prove physical NPU/process/container ownership in the same session as each
  action. HTTP health or container existence alone is insufficient.
- Resolve physical devices from Docker `HostConfig.Devices.PathOnHost`, then
  cross-check physical `npu-smi` process/memory state and the collaboration
  lock. Container-local `ASCEND_RT_VISIBLE_DEVICES=0,1,2,3` and logical NPU
  numbers do not prove that physical NPU0-3 are occupied; they can represent
  physical NPU4-7 after remapping.
- For a privileged container or an unexplained physical PID, inspect the
  device namespace mapping in `/proc/uda/namespace_node` and use the
  namespace root PID's cgroup to attribute the exact container. A missing
  explicit Docker device mapping or an empty per-card process table does
  not clear the reservation. A free lock also cannot clear external device
  ownership. For a TP4 test, admit the complete authorized group only after
  all four cards are available under the workstream's ownership rule.
- Report container device declarations together with container state. By
  default, running containers and live processes are active occupancy claims;
  exited containers are historical provenance that still requires owner and
  cleanup review but does not by itself prove current device use. If the user
  or experiment contract explicitly says any declaration blocks allocation,
  apply that stricter gate without reinterpretation.
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- Do not stop, restart, or replace a workload until its owning workstream and
  rollback instructions are identified.
- Inspect 1 GiB HugeTLB sysfs state and consumers before any memory-pool change.
  Free pages inside the pool are not ordinary free RAM or permission to release
  them.
- Keep datasets, weights, checkpoints, credentials, raw profiles, and large
  generated artifacts outside Git.

For performance work, also use `ascend-npu-environment-orientation`,
`ascend-inference-tuning-loop`, and `ascend-benchmark-evidence`.

For Qwen3.x BF16 runtime work on the pinned vLLM-Ascend v0.23 family, read
[references/qwen35-v023-runtime-lessons.md](references/qwen35-v023-runtime-lessons.md)
before allocating NPUs. It records which upstream and built-in routes were
measured, retired, rejected, or retained as partial components. Treat it as
candidate-screening knowledge, not as proof of current host state or final
performance attainment.

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
- Container occupancy reports include state and identify whether the default
  active-claim rule or an explicitly stricter declaration rule was applied.
- No verification value or other credential appears in tracked files or diffs.
- `./scripts/validate-mst.sh` and `git diff --check` pass.

## Failure handling

Preserve exact AWMCP errors. Refresh topology after routing drift and retry only
when the response marks the failure retryable. A control-plane timeout is not
proof of host, command, container, or NPU failure and can occur after a command
has already produced partial side effects. Before retrying, inspect the exact
branch, worktree, container, process, or file target idempotently. Do not mutate
the machine to compensate for an unproven diagnosis.

If gateway health responds but topology omits the exact host, record the
target route as unavailable. Confirm the identity of any approved alternate
route before using it. A timeout or a missing operation ID after dispatch
requires checking the original operation, unique run root, and exact owned
container or process for terminal evidence before any relaunch. When the
host returns, re-prove the route and take a fresh resource snapshot. The
earlier connection problem and any new resource conflict are separate facts.
