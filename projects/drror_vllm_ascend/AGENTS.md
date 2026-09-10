# Project working instructions

## Shared maintenance scope

This project is maintained from the Model Tuning Lab monorepo. Read
`../../AGENTS.md`, `../../.agents/HANDOFF.md`, and the root
`../../.agents/skills.registry.yaml` before using the project-specific rules
below. Root maintainer skills are canonical. This file only narrows DRRQR
algorithm, resource, evidence, and acceptance boundaries.

## Skill review before execution

The user requires reviewing each relevant skill before acting on it. Read the skill fully,
then check its technical evidence, installed-version assumptions, task fit, authorization
boundaries, side effects and whether its validation really proves its claimed outcome.

Correct demonstrated problems directly within the user's authorized scope before following
the affected instructions. Do not treat speculation as a reason for broad rewrites. Record
the issue, evidence and correction; a format-validator pass is not technical validation.
Do not repeatedly ask questions already answered by the user.

For Ascend profiling in this project, use the audited task-local skill at
`skills/model-infer-profiling/SKILL.md` instead of the uncorrected cann bot reference.
If another skill needs adaptation, keep project-specific corrections in this project
rather than silently editing shared skills or upstream runtime code.

## Current experiment boundaries

All DRRQR implementation changes belong under this project directory. Reference
vLLM-Ascend, ops-transformer and cann bot
trees are read-only. On 2026-09-09 the user authorized push to this repository and
research beyond 1–3 days on heterogeneous cache/native operators; all other boundaries
remain unchanged. See docs/experiments/qwen38-drrqr-correctness-20260908/EXTENDED_RUNTIME_RESEARCH.md.
Use only physical NPU4–7 and verify
container device mappings; never affect physical NPU0–3 or unrelated processes.

The current strategy is performance first, with numerical correctness mandatory. No LoRA
or thinking-mode evaluation currently. Final success requires the same configuration to
deliver reproducible 10%+ end-to-end throughput gain without accuracy decline. Accuracy
baseline and candidate use max_tokens=2048; the separate fixed-output performance protocol
uses 1024. Preserve historical results and label invalid or non-comparable evidence.

## Frozen baseline reuse

Use
`docs/experiments/qwen38-drrqr-correctness-20260908/FROZEN_BASELINE_V1.json`
as the fixed development performance baseline. Do not rerun dense for every
candidate. Before comparison, verify the current environment and dense-path
manifest against that contract. Candidate-only changes proven inactive when
DRRQR is disabled keep the baseline valid. Rebaseline only for a listed material
change affecting the model, runtime identity, dense path, common optimization,
device/topology, or workload protocol.

The frozen performance reference is 135.14246991715385 output tok/s,
34693.57763297157 ms mean TTFT, and 69.43622686534793 ms mean TPOT. The fixed
10% target is 148.65671690886924 output tok/s. This is a reusable single-run
development baseline, not retroactive three-run final acceptance. The current
same-stack final-protocol accuracy baseline remains a one-time missing artifact;
historical LongBench-v2 runs are context only. After that accuracy artifact is
created, reuse it under the same material-change policy.

## Mainline experiment admission and scope control

The user's latest steering is algorithm-first: adapt DRRQR selectors, rank
budgets and recurrence behavior to obtain the joint objective. Operator/cache
changes are authorized when they enable or improve a concrete DRRQR candidate;
generic operator development is not an independent completion target. Continue
to apply any general optimization equally to the contemporaneous dense control.

The user explicitly reaffirmed the DRRQR-only mainline after an off-scope MTP
recommendation. Do not substitute MTP, speculative decoding, quantization or
another acceleration algorithm for this objective without explicit new direction.
At experiment admission, result interpretation, and next-step selection, check:
(1) the work directly enables DRRQR or tests a named DRRQR algorithm/operator
change against an observed limitation; (2) the deciding evidence advances the
same 10% end-to-end throughput/no-accuracy-loss objective; (3) numerical/storage
or local-fidelity evidence is not reported as throughput/task-accuracy success.
State this link concisely in progress updates. If the link is absent, defer the
branch and return to the mainline. Label official StrongRRQR and energy-selector
variants separately; neither a variant nor a generic optimization is evidence
of exact paper reproduction. These are workflow checkpoints, not authorization
for a scheduled/background automation.

