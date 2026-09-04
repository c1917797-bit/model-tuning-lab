# Handoff Dense Transition Workstream

- State: `completed / ready`.
- Base: `origin/main@fbc79c41c37c8900f0623ce8941304e9bfde5cf1`.
- Purpose: reconcile durable lessons and global maintainer handoff after the Dynamic MoE negative result and the switch to dense-model Paper-to-Ascend work.
- Protected scope: `.agents/HANDOFF.md`, `docs/LESSONS_LEARNED.md`, `docs/RUNBOOK.md` only after this start checkpoint is pushed.
- Concurrent workstreams remain authoritative for their own execution state:
  - `work/exp-20260904-qwen35-dense-mtp-paper-to-ascend`
  - `work/exp-20260904-qwen38-prefix-cache-general-eval-final`
- Dynamic MoE audit branch is superseded for the current dense target and retained remotely at its own branch.
- Start checkpoint: `2671136845421c8b6c155bdb9a78e52f5488e7a7`, pushed and equal to upstream before protected-path edits.
- Current change: global handoff now points to the two active isolated workstreams; durable lessons/runbook capture the Dynamic MoE negative result and the architecture-applicability gate.
- Implementation commit: `e8e1db1f56a3d378bd98d79918d7cdfcd0d6294f`.
- Validation: Maintainer Skill Tree PASS (17 skills), JSON parse PASS, required global HANDOFF section order PASS, `git diff --check` PASS.
- Resume: fetch target and this remote workstream, require zero target drift or revalidate, then integrate this exact source with a non-fast-forward merge and rerun the handoff-only gates on the final merge tree.
