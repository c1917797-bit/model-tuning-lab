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

Read [references/session-orientation.md](references/session-orientation.md)
at the start of every remote session, before touching claimed files or resources.

## Host-side Python test environment

Before host-side Python tests, read
[references/host-python-tests.md](references/host-python-tests.md).
Do not install device packages into the host-test environment.

## Machine and experiment safety

Before inspecting or changing machine/runtime resources, read
[references/machine-experiment-safety.md](references/machine-experiment-safety.md).
This includes container, port, process, NPU, HugeTLB and long-controller work.
Read its Qwen runtime lesson when that stated runtime condition applies.

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
