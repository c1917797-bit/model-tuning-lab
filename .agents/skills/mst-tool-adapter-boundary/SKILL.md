---
name: mst-tool-adapter-boundary
description: Use when a repository uses Codex, OpenCode, Claude, Cursor, or other coding agents and needs thin adapters without duplicating the Maintainer Skill Tree.
---

# Tool Adapter Boundary

## Purpose

Keep tool-specific configuration useful but non-canonical. Tool adapters must point back to `AGENTS.md` and `.agents/skills/**` instead of duplicating governance rules.

## Core rule

`AGENTS.md` and `.agents/skills/**` are the source of truth. Tool-specific files are adapters.

## Examples of adapters

- `CLAUDE.md`
- `.opencode/opencode.json`
- `.opencode/agents/*.md`
- `.codex/config.toml`
- `.codex/agents/*.toml`
- `.cursor/rules/**`
- `.cursorrules`

## Workflow

1. Identify which tool-specific files exist in the repository.
2. For each adapter, check whether it duplicates rules from `AGENTS.md` or `.agents/skills/**`.
3. Replace duplication with references to `AGENTS.md` and `.agents/skills` where possible.
4. Keep only tool-specific execution settings in adapters:
   - model choice,
   - sandbox configuration,
   - approval behavior,
   - local permissions,
   - tool-specific agent role mapping.
5. If an adapter must contain instructions, add a comment pointing to the canonical source.
6. Verify adapters do not conflict with canonical sources.

## Verification

For each adapter file, check:

- It does not contain a full copy of `AGENTS.md` content.
- It does not define repository governance rules (commit policy, skill selection, etc.).
- It references `AGENTS.md` or `.agents/skills` for maintenance knowledge.
- Tool-specific settings (model, sandbox) are the only content.

Run:

```sh
# Check for duplication: if an adapter has more than 20 lines, flag it
for f in CLAUDE.md .cursorrules; do
  [ -f "$f" ] && [ "$(wc -l < "$f")" -gt 20 ] && echo "WARN: $f may duplicate canonical content"
done
```

## Recommended policy text

Include this in `AGENTS.md`:

```md
Tool-specific files are adapters. If an adapter conflicts with `AGENTS.md` or `.agents/skills.registry.yaml`, the repository bootstrap and registry win.
```

## When to introduce profiles

Do not rush a cross-tool profile system. Add `.agents/profiles/**` only after the repository has stable repeated roles such as:

- maintainer,
- reviewer,
- security reviewer,
- release manager,
- runtime skill author.

## Anti-patterns

Do not:

- duplicate governance rules in a tool adapter,
- make an adapter the canonical source for maintenance knowledge,
- embed skill-level workflows in a tool-specific config file,
- create tool-specific skills in `.agents/skills/` (skills are tool-agnostic),
- or update an adapter without checking whether `AGENTS.md` should be updated instead.
