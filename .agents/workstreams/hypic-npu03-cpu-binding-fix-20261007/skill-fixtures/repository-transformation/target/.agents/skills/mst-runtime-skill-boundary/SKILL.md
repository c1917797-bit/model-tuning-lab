---
name: mst-runtime-skill-boundary
description: Use when tenant runtime Skills or publication policy changes.
---

# Runtime Skill Boundary

## Purpose

Keep tenant product Skills separate from repository-maintainer instructions.

## Workflow

1. Keep runtime Skills outside `.agents/skills`.
2. Declare runtime visibility and permissions.
3. Keep runtime Skills free of maintainer-governance authority.
4. Validate the runtime registry and publication policy.
