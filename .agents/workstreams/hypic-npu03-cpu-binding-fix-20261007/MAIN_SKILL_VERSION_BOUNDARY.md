# Main-Skill version boundary for the HYPIC validation campaign

The 29-Skill inventory is pinned to `origin/main` commit
`f1f37a39bd86f7db5fd3ee3dea358ae6868275c6`. This worktree executes
on `work/hypic-npu03-cpu-binding-fix-20261007`; campaign evidence is not
automatically proof that the exact main-branch text behaved the same way.

A read-only `git diff --name-only origin/main -- .agents/skills` check on
2026-10-08 found these five Skill identities changed in this branch:

| Skill | Changed files relative to pinned main | Attribution |
| --- | --- | --- |
| `ascend-benchmark-evidence` | `SKILL.md` | Branch rule; main promotion pending |
| `ascend-model-quality-evaluation` | `SKILL.md`, `references/quality-test-contract.md` | Branch quality protocol; full hot-path paired audit pending |
| `ascend-performance-optimization` | `SKILL.md` | Branch CPU-floor attribution rule; main promotion pending |
| `paper-ingestion` | `SKILL.md` | Branch derivative-coverage rule; main promotion pending |
| `paper-to-ascend-reproduction` | `SKILL.md` | Branch reproduction rule; full hot-path quality pending |

The other 24 Skill identities have no file diff against pinned main in this
worktree. In particular, `mst-repo-onboarding` is unchanged, so the
resume-session check in `ONBOARDING_RESUME_CHECK_20261008.md` is evidence
about the main text for that bounded route. Its fresh-clone route remains
unverified.

Before changing a main-Skill status to `verified`, record the exact Skill
blob/ref tested, the real task and acceptance gate, raw-evidence hash,
environment/date, and failure boundary. For the five changed identities,
either test the pinned main version separately or merge reviewed branch
repairs and rerun focused behavior checks on the promoted version. The
structural 29-Skill validator is not a substitute for this behavioral gate.
