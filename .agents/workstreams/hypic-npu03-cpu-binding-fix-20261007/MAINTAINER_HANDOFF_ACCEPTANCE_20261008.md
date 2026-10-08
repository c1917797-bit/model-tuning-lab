# Maintainer handoff: bounded branch-local real-task acceptance

Current main Skill `mst-maintainer-handoff` has Git blob
`f9eba56e3048643163342b1bab024632929b382c`. This case exercises
its branch-local current/historical separation, not a global main
integration handoff.

Real task: after cache10r3's real NPU3 collision and subsequent Skill
case progress, leave the active HYPIC workstream resumable without
requiring the next maintainer to parse every prior checkpoint.
`AGENTS.md`, global `.agents/HANDOFF.md`, branch task.json, the
relevant Skill, branch status and recent Git log were read first.

Checkpoint `622d68af221d76cf9098db8ef4ce9141da2cf047` replaced
the branch-local current handoff with 102 lines in the Skill's ordered
0–8 sections. It gives the status, three-stage goal, actual blocker,
evidence links, next actions, validation commands, prohibitions and
recovery commands. The old 387-line checkpoint chronology was retained
unchanged except its heading in `HANDOFF_HISTORY.md`. The integrated
global handoff was not edited, avoiding a false merged/shipped claim.

Direct target-host operation `exec-00000000000014a5` exited 0 before
the commit: 30 focused/offline tests passed, the three-case provenance
verifier passed, `./scripts/validate-mst.sh` reported 29 Skills valid,
and `git diff --check` passed. Operation
`exec-00000000000014a6` committed the three scoped files, pushed to
the named workstream branch, and reported a clean working tree.

Pinned SHA256 of the committed current handoff:
`6f850f99cc4d2390e590ef9336f5045b9e042d3e3a8928f044612f950d0674b7`.
Pinned history SHA256:
`0e3acab34a83a78c03b398c7055db561ae66c3021c5ffe56a1f68025f1d127fc`.
Focused regression SHA256:
`15093b0b5a6135f80aad07b726553e0116ef4c7b2fe50d5feb736f02f599e827`.

Replay the immutable snapshot from the named worktree:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_handoff_case.py
```

The replay checks the exact main Skill blob, historical Git bytes,
section order, concise/current versus preserved-history boundary,
critical resume markers and global handoff nonmutation. The handoff
still needs normal updates as the task progresses. This case does not
claim the global handoff is current, HYPIC is accepted, or every future
agent will execute the next action correctly.
