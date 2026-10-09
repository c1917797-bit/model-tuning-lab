# Maintainer transformation suite real-task case

Date: 2026-10-09

## Task

Transform an isolated ordinary Python service whose legacy tool instructions
duplicated governance and whose tenant runtime Skill was misplaced under the
maintainer path. Preserve product behavior and produce a minimal, replayable
Maintainer Skill Tree.

The immutable input description is
`skill-fixtures/repository-transformation/input-snapshot.json`; the resulting
repository is under `skill-fixtures/repository-transformation/target`.

## Skills exercised

- `mst-repo-transformation`: inventoried the service and produced the complete
  maintainer scaffold without replacing the product.
- `mst-agentsmd-authoring`: produced a 23-line canonical bootstrap and an exact
  one-line `CLAUDE.md` adapter.
- `mst-skill-tree-design`: produced the six-Skill core plus one justified
  runtime-boundary Skill, with triggers, purposes, scopes, and unique paths.
- `mst-runtime-skill-boundary`: moved the tenant Skill to
  `runtime-skills/`, declared visibility and permissions, and added a
  deny-by-default publication policy.
- `mst-skill-governor`: recorded the reusable problem, classification,
  narrow change, registry update, and replayable verification.

## Replay

From the fixture target:

`bash scripts/validate-mst.sh`

The verifier checks the full fixture, compiles the retained Python product, and
executes its health path. Passing output reports seven maintainer Skills, a thin
adapter, a valid runtime boundary, a governance record, and product health
`ok`.

## Acceptance boundary

This is a bounded real transformation of an isolated single-package Python
service. It verifies the five named Skill behaviors for this repository shape.
It does not prove monorepo transformation, live tenant publication, CI-provider
integration, or every future registry schema.
