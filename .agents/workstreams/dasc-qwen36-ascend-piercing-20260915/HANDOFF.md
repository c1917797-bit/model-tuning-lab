# DASC Qwen3.6 Ascend Piercing Handoff

## NPU4-7 v12 resumable controller

The next immutable attempt is dasc-qwen36-physical-cache-v12. It is pinned to
physical NPU4-7 and port 8030; NPU0-3 are explicitly outside scope. Validate and
start exactly once with run_physical_cache_v12.sh --self-test, followed by the
same script without arguments.

The controller waits while any physical NPU4-7 has a live device process, then
takes /cache/cch/.locks/npu4-7.lock, repeats the occupancy check, checks port
8030, snapshots the plugin bytes, and starts the exact owned v12 container. Do
not start a second controller. Poll its authoritative remote exec handle and
inspect the controller log at
/cache/cch/dasc-qwen36-ascend-20260915/controllers/dasc-qwen36-physical-cache-v12.log.
The immutable result directory is
/cache/cch/dasc-qwen36-ascend-20260915/physical-cache-order-fix-v12.

## Current Status

Workstream opened on 2026-09-15 for arXiv:2608.30386 DASC. Paper ingestion,
architecture fit, the state-lifecycle source map, and the first plugin-owned
DASC-NR numerical canary are complete and verified on physical NPU4-7.

The canary lives under `projects/dasc_vllm_ascend`. It is disabled by default,
version/source guarded, and only changes temporal-state copying on a genuine
new/resumed prefix restore. It keeps dense allocation and therefore is not yet
a cache-capacity or performance implementation.

## Mainline Goal

Pierce whether DASC can produce a real cache-hit TTFT or throughput gain on Qwen3.6-27B in the chicaihong01 Ascend environment, while keeping E2E quality within the user's gate. Do not judge it with no-cache decode throughput.

## Delivery Constraint

The final runnable implementation must be a plugin-owned monkeypatch that runs on Ascend. Do not modify upstream vLLM, vLLM-Ascend, CANN, model weights, or original images. CPU/offline probes and source inspection are allowed only as gates; they are not a valid final delivery.

## Short-Term Plan

1. Inspect Qwen3.6 GDN weights and vLLM-Ascend state layout.
2. Generate a DASC-GDN head-retention plan for `W_max` values such as 16, 64, 128, and 512.
3. Compute dense vs compressed checkpoint bytes including recurrent temporal state and convolution state.
4. Source-map vLLM-Ascend prefix-cache/state-checkpoint store/load behavior.
   This is complete: `MambaManager` and `preprocess_mamba` preserve and copy
   aligned convolution and temporal checkpoints by block ID.
5. Review, package, and run the implemented DASC-NR numerical canary with a
   disabled control on physical NPU4-7.
6. After all-rank activation and correctness pass, implement compact temporal
   pages plus dense active-state workspace. Do not mistake the current
   zero-filled dense storage for a capacity optimization.
7. Prove real cache-block admission growth before any service performance claim.

## HYPIC Lessons Applied

- Use one denominator and one treatment switch.
- Prove mechanism activation before timing.
- Separate source compatibility, canary correctness, service integration, performance, and quality.
- Keep per-run artifacts resumable and auditable.
- Do not claim the paper result from a partial primitive.

## Current Decision

Open, with a narrower integration risk. The paper has credible relevance to
Qwen-GDN and the current stack already supports aligned recurrent-state prefix
checkpoints. Local feasibility now depends on whether a plugin monkeypatch can
replace dense block storage with compact retained-head storage plus a dense
active-request workspace while keeping native Ascend GDN kernels unchanged.

## Verified NPU canary and decision

The W64 dense-storage canary ran on Qwen3.6-27B with TP4, vLLM/vLLM-Ascend
v0.23.0, eager mode, Mamba align cache, and physical NPU4-7. Two 2,350-token
prompts shared one 1,536-token cache page. All 48 GDN layers fired on all four
TP workers, yielding exactly 192 temporal-restore events. Candidate and
plugin-disabled control returned identical 16-token continuations.

The steady cache-reuse request was 4.213 s for the canary and 4.008 s for the
control, so the dense-storage canary regressed by 5.095%. It is rejected as a
performance candidate but accepted as runtime-path and semantic evidence.
First-request latency is excluded because both runs included cold operator
initialization.

