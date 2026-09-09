# Qwen3.5 standalone patch import handoff

## Status

- Execution: completed.
- Integration: ready for serialized review; not merged to the primary branch.
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

The deliberate import merge is
`d62a79ca208370604cb91a697f9f2d7c164d5d65`. Its first parent is the pushed
start checkpoint `f6f7032ee6c9a60b31d01fb3fcbc2d71c4dce747`; its second parent is the
exact source HEAD `c61f5f984e13e2ca37fd410783b7e97f960a57f3`. All 3 source commits are
reachable. The 10 tracked source files match byte-for-byte; only the documented
project `AGENTS.md` and `PROJECT.md` additions differ from the prefixed
source tree.

## Next actions

1. Push the validated documentation checkpoint and verify local/remote equality.
2. Open or review the work branch for serialized integration; do not bypass the
   current DRRQR import dependency by targeting stale `origin/main`.
3. Later adapt the standalone README deployment path and optional root test
   routing. Keep these distinct from performance/quality acceptance.
4. Continue the original Qwen3.5 optimization research separately; this import
   does not satisfy the TTFT, TPOT, or all-357 quality gates.
