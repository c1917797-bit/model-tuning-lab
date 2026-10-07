# Maintainer/adapter/runtime boundary audit (2026-10-07)

Scope: the independent HYPIC work branch at `9ef30f3`, not external product deployments or the dirty canonical checkout. This is a repository-source audit, not a runtime publication test.

Methods and direct evidence:

- Read `mst-tool-adapter-boundary`, `mst-runtime-skill-boundary` and `mst-transformation-verification` in full, then read root `AGENTS.md`, `CLAUDE.md`, `.gitignore`, and `scripts/validate-mst.sh`.
- `git ls-files` returned 220 tracked paths. Its only tool-specific adapter is `CLAUDE.md`, whose entire content is `@AGENTS.md`. Root `AGENTS.md` names `.agents/skills.registry.yaml` and `.agents/skills/**/SKILL.md` as canonical maintainer sources and explicitly calls tool-specific files adapters.
- `find . -maxdepth 2 -type d` showed no `runtime-skills/`, `.codex/`, `.cursor/`, or `.opencode/` directory. No tracked path begins with `runtime-skills/` or a nested product `.agents/` registry. `.gitignore` does not hide a runtime-skills tree.
- `bash scripts/validate-mst.sh` passed with 29 Skills. This script checks basic structure/frontmatter and delegates to available secondary checks; it cannot by itself prove behavioral correctness or external publication safety.

Scoped decision: `mst-tool-adapter-boundary` has a directly exercised **V** result for the one present adapter. `mst-runtime-skill-boundary` is **N** (not applicable to this repository as currently laid out): no runtime/product Skill exists here to separate or publish. An external runtime deployment, if later introduced, requires a new audit; absence in this Git tree is not proof about external systems. `mst-transformation-verification` remains **P** because structural and boundary checks pass but the full HYPIC behavior/quality gate and broader transformation review remain open.
