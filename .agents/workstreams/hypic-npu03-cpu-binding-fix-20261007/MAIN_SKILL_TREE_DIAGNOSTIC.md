# Main Skill-tree design diagnostic (2026-10-08)

Scope: read-only inspection of all 29 `SKILL.md` blobs and the registry at
`origin/main` commit `f1f37a39bd86f7db5fd3ee3dea358ae6868275c6`,
using the stated checks in `mst-skill-tree-design` and
`mst-transformation-verification`. This is a design/structure result, **not**
a behavioral acceptance of all 29 Skills.

## Pass/fail summary

- PASS: `AGENTS.md` declares the maintainer role and canonical
  registry/Skill paths. `CLAUDE.md` is only `@AGENTS.md`, not a second
  policy. The 29 registry IDs, paths, directories and frontmatter names
  match; no orphan or missing Skill directory. Registered status values are
  stable/experimental. No exact duplicate trigger string was found.
- PASS: `bash scripts/validate-mst.sh` reports a structurally valid
  29-Skill tree. This validator does not currently enforce the design limits
  below, so its green result is not a complete design or behavior verdict.
- FAIL against the design Skill's stated `SKILL.md <= 120 lines` rule:
  8 main files exceed it: `chicaihong01-host-maintenance` 167,
  `ascend-cannbot-profiler` 143, `ascend-performance-optimization` 126,
  `paper-to-ascend-reproduction` 195, `paper-to-ascend` 191,
  `mst-git-checkpoint-policy` 128, `mst-loop-engineering-framework` 142,
  and `mst-parallel-workstreams` 188. The current experimental branch has
  10 over-limit files because some branch lessons lengthened Skills; do not
  conflate that count with pinned main.
- FAIL against the design Skill's registry metadata rule: 14 generic
  `mst-*` entries omit explicit `triggers` and `scope`. Their
  frontmatter descriptions may still guide selection, but the registry
  lacks the promised selection data.
- REVIEW, not automatic failure: exact headings `## Purpose`,
  `## Workflow`, or `## Verification` are absent in some files
  (1, 9, and 12 respectively). Several may express equivalent content
  under alternate headings; semantic inspection is needed before editing.

## Boundary and recommended repair

No runtime/product Skill tree was identified as a canonical maintainer
source in this checkout; the adapter remains one line. This audit did not
exercise a runtime product deployment or sub-repository registry, so that
boundary is not behaviorally verified.

Do not shorten eight large Skills by deleting safety gates. First map each
oversized file's core trigger/workflow versus reusable references, then move
detail into reference files while preserving exact meaning and reading
requirements. Add narrow trigger/scope metadata for the 14 generic entries,
test ambiguous selection cases, and extend structural validation to catch
future drift. Use an independent fixture or real fresh-clone task for
behavioral acceptance. Until repaired and rechecked, keep
`mst-skill-tree-design` and `mst-transformation-verification` partial;
do not treat a passing `validate-mst.sh` as proof of their full contracts.
