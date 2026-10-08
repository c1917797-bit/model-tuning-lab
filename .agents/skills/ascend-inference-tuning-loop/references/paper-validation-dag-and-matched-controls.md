# Paper validation DAG and matched dense controls

## Trigger and ownership

Use with the portfolio reference when multiple papers prepare independently
but MAIN serializes the user's four-card Ascend validation lane. This is a
reusable workflow, not permission to use protected cards or a claim that an
authored packet is runnable. Keep live queue counts, owners, fixed cutoffs and
actual operation handles in the active workstream, not this timeless reference.

Practice source: the user's Oct8 DAG and same-configuration clarification,
SparsePrefix SP11's missing installed HYPIC runner, and SparQ's software PASS
followed by a same-image arithmetic-preflight failure. These distinguish real
prerequisites from prepared source. They do not establish a paper-wide no-go.

## DAG: independent preparation, serialized device validation

For every paper, prepare this independent chain:

```text
P0 official mechanism / equation and source provenance
 -> P1 exact deployed Ascend call path and algorithm-specific adaptation seam
 -> P2 opt-in plugin adaptation + independent semantic reference
 -> P3 complete software regression + real CLI + same-image no-device checks
 -> P4 frozen inputs / commands / budgets / fresh output roots / consumers
 -> Q  MAIN-reviewed ready packet for one named device gate

Q -> N0 fresh physical-device mapping / ownership / aggregate resource admission
  -> N1 real plugin / operator / binary load and every relevant worker dispatch
  -> N2 actual NPU numerical + multi-step state / lifecycle / graph matrix
  -> E1 same-config dense/candidate single-round E2E screen
  -> E3 worthwhile candidate: three formal paired performance rounds
  -> A  final LongBench-v2 and GSM8K paired task accuracy
  -> T  supported-environment portability verification + plugin delivery
  -> L  scoped decision, reusable lessons and resumable checkpoint
```

Edges represent evidence that the next consumer must actually validate, not
a checklist satisfied by prose. Every node names its producer, exact input and
output Refs/source identities, entrypoint, exit/acceptance predicate, budget,
failure/recovery policy, and successor consumer. Numerical readiness does not
mean E2E or final acceptance. N2 includes the matrix relevant to the algorithm:
an attention selector cannot borrow a recurrent-state test, or vice versa.

Data-dependent algorithms also have this explicit branch:

```text
prepared capture adapter -> admitted NPU capture -> frozen real-data Ref
 -> bounded CPU calibration / author selector / teacher checks
 -> frozen algorithm artifact -> candidate NPU correctness -> E2E
```

Without genuine capture or required author artifacts, say DATA-PENDING; do not
manufacture an input or promote a CPU toy into model correctness. Calibration
is not training/distillation, but must still obey the user's algorithm scope
and resource budget. Prepare these consumers before taking the capture lease.

Hardware-dependent runner imports may query HAL before model allocation.
After proving that dependency from the installed source, move only that check
to N1. Keep all executable static checks in P3; do not create fake CPU/HAL
architecture stubs to call the packet ready. Mark Q as ready for the named
hardware gate, not as having passed that gate.

## What "same configuration" and dense/candidate mean

Dense/control means the unmodified model semantics under the frozen common
runtime optimizations, with only the paper-specific candidate disabled. In a
hybrid model it retains the original full-attention AND linear/GDN paths:
"dense" does not turn all attention into a different architecture.

Candidate means that same model/workload/common stack with the one declared
paper mechanism and its necessary, explicitly named Ascend adaptation enabled.
No training/distillation or unrelated operator changes are silently included.
Existing HYPIC, graph, communication or native-kernel improvements, if in the
common contract, remain identical in both arms.

Freeze and compare at least:

| Field | Required match |
| --- | --- |
| Model and tokenizer | Same checkpoint/tokenizer content hashes; model dtype and TP degree |
| Software | Same image, vLLM-Ascend, CANN, driver/firmware and common source identities |
| Hardware/resources | Same physical cards, CPU/cgroup/NUMA budget, host reserve; no competing timed load |
| Workload | Same exact input/prompt set, order/seed, context/prefix distribution, concurrency and request count |
| Runtime | Same common optimizations, engine scheduler/cache settings and graph/eager regime |
| Performance generation | Same generation settings; force exactly 1024 output tokens in both arms |
| Task accuracy | Same datasets/prompts/scorers; no thinking, max output 2048, normal EOS, same sampling settings |
| Measurement | Same metric definitions, warmup policy, timed boundary, repetition and failed-request handling |

