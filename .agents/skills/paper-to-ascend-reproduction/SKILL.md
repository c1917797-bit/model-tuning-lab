---
name: paper-to-ascend-reproduction
description: Use to reproduce a prior paper or practice result on Ascend with a frozen one-switch A/B ruler, mechanism activation evidence, repeated performance and quality units, resumable execution, and a fail-closed adoption decision.
---

# Paper-to-Ascend Reproduction

## Purpose

Turn a paper claim or prior success report into auditable Ascend evidence that
answers four separate questions:

1. did the intended mechanism activate;
2. did it improve the frozen target workload;
3. did quality remain inside an evidence-backed acceptance boundary;
4. if it failed, was the cause algorithmic, environmental, statistical,
   capacity-related, or tooling/evidence-related?

Use this skill for historical benchmark reproduction, algorithm piercing,
paper-aligned A/B validation, adoption decisions, or explaining why a paper does
not reproduce on the current Ascend target.

Read `references/evidence-contract.md` before reserving accelerator resources
or starting a long run.

## Hard constraints

- Freeze the scientific question before execution.
- Change exactly one declared treatment switch in each primary A/B.
- Treat model/checkpoint, accelerator generation, card count, topology, cache
  denominator, image, capacity budget, dataset hashes, prompt/scorer, traffic
  shape, and repetitions as experiment identity.
- A changed identity requires a fresh baseline and artifact root.
- Never pool evidence across different scientific questions, rulers, cache
  denominators, topologies, or invalid attempts.
- Do not attribute a favorable metric to the mechanism without activation
  evidence. Report a valid all-request deployment result independently of
  incomplete conditional-path coverage.
- Do not claim losslessness from a point estimate or invented tolerance.
- Never restart a controller that is authoritatively live.
- Do not inspect, stop, or reconfigure workloads outside the declared resource
  lane.
- Completion requires an independent fail-closed artifact audit and proof that
  experiment resources were released.

## Workflow

### 1. Translate the claim

Record the paper/practice claim, mechanism, exact runtime path expected to
activate, primary metrics, quality tasks, falsifiers, and differences between
the reference environment and the current target. Historical numbers are context
unless model, hardware, topology, cache denominator, and ruler match.

State whether the goal is direction reproduction, magnitude reproduction, or
absolute-value reproduction.

### 2. Freeze experiment identity

Create separate experiment, evidence, and decision ledgers for each scientific
question. Hash immutable inputs. Define baseline and treatment in plain
language, and list their machine-readable differences.

Use orthogonal groups when needed:

- G1: native optimization off, paper algorithm off;
- G2: native optimization on, paper algorithm off;
- G3: native optimization off, paper algorithm on;
- G4: native optimization on, paper algorithm on.

Do not use G4 versus G1 to attribute an interaction to one component. A
historical reproduction can be a two-arm question, but its denominator must be
named explicitly.

### 3. Claim and verify resources

Record host accelerator IDs, container-visible IDs, TP degree, CPU set, service
port, communication-port range, container names, and artifact root. Verify
host-to-container remapping explicitly. Read-only preflight must fail if the
owned devices or ports have unexpected users, exact container invariants differ,
container device count does not match TP, or another controller is live.

Never broaden authority from an owned lane to neighboring devices.

### 4. Prove feasibility before the full run

Use the smallest representative real-weight smoke that exercises the mechanism.
Verify health plus a real request, not startup text alone. Check capacity
arithmetic, including private suffix, seam sink, block alignment, workspace, and
reserved tokens.

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
`ignore_eos`, thinking mode, capture, profiler, or cache state leak between
them.

### 6. Require mechanism evidence

Define a strict activation gate before measurement. It should prove both the
planner/scheduler decision and the worker/operator hot path. Configuration
flags or import logs alone do not prove activation.

When treatment activation is conditional (for example, a cache-dependent hot
path), predeclare and report two lenses:

- **Deployment effect:** score every preregistered request, including cold,
  fallback, and non-activated requests. If the paired data and environment
  audit are valid, incomplete hot-path coverage does not erase the all-request
  quality or performance result.
- **Mechanism attribution:** report the request IDs with the required events
  and the exact coverage denominator. Complete per-request proof is required
  only for a claim that every scored request exercised the mechanism. A failed
  activation gate limits that attribution claim; it does not replace the
  deployment result.

