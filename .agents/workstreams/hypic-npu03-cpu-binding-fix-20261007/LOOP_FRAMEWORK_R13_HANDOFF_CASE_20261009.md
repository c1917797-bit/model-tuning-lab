# Loop-framework real-task case: stale active-r13 handoff caught and repaired

Task: keep a long-running HYPIC full-pair experiment aligned with the user's
short-, medium-, and long-term Skill-validation goals while another maintainer
could resume from Git alone. Scope: named chicaihong01 worktree, CPU-only
handoff repair; the already-running NPU0–3 service was not restarted,
modified, or treated as a completed result.

Exact integrated-main Skill: `mst-loop-engineering-framework` blob
`32ae84455395011aa83308e3cc05759aa2206441` at main
`ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`. The main Skill's
non-drift contract requires persistent current state, a known validation
gate, independent checking, a next step and Git checkpoint/blocker. The
branch's extra three-horizon reference is **not** attributed to main.

Observed counterexample: before commit
`494771a8157624d659f562837f380f166f499d8d`, `task.json` still
said r12 terminal and `active_attempt: null`; its next action asked to
resolve the quality estimand even though the r13 dual-estimand protocol had
already been frozen and baseline operation `exec-0000000000001a76` was live.
The old handoff test asserted that stale null value. A successor following
that machine-readable task state could have relaunched an occupied lane or
repeated a settled protocol decision.

Repair checkpoint `494771a8157624d659f562837f380f166f499d8d`
records the active controller handle, immutable root, source commit,
actual-idle NPU0–3 boundary, no NPU4–7 rule, and long/medium/short
objectives. Its next action says to poll the same operation, inspect 127×3
terminal raw/guard/source/release receipts, and only then launch the
candidate on an actually idle lane. The handoff regression now rejects
`active_attempt: null`. The focused replay
`verify_loop_framework_case.py` checks the before/after Git snapshots.

At this checkpoint, 79 workstream offline tests, the 29-Skill structure
validator and the 19-case provenance verifier passed. The AWMCP operation
was confirmed running separately from the task file; neither a task-file
string nor a green structural test proves a final HYPIC result. GitHub
authentication remains unavailable on this host, so local commits are not
misreported as pushed. A fresh-agent orient/execute/push trial and terminal
quality/performance decision are still missing. Long-term acceptance for
this exact main Skill is therefore **partial-evidence**, not verified.

Reusable failure rule: compare the task manifest's active handle and
decision state with the live operation and branch-local handoff before each
iteration; a syntactically valid but stale manifest is a failed non-drift
gate. Do not encode a transient sample count as immutable task state.
