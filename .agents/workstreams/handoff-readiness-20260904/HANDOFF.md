# Workstream Handoff

- Task: consolidate historical tuning knowledge and make the repository ready for immediate maintainer takeover.
- Branch: `work/handoff-readiness-20260904`.
- Base: `f49c63f8c8f790f8bb79b047cf689f852e1a4682` (`origin/main`).
- State: `started / not-ready`.
- Boundary: add durable lessons/runbook and propose a target-owned global handoff refresh; do not modify the active prefix-cache experiment files or NPU resources.
- Concurrent work: `work/exp-20260903-qwen38-prefix-cache-general-eval` is active and owns the Qwen prefix-cache experiment plus NPU4-7 candidate resource.
- Validation: `./scripts/validate-mst.sh` and `git diff --check`.
- Resume: confirm the remote start checkpoint exists, then add evidence-backed success/failure lessons and takeover runbook; keep observed incidents separate from upstream-only risk patterns.
