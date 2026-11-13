# Agent-assisted kernel porting and useful validation

Use for a new Ascend operator, a proved operator defect, or repeated preparation
that is not advancing a paper into the real model. These rules are drawn from
the BOLE/DeltaLog continuation; they do not replace its frozen acceptance gates.

## Select the tool at the failing boundary

- Prefer the maintained CANNBot workflows for new Ascend kernels and confirmed
  kernel defects when the installed client, chip and CANN version are supported.
  Use ops-direct-invoke for a direct kernel, ops-registry-invoke for ACLNN/GEIR
  registration, ops-perf-optimize for measured kernel tuning, and
  model-infer-optimize for model migration/profiling assistance. Check current
  upstream contracts instead of copying an obsolete plugin directory.
- First inspect a matching native CANN/framework operator or official paper
  implementation. Reuse a compatible implementation before generating another.
  Publication year or the existence of CUDA/SGLang code does not establish
  support for the actual Qwen hybrid GDN path or this Ascend product.
- A kernel that already passed its declared cases should not be rewritten to
  demonstrate tool adoption. A binary-loading, wrapper, source-binding, report,
  or launcher defect is repaired at that boundary, with focused regression.
- CANNBot is not assumed installed or successful. Record its real repository
  revision/plugin, relevant skill entry, target stack, invocation, resulting
  source/binary identities and actual validation receipts. Tool documentation,
  copied skill files or a proposed command do not establish an executed run.
  External agent use remains subject to the source-confidentiality boundary;
  do not send host-only source/RAW to another service without authorization.

Supply the tool with the mathematical operation and invariants, actual
shape/dtype/stride/layout distribution, update/reset/slot semantics, chip and
software versions, supported call ABI, independent oracle and error limits.
A paper title alone is not an implementation contract. In particular, do not
apply an Ascend950-only implementation recipe to a 910B4 target.

## Define the next useful test before editing

Name the observed first fault, the smallest change that could fix it, and the
next real consumer that will exercise it. Use this decision rule:

| Evidence | Next action |
| --- | --- |
| Candidate and independent oracle disagree on the same actual input | Diagnose kernel math/layout/state or synchronization; preserve the failing input and thresholds. |
| Standalone candidate matches but production differs | Prove the production callee, loaded library and adapter identities, then replay the same input through that wrapper. |
| Math passes but an identity/report predicate fails | Repair or explicitly reconcile that contract; preserve the original result and do not rerun numerical coverage only for a label. |
| A source tree was written but report publication failed | Preserve the failed exit; inspect exact expected files/hashes and writers, then use the native recovery/bind path. |
| Required numerical/state gates and the actual model binding pass | Advance to the preregistered matched model screening; do not add unrelated software suites or review frameworks. |

At the actual production call, retain the loaded binary hash and module
realpath/adapter identity, actual shape and dtype, device mapping, and
candidate invocation/commit counters. An installed package or registry entry
alone does not show that the intended implementation ran. See
[production dispatch attribution](production-library-dispatch-attribution.md)
for the new/old/new causal control and original-consumer requirements.

## Reuse evidence without borrowing acceptance

- Scope every result to source, stack, input, device and coverage. Check the
  change's dependency surface. Reuse unchanged, hash-bound results; rerun the
  affected boundary and required downstream numerical/state/model gates.
- CPU is appropriate for independent high-precision reference calculation and
  cheap software/ABI checks. It cannot qualify NPU execution or performance.
  If the actual model owner already includes CPU -> release -> device canary,
  do not launch a second copy of its unchanged CPU phase.
- A report/schema-only repair does not justify repeating a valid 192-case NPU
  matrix. A kernel math change can invalidate those numerical results. Neither
  reuse nor narrow regression may waive missing state/graph/model coverage.
- Preserve erroneous aggregates. A correction consumer must bind the exact
  original report, actual owner/mapping and discrepancy evidence; it must not
  silently rewrite a physical-card label or promote component coverage to TP4.
