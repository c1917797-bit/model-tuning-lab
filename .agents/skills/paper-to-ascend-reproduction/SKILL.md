---
name: paper-to-ascend-reproduction
description: "Reproduce an academic inference optimization on Ascend with a frozen one-switch baseline/treatment ruler, isolated accelerator resources, performance-quality-profile evidence, resumable execution, and a fail-closed adoption decision. Use for paper reproduction, algorithm piercing, Ascend benefit validation, historical benchmark reproduction, or explaining why a paper has no measurable gain."
---

# Paper-to-Ascend Reproduction

## Purpose

Turn a paper or prior success report into auditable Ascend evidence that answers:

1. did the intended mechanism activate;
2. did it improve the frozen target workload;
3. did quality remain inside an evidence-backed acceptance boundary;
4. if it failed, was the cause algorithmic, environmental, statistical, or
   evidence/tooling related?

Read `references/evidence-contract.md` before reserving accelerator resources.

## Hard constraints

- Freeze the scientific question before execution.
- Change exactly one declared treatment switch in each primary A/B.
- Treat model/checkpoint, accelerator generation, card count, topology, cache
  denominator, image, capacity budgets, dataset hashes, prompt/scorer, traffic
  shape and repetitions as experiment identity.
- A changed identity requires a fresh baseline and artifact root.
- Never pool evidence across different scientific questions or invalid rulers.
- Do not accept a favorable metric without mechanism activation evidence.
- Do not claim losslessness from a point estimate or invented tolerance.
- Never restart a controller that is authoritatively live.
- Do not inspect, stop or reconfigure workloads outside the declared resource
  lane.
- Completion requires an independent fail-closed artifact audit and proof that
  experiment resources were released.

## Workflow

### 1. Translate the claim

Record:

- paper/practice claim and expected direction;
- mechanism and the exact runtime code path that should activate;
- primary performance metrics and quality tasks;
- falsifiers and explanations to collect if no gain appears;
- differences between the reference environment and the current target.

Historical numbers are context unless model, hardware, topology and ruler match.
State whether the goal is direction reproduction, magnitude reproduction, or
absolute-value reproduction.

### 2. Freeze experiment identity

Create separate experiment, evidence and decision ledgers. Hash immutable
inputs. Define baseline and treatment in plain language and list their
machine-readable differences.

Use orthogonal groups when needed:

- G1: baseline;
- G2: native optimization only;
- G3: paper algorithm only;
- G4: combined configuration.

Do not use G4 versus G1 to attribute an interaction to one component.

### 3. Claim and verify resources

Record host accelerator device paths, container-visible IDs, TP degree, CPU
set, service port, communication-port range, container names and artifact root.
Verify host-to-container remapping explicitly.

Read-only preflight must fail if:

- any owned device or port has an unexpected user;
- the exact container invariants differ;
- host and container device counts do not match TP;
- another controller for the same experiment is live.

Never broaden authority from an owned lane to neighboring devices.

### 4. Prove feasibility before the full matrix

Use the smallest representative real-weight smoke that exercises the mechanism.
Verify health plus a real request, not startup text alone. Check capacity
arithmetic, including reserved, seam, sink, block-alignment or workspace tokens.

Archive pre-measurement failures separately. If a frozen invariant changes,
start a new experiment; do not repair the ruler in place and reuse its baseline.

### 5. Separate execution phases

For each frozen arm:

1. start and verify the exact service;
2. warm up under the declared policy;
3. collect repeated fixed-output performance;
4. stop the service;
5. restart the identical arm;
6. collect deterministic, EOS-respecting quality repetitions;
7. stop again;
8. profile only when the mechanism claim or decision contract requires it.

Performance and quality sampling semantics are different contracts. Do not let
`ignore_eos`, thinking mode, capture, profiler or cache state leak between
them.

### 6. Require mechanism evidence

Define a strict activation gate before measurement. It should prove both the
planner/scheduler decision and the worker/operator hot path, with no required
event missing.

Use native profiling when the claim depends on kernel time, communication,
memory traffic or an operator fusion. Profile baseline and the unique candidate
with identical bounded stimulus. Keep profiling capture disabled during clean
A/B benchmarks.

### 7. Make long runs resumable

Persist one result per request/sample with stable index, success state and
response/content hash. A resume may:

- skip a completed unit only after validating its full contract and hash;
- retain accepted rows;
- retry only indexes without a valid `ok=true` row;
- regenerate a summary only after the expected unique index set is complete.

If the controller and evaluator remain live inside declared timeouts, wait.
Out-of-order concurrent completion or a long tail is not proof of a hang.

### 8. Analyze repetitions and quality

Report every repetition, mean and dispersion. Compare treatment quality deltas
with measured baseline repeat variability or a predeclared task-specific
threshold. Preserve both point estimates and interpretation.

Use these claim levels:

- `regression-observed`: treatment crosses the rejection boundary;
- `no-material-regression-observed`: delta remains inside the evidence-backed
  boundary;
- `lossless-proven`: only when the contract explicitly defines and proves
  equality; do not use it as a synonym for the previous level.

### 9. Audit and decide

Run an independent verifier that checks raw files rather than trusting the
renderer. It must cover every planned unit and the requirements in the
reference contract.

Keep decisions separate:

- feasibility;
- mechanism activation;
- performance benefit;
- quality safety;
- profile/mechanism attribution;
- adoption for the frozen scope;
- generalization.

List allowed and forbidden claims. A successful local reproduction does not
prove topology independence or universal benefit.

### 10. Handoff and maintain

Update `task.json`, `HANDOFF.md`, experiment/evidence/decision ledgers and
knowledge proposals. Include:

- exact artifact paths and SHA256 values;
- resource state and release evidence;
- successful and rejected attempts;
- exact read-only audit command;
- exact idempotent resume command and its preconditions;
- remaining risks and the next scientific question.

Promote only repeated, decision-changing lessons into this skill. Keep
machine-specific values and one-off incidents in the workstream retrospective.

## Completion gate

Do not declare completion unless all are true:

- every planned unit is accepted;
- baseline/treatment invariants and one-switch difference are proven;
- mechanism activation gate passed;
- all quality JSONL/summary counts, indexes and hashes agree;
- dataset, evaluator and prompt identities are stable;
- performance repetitions and dispersion are reported;
- profile evidence is present or explicitly not required by the frozen claim;
- decision scope and forbidden claims are written;
- exact experiment containers/processes are stopped and owned resources released;
- independent audit exits zero with no errors;
- handoff and recovery commands are current.
