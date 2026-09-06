# Evidence contract

## Required ledgers

Maintain one set per scientific question:

- `task.json`: current state, resource boundaries, next action;
- `experiment-<id>.json` or `.agents/experiments/<id>.yaml`: frozen identity,
  arms, rulers, and lifecycle;
- `evidence-<id>.json`: raw paths, hashes, run results, and failure evidence;
- `decision-<id>.json`: decision, reason, allowed and forbidden claims;
- `HANDOFF.md`: human recovery and verification guide;
- `knowledge-proposals.json`: candidate reusable lessons.

Never overwrite a rejected experiment with a corrected configuration. Link the
superseding experiment and keep both decisions.

## Performance unit

Require frozen input/shared/output lengths, request count, concurrency, warmups,
all measured requests successful, fixed output verified when used for
throughput/TPOT, raw per-request results, TTFT, TPOT, output throughput, total
duration, file SHA256, and three unique repetitions unless the contract states a
stronger requirement.

Exclude compile/capture warmup from steady-state aggregates.

## Quality unit

Require dataset and evaluator hashes, deterministic sampling contract, expected
request count, successful count and zero failures, one parseable JSON object per
sample, complete unique index set, canonical response hash per row, summary
correct count equal to raw-row recomputation, summary-to-details digest match,
and repeated baseline/treatment runs.

Do not substitute an unavailable dataset without explicit operator approval and
a new contract.

## Activation evidence

Define required events for the target mechanism. At minimum distinguish:
configuration enabled, planner/scheduler chose the mechanism,
materialization/cache/operator state became ready, worker/device hot path
executed, required repair/isolation/reclaim behavior completed, and missing or
failure events are empty.

Configuration flags or plugin import logs alone do not prove activation.

## Profiling evidence

When required, bind profiler tool/version and exit status, exact service and
workload hashes, baseline and candidate with identical stimulus, benchmark runs
without profiler capture contamination, exported file list/sizes/SHA256, target
regions and direction of improvement, and workload success independently from
algorithm acceptance.

A valid profile capture does not override a failed quality or semantic gate.

## Resource evidence

Record host devices and container-visible mapping, CPU set and ports, exact
container/process names, ownership preflight, final container/process state,
OOM state, and listener release.

Inspect only the declared lane. Neighboring devices may be protected even when
they are on the same host.

## Failure classification

Classify every rejected attempt as algorithm, capacity, environment, tooling,
evidence, operator pause, or scope change. Do not convert operational failure
into an algorithm conclusion. Do not hide it either: retain the evidence and
recovery.

## Resume contract

Before resume: poll the authoritative controller handle; if live, do not
restart; if terminal, verify exact owned resources; run controller self-test;
validate existing units and raw rows against the frozen contract; resume only
incomplete units/indexes; run the full independent audit after completion.

Resume commands must pin experiment ID, artifact root, topology, device map,
ports, budgets, and reference hashes. Place exact values in the workstream
handoff, not in the reusable skill.

## Decision template

State frozen scope, baseline and treatment, measured performance deltas and
dispersion, quality deltas and evidence-backed boundary, activation/profile
result, accepted and rejected evidence, current decision, allowed claims,
forbidden claims, and identity changes that require a fresh experiment.