- Before source materialization, check all source, preview, execution-report
  and output destinations together. Preview and execution need distinct
  immutable report paths. Never regenerate into a populated tree to make a
  final-report collision disappear.
- Record real compile/load/transfer/compute/reference/cleanup durations.
  A 5400/10800-second phase cap is not measured work. Preparation agents finish
  independent nodes and feed MAIN's ready queue; finishing preparation does
  not grant a device lease. Use the existing scheduling reference rather than
  adding a second scheduler.

## Evidence-backed successes and remaining limits

Evidence was re-read on chicaihong01 on 2026-11-13; the following runs remain
historical 2026-11-04 results, not new model acceptance.

- Controlled new-f65/old-8e7/new-f65 replay on the same captured input and
  adapter reproduced seven NPU/FP64 matches for the new library and six
  mismatches for the old. This supports a library-dependent difference for
  that case, not a uniquely proved stream mechanism.
- The registered f65 wrapper passed its original 18 one-frame checks. Its
  saved-output independent FP64 consumer also passed; this is useful separate
  reference verification, not another complete algorithm CPU suite.
- The actual f65 matrix on physical1 passed 192 saved cases/3456 original
  predicates, with verify192/commit768/direct0. Four source TP ranks x48 layers
  executed on one physical card; this is not a live TP4 model. The independent
  RAW/hash audit is not a second numerical recomputation. Its stale physical4
  label still blocks the registered model consumer until explicit correction.
- DeltaLog's exact CPU004 unused logical reservation was closed once while
  preserving the original ledger and 235051 bytes. The subsequent 176-file
  source recovery proves completeness only; actual capture005/native binding
  and NPU validation remain required. Never spend the closure allowance again.

Host evidence, relative to
`.agents/workstreams/qwen36-damp-ascend-20261006/dual_resume_20261104T091749Z/`:

- `BOLE_NEW_OLD_NEW_CASE_REVIEW_20261104.json`
- `BOLE_F65_REGISTERED_WRAPPER_ONE_FRAME_MAIN_ACCEPTED_20261104.json`
- `bole_f65_registered_matrix192_evidence_scope_review_v2/INDEX.json`
- `EXECUTION_DELTA_CPU004_EXACT_ABSENT_LOGICAL_CLOSE_VERIFIED_20261104.json`
- `delta_CPU005_materialization_recovery_v1/INDEX.json`

Failures to avoid repeating: testing helper code instead of the real runtime
identity predicate; loading an old binary through an unchanged adapter;
stale device/report labels; overwriting a preview report at final publication;
and restarting after a transport timeout without inspecting the original
operation plus boot/PID/start/CID. These are scoped engineering failures, not
evidence that a paper is mathematically invalid.

## Upstream sources and adoption limits

Checked 2026-11-13. These describe external tooling, not local execution:

- [CANNBot application workflows](https://gitcode.com/cann/cannbot):
  maintained workflow entrypoint.
- [CANNBot skills changelog](https://gitcode.com/cann/cannbot-skills/blob/master/CHANGELOG.md):
  Codex support and migration of direct-invoke, performance and model workflows
  to the application repository; do not fall back to removed plugin copies.
- [AKG Agents](https://github.com/mindspore-ai/akg/blob/master/akg_agents/README.md):
  alternative generation/migration/iterative-search tooling; verify the chosen
  branch's actual Ascend backend rather than a general capability list.
- [ForgeKernel](https://arxiv.org/abs/2611.04998):
  reuse hardware-validated knowledge and revisit kernel architecture. Its
  operator-level benchmark gains do not establish this model's speedup.
- [CANN Bench](https://arxiv.org/abs/2607.20518):
  compilation, correctness and performance are separate evaluation axes.

A successful adoption must reduce a measured implementation/validation
bottleneck or produce a qualifying artifact. Installing tools or editing this
skill is not paper success. Final model performance and task-quality
requirements continue to come from the latest frozen experiment protocol.
