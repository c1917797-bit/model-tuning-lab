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
