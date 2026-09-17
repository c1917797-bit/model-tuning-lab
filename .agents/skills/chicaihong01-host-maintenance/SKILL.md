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
- Treat NPU0-3, NPU4-7, ports, and running services as leased resources, not
  permanent assignments.
- Current operator-approved admission rule: a test may start when the intended
  physical cards have no actual NPU processes and the cooperative lease is
  held. An idle privileged or device-declaring container is inventory
  evidence, not by itself an occupancy veto. Recheck real device processes
  immediately after acquiring the lease and abort rather than compete.
- Do not stop, restart, or replace a workload until its owning workstream and
  rollback instructions are identified.
- Inspect 1 GiB HugeTLB sysfs state and consumers before any memory-pool change.
  Free pages inside the pool are not ordinary free RAM or permission to release
  them.
- Keep datasets, weights, checkpoints, credentials, raw profiles, and large
  generated artifacts outside Git.

For performance work, also use `ascend-npu-environment-orientation`,
`ascend-inference-tuning-loop`, and `ascend-benchmark-evidence`.

For Qwen3.5-27B performance work, do not mix the objective with
Paper-to-Ascend. The operator-approved stopping rule is TTFT P95 reduction at
least 20% and TPOT P95 reduction at least 8%, delivered as a removable runtime
Python monkeypatch plus an optional read-only custom OPP/bridge in the
unchanged official image. Absorb upstream optimizations first and do not
duplicate them, but require a profile-grounded model-specific integration
delta and an ablation that separates upstream-base benefit from the added
project benefit.

## Qwen3.5 delivery-convergence lessons

Use these rules when resuming `work/qwen35-performance-delivery`; they are
durable process guidance, while exact live metrics and paths belong in the
handoff and experiment evidence.

### Successful practices

- Freeze the acceptance rule before launching more experiments. Once an
  apples-to-apples candidate clears TTFT and TPOT, stop performance piercing
  and enter delivery convergence.
- Reuse the pinned upstream operator implementation unchanged. Keep the
  project delta to Qwen3.5 shape/dtype admission, pure-decode dispatch,
  fail-closed guards, activation evidence, and rollback.
- Deliver through a removable `sitecustomize.py` monkeypatch with read-only
  OPP/bridge mounts. Do not overlay or rebuild the vLLM-Ascend source tree.
- Preserve full-matrix evidence, hashes, activation proof, and the exact
  control/candidate protocol outside Git; commit only contracts, checkers,
  manifests, small reports, and reproducible launch/rollback instructions.
- Use a narrow quality subset only for causal isolation. T42, which disabled
  FusedGdnDecode while retaining the other T36 components, restored the two
  known query-rewrite intent regressions; this localized the risk without
  pretending that the subset was a final quality pass.
- Abort expensive downstream gates when an earlier mandatory gate has already
  failed. Stopping the T36 GSM8K run after the 357-row quality failure saved
  NPU time without weakening the final acceptance standard.
- Repair the six-way GDN projection at the arithmetic boundary rather than
  hiding its mismatch. The exact candidate pads each TP rank's fused output
  width from 4120 to 4128 with eight zero columns, runs the fused GEMM, then
  discards the padding. Preserve the official `qkvz` and `ba` weights for a
  fail-closed fallback and an independent exact oracle.
- Gate projection fusion with runtime metadata, not a concurrency label. Admit
  only pure Decode (`num_prefills == 0`, `num_decodes > 0`, hidden rows equal
  decode rows) within the evidence-backed row bound; route Prefill, mixed
  batches, malformed metadata, and larger shapes to the official path.
- Prove numerical equivalence at the affected layer before spending time on
  end-to-end quality. The repaired projection completed all 12
  `c1/c5/c8/c16` x three-run cells, 384 streaming requests, with no exact
  mismatch, engine fatal, request error, or abnormal finish. The oracle used
  `torch.equal`, so this is bit-exact evidence rather than tolerance-based
  similarity.
- Validate actual engine shapes. In the completed matrix, logical c5 produced
  padded decode GEMM rows of 6 followed by 4, 2, and 1. Runtime metadata and
  timestamped cell boundaries are therefore authoritative for shape coverage;
  the client concurrency name is not.
- Treat Conv weight prepacking as a recurrent-state transformation, not only a
  one-call output check. The accepted numerical campaign covered NPU0-3,
  batches 1/5/8/16, multiple seeds, and four recurrent steps, checking output,
  state, and determinism with zero mismatch.
- Keep the three accuracy layers separate: layer-local exact arithmetic,
  deterministic semantic regression samples, and the final full GSM8K
  Control/Candidate gate. A fixed 26-row semantic capture can confirm that a
  repaired service is operational, but it cannot replace full GSM8K.

### Failed practices and corrections

- Do not keep optimizing toward a superseded 10% TPOT target after the
  operator has accepted 8%. Stale Skill or HANDOFF text is not authority over
  the latest explicit acceptance rule; update both immediately.
- Do not restart from a clean design after delivery work has begun. Inherit
  the existing branch, dirty files, contracts, capture/check scripts,
  evidence hashes, and rollback path; inventory them before editing.
- Do not equate a performance pass with final promotion. T36 cleared the
  revised performance rule but its full 357-row comparison exposed material
  intent regressions at dataset indices 3 and 29. Preserve that evidence and
  never label the candidate accuracy-safe.
- Do not describe the run order from memory. Read the artifact timestamps.
  The 2026-09-16 T36 matrix ran Candidate before Control, despite an earlier
  summary saying the reverse. This is valid measured evidence but leaves
  temporal-order drift as a delivery risk, especially when c1 is close to the
  threshold; resolve it with a bounded reverse-order confirmation, not a new
  optimization campaign.
- Do not continue unrelated T41/T42 piercing merely because experimental
  assets exist. After the performance stopping rule is met, only work that
  closes a delivery gate is in scope: patch packaging, provenance, tests,
  activation/rollback proof, quality disposition, evidence manifest, and PR.
- Do not lower, omit, or fabricate quality results to make a PR look verified.
  A performance-ready package may be prepared, but final promotion still
  requires an explicit, honest quality decision.
- Do not treat an M=1 unit test as coverage for real continuous batching.
  Graph padding and scheduler shrink produce different GEMM row counts even
  inside one client-concurrency cell. Expand the bound only after exact
  evidence covers every observed runtime shape.
- Do not count graph-capture warmup shapes as workload evidence. Correlate
  timestamps and process/cell boundaries before attributing a shape to a
  benchmark run.
- Do not report an exact-oracle matrix as performance evidence. Recomputing the
  official projection beside the candidate deliberately adds work and distorts
  TTFT and TPOT. Final performance must run the same removable patch with the
  oracle disabled and otherwise identical Control/Candidate settings.
- Do not use generated-text equality to prove projection arithmetic. Sampling
  and scheduler nondeterminism can change text independently of the fused
  layer. Use `torch.equal` at the layer boundary, then run semantic and GSM8K
  gates for end-to-end quality.
- Keep upstream FusedGdnDecode excluded after its demonstrated semantic
  regressions, even when it improves performance. Admit it only after an
  upstream correctness fix is independently verified; do not mask its failure
  with unrelated projection or Conv changes.
- Do not restart a healthy NPU workload because one control-plane read returns
  a transient error. Preserve the error, re-prove the direct route, and retry
  the narrow control operation; distinguish transport failure from compute
  failure.

### Resume invariant

The authoritative continuation point is the existing
`work/qwen35-performance-delivery` worktree. Before any new run, read its Git
status and current handoff, reuse completed artifacts, and ask whether the run
closes a named delivery gate. If it does not, do not start it.

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
