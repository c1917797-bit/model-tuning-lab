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
   again before every remote mutation. After a timeout, routing error, or long
   pause, refresh topology and re-prove that the peer still owns
   `chicaihong01/ma` before continuing.
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

## Host-side Python test environment

The host system Python is 3.9 and does not satisfy this repository's
`requires-python >=3.10`. For CPU-only unit tests, use:

- uv: `/cache/cch/toolchains/uv/bin/uv`;
- managed Python: `/cache/cch/toolchains/uv/python`;
- virtual environment: `/cache/cch/python-envs/model-tuning-lab-py311`;
- CPU dependency cache: `/cache/cch/toolchains/uv/cache-cpu`.

From any fresh clone or worktree, run
`./scripts/bootstrap-host-test-env.sh`, then use the printed command. The
script is idempotent, keeps large dependencies on `/cache`, and passes the
current clone's `src` through `PYTHONPATH` instead of binding the shared
environment to one worktree.

This environment is only for host-side unit tests. Device execution remains
inside the pinned Ascend container with its matching CANN, `torch_npu`, vLLM,
and vLLM-Ascend stack. Do not install device packages into the host-test
environment. If dependency resolution selects CUDA/NVIDIA packages or an
unpinned newer Torch, stop and inspect the plan rather than completing the
download.

## Machine and experiment safety

- Re-prove physical NPU/process/container ownership in the same session as each
  action. HTTP health or container existence alone is insufficient.
- Resolve physical devices from Docker `HostConfig.Devices.PathOnHost`, then
  cross-check physical `npu-smi` process/memory state and the collaboration
  lock. Container-local `ASCEND_RT_VISIBLE_DEVICES=0,1,2,3` and logical NPU
  numbers do not prove that physical NPU0-3 are occupied; they can represent
  physical NPU4-7 after remapping.
- Report container device declarations together with container state. By
  default, running containers and live processes are active occupancy claims;
  exited containers are historical provenance that still requires owner and
  cleanup review but does not by itself prove current device use. If the user
  or experiment contract explicitly says any declaration blocks allocation,
  apply that stricter gate without reinterpretation.
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- For a long or repeated device experiment, check active jobs that can
  intermittently enter the target physical cards; one empty `npu-smi` snapshot
  does not establish an interference-free window. Keep a continuous
  physical-device process guard during the run. If an unexpected PID appears,
  invalidate that arm, capture its cgroup/container identity at detection time
  before a short-lived PID exits, preserve the PID/time and raw artifacts,
  release only owned resources, and re-establish isolation before any new-root
  retry. Container identity is not proof of the human launcher; a vanished PID
  without retained cgroup evidence does not prove its owner.

For a multi-minute or multi-hour controller, do not set the remote executor's
process timeout shorter than the campaign. Prefer asynchronous execution with
a campaign-length timeout and poll the stable operation ID. If the connector
or executor times out, treat that as control-plane ambiguity: inspect the same
operation, exact container labels, device processes, port, and immutable root
before retrying. A detached owned container can outlive its controller; never
blindly relaunch, and release only the exact resources proven to belong to the
failed attempt.
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
