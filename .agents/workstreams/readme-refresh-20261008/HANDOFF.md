# README refresh handoff

## State

- Execution: in-progress; integration: not-ready.
- Original base: `f1f37a39bd86f7db5fd3ee3dea358ae6868275c6` (`origin/main`).
- Named branch: `work/readme-refresh-20261008`; target: `main`.
- Target host: verified `chicaihong01/mb`; canonical repository is on chicaihong01.
- Scope: README plus this task's records; global HANDOFF changes only during integration.
- Existing eight worktrees are preserved. The maintainer approved one temporary ninth tree.
- No NPU or runtime resources are leased or changed.

## Reviewed input

The README draft describes the actual 29 registered Skills, distinguishes instructions and templates from future automation, and qualifies historical HYPIC mean results by their original configuration. It does not claim current Qwen3.5 P95 acceptance or universal lossless performance.

Draft SHA256: `4dffc4b1ee436edb5c782162308ac384ab68b6c45f4d7e2bd995351f9891c880`.

## Resume

Remote start checkpoint: `21ac496b89baaa84e37073bc0c42d8d341ebcf69` (pushed and clean). Reviewed README applied. Preliminary audits passed: validate-mst (29 Skills), 31 relative links, exact registered names, JSON state, frozen hashes, formatting and git diff --check. The read-only audit script will be rerun on the staged content before commit. Then commit and push the work branch. A single integrator merges only its fetched remote ref, records exact source and target parent, validates the final tree, then pushes main. Reclaim only this clean merged temporary worktree and its local branch; retain the remote branch.
