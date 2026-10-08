# Git checkpoint policy: bounded real-task acceptance

The exact current main Skill blob for `mst-git-checkpoint-policy` is
`10da1ba69cb54c46dc6bdbdbbe7c434bc1b423f8`; the main registry blob
is `2611864bbcf719d57920aae03ff9eb85521526b4`. The confirmed
`.agents/git-policy.yaml` selects `commit_implies_push`. This case
tests its **named workstream checkpoint** path, not manual-only, direct
primary, PR, force-push rejection, or lifecycle reclamation.

Real task: preserve the new, bounded chicaihong01 host-isolation Skill
case and its audit update on the existing
`work/hypic-npu03-cpu-binding-fix-20261007` branch. The three committed
files are the case JSON, its provenance unit test, and the 29-Skill gap
audit. No local machine file or product code is mixed into that commit.

Ordered execution evidence from the direct target-host AWMCP operations:

1. `exec-0000000000001497` exited 0 after the case verifier,
   27 offline tests, `./scripts/validate-mst.sh` and
   `git diff --check`. It reported
   `PASS: Maintainer Skill Tree structure is valid (29 skills)`.
2. Only then did `exec-0000000000001498` stage those exact three files,
   create checkpoint `57771f36d194098883119aeb28692017399cac15`,
   push it to `origin/work/hypic-npu03-cpu-binding-fix-20261007`, and
   report an empty `git status --short`. Both operations used the same
   direct chicaihong01/ma peer; their terminal exit codes were 0.
3. A separate read-only `git ls-remote --heads origin` check in
   `exec-000000000000149d` returned exactly the checkpoint hash for
   the named remote branch. HEAD, configured upstream and live remote
   matched; the working tree was clean. The checkpoint's commit time was
   2026-10-08 15:15:26 UTC.

Replay from the named worktree after this case is pushed:

```sh
./scripts/validate-mst.sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_git_checkpoint_case.py
```

The script fails closed if the confirmed policy, exact main Skill blob,
branch/upstream, checkpoint parent/files, clean worktree, live remote
equality or checkpoint ancestry drifts. Re-run the ordered AWMCP operation
queries while those control-plane records are retained to review the
historical validation-before-commit proof. The repository checks are
repeatable; they do not prove that all future agents will obey this policy.
