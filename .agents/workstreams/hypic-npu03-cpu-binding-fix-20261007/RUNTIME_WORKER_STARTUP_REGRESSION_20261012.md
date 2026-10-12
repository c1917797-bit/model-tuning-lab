# Runtime delivery: worker-local startup failure is not a successful control

Date: 2026-10-12 UTC. Scope: copied generic monkeypatch template, CPU only.
No HYPIC source, frozen package copy, image, old raw root or live service changed.

## Demonstrated defect and repair

The wrapper runs a short preflight Python process. That process can activate
successfully while a later service/worker interpreter encounters an import or
activation error. CPython can print a sitecustomize error and continue into the
service body with exit0. A preflight marker therefore cannot establish worker
activation or fail-closed startup.

New regression exec00bb reproduced this: preflight emitted ACTIVE, actual
service import raised RuntimeError, yet the service returned0 instead of78.
The test failed as intended (1 failure among9); disabled control succeeded.
This is a synthetic worker-local failure injected into a disposable template
copy, not a reproduction of the HYPIC numerical/quality regression.

The default-disabled sitecustomize now catches enabled import/activation
exceptions, emits a bounded FAILED event (PID and error type, no exception
payload or environment) and exits that interpreter with78. ACTIVE is emitted
only after successful activation. Disabled mode never calls the broken patch.
Manifest loader hash is updated. Existing frozen observer/HYPIC packages are
not silently overwritten; their historical source and evidence remain valid.

exec00bd: all9 tests PASS, including actual-service failure and disabled
control, plus existing template/hash/traversal/same-wrapper checks.
The loader fix supplements, not replaces, per-worker activation and real device
rollback requirements. It does not enforce every possible framework/ABI
failure or prove source/package bytes alone control live execution.

## Reused device evidence, no rerun

exec00bf replays the existing bounded delivery case: r12 52/57 hot proofs and
279 guards, r13 full same-source quality/performance, source binds, static
repairs; all retained verdicts unchanged. Pinned main still lacks its documented
validator and forces the template switch enabled; branch repair remains local.

r25retry2 audit hash was freshly verified in exec00ba:
01d49278c92c931ccaff5a6d204e750d20010953e32daa64a5c7e980c3bd83c5.
It proves the bounded observer lifecycle,117 clean guards and exact release.
It is not the actual HYPIC technique's full disable/uninstall/restart delivery.

## Obligation correction

Exact-main Skill/reference explicitly allow rejected, failed, partial-component
and inconclusive terminal outcomes. Fixing HYPIC quality until adoption passes
is not a universal prerequisite to evaluating this Skill. The old case's
next_gate wrongly coupled all further Skill validation to algorithm repair.

The real remaining HYPIC delivery gaps are: actual hash-bound technique package,
same-wrapper enabled/disabled process evidence for that identity, and executed
disable/uninstall/restart rollback. Full success still needs the matched
performance/quality/attribution gates. Archive a valid negative decision instead
of relabelling it accepted; do not run forbidden later gates after failure.

The existing r19 quality-first restriction and pending choice about descriptive
same-source performance remain unchanged. No new device run is authorized here.
A retrospective manifest cannot manufacture old runtime proof, and observer
success cannot substitute for technique delivery.

## Experience ingestion and boundaries

Practice source: HYPIC Skill acceptance; exact-main Skill blob
5ac9f8b07d8e092dcba7e1b0cfd5423469534666; reference
302cf8cde20e7fda93b2972bbf1e5bab9fd81dde.
Classification:5 eval/verification case with supporting existing-template fix.
Trigger: a template loaded through sitecustomize in multiple interpreters.
Different action: test a failure in the actual service interpreter after
successful preflight; require nonzero exit and absence of service execution.
Destination: existing template loader, manifest and package regression suite.
Verification: red/green subprocess tests, package hashes, Skill Creator
quick validation (00be), repo structure and case provenance.

The copied-template asset is narrowly repaired per skill-creator; no universal
new paper gate, fresh Skill or diagnostic framework is introduced.
Counts remain8 bounded verified/21 partial. runtime-monkeypatch-delivery stays
partial. No causal claim about HYPIC, whole-main pass or remote sync follows.