The user also requires performance portability across Ascend environments.
Portability is a design-time requirement, not something to postpone until a
second machine is available. For each proposed algorithm/operator change,
explain the model-level reasoning, the saved versus added compute/memory/data-
movement costs, the backend capability assumptions, and the conditions under
which the benefit may disappear. Separate algorithm semantics and rank budgets
from backend implementation; distinguish logical Dk from physical alignment,
stride and padding. Do not silently hard-code the current chip/runtime's
incidental behavior into the algorithm. Keep a consistent mathematical reference
and explicit backend capability dispatch. Compatibility fallback preserves
correctness but is not evidence of a performance gain. Frozen paths and source
hashes in experiment probes establish reproducibility, not a portable public
interface. Do not fit algorithms to the new local screening prompts. Review
these design obligations now; cross-environment tests later check the reasoning
rather than substitute for it. A missing second machine does not pause in-scope
design or current-environment DRRQR experiments.
Keep the primary same-stack paired target (10%+ throughput, no accuracy loss)
and additionally require measured positive throughput gain against each admitted
environment's own contemporaneous dense baseline. Define the supported hardware,
runtime and workload matrix with the user; a second environment is not yet
specified. Running successfully, a portable interface, CPU tests, or primary-host
results do not satisfy cross-environment performance acceptance. Each supported
environment needs relevant NPU numerical checks, paired end-to-end measurements
with TTFT/TPOT, and the final accuracy requirements. Unavailable or untested
environments remain explicitly unverified. Do not claim universal speedup across
arbitrary hardware/software/workloads or access other devices without resolving
the user's intended target and existing resource boundaries.

## DRRQR goal-chain specialization

Use the shared `mst-practice-iteration-planning` goal-chain review when
admitting a short task, when its deciding evidence or budget arrives, before
expanding cost or changing research branch, and at handoff.

For this project, the fixed long-term objective is the same-stack joint
acceptance: reproducible 10% or greater end-to-end output-throughput gain with
no LongBench-v2 or GSM8K accuracy decline and with the declared TTFT/TPOT,
output-length, EOS, resource, and portability contracts. The medium-term
milestone is a defensible DRRQR candidate that can proceed toward that
acceptance, not an independent cache, operator, diagnostic, or report project.
Every short task must name the joint-acceptance gap it addresses, the DRRQR
candidate decision it can change, its bounded evidence budget, and the action
for pass, failure, or inconclusive evidence.

Do not redefine success around local numerical checks, lower an existing gate,
or treat code, reports, commits, and pushes as joint-target progress. Negative
evidence is useful when it rejects or redirects a candidate. If a diagnostic
budget ends without changing a candidate decision or enabling a named
milestone, preserve it and return to DRRQR candidate selection.

Before each experiment state its performance-first phase, concrete hypothesis, deciding
evidence, and bounded run/time budget. After completion report the evidence and return to
the mainline. No automatic unbounded retry/search or new acceptance criteria.

Use minimal controls to determine whether an anomaly requires our change. A phenomenon
also present in the unmodified baseline is not alone proof that our change is safe, nor
grounds to invalidate historical evaluations. Test our incremental numerical effect.
Generic framework investigations are deferred unless necessary to trust a comparison;
if that requires expanding scope, stop that candidate and request the user's direction.
Do not launch the prepared diagnostic-determinism worker experiment without renewed
direction. No skill, diagnostic or passing microbenchmark overrides the final joint target.

Exploration uses representative change-specific numerical/state checks and a single
performance screen to prioritize candidates. Expand coverage and repeat paired runs for
promising candidates and final acceptance, not for every speculative change. Bitwise
equality is appropriate for pure storage-layout transformations; arithmetic/fusion changes
use justified predeclared error criteria and multi-step state checks. Never relax criteria
after a numerical failure just to obtain a pass. Final accuracy requirements are unchanged.

A new aligned logical Dk must pass the real prefill and decode implementations separately.
Short synthetic chunk-prefill parity and recurrent decode graph parity do not establish
production-context finiteness. If an integrated candidate becomes non-finite, reject its
endpoint promotion first, then bind the first non-finite tensor at the actual model/operator
seam before choosing between algorithm redesign and candidate-specific operator adaptation.
Do not infer an algorithm failure from an unproven backend shape path, and do not build a
replacement operator merely because the failure is plausibly kernel-related.

A finite serial long-prefill trace does not clear a failure observed only under concurrent
mixed prefill/decode scheduling. Preserve the exact prompt cohort, concurrency, cache
occupancy and decode phase when localizing that failure. Before adapting an operator, bind
the first non-finite tensor to a concrete request phase and record the real state-cache slot,
storage identity, shape, stride and non-overlap evidence. A safe prompt or low-occupancy run
may narrow the failure scope, but cannot be substituted for the failed production regime.
