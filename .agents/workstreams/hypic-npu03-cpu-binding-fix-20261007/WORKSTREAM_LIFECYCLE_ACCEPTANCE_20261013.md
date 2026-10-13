# Named workstream lifecycle acceptance — 2026-10-13

## Outcome and source

Bounded PASS for exact-main mst-parallel-workstreams:
main ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2,
Skill blob c47b989bc006561d347e0fbfe5d59026fb8e91e0.
The runner copies that exact Skill into the subject repository; the independent
auditor confirms its Git blob in the final merged tree.

Actual Git transactions completed, not merely schema checks or mocked pushes.
Execution chicaihong01/mc exec-0000000000000069 exit0; independent read-only
audit006a exit0. Additional false-attestation checks initially found one error
type inconsistency in006b: invalid ancestry was rejected as CalledProcessError,
rather than the auditor's expected RuntimeError. The auditor now reports a
uniform ancestry rejection. Six controls plus the original-object audit pass006c.
The Git scenario was NOT rerun to repair this reporting detail.

## Retained subject and exact graph

Retained fixture root: /cache/cch/mst-workstream-lifecycle-f6v78cil
Transport: local bare Git origin; no GitHub credential or network test.
Primary: root/primary; remote: root/origin.git.
The exact fixture worker and detached read-only test checkout were removed after
the required eligibility checks; the original repository, its real worktree,
two unrelated drafts and all NPU resources were untouched. The source branch
is retained in the bare remote and reachable from the fixture's merged main.

| Checkpoint | Commit |
|---|---|
| Original main/base | 10bc1b154a53571b10439d5f97cee2ea3504bb60 |
| Pushed start,product still unchanged | 494fdc5137404ac6b986da2e355a5bf5b854b9b4 |
| Product implementation | 470147cdcfdc70882c3311418e96da644f96b055 |
| Controlled target-drift injection | aadfe8157be5e85b265413d88b734d29c9389032 |
| Target merged and revalidated | 0f43f88449316f3168019aa36c6096950ede9418 |
| Ready evidence envelope/source | b483d2bd58757b6d1604c1199ab7747d9438718c |
| Validated no-ff integration | 6cfd993eb1619626ea16c1535f26ca1e88f964ba |

The source handoff names the validated content checkpoint; the later ready
envelope is bound by its exact fetched remote OID in target-owned evidence.
This avoids pretending that a commit can contain its own future Git hash.

## Requirement coverage

- Route: work/bounded-lifecycle attached to an independent worktree; no detached
  authoring. The deliberate target advancement is fixture setup for drift,
  not an example authorizing arbitrary direct-primary production changes.
- Start: original base,frozen policy hash,owner,creation time,objective,boundaries,
  dependency list,all five claim kinds,resource/retention/resume records exist.
  The start checkpoint was validated,pushed and matched upstream before product
  code changed. Dependencies were empty and resource leases were fixture-only.
- Checkpoint: seven actual commits each follow focused validation. The ordered
  journal's write-tree value matches the subsequent committed tree object.
  Seven actual pushes succeeded without force flags.
- Drift: target advancement was rejected until merged into the workstream;
  original base and constraining policy hash remained unchanged.
- Readiness: dirty worktrees and detached authoring are rejected; completed/ready
  is separate from target-owned merged. Validated content identity is retained.
- Integration: exclusive lock rejects a second integrator. Source is the fetched
  origin/work ref. Wrong attestation is rejected. Final evidence binds exact
  target parent and source. Final merged tree (including target-owned state,
  accepted knowledge and global handoff) passes before the integration commit.
- Post-push: actual bare remote main equals the audited integration commit;
  the merge parents are exactly target parent and source. Source is reachable.
- Reclamation: clean,pushed,reachable source and released target-owned claims are
  required. Unmerged cleanup is rejected. Only fixture-owned worker and its
  local branch are reclaimed; one primary worktree remains. Remote source retained.
- Claims: earlier (created_at,task_id) wins the conflicting exclusive claim control.
  This is arbitration-rule evidence,not proof of actual concurrent-agent scheduling.

Seven lifecycle negative controls: detached authoring,dirty readiness,stale target,
wrong source attestation,competing integrator,later exclusive claimant and
unmerged reclamation.
Six independent-auditor controls: wrong source,parent,original base,policy hash,
Skill identity and merge commit.

## Durable receipts

result.json SHA256 a77919f54f7fc39451f5f08fa633a1679f1cb8e35b20ca0e70977b40f46f680f
execution-journal.json SHA256 c736250fb3bedf891af59119d6e0932b8ebac858caa1f14686c4988fce032cf9

Both files remain under the retained fixture root. The sanitized outer execution,
initial auditor-error result and corrected regression result are in
WORKSTREAM_LIFECYCLE_RECEIPTS_20261013.json.

## Replay without repeating the scenario

From the model-tuning-lab task repository:

```bash
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/audit_local_git_lifecycle.py /cache/cch/mst-workstream-lifecycle-f6v78cil
MST_LIFECYCLE_FIXTURE=/cache/cch/mst-workstream-lifecycle-f6v78cil python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_local_git_lifecycle_audit.py
```

The runner's --run creates a NEW isolated fixture; do not repeat a completed
scenario merely to increase pass counts. Existing objects are sufficient for replay.

## Acceptance and remaining scope

This one main Skill gains bounded functional acceptance for a single serialized
integrator and local bare Git transport: current totals12 bounded verified/17 partial.
It does not prove GitHub authentication,remote protection rules,real multi-agent
race scheduling,real model-tuning-lab main integration or all29 Skill behaviors.

The real repository remains unmerged and locally ahead while authentication is
unresolved. No repeated failing push was attempted. Do not mark its execution
completed/integration ready based on this fixture. No HYPIC quality work or NPU work.
