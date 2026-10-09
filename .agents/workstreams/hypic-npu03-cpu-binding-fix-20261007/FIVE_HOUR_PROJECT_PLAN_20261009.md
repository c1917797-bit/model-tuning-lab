# HYPIC verification — five-hour project plan

Window: 2026-10-09 12:21:24–17:21:24 UTC
Workstream: `work/hypic-npu03-cpu-binding-fix-20261007`
Target: chicaihong01/ma, physical NPU0–3 only.

## Objective and completion boundary

Close the remaining frozen HYPIC evidence, map the observed outcomes to their
maintainer Skills, and leave a reproducible handoff before the deadline. This
is an evidence-completion goal, not permission to weaken the frozen protocol.
HYPIC adoption is not the expected conclusion: the valid r13 quality result is
no-cache 230/381 versus HYPIC 219/381 (−2.887 percentage points,
`REJECT_OR_QUALIFY`), and strict four-worker hot coverage is 368/381.
No later speed result can reverse those quality findings.

## Frozen facts and current state

- Quality: r13 is complete and independently audited at 127 samples × 3 runs
  per arm, 381 scored responses per arm. Preserve its denominator and verdict.
- Performance: five of the six matched phases have valid independent audits.
  Only `hypic-only/repeat3` remains unmeasured.
- Retries 15–16 are environmental pre-health isolation failures: the same
  external `cannbench_ds` container entered physical NPU2 (retry15 PID 865188;
  retry16 PID 1032336). Both attempts produced zero scored requests and no
  performance metrics; only each attempt's exact owned service was removed.
  The external workload was untouched. Their unique roots are immutable and
  are not HYPIC results.
- Retry19 terminally failed before health/scoring when the continuous guard
  captured foreign PID 1731309 on physical NPU2 (46 samples, zero errors and
  zero scored requests); only its exact owned container was removed. Its
  immutable receipts pass `verify_retry19_environmental_failure.py`.
- Retry20 terminally failed before service health/scoring: its continuous guard
  captured foreign PID 1890601 on physical NPU3 after 36 samples with zero
  probe errors. It yielded zero scored requests and metrics; only its exact
  owned container was removed. Immutable receipts replay-check with
  `verify_retry20_environmental_failure.py`.
- At the 14:38 UTC follow-up, external PIDs 1890601 and 1920829 still occupied
  NPU3 under the running `cannbench_ds` container; port 8223 was free. Wait
  until a fresh direct-route snapshot proves physical NPU0–3 and 8223 idle
  before any distinct, preregistered retry. Never touch the external task.
- The original repeat3 root and retry1–14 roots already exist and are immutable.
  Retry15 is registered under a new root; no controller was live at 12:42 UTC.
- Main Skill inventory is 29: 23 case records (2 verified, 21 partial), 6
  missing. A case record is not itself behavioral acceptance.

## Milestones

| ID | Due (UTC) | Status | Work and acceptance |
|---|---:|---|---|
| M0 | 12:45 | Complete | Add retry14 receipts to the Paper-to-Ascend reproduction case; its focused verifier passes. |
| M1 | 13:30 | Complete | Map r13 quality and retry14 performance/host outcomes to benchmark-evidence, inference-tuning-loop, and host-maintenance cases. Verify immutable hashes and run repository regressions; keep environmental failure separate from technique verdict. |
| M2 | 15:00 | Waiting for an actually idle lane; retries15–20 environmental | Retry20 is independently replay-verified as pre-health foreign NPU3 interference (36 samples, zero errors/scored requests, exact cleanup). Monitor external use; launch another unique root only after a fresh physical NPU0–3/8223 idle proof. Never stop or modify foreign work. |
| M3 | 16:00 | Pending | Independently audit all six phase roots for identity, request coverage, four-worker proof, isolation, cleanup, and comparable metrics. Report performance only if all required evidence is valid; report quality independently. |
| M4 | 16:50 | Pending | Run the full 29-Skill registry/case audit and repository regression suite. Fill safely runnable gaps; preserve explicit partial/missing status for anything not behaviorally tested. |
| M5 | 17:21:24 | Pending | Refresh task state and handoff, record decisions/blockers, run final checks, and create a coherent local checkpoint. Push only if existing authorization and working authentication allow it; then verify the remote ref. |

## Execution sequence and gates

1. **Orient:** read repository instructions, current handoff, task state, frozen
   protocol, and immutable audit reports. Resolve `chicaihong01/ma` anew via
   AWMCP and prove that commands target that peer directly.
2. **Preflight:** immediately before any device launch, inspect physical NPU0–3
   processes and port 8223. Container mapping alone is not occupancy evidence.
   NPU4–7 are out of scope. Never stop or modify foreign work.
3. **Preregister:** only if the live lane and port are free, create a unique
   attempt root and freeze source/image/model/workload/commands before launch.
   No old attempt root may be reused or overwritten.
4. **Run the missing phase only:** keep the six-phase ordering and treatment
   unchanged; continuously sample physical process ownership. A foreign PID or
   probe error before health/scoring classifies the attempt as environmental,
   yields zero benchmark rows, and cannot be called a HYPIC performance result.
   Clean up only resources proven to belong to this attempt.
5. **Audit and decide:** verify immutable receipts independently before
   calculating paired metrics. Keep mechanism activation, deployed effect,
   quality, performance, isolation, and adoption as separate conclusions.
6. **Learn and hand off:** update the exact related Skill cases and regression
   checks. Do not silently promote branch-local learning to main.

Monitor opportunistically: no coordination prerequisite and no arbitrary idle-duration threshold. Launch only after a fresh direct-target preflight shows no physical NPU0–3 processes and port 8223 free. The controller's preflight and continuous physical-PID/cgroup guard handle the race. If external work enters, invalidate the attempt, preserve its root, release only exact owned resources, and wait for the next idle observation; never stop or alter foreign work.

## Decision states

- **Measured/valid:** all frozen sample, identity, activation, isolation,
  cleanup, and audit requirements pass; report the measured result.
- **Environmental/no result:** external work or probe failure prevents health
  or scoring; retain the attempt and exact cleanup, report zero scored rows,
  and do not infer technique success or failure.
- **Inconclusive/partial:** evidence exists but misses a declared coverage or
  audit requirement; preserve its exact boundary and remaining evidence.
- **Not run:** physical lane or port remains unavailable by the milestone
  deadline; state the live blocker and keep the phase unmeasured.

## Final deliverables

- Immutable six-phase evidence index and final HYPIC report with independent
  quality/performance decisions.
- Updated replayable Skill cases and passing regression outputs.
- Updated handoff, active milestone state, and clean diff check.
- Honest branch/remote state; no claim of commit, push, or main integration
  until independently verified.
