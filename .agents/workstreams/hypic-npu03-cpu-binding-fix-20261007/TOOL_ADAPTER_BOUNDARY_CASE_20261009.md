# Tool-adapter boundary: bounded real-repository audit

On 2026-10-09 UTC, the actual HYPIC task clone was checked against exact
`origin/main` Skill `mst-tool-adapter-boundary` and the repository bootstrap.
This was an inspection task, not a runtime model test or an adapter rewrite.

- The tracked adapter inventory is only `CLAUDE.md`; no tracked `.codex/`,
  `.opencode/`, `.cursor/` or `.cursorrules` adapter exists.
- `CLAUDE.md` is exactly the one-line `@AGENTS.md` shim on both this branch and
  `origin/main` (SHA256 `336cc4fbf19beaada7ccf9986414fa91851a8d7a07dfb3ccbe800a69eed0ab49`).
- Root `AGENTS.md` contains the maintainer role and pointers to the registry
  and canonical Skill tree, and explicitly says tool-specific files are
  adapters (SHA256 `a904211035ad5498b5392a38bfaf4c3dba28a0d6b024f63b5fb2476f8b29f9e8`).
- The one-line adapter carries no independent commit, skill-selection,
  sandbox or device policy and therefore does not duplicate governance.
- Re-run `python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_tool_adapter_boundary_case.py`
  when main, AGENTS.md, or any tracked adapter changes.

This is partial evidence for one existing thin adapter. It does not verify
behavior in Claude, a conflict-resolution scenario, or future Codex/Cursor/
OpenCode adapters. No Skill-wide pass or HYPIC result follows.
