# Transformation verification: real missed-status defect and regression

Exact-main mst-transformation-verification blob:
549bc84019471e696af0dac5eb90f1664e19c2d8 at
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2.
Branch Skill text is identical. The main instruction was correct; the older
fixture's executable checker did not enforce it.

## Failure and correction

The existing single-package Python transformation had7 registry entries with
status active. Main permits stable/experimental/deprecated/retired. The old
checker only required a nonempty status and therefore returned a false-positive
structural pass. The old report and Git version remain historical evidence;
they are not proof that this status rule was previously exercised.

New verify_registry_contract rejects the unchanged old fixture at the first
active status (exec009d exit1). All7 fixture states are now experimental, not
stable or falsely production-ready. Full fixture scripts/validate-mst.sh then
passed (exec009e), preserving23-line AGENTS,7 Skills, exact thin adapter,
runtime separation/governance record and product health ok.

The checker now validates every discovered component registry, legal statuses,
unique IDs/paths, declared-versus-present directories, frontmatter identity,
purpose/workflow, trigger presence and narrower component selection precedence.
It rejects maintainer/unknown publication entries in the actual runtime policy.
The full product fixture stays explicitly single-package; Cargo dependency
hierarchy and a live tenant publisher were not tested or claimed.

## Negative regression

test_mst_transformation_registry.py passed12 tests (exec00a1):
valid root; illegal active status; duplicate ID; empty trigger; orphan directory;
missing SKILL.md; maintainer path entering runtime tree; mismatched frontmatter;
maintainer publication; missing component precedence; invalid status hidden in
a component registry; valid nested registry traversal.
All mutations occur in disposable copies under/cache/cch; no original raw
experiment root, runtime service or NPU is touched.

The broad original case on the29-Skill main tree remains partial: its14 generic
entries without explicit trigger/scope and its selection/design review were
not repaired by changing this separate fixture. This supplement establishes
real checker behavior and fixes a false pass; it does not substitute a7-Skill
fixture for the requested whole-main acceptance.

## Files and manual semantic review

Checked fixture files: AGENTS.md, CLAUDE.md, root registry and seven SKILL.md,
runtime registry/Skill/publication policy, governance record, validation entry
and retained src/app.py. Reusable experience is in executable checks/tests,
not just prose.

The registry purposes/scopes distinguish onboarding, transformation, bootstrap,
tree design, verification, governance and runtime boundary. Missing trigger
text is rejected mechanically. Natural-language ambiguity remains a human
selection concern, not proven by merely checking nonempty strings.
Nested-registry tests prove discovery/precedence/status traversal only, not
all monorepo dependency semantics.

Replay:
- From this workstream: python3 -B -m unittest test_mst_transformation_registry
- From skill-fixtures/repository-transformation/target:
  bash scripts/validate-mst.sh
- From task repo: python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_skill_cases.py

Keep the exact-main behavior, fixture fix and branch integration status separate.
No new HYPIC measurement, no29-Skill full pass and no remote/main sync follow.
