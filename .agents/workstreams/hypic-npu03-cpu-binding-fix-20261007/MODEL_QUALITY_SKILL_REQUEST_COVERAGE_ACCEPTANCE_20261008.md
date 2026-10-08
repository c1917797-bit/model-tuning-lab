# Main model-quality Skill: request-level HYPIC coverage case

Status: **partial evidence for current main**, not a full Skill pass or a
HYPIC quality verdict. Reviewed 2026-10-08 against
`origin/main=ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2`.
The main `ascend-model-quality-evaluation/SKILL.md` Git blob is
`303658f0a652ed392c875e58941c6b1d246552f7`; its quality-contract
reference blob is `a3d5ca9a98883ce651fc275f404a524b126f07c7`.

## Representative real task and expected behavior

The task is to decide whether a physical-NPU0–3, TP4, 2048-output-cap,
explicit-boundary HYPIC LongBench-v2 scored request took the actual
worker-hot path under concurrency 8. A defensible *each scored request*
claim requires a unique join from the scored API response ID to the
scheduler-internal ID, then to work-performing evidence from all four
expected workers. A boundary/admission event plus aggregate repair
counter proves only eligibility and overall activity. It cannot assign
work to an individual concurrent request.

The current-main Skill says treatment activation must be proven, but
neither its Skill file nor its referenced quality contract states this
per-request granularity rule or the concurrent warm-request
counterexample. It also lacks the branch's explicit incomplete-arm,
continuous-isolation, full-run feasibility and exact baseline-reuse
checks. This is an underspecified acceptance contract, not proof that
every use of main would make the wrong decision.

## Observed bounded behavior

The live cache10r9 original-protocol candidate remains in progress.
At the 17:48 UTC read-only checkpoint, 162 scored IDs were complete;
all had scheduler boundary evidence, but the existing plugin's worker
and complete-repair events had no request IDs. An independent
`audit_coverage` replay returned `UNVERIFIED` for 162/162 scored IDs
under the stricter each-request gate. A serialized first-sample
four-worker sentinel and aggregate positive repair counts remain valid
narrower observations. No terminal 127×3 quality, paired baseline,
performance or isolation verdict follows from this snapshot.

The branch-local quality-contract repair explicitly distinguishes
per-request worker proof from batch counters; the branch-local
`verify_hotpath_request_coverage.py` implements that narrow join and
six offline counterexample tests reject batch-only, missing-worker,
pre-repair and zero-skipped-token evidence. All 43 workstream tests and
the 29-Skill structural check passed. Those tests validate the repair's
decision boundary, not main-wide Skill effectiveness or NPU output
accuracy. The controller and mounted plugin remain unchanged while r9
runs.

## Acceptance boundary and next gate

Retain current-main `ascend-model-quality-evaluation` as
`partial-evidence`. The branch repair has not been integrated into
main or exercised on a terminal, request-ID-instrumented 127×3 pair.
After r9 terminates, hash and audit its raw rows, guard and exact
release; preserve any narrower result. Instrument worker request IDs
only after its service releases, then validate a fresh same-identity
candidate/control pair on actually idle physical NPU0–3. Replay the
per-request gate on that immutable evidence, test the Skill from the
resulting main blob, and only then reconsider long-term acceptance.
Any main Skill/reference blob, plugin source, model/service fingerprint,
dataset/evaluator, concurrency or generation-ruler change triggers
revalidation.
