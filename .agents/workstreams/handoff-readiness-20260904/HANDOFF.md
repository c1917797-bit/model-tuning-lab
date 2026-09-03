# Workstream Handoff

- Task: consolidate historical tuning knowledge and make the repository ready for immediate maintainer takeover.
- Branch: `work/handoff-readiness-20260904`.
- Base: `f49c63f8c8f790f8bb79b047cf689f852e1a4682` (`origin/main`).
- State: `in-progress / not-ready`.
- Boundary: add durable lessons/runbook and propose a target-owned global handoff refresh; do not modify the active prefix-cache experiment files or NPU resources.
- Concurrent work: `work/exp-20260903-qwen38-prefix-cache-general-eval` is active and owns the Qwen prefix-cache experiment plus NPU4-7 candidate resource.
- Validation: `./scripts/validate-mst.sh` and `git diff --check`.
- Remote start checkpoint: `ffa9e3f4124dd8417e3d672fd45f767f939dd293` is pushed and matches the branch upstream.
- Live snapshot: the prefix-cache workstream baseline is serving on 8200 and owns physical NPU4-7; an eval client is currently running. NPU0-3 are idle and 8100 is not listening at the snapshot time.
- Changes in progress: add `docs/LESSONS_LEARNED.md` and `docs/RUNBOOK.md`; propose target-owned global handoff reconciliation at integration.
- Resume: validate the durable docs, commit/push them, then create exact-source readiness evidence before serialized integration.
