# Qwen3.5 standalone patch import handoff

## Status

- Execution: started.
- Integration: not ready.
- Base: DRRQR import commit `b4962e414aa21fb319b3935dc0d7125b94b058f7`.
- Source repository: `https://github.com/c1917797-bit/qwen35-vllm-ascend-patch.git`.
- Source branch: `feature/qwen35-validated-runtime-patch`.
- Source HEAD: `c61f5f984e13e2ca37fd410783b7e97f960a57f3`.
- Source history: 3 commits, retained as a merge parent.

## Scope

Import source code and complete history under
`projects/qwen35_vllm_ascend_patch/`, register the second project, and record
provenance. Do not modify the source clone or claim that repository import
completes Qwen3.5 performance or accuracy acceptance.

## Current action

Push this start checkpoint, then create a deliberate two-parent merge whose
second parent is the exact source HEAD. Keep the source tree identical under
the project prefix except for explicitly documented project-level governance
additions or adaptations.

## Next actions

1. Import the exact source tree beneath the stable project prefix.
2. Add project `PROJECT.md` and a root-rules-referencing project `AGENTS.md`.
3. Register source provenance and history policy in `projects/registry.yaml`.
4. Verify ancestry, two-parent shape, tree equivalence, structure validation,
   clean worktree, and pushed branch identity.
5. Record tests and old-path adaptations as follow-up work; do not block the
   code-and-history import on them.
