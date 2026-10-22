# Continuation clock reachability — source review

This review covers the stable 22-file continuation preparation package. It
establishes the declared source clock substitutions and current test closure.
It does not freeze source, create a review approval, run an owner, execute an
NPU request, or establish numerical, performance, or accuracy success.

The original hard reporting deadline remains 2026-10-22 12:38:41 UTC. The new
explicit continuation uses a separate internal batch from 12:00:55 to 18:00:55
UTC. Its internal cap is 21600 seconds. Phase 3600 seconds, cleanup 180 seconds,
and complete preparation/admission allowance 3780 seconds are unchanged.

## Clock coverage

MAIN supplied a read-only exact-reference scan of all 239 top-level Python
files in the completed ON-v2 source. It found nine files containing the old
batch clock patterns. This local review reopened all nine complete files,
verified every SHA/byte count against the scan index and source identities,
and checked the recorded matching lines. It did not locally reopen all 239
whole bodies. A separate exact-source name scan covers three constructor and
renderer names.

| Group | Count | Treatment |
|---|---:|---|
| Original runtime clock files | 6 | The builder and original validator select the same fixed qualified ancestor and apply the unchanged original `clock` function with the new authority. |
| Current software coordinator | 1 | Only its three cutoff literals change; its original full-file pin and complete inverse remain required. |
| Original runtime validator | 1 | Exactly one authority predicate changes. Existing validator logic, numerical checks, test enumeration and dependency contract remain exact. |
| Historical `prepare_bound_short.py` | 1 | Retained unchanged. The narrow name scan finds its name only in its own source list; the new builder does not invoke it. |

The original `prepare_short_gate` and `performance_binding_delta` modules stay
as exact pure source renderers. Their historical ancestor constants remain
necessary for original-text matching. They are not global targets for clock
replacement. The new current coordinator and validator receive separate
whole-file-checked transformations. Both manifest software scope dictionaries
allow only the `fixed_cutoff` substitution.

The original clock renderer for all six files is statically unchanged, with
the same fixed ancestor selection. This is not an actual generated-six-file
receipt. All six ancestor bodies were not available locally, and no new source
was generated here. MAIN must still run the reviewed builder and the unchanged
original runtime comparisons plus the independent v4 source auditor. The name
scan is a bounded check of the pinned source closure; it is not a universal
claim about arbitrary dynamic Python imports.

## Original current twenty controls

The three exact test sources were fully reopened and checked against both the
239-source scan identities and their supplied test Refs:

- `test_short_state_digest.py`: 10 tests.
- `test_digest_reader.py`: 6 tests.
- `test_short_dependency_contract.py`: 4 tests.

None contains a hardcoded old batch time or cutoff expectation. No current
same-image test was changed. The original rejection controls remain intact.
There was no local attempt to stand in for the mandatory fresh same-image
20-test execution on the actual frozen source.

## Preparation-control readset correction

The integration test actually reads four immutable ON-v2 inputs. The runner
now requires their exact complete Refs in the preparation descriptor before
creating any output: `short_binding_delta.py`, `performance_validate.py`,
`performance_software_stages.py` and `SHORT_AUTHORITY.json`. They then join the
existing complete before/after readset. Their exact originals were locally
reopened and all four pins verified. The correction changes the runner's
source contract, not test results, phase budgets, model code, or tolerances.

The previous direct local eight-integration-test PASS remains source-only
control evidence. It is not a host-control receipt, same-image receipt, or
NPU qualification. The new host four-stage controls must actually execute
with the complete pinned descriptor.

## Remaining concrete gates

The stable package is ready for independent source review. Deployment hash
readback, genuine host controls, an honest MAIN review, a single fresh freeze,
source audit, real same-image controls and current physical-device/resource
admission remain mandatory before the bounded diagnostic. Final project
acceptance remains the user's original true-NPU correctness, paired full-model
performance and task-accuracy protocol.

The accompanying JSON records exact source and scan Refs, every old-clock
match, all twenty test names, the original observed local test receipt class,
and the explicit limits above.