Runtime artifacts:
`/cache/cch/dasc-qwen36-ascend-20260915/`

The next admissible successor must change the physical representation:
compact retained-head checkpoint storage, dense workspace expansion on restore,
and measured post-alignment cache capacity. Repeating or tuning the existing
dense masking route is closed.

## Physical-cache integration attempts

Two bounded service launches advanced the integration boundary without
producing performance or quality results:

- `physical-cache-eager-v1` reached cache-spec collection on all four TP ranks
  and failed because independently selected local head counts produced
  different shapes for the same layer across workers. Logs and activation
  evidence are retained under the runtime artifact root; their SHA256 values
  are `24732fd...e83854` and `f51df7d...40fcf`.
- Commit `fc1fb2b` added a per-layer HCCL MAX of retained counts. Each rank
  keeps its own weight-derived indices and pads only with its longest-horizon
  omitted heads. The complete v0.23 suite passed 37 tests.
- `physical-cache-eager-v2` proved that collective on physical NPU4-7. All
  four workers emitted identical 48-layer common-count vectors, and the run
  passed the former cross-worker merge assertion. It then failed at the next
  framework gate because heterogeneous Mamba pages were sent through vLLM's
  global page-divisibility path. Logs/evidence SHA256 are
  `831fcf5...09644` and `2237ca8...8e18`.
- Commit `e4587c3` represents aligned attention plus heterogeneous Mamba specs
  as one `UniformTypeKVCacheSpecs` aggregate, retaining the exact inner page
  sizes instead of padding every layer to the dense maximum. It fails closed
  if hidden-state cache or unequal token block sizes appear. The v0.23 suite
  passes 39 tests and the commit is pushed.

No TTFT, TPOT, throughput, or E2E accuracy conclusion follows from v1/v2.
The next run must use a new `physical-cache-eager-v3` artifact directory and
first prove service readiness, physical bytes, real prefix reuse, and retained
state correctness. At the latest orientation, NPU4-7 were occupied by the
separate `vllm_23_au` DeltaLog/fused-GDN piercing process, so v3 was not
started and that workload was not interrupted.

## 2026-09-16 authoritative continuation

The earlier v3 wording above is historical. Attempts through v11 narrowed the
remaining integration issue to cache-group ordering. Commit `48594bf` fixed
that ordering and the current immutable mechanism attempt is v12.

The only v12 controller is remote exec operation
`exec-0000000000001235`. It is live and waits only on physical NPU4-7. Do not
restart it after a poll timeout and do not inspect, stop, or schedule on
NPU0-3. Its log is
`/cache/cch/dasc-qwen36-ascend-20260915/controllers/dasc-qwen36-physical-cache-v12.log`.
At the last check, an unrelated TP4 service still owned NPU4-7, using about
28,068 MiB per card, so the owned v12 container and immutable result root did
not yet exist.

That historical statement is now superseded. The external TP8 service briefly
removed its device PIDs at 22:48 UTC while retaining about 94% HBM, so v12
passed the PID-only idle check and then failed before service readiness with
only 1.91/29.49 GiB free per rank. The immutable v12 root is retained and the
independent verifier correctly rejects it because SUCCESS, evidence.jsonl, and
physical-canary.json are absent. This is a resource handoff race, not DASC
mechanism evidence.

The successor controller must use a new immutable root and container. It
inherits the same mechanism code but requires both no device PID and a bounded
idle HBM floor on every physical NPU4-7 before and after taking the lock.
The initial 5% ceiling was itself invalid on this host: a fresh process-free
observation showed a stable 8% driver/runtime floor. The corrected host-local
ceiling is 12%, still fail-closing on the observed 94% teardown residue. Never
reuse or overwrite the failed v12 root or any superseded successor root.

The authoritative v12r1 controller is remote operation
`exec-0000000000001326`; its immutable root is
`/cache/cch/dasc-qwen36-ascend-20260915/physical-cache-order-fix-v12r1`
and its owned container is
`dasc_qwen36_physical_order_fix_v12r1_20260915`. The replacement v12r1-to-v13
supervisor is `exec-0000000000001327`. Both were launched from clean commit
`181fe72`. Poll these handles; the older v12 handle is terminal-failed and
the older supervisor can never observe a v12 SUCCESS marker.