Freeze any eligible-request denominator and activation threshold before
candidate outcomes are observed. Never drop cold or non-activated requests
post hoc, and never use a deployment-level pass to claim complete mechanism
coverage.

Use native profiling when the claim depends on kernel time, communication,
memory traffic, or operator fusion. Profile baseline and the unique candidate
with identical bounded stimulus. Keep profiling capture disabled during clean
A/B benchmarks.

### 7. Make long runs resumable

Persist one result per request or sample with stable index, success state, and
response/content hash. A resume may skip a completed unit only after validating
its full contract and hash, retain accepted rows, retry only missing or invalid
indexes, and regenerate summaries only after the expected unique index set is
complete.

If the controller and evaluator remain live inside declared timeouts, wait.
Out-of-order concurrent completion or a long tail is not proof of a hang.

### 8. Analyze repetitions and quality

Report every repetition, mean, and dispersion. Compare treatment quality deltas
with measured baseline repeat variability or a predeclared task-specific
threshold.

When explaining a prior success versus a fresh run on a different physical
device lane or topology, report **both** the within-lane absolute treatment
effect (baseline minus treatment in ms/s) and its relative percentage. A
common additive slowdown in both arms can leave the absolute technique effect
nearly unchanged while shrinking percentage latency and reciprocal-throughput
gains. Decompose baseline drift, treatment drift, and the difference of their
within-lane effects before calling the technique itself a regression. Keep
these three decisions separate: mechanism/effect reproduction, the frozen
same-lane service-performance gate, and full adoption including paired quality.
Retrospective cross-lane decomposition is diagnostic, not a replacement for a
preregistered gate or a license to pool baselines. If equivalence of effect
size matters, preregister its tolerance and repeat contract in the successor
experiment rather than declaring retrospective equivalence proven.

Use these claim levels:

- `regression-observed`: treatment crosses the rejection boundary;
- `no-material-regression-observed`: delta remains inside the evidence-backed
  boundary;
- `lossless-proven`: only when the contract explicitly defines and proves
  equality. Do not use it as a synonym for no material regression observed.

### 9. Audit and decide

Run an independent verifier that checks raw files rather than trusting a status
line or renderer. Keep decisions separate for feasibility, mechanism activation,
performance benefit, quality safety, profile attribution, adoption for the
frozen scope, and generalization.

List allowed and forbidden claims. A successful local reproduction does not
prove topology independence, universal benefit, or absolute equality with the
historical environment.

### 10. Handoff and maintain

Update task, handoff, experiment/evidence/decision ledgers, and knowledge
proposals with exact artifact paths, SHA256 values, resource state and release
evidence, successful and rejected attempts, read-only audit command, idempotent
resume command, remaining risks, and the next scientific question.

Promote only repeated, decision-changing lessons into reusable skills. Keep
machine-specific values and one-off incidents in the workstream retrospective.

## HYPIC lessons already learned

HYPIC reproduced a prior practice direction on a changed environment by keeping
a same-denominator A/B: native prefix cache off in both arms, with only
`VLLM_ASCEND_HYPIC_ENABLE` changed. It showed large latency/throughput gains for
the frozen Qwen3.6-27B TP4 workload while quality deltas stayed inside measured
baseline repeat ranges.

Reusable lessons:

- name the cache denominator before comparing gains;
- treat host/container device remapping as experiment identity;
- budget private suffix plus seam sink before admission;
- require hot-path activation evidence in addition to favorable latency;
- resume by verified unit/sample index, not by rerunning the whole workload;
- separate performance and quality generation semantics;
- complete only after independent hash/count/index audit and resource release;
- distinguish direction reproduction from absolute reproduction when model,
  accelerator generation, or TP degree changes.

## Completion gate

Distinguish experiment completion from adoption. An experiment may be complete
with an accepted, rejected, inconclusive, or failed outcome when every planned
unit is terminally classified, the one-switch identity and raw JSONL/summary
counts and hashes are audited, dataset/evaluator/prompt identities are stable,
performance repetitions and dispersion are reported, profiling is present or
explicitly not required, decision scope and forbidden claims are written,
owned resources are released, the independent audit exits zero, and
handoff/recovery commands are current. Accepting adoption additionally
requires the predeclared performance, quality, and claim-scope activation gates
to pass. A negative result must not be mislabeled as an incomplete experiment
merely because the hypothesis was rejected.
