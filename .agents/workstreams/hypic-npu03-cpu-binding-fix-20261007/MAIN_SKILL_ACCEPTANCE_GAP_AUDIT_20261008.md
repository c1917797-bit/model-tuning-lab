# Main Skill real-task acceptance gap audit — 2026-10-08

This is a scope check, **not** a new Skill acceptance result. Fresh
`git fetch origin main` resolved `origin/main` to
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`; its tree contains 29
`SKILL.md` files. `verify_skill_matrix.py` matches all 29 registry IDs
exactly once against `SKILL_VERIFICATION.md` and reports bounded campaign
codes V11/P14/N4. Those codes do not mean 29 universally verified Skills.

At 14:51 UTC, `verify_skill_cases.py` independently checked the first
per-Skill case receipt, `skill-cases/mst-repo-onboarding.json`: its report
SHA256 and tested/current Skill and registry Git blobs match. The original
fresh clone is absent, so that case correctly says `partial-evidence` for
long-term portable acceptance. The verifier reports **1 case with verified
provenance, 28 Skills without a case, 0 cases claimed long-term verified**.
It does not replace the bounded V11/P14/N4 campaign ledger or rerun onboarding.

At 15:09 UTC, the cache10r3 HYPIC service's continuous guard caught an
actual foreign physical NPU3 process and released only the owned container
before any scored request. A second per-Skill case now binds this bounded
host-maintenance safety observation to the exact main Skill blob and the
retained conflict report hash. Its long-term state is also
`partial-evidence`: user-specific mapping override, work-branch script
differences and incomplete canonical-main workflow preclude full acceptance.
The case inventory is now 2 provenance-checked partial cases, 27 missing,
and 0 long-term verified. No quality score or Skill-wide pass is inferred.

At 15:15 UTC, a separate real Git checkpoint exercised the confirmed
`commit_implies_push` named-workstream path: validation exited 0 before
the coherent commit, immediate push reached the named remote branch, and
a subsequent live remote check matched HEAD/upstream with a clean worktree.
The new `mst-git-checkpoint-policy` case and focused replay script limit
acceptance to that representative path. The inventory is now **3 cases:
1 long-term verified in bounded scope, 2 partial, 26 missing**. This does
not upgrade the other policy options or HYPIC quality.

The branch-local maintainer handoff was then condensed to a 102-line
current state, preserving 387 historical lines separately. A pinned Git
snapshot replay verifies the 0–8 section order, critical resume facts and
unchanged integrated global handoff. This supplies a second bounded
long-term verified representative case. Current inventory: **4 cases:
2 verified, 2 partial, 25 missing**. No global handoff or HYPIC acceptance
is inferred.

At 16:08 UTC, the real cache10r5 host-orientation task supplied a fifth
case tied to the exact current-main `ascend-npu-environment-orientation`
blob. The frozen contract pins source/image/model/dataset/device fields,
the older paired canary proves a related device-side path, and the new
startup guard proves actual foreign process/cgroup isolation. Missing
complete software/topology fields, a same-identity cache10r5 canary and
baseline-drift decision keep its long-term state **partial-evidence**.
The verifier now reports **5 provenance-checked cases: 2 bounded verified,
3 partial, 24 missing**. The historical V campaign row is not upgraded
to a portable full-Skill pass by this case.

At 16:39 UTC, the sixth case exercised `mst-experience-ingestion` on the
real cache10r6/r7 shared-NPU startup intrusions. The lesson was classified
as an existing host-maintenance Skill update, with a branch registry trigger
and a structured eval. A focused replay rehashed the raw lane-guard and
cleanup receipts, verified physical NPU2/NPU3 foreign PIDs and 0/127
pre-health aborts, and passed the 29-Skill structure check. Main's host Skill
does not yet contain the continuous guard, so the long-term state remains
**partial-evidence**. Inventory: **6 cases, 2 bounded verified, 4 partial,
23 missing**. This does not validate HYPIC algorithm quality or performance.

## What the current records prove

- The branch has a human-readable 29-row inventory with each Skill's
  bounded status and remaining acceptance condition. The 2026-10-06
  `hypic-qwen36-e2e-2048-20261006/skill-validation.json` covers only
  11 named Skills from a different historical attempt. It must not be
  treated as a 29-item current behavioral pass.
- Specific HYPIC performance, quality, isolation, source and handoff
  artifacts carry hashes in their owning reports. For example, the
  cache10r2 clean-set receipt is SHA256
  `99f2578adddd041f7a84fe441a1ac02b754b2c1a8217054e80e855b67e7f55bd`.
  It proves 56 pre-intrusion candidate samples, not the whole quality arm.
- The 29-Skill `scripts/validate-mst.sh` check proves repository
  structure. The matrix verifier proves inventory integrity. Neither
  exercises a Skill on a representative new task.
- The fresh-clone onboarding case has a separately recorded real task and
  result in `ONBOARDING_FRESH_CLONE_ACCEPTANCE_20261008.md`; this is
  bounded onboarding evidence, not host/NPU entry or all-Skill acceptance.

## Unmet long-term acceptance fields

| Required per Skill | Current state | Closure evidence needed |
| --- | --- | --- |
| Exact main Skill bytes/version | Main commit pinned globally; most rows do not name the individual Skill blob | Pin each tested `SKILL.md` blob/commit in its case receipt. |
| Representative real task and outcome | HYPIC and onboarding are named, but several P/N rows have no independently executed task | One task ID, request, environment and observed artifact per Skill; keep N when not exercised. |
| Applicable behavioral gate | Remaining work is described, but not always as an executable oracle | Record expected behavior, failure boundary and actual observation before assigning long-term verified. |
| Raw evidence provenance | Some reports include external hashes, but the 29-row table lacks a per-row artifact/hash link | Resolve and rehash the exact raw receipt(s) for each verified claim. |
| Environment and date | HYPIC scope/date are global; not bound to every row | Record host/runtime/model or CPU-only scope and execution time per case. |
| Repeatable regression | Shared structural/matrix checks and focused HYPIC tests exist; no one-to-one regression for all 29 | Save a runnable focused check or a precisely reproducible manual acceptance procedure with expected result. |
| Decision scope and drift trigger | Some row notes state limits; no uniform revalidation trigger | State what the result does *not* cover and which main/runtime/data change forces recheck. |

Do not raise a P/N row to V merely to fill this table. Conversely, a bounded
V row may remain V in the current HYPIC campaign while its broader long-term
portable acceptance record is still incomplete. The next durable artifact
should be a versioned per-Skill case index with explicit missing fields,
then real representative tasks for the open rows. HYPIC quality and
performance remain separate short-/medium-term gates; no NPU work is
authorized by this audit.
