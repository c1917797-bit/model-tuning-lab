# Evidence contract

## Required ledgers

Maintain one set per scientific question:

- `task.json`: current state, resource boundaries, next action;
- `experiment-<id>.json`: frozen identity, arms, rulers and lifecycle;
- `evidence-<id>.json`: raw paths, hashes, run results and failure evidence;
- `decision-<id>.json`: decision, reason, allowed/forbidden claims;
- `HANDOFF.md`: human recovery and verification guide;
- `knowledge-proposals.json`: candidate reusable lessons.

Never overwrite a rejected experiment with a corrected configuration. Link the
superseding experiment and keep both decisions.

## Performance unit

Require:

- frozen input/shared/output lengths, request count, concurrency and warmups;
- all measured requests successful;
- fixed output verified when used for throughput/TPOT;
- raw per-request results;
- TTFT, TPOT, output throughput and total duration;
- file SHA256;
- three unique repetitions unless the contract states a stronger requirement.

Exclude compile/capture warmup from steady-state aggregates.

## Quality unit

Require:

- dataset and evaluator hashes;
- deterministic sampling contract;
- expected request count, successful count and zero failures;
- one parseable JSON object per sample;
- complete unique index set;
- canonical response hash per row;
- summary correct count equal to raw-row recomputation;
- summary `details_sha256` equal to the JSONL digest;
- repeated baseline and treatment runs.

Do not substitute an unavailable dataset without explicit operator approval and
a new contract.

## Activation evidence

Define required events for the target mechanism. At minimum distinguish:

- configuration enabled;
- planner/scheduler chose the mechanism;
- materialization/cache/operator state became ready;
- worker/device hot path executed;
- required repair/isolation/reclaim behavior completed;
- missing or failure events are empty.

Configuration flags or plugin import logs alone do not prove activation.

## Profiling evidence

When required, bind:

- profiler tool/version and exit status;
- exact service and workload hashes;
- baseline and candidate with identical stimulus;
- capture disabled in benchmark runs;
- exported file list, sizes and SHA256 values;
- target regions and direction of improvement;
- workload success independently from algorithm acceptance.

A valid profile capture does not override a failed quality or semantic gate.

## Resource evidence

Record:

- host devices and container-visible mapping;
- CPU set and ports;
- exact container/process names;
- ownership preflight;
- final container/process state;
- OOM state;
- listener release.

Inspect only the declared lane. Neighboring devices may be protected even when
they are on the same host.

## Failure classification

Classify every rejected attempt:

- `algorithm`: mechanism activated but outcome failed;
- `capacity`: ruler cannot be admitted;
- `environment`: image, checkpoint, driver, service or device mapping;
- `tooling`: evaluator, renderer, profiler or controller defect;
- `evidence`: missing, partial, inconsistent or unhashed artifacts;
- `operator`: pause or scope change.

Do not convert operational failure into an algorithm conclusion. Do not hide it
either: retain the evidence and recovery.

## Resume contract

Before resume:

1. poll the authoritative controller handle;
2. if live, do not restart;
3. if terminal, verify exact owned resources;
4. run controller self-test;
5. validate existing units and raw rows against the frozen contract;
6. resume only incomplete units/indexes;
7. run the full independent audit after completion.

Resume commands must pin experiment ID, artifact root, topology, device map,
ports, budgets and reference hashes. Place exact values in the workstream
handoff, not in the reusable skill.

## Decision template

State:

- frozen scope;
- baseline and treatment;
- measured performance deltas and dispersion;
- quality deltas and their evidence-backed boundary;
- activation/profile result;
- accepted and rejected evidence;
- current decision;
- allowed claims;
- forbidden claims;
- new identity conditions that require a fresh experiment.
