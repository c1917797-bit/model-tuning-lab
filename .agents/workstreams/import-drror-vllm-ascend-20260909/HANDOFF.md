# Import drror_vllm_ascend

## Objective

Place the DRRQR plugin under `projects/drror_vllm_ascend/`, retain the source
repository's committed history, and make the root Maintainer Skill Tree the
shared maintenance system for this and future imported projects.

## Start state

- Work branch: `work/import-drror-vllm-ascend-20260909`.
- Target base: `origin/main@0881de79ec6ad6623e277a38ab544704fa304b34`.
- Source: `research/qwen38-drrqr-correctness-20260908@7eec54c9caacad3f37f80a493e01171ec8f62003`.
- The source commit will remain reachable as a second parent of the import
  commit. Squashed or provenance-only import is not acceptable.
- Source `AGENTS.md` has one uncommitted goal-alignment rule. Its reusable
  behavior belongs in the root planning skill; DRRQR-only constraints remain
  project-local.
- Untracked `native/` and the two native gate tests are excluded because
  they are not part of the named source commit and have not been validated.
- This workstream owns no NPU, model, container, process, or port resources.

## Planned stages

1. Push this start checkpoint before changing shared skills or importing code.
2. Add a stable `projects/` contract and update the root maintainer routing.
3. Import the full DRRQR committed tree and history under its project directory.
4. Adapt paths and project-local instructions without changing DRRQR semantics.
5. Run root skill-tree validation, root tests, project tests, history checks,
   and a secrets/large-artifact review.
6. Push the ready workstream. A serialized integrator alone may update `main`.

## Resume point

Validate and push the start checkpoint. Do not begin protected or product edits
until the remote workstream checkpoint exists.