That v12r1 pair is now a closed waiting route because its 5% ceiling cannot
admit the verified 8% idle floor. Cancel only those two owned operations before
launching a v12r2 pair from the threshold-fix commit. v12r2 must use a new
immutable root and container and must retain the no-PID check, NPU4-7 lock,
post-lock recheck, and all existing mechanism gates.

When the operation becomes terminal, inspect its result and the immutable root
`/cache/cch/dasc-qwen36-ascend-20260915/physical-cache-order-fix-v12`, then run
`verify_physical_v12.py --root ...`. Only a zero controller exit, complete
artifact manifests, exact service responses, positive cache-hit delta, compact
bytes, and one aligned four-worker cohort pass the mechanism gate.

The successor formal experiment is specified in
`.agents/experiments/dasc-qwen36-formal-ab-v13.yaml`. Its resumable controller
is `run_formal_ab_v13.sh`; `--self-test` passed without starting an NPU
workload. It refuses to run before v12 verification succeeds and uses the same
NPU4-7 lock. Dense and candidate arms are TP4/HCCL and differ only by the DASC
plugin treatment. Each arm runs three fixed shared-prefix performance rounds
and three LongBench-v2 plus GSM8K quality rounds.

The single automatic v12-to-v13 handoff supervisor is remote exec operation
`exec-00000000000012c5`, launched from `run_v13_after_v12.sh`. It waits for
the v12 `SUCCESS` marker, independently reruns `verify_physical_v12.py`, and
then invokes the formal controller. Exit 75 means the NPU4-7 lock or devices
are not yet ready and is retried after 60 seconds; any other nonzero result is
fail-closed and must be inspected rather than restarted blindly.

Formal evidence is deliberately not accepted from a hand-written summary:

- `extract_formal_identity.py` derives arm identity from Docker inspect and
  rejects protected-device mappings or treatment drift.
- `capture_runtime_manifest.py` hashes the model config and weight index,
  tokenizer, image inspection, driver/CANN metadata, benchmark, evaluator, and
  datasets separately for each arm. The normalized decision requires the raw
  manifests and their hashes to match.
- `capture_prometheus_metrics.py` captures the exact prefix-cache counters.
- `verify_cache_capacity.py` reconciles live aggregate cache tokens with the
  per-group dense budget and four-worker candidate allocation evidence.
- `verify_performance_triplet.py` applies the final performance-run rules
  before an interrupted run is reused; malformed or incomplete artifacts are
  archived and regenerated.
- `verify_quality_pair.py` applies the final row-count, index, rescoring, and
  cache-hit rules before a LongBench-v2 or GSM8K run is reused. The final
  evidence additionally binds raw JSONL, response text, prompt contract,
  dataset, adapter, and underlying evaluator hashes.
- `verify_device_ownership.py` compares every process observed on physical
  NPU4-7 with the active arm's Docker PID set. The controller polls it while
  the arm is live, appends every sample to an arm-local durable JSONL history,
  and stops immediately on a foreign PID. The normalized decision rejects a
  missing history, any foreign PID, card/container drift, or a history that
  never observed an NPU worker.
- `build_formal_evidence.py` reads a fixed raw-artifact layout.
- `verify_formal_decision.py` recomputes completeness, cache-hit deltas,
  paired performance direction, quality tolerance, and the four-worker
  candidate activation gate.

Two preparation failures are retained as lessons. The first CPU-only full
test omitted the read-only model-config mount and produced two
`FileNotFoundError` failures; adding the mount yielded a clean run. The first
activation-gate patch displaced `verify_identity()`'s return block; tests
caught the `None` result before runtime and commit `5fc08a5` corrected it. A
later review also found that prefix matching would misclassify
`/dev/davinci_manager` as a compute card; commit `a7c2173` changed this to an
exact numeric-device match and added realistic auxiliary devices to the test.

The last full CPU-only workstream run passed 51 tests with 14 upstream Torch
deprecation warnings. The current branch is intentionally unpushed; pushing
requires explicit user authorization for the exact branch and payload.
