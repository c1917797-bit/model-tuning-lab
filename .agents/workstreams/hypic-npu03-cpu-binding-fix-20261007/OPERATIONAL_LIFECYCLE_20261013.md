# Authorized operational lifecycle — 2026-10-13

Human authorization: “允许，仅做生命周期验证”.
Scope: exactly one two-stage operational campaign, disabled then uninstalled
replacement restart, only on actually idle physical NPU0–3 and port8223.
This is new authority after the old performance deadline, not its extension.

## Frozen execution
- Code/source/image: reuse immutable native controller support and package,
  source4429e35177979c874bf053ab29789e4773f39b22/image660ce23; no observer.
- New contract: operational_lifecycle_20261013.json pins all new support,
  old contract/support, both actual Docker specifications and request hashes.
- New roots: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/
  operational-lifecycle-20261013-{disabled,uninstalled}; never reuse older roots.
- One retained prompt59 per mode, only1 output token, non-thinking, no scoring.
  The retained base preflight checks historical dataset identity but does not
  execute a quality suite; its legacy max2048 fingerprint is NOT this request cap.
- Disable: same native wrapper/package, switch0, four workers and valid response,
  no treatment events, exact release.
- Uninstall: only after independent disabled audit; install pinned package in
  a replacement owned container, pip-uninstall it, prove distribution/module/
  entrypoint absent before startup and at health, restart official service,
  complete one response and release.
- This is stateless replacement restart, NOT hot-unload or same-layer restoration.
  Prior enabled activation is retained evidence, not retested here.
- Per phase1200s alarm plus300s cleanup reserve; executor1600s.
  Fixed campaign deadline2026-10-13T18:00:00Z. No start with less than1500s
  remaining. No retry, no threshold changes after execution.
- Fresh topology/force_direct/physical processes before EACH stage; sustained
  isolation guard. Foreign tasks never stopped/modified;4–7 forbidden.
- Root/ filesystem full; DockerRootDir=/cache/docker and /cache has109GiB in
  prep00bc. Host TMPDIR=/cache/cch. No cleanup authorized/performed.

## Independent acceptance
operational_lifecycle_audit_20261013.py verifies exact Docker spec, live source,
request identity/accounting, four-rank physical PID mapping, absent treatment
events, uninstall probes, continuous isolation and exact release. A one-token
response may finish length; that is explicitly operational, not semantic success.
19 CPU checks passed in mc00bc before freezing (10new plus9existing).

Old native enabled/disabled semantic failures and r19 quality rejection remain
unchanged. This can close only bounded lifecycle obligations, never deployment,
full Canary correctness, whole Skill acceptance, or all29 success.

## Integration checkpoint remains separate
Worktree /cache/cch/model-tuning-lab-skill-repairs-20261013 local start3194848e,
remote equality unknown: push00af timed out, read probes00b1/00b4 timed out.
No six-file repair import performed. Both real integration worktrees and
owned mst-integrator-skill-repairs-20261013.lock are retained; do not recreate.
No authentication change or remote publication claim for that start checkpoint.

## Commands
Run from this workstream with TMPDIR=/cache/cch:
python3 -B operational_lifecycle_20261013.py --mode disabled
python3 -B operational_lifecycle_20261013.py --mode disabled --run
python3 -B operational_lifecycle_audit_20261013.py --mode disabled --write
After fresh admission only, repeat these for uninstalled.
