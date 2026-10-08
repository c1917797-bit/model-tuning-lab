# Practice-iteration planning real-task acceptance — 2026-10-08

Task: use the current-main `mst-practice-iteration-planning` instructions to
record a bounded HYPIC physical NPU0–3 quality-preflight stage, then validate
the result in the named worktree. Tested main: `ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`;
main Skill blob: `171e1f401b18dc6aaa4d38a2c3b6b260fca46123`.

1. The main Skill's exact output example prescribed `schema:
   practice-iteration/v1` and omitted `validated_commit`. The repository's
   `scripts/validate-mst.sh` requires `schema: mst-practice-iteration/v1`
   and a `validated_commit:` field for every practice-iteration YAML.
2. A new real HYPIC preflight plan following the main example failed the
   validator, `exec-000000000000155e`, exit 1: `missing practice iteration
   schema`. This is a Skill output-contract defect, not an NPU result.
3. The branch Skill now states the validator-compatible schema and defines
   `validated_commit` as a prior validated input checkpoint while the plan
   remains `in_progress`. The plan pins checkpoint `29d5d5dd8834dcf739937b1a7abc2f411f28a09e`,
   two next iterations with explicit pass criteria, and no claim that HYPIC
   quality or matched performance has completed.
4. The focused replay and `./scripts/validate-mst.sh` passed after the fix,
   `exec-0000000000001564`; the repair was committed at
   `4a95c87b8bf6a59557ad0e45c42e7b0616593caa`. The original main Skill
   remains unchanged, so this is a branch-local fix and a **partial**
   long-term main-Skill acceptance case.

Replay from the named branch:

```sh
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_practice_iteration_case.py
./scripts/validate-mst.sh
git diff --check
```

The focused check resolves the pinned checkpoint, verifies bounded pass
criteria and current-main-versus-branch Skill format, and fails when its
assumptions drift. It does not prove an uninterrupted NPU0–3 window, the
127-sample quality pair, a performance result, or execution from a fresh
main clone. Those remain separate acceptance gates.
