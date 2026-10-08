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

The default script replays the **historical** checkpoint offline: it
fails closed if the confirmed policy, exact main Skill blob, branch/upstream
identity, checkpoint parent/files, or ancestry in the local HEAD and cached
remote-tracking ref drifts. The cached ref is not a fresh GitHub read; the
separate live `exec-000000000000149d` receipt proves the historical push.
The default `current_branch_synced` field means equality with the cached
tracking ref only and is not proof of live remote equality. Run with
`--require-current-sync` to check current HEAD against the **live** remote;
that mode uses a bounded 15-second network call and fails on authentication,
network uncertainty, dirty worktree, or unpushed commits. It now correctly
fails while the branch is ahead and target-host HTTPS auth is missing. The
later authentication failure does not erase the earlier successful
checkpoint. Re-run the ordered AWMCP operation queries while retained
to review validation-before-commit proof. Neither check proves that all
future agents will obey this policy.
