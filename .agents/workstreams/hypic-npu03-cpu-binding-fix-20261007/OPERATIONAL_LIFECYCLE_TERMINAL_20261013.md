# Operational lifecycle terminal — 2026-10-13

## Result
ISOLATION_FAILED_BEFORE_HEALTH. No operational responses, no quality/performance
measurement. Disabled stage aborted; uninstalled replacement restart NOT started.
Lifecycle acceptance remains incomplete; all29 acceptance remains12 bounded/17 partial.

## Execution and independent audit
- Frozen checkpoint059f343a4c33d6ad5024a15eeb6cf9d9138aaa87; same4429e35
  plugin package and image660ce23. Prior quality/canary verdicts unchanged.
- mc controller exec-00000000000000bf terminated exit1 after168.934s.
- Raw root: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/
  operational-lifecycle-20261013-disabled (immutable, do not rerun).
- At16:58:03.308276 UTC physical NPU3 PID3713849 belonged to container
  efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6.
  The same-snapshot guard retained its cgroup owner; later docker inspection
  identified the container as cannbench_ds. Human launcher remains unknown.
-20 guard samples,2 retained foreign observations,0 probe errors.
  This is an intermittent actual occupancy conflict, not a passive mapping.
- Exact own container ee50838d44e14e2d59cdde68d3d08a4749f153f1adcc83f2ddc8e66ad876fe33
  stopped/removed by the frozen controller; at16:59:08 UTC own NPUs and8223
  released. Foreign processes remained then, so lane_available=false.
- Later independent snapshot mc00c9: exact own container absent,8223 free,
  physical0–3 no processes. That later idle snapshot does not invalidate the
  captured interference or establish a protected restart window.
- Read-only failure audit mc00cb exit0; six false-claim/failure controls passed.
  Audit asserts executed contract/spec, physical scope, source checkpoint,
  retained full log, exact ownership/release and no health/request/second root.
  It does not claim live source-at-health or semantic correctness.
- Thirty focused tests total:24 pre-run plus6 failure-audit controls.
  Full positive lifecycle auditor cannot pass an incomplete run.

## Skill experience
Host-maintenance sustained guard correctly caught entry after an idle snapshot,
preserved the transient owner and released only owned resources. Runtime delivery
and Canary lifecycle obligations remain incomplete. Do not relabel this as
algorithm failure, a semantic recovery pass, or an uninstall acceptance.
No foreign job was stopped/modified; no physical4–7 allocation occurred.
No new retry is scheduled under this single frozen attempt.

## Handoff and remote state
Frozen plan059f343a was pushed and remotely verified in mc00c0; main remains
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2. The integration start checkpoint
3194848e598a919ad2d499867330fe23c5732b33 was subsequently pushed and verified
in mc00c2; this supersedes the earlier timeout for that start only. No repair
product files imported into the integration worktree yet. The integrator lock
and both worktrees remain owned/retained pending selective integration.
Current terminal edits require their own commit/push verification.

Replay:
python3 -B operational_lifecycle_failure_20261013.py
Keep the original success/failure roots and contracts unchanged.
