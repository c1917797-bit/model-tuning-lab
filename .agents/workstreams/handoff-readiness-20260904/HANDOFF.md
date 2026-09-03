# Workstream Handoff

- Task: consolidate historical tuning knowledge and make the repository ready for immediate maintainer takeover.
- Branch: `work/handoff-readiness-20260904`.
- Base: `f49c63f8c8f790f8bb79b047cf689f852e1a4682` (`origin/main`).
- State: `completed / ready`.
- Boundary: add durable lessons/runbook and propose a target-owned global handoff refresh; do not modify the active prefix-cache experiment files or NPU resources.
- Concurrent work: `work/exp-20260903-qwen38-prefix-cache-general-eval` is active and owns the Qwen prefix-cache experiment plus NPU4-7 candidate resource.
- Validation: `./scripts/validate-mst.sh` and `git diff --check`.
- Remote start checkpoint: `ffa9e3f4124dd8417e3d672fd45f767f939dd293` is pushed and matches the branch upstream.
- Live snapshot: the prefix-cache workstream baseline is serving on 8200 and owns physical NPU4-7; an eval client is currently running. NPU0-3 are idle and 8100 is not listening at the snapshot time.
- Implemented commit: `1cbf003034b6e2e2df4080479fae302b5e4518dd`.
- Validation: Maintainer Skill Tree PASS with 17 skills; `git diff --check` PASS.
- Integration: merge the fetched remote workstream non-fast-forward into `main`, reconcile target-owned `.agents/HANDOFF.md`, validate the exact final merge tree, and verify the primary push.
