# Tool-adapter Skill: requirement-by-requirement bounded acceptance

Date: 2026-10-12 UTC. Exact-main Skill at
ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2, blob
bf3b70bccafd5d264ed6ab767022eb96d450a4e6. Its branch text is unchanged.
This reviews the original actual-repository adapter task, not a replacement
task with fewer adapters. It does not claim HYPIC or whole-main acceptance.

## Actual scope and six workflow obligations

| Main workflow | Actual evidence and disposition |
| --- | --- |
| Identify existing tool files | Fresh exec00b2 found only root CLAUDE.md across CLAUDE/.cursorrules/.codex/.opencode/.cursor; exec00b4 reconciled tracked and filesystem inventories, including untracked files. |
| Check duplication per adapter | CLAUDE.md is exactly @AGENTS.md plus newline, matching main; it contains no copied workflow or independent policy. |
| Replace duplication where possible | No duplication exists in this actual task, so no destructive rewrite is required. This conditional step is not an instruction to invent a migration. |
| Keep only tool-specific settings | No independent model, sandbox, permission, commit or selection settings exist in this reference-only adapter. |
| Canonical-source pointer for instructions | The sole line directly names AGENTS.md; the canonical bootstrap names the Skill registry/tree. |
| Verify no canonical conflict | The sole reference cannot override governance; canonical bootstrap explicitly labels tool-specific files as adapters. Real-file replay and negative controls pass. |

The existing historical report remains unchanged. Its exclusions of live
Claude interpretation, future Codex/Cursor/OpenCode files, and adapter migration
are still true, but are not unconditional requirements of this Skill for an
audit of an already-thin single-adapter repository. The historical broad
partial label was conservative; the scoped case is now bounded verified.
No universal tool interoperability or instruction-following guarantee follows.

## Concrete checker improvement and replay

The previous verifier enumerated tracked adapters only. New adapter_inventory
also examines untracked files in the named tool directories and rejects
symlinked adapters for manual review rather than following external paths.
A new adapter causes explicit scope drift, not a guessed pass or a claim that
every new adapter is intrinsically invalid.

exec00b4: actual repository audit exit0 and8 tests pass:
valid actual-bootstrap/reference; full canonical copy; independent governance
override; untracked config; missing canonical pointer; main-shim drift;
missing adapter; symlink requiring review. Tests use disposable temporary
files, not a running Claude agent, repository policy rewrite or NPU workload.

- CLAUDE SHA256: 336cc4fbf19beaada7ccf9986414fa91851a8d7a07dfb3ccbe800a69eed0ab49
- AGENTS SHA256: a904211035ad5498b5392a38bfaf4c3dba28a0d6b024f63b5fb2476f8b29f9e8
- verifier SHA256: 699211a0b69c30f6327fb2937f10fecd12ed1b6037e3a268252ef81a0b1faad1
- tests SHA256: 577bd127a60115349e5006ce7b99fb86d084e8be5f7feadb85e8dd84a848b934

Replay from this workstream:
python3 -B verify_tool_adapter_boundary_case.py
python3 -B -m unittest test_tool_adapter_boundary_case

## Reusable lesson and remaining boundaries

Practice source: HYPIC maintainer acceptance campaign, original Oct9
tool-adapter audit plus Oct12 real-filesystem replay. Selected Skills:
mst-tool-adapter-boundary, mst-transformation-verification and
mst-experience-ingestion.

Classification destination5: eval/verification case. Trigger: reviewing a
thin-adapter repository or adding an adapter. Different future action: inventory
actual files as well as Git-tracked paths, and distinguish conditional migration
from mandatory audit obligations; do not demand every possible tool's live
execution merely to accept this bounded repository audit. Destination: existing
verifier, negative tests and this case's obligation table. Verification: actual
file replay, negative controls, case hashes and whole-tree validation.

Registry trigger/scope metadata was also freshly checked in exec00b1: the
14 generic entries remain incomplete in pinned main, but are already complete
in this workstream. No duplicate metadata repair was made. Remote integration
is still pending; origin authentication is not assumed repaired.

Counts after this scoped acceptance:8 bounded verified and21 partial,29 cases.
All29 functional acceptance, HYPIC same-source performance, unresolved quality
cause and remote/main integration remain incomplete. Original scientific
results and immutable experiment roots are unchanged.
