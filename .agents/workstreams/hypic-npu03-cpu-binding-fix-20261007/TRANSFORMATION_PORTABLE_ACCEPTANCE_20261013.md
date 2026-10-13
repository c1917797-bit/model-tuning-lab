# Transformation verification — portable delivery acceptance, 2026-10-13

## Verdict and exact instruction source

Bounded PASS for mst-transformation-verification on the retained single-package
Python service transformation. The instruction itself is unchanged from main
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2, blob
549bc84019471e696af0dac5eb90f1664e19c2d8; branch/main blob equality was checked
through the freshly resolved direct chicaihong01/mc connection.

This does NOT mean all29 Skills work. It means the exact-main verification
Skill was applied to a real transformation output, detected defects, guided
their correction and verified a bounded delivered tree. Its effectiveness
does not depend on a positive HYPIC accuracy result or a GitHub push: neither
is a requirement in this Skill's Checks/Output/Verification sections.

## Newly demonstrated failure and repair

The target's validate-mst.sh invoked ../../../verify_mst_transformation_suite.py.
A target-only copy had no such parent helper. Three new portable-delivery
tests failed in mc exec-0000000000000059. In particular, a valid target could
not run, and malformed targets failed before reaching their intended checks.

The complete validator now lives under the target's scripts directory.
The entrypoint resolves its own directory, not the caller's working directory.
The parent verifier is a compatibility/history adapter importing that one
implementation; it separately retains the input-snapshot history check.
Python syntax validation no longer writes __pycache__ into the delivered tree.
No Skill instructions or product source changed.

mc exec-000000000000005b exit0:
- Three standalone-copy tests pass: valid tree, rejected illegal status,
  rejected adapter duplication. The copy contains no parent helper/snapshot.
- All12 existing registry/runtime/nested-registry controls still pass.
- Parent historical replay and target-local entrypoint both pass:
  seven Skills,23-line AGENTS,thin adapter,runtime boundary,product health ok.

Both failure and successful execution records are retained in
TRANSFORMATION_PORTABILITY_RECEIPTS_20261013.json. Dependencies remain explicit:
bash,Python3.10+ and PyYAML. No dependency installation or bare-OS readiness claim.

## Requirement-by-requirement review

| Exact-main requirement | Inspected evidence and result |
|---|---|
| Bootstrap exists,maintainer role,canonical pointers,short/no duplicated procedures | Read all23 AGENTS lines; role and both pointers present; detailed procedures remain in Skills; checker enforces pointers and size. |
| Registry paths,entry files,unique IDs,legal statuses | Inspected root registry and all7 entries/files; existing negative controls reject absent files,orphans,duplicates and illegal active status. |
| Specific selection triggers | Manually compared all7 registry purposes/triggers/scopes with all7 SKILL.md descriptions/workflows; narrow task/path selection examples below. Nonempty strings alone are not treated as semantic proof. |
| Frontmatter,purpose,workflow,narrow scope,verification expectations | Read all7 complete Skill files; each names one maintenance concern and concrete workflow. Relevant paths end in validation/replay or recording unresolved assumptions. |
| Component registries and dependency hierarchy | Delivered service has no components or Cargo.toml; therefore no live crate hierarchy obligation applies. Existing copied nested-registry tests cover discovery/precedence/status only,not Cargo semantics. |
| Adapter authority | Exact one-line CLAUDE.md delegates to AGENTS; new standalone negative control rejects added override text. |
| Runtime separation and publication | Runtime Skill is outside .agents; explicit tenant visibility/catalog.read permission; publication denies by default; existing full-runner counterexample rejects a maintainer publication entry. This is static policy verification,not a live tenant service. |
| Durable experience | Governance JSON plus executable checks and regression tests are retained; this report is not the sole ingestion artifact. |
| Output and final validator | This report states verdict,checked files,missing files,boundary risks and fixes; target-local scripts/validate-mst.sh passes. |

Checked files: AGENTS.md,CLAUDE.md,root skills.registry.yaml,all7 maintainer
SKILL.md files,runtime registry/customer-helper Skill/publication policy,
governance-record.json,src/app.py and both delivered validation scripts.
Missing required files after repair: none within this single-package task.

## Manual selection review

These are semantic review examples,not an assertion of an automated router:
- First task in an unfamiliar service: onboarding; not a whole transformation.
- Edit AGENTS.md: agentsmd-authoring; transformation-verification checks result.
- Redesign registry/path layout: skill-tree-design; governor handles lifecycle.
- Audit an already transformed tree (this task): transformation-verification.
- Add/move/retire a maintainer Skill: governor,plus tree design if structure changes.
- Change tenant permissions/publication: runtime-skill-boundary,not tenant guidance
  overriding maintainers.
- Convert legacy instructions into the maintainer system: repo-transformation.

Some tasks intentionally select more than one narrow Skill; this is not evidence
of ambiguous all-purpose routing. No universal natural-language routing claim.

## Scope correction and remaining risks

The old case was an audit of the whole29-Skill input tree. Its14 generic routing
gaps were real; their branch repairs and main integration remain separate work.
The later seven-Skill transformation had already demonstrated behavior, but its
case boundary still said no transformed repository had been verified. This
review completes the portable-delivery gap and explicitly records a new bounded
task acceptance; it does not rewrite the old observation as historically passing.

Promote this one exact-main Skill to bounded verified: totals11 verified/18
partial. No monorepo/Cargo/live publisher acceptance,all-Skill success,NPU work,
HYPIC quality change,main integration or remote synchronization follows.
Recommended next work: remaining main Skill obligations and authorized integration;
do not repeat these15 tests unless relevant code or evidence changes.

## Replay

From the task repository:

```bash
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_transformation_portability.py
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_mst_transformation_registry.py
bash .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/skill-fixtures/repository-transformation/target/scripts/validate-mst.sh
```