An algorithm's intrinsic change (selected support, compressed state/cache,
different capacity or algorithm-specific policy) belongs in the declared
candidate delta; do not pretend that changed quantity is held constant.
For capacity-oriented papers, distinguish iso-workload latency/throughput from
separate max-capacity measurements. More concurrency only for the candidate
is not an iso-workload speedup.

The actual comparison proves OFF/ON and per-worker dispatch, counts fallbacks,
and records correctness and successful-token coverage. Same seed/config does
not itself guarantee determinism. A failed implementation or incomplete request
set is not a legal performance arm. For exact methods check the predeclared
native semantic parity; for approximate methods use the independent paper
reference and separately measure final task accuracy. The user's E2E accuracy
allowance never becomes a tensor tolerance.

Formal performance is profiler-off and without correctness instrumentation
whose overhead differs between arms. Report output throughput, TTFT and TPOT
separately; do not sum kernel time into an E2E claim. For matching successful
1024-token coverage:

```text
throughput improvement = (candidate throughput / dense throughput - 1) * 100%
```

Lower TTFT/TPOT and higher throughput are different outcomes. Three formal
paired rounds, not one screen, support the >=10% acceptance claim. Rotate or
interleave OFF/ON runs under the predeclared order so temporal drift is visible.

A frozen, source-bound baseline can be reused for screening while its complete
identity and workload remain valid; do not rerun expensive task baselines for
every source edit. A software/common-optimization, workload, resource or
measurement change invalidates the affected comparison. Final acceptance needs
the prescribed paired performance/task evidence; an old baseline with an
incompatible fingerprint cannot serve as the other arm. Keep precision-loss
units and the latest user-approved task threshold in the experiment contract.

## Failure edges and non-drift scheduling

- P0/P1 unknown: acquire specific source/path evidence. Unsupported means
  inconclusive for that scope, not "the paper has no benefit."
- P3/P4 failure: preserve the original; fix the proved import/schema/CLI/input
  or budget handoff. Do not take cards to discover an already-known missing edge.
- N0 denial: perform independent safe preparation; never dummy-load cards or
  reclaim protected work. Mere device declarations do not prove occupation.
- N1 failure: repair the evidenced plugin/operator integration dependency.
  A successful canary before failed registration is not algorithm correctness.
- N2 failure: retain raw per-case outputs/state before first aggregate assert;
  isolate algorithm, ABI, lifecycle or reference error. No tolerance relaxation,
  unsupported source rewrite or unchanged deterministic retry.
- E1/E3 valid regression: use actual stage/critical-path evidence for a bounded
  paper-specific redesign; do not polish an unrelated operator to claim a gain.
- A failure: target the paper's error mechanism within the remaining fixed
  deadline and allowed scope; otherwise close the current implementation.
- T: declare the supported capability/version envelope and fail-closed fallback.
  Portability is designed in, but untested environments remain unverified;
  no finite test supports a guarantee on every future Ascend stack.

After each terminal event, verify own-only cleanup, consume immutable evidence,
and select the highest-value actually ready successor. Keep CURRENT/NEXT/BACKUP
and missing dependencies explicit; preparation/source count is not ready count.
Do not delay a ready NPU successor for report prose. Reconcile short work with
mechanism -> NPU correctness -> paired E2E -> task quality, and preserve fixed
paper/portfolio cutoffs. Stop only the failed scope, not all independent prep.

## Verifiable lessons from this practice

Configuration enablement is not dependency installation. SP11 passed full186
software and same-image preflight and all four device canaries, then stopped
before model execution because the genuine HYPIC runner was not installed.
A successor must prove explicit dependency ordering and actual every-worker
installation; frontend PID proof cannot stand in for four worker proofs.

SparQ's current observer full174 and real CLI checks passed, but its preceding
same-image four-case arithmetic aggregate failed before any NPU create.
That proves at least one aggregate condition failed, not that all four cases
failed. Preserve raw per-case values before asserting so the next adaptation
addresses a measured cause. Both cases are scoped preparation/integration
evidence, not performance or final task results.

## Verification

Run `./scripts/validate-mst.sh` and focused `git diff --check`. Inspect the
entry-skill/registry routing to this reference and require all DAG node labels,
both performance/task generation protocols, and the failure branches above.
Validate actual experiment commands and consumers separately: this documentation
check never issues numerical, model, E2E or final-acceptance permission.
