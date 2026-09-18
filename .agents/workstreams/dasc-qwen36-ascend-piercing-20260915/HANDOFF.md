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

## 2026-09-16 v12r2 recovery result

The v12r2 service reached readiness on physical NPU4-7, but its original AWMCP
controller handle had already timed out and exited before the canary. A bounded
recovery controller acquired the same NPU4-7 lock and failed closed before any
request because `verify_device_ownership.py` used `docker top -eo pid=`, which
the host Docker/ps combination rejects. Cleanup stopped only the owned v12r2
container and retained the immutable failed root. This is a control-plane
compatibility failure, not DASC numerical or performance evidence.

The verifier now uses the portable `docker top -eo pid` form and ignores the
header during numeric PID parsing. The physical-v12 verifier and v13 handoff
also accept an explicit successor container and experiment while still binding
the result mount to the exact `--root`. The next attempt is v12r3, with a new
immutable root and container. Its controller continuously records NPU4-7
ownership from service launch through the canary. The updated complete
CPU-only workstream suite passes 52 tests, and a live host smoke check of the
corrected Docker top path succeeds.

The subsequent v12r3 service reached readiness and completed all five strict
HTTP requests with exact outputs. It also observed 4,608 prefix-cache hit
tokens, with the first long request taking about 19.99 seconds and the two
replays about 0.52 and 0.50 seconds. The mechanism gate still rejected the run:
no `evidence.jsonl` was created. Inspection proved that adding the project
source to `PYTHONPATH` did not make it discoverable by vLLM's
`vllm.general_plugins` entry-point loader. Therefore the 4,608-token hit is
ordinary vLLM prefix-cache evidence, not DASC activation evidence.

The successor controller builds the immutable plugin snapshot into a
`plugin-snapshot/site` target with the same pinned image, records the
discovered entry points, and refuses to launch the NPU service unless the exact
`dasc_vllm_ascend:register` entry is visible. A no-device smoke build with the
pinned image produced that entry successfully. The next NPU attempt must use a
new v12r4 root and container; never reuse v12r3.

## 2026-09-16 v12r4 graph-capture result

v12r4 installed and discovered the plugin and reached the real physical-cache
path on all four TP ranks. Evidence contains seven `plugin_registered`, seven
`heterogeneous_mamba_lifecycle_installed`, four
`tp_geometry_aligned`, four `worker_dispatch_verified`, one
`heterogeneous_cache_grouped`, and twelve `physical_cache_bound` events.
The aggregate page is 60,047,360 bytes for 16 attention plus 48 heterogeneous
Mamba layers. This is direct activation and allocation evidence, not a service,
performance, or accuracy pass.

Graph capture then failed on every rank in
`aclnnFusedInferAttentionScoreV3` with error 561002: the no-RoPE TND path
received unsupported head dimension 256. The owned container was stopped and
physical NPU4-7 were released. Keep the immutable v12r4 artifacts; do not retry
the same bytes.

The failure disproves the earlier statement that model-order/Mamba-first alone
restores correct dispatch. The pinned vLLM-Ascend runner picks the first inner
spec from a `UniformTypeKVCacheSpecs` group under a same-type assumption.
DASC's aggregate is intentionally mixed, so ordering cannot represent both
attention slot mapping and Mamba state lifecycle. The v12r5 hypothesis is to
preserve authoritative storage and layer order, provide an attention-first
proxy only to `may_reinitialize_input_batch`, and keep the existing
Mamba-only copy/invalidation filter. This must first pass targeted and complete
no-device tests, then one fresh NPU4-7 graph-capture attempt. Do not start v13
unless the complete physical mechanism verifier passes.

The successor adapter's focused file passes 8 tests and the complete pinned
image workstream suite passes 97 tests (16 upstream Torch/read-only-cache
warnings). The first complete-suite invocation mounted the model config at the
wrong container path and produced two expected FileNotFoundErrors; rerunning
with the exact `/cache/efim/Qwen3.6-27B/config.json` path passed. The maintainer
skill tree validator passes all 26 skills, JSON parsing and `git diff --check`
also pass. NPU4-7 were then process-free at the verified 8% idle HBM floor and
port 8030 was free, so the next action is one immutable v12r5 run.

## 2026-09-16 v12r5 first-spec hypothesis rejected

v12r5 ran once from commit `373b448` on physical NPU4-7. The adapter emitted
four `heterogeneous_input_batch_dispatch_adapted` events, proving activation
on every TP worker. Crucially, every event recorded the same attention layer as
both `storage_first` and `dispatch_first`
(`language_model.model.layers.3.self_attn.attn`). The attempted reorder was
therefore a runtime no-op.

Graph capture failed at the identical
`aclnnFusedInferAttentionScoreV3` 561002 no-RoPE TND headDim=256 gate. The
controller exited 1, the independent verifier correctly rejected the root
because `SUCCESS` and `physical-canary.json` are absent, and the exact owned
container was stopped. NPU4-7 were subsequently process-free. Evidence SHA256
is `d4927792b2fbd55a04ffd9a9c78fd152d06cfde7c52f6468bcae20dd8ee25e68`;
service log SHA256 is
`0c4c844f58c378325c82673b4c2192bf9f3336e9c046e1cc8af8f2543002218a`.

Close the first-inner-spec ordering route. The next work is source-backed
localization of every downstream consumer that assumes a
`UniformTypeKVCacheSpecs` wrapper contains one type. Do not launch another NPU
attempt until a materially different metadata or grouping invariant is proved
and covered by a bounded test.

The failed adapter was removed from the active plugin tree while its
`373b448` commit remains in history. The recovered tree passes the complete
pinned-image suite: 95 tests with 16 upstream Torch/read-only-cache warnings.

## 2026-09-16 implementation provenance

No first-party DASC repository is linked by arXiv or the paper, and exact
title/algorithm GitHub searches found no author release as of this date. The
plugin is an independent paper-derived DASC-NR/Ascend adaptation. It must not be
described as the authors' official implementation or as method-chain equivalent
while the paper's SGLang ragged flat-pack, model-load head permutation,
variable-split all-to-all TP balancing, and DASC-WR suffix refresh are absent.
The authoritative comparison is `METHOD_PARITY.md`.

## 2026-09-16 dense-control evidence recovery

The previously empty
`/cache/cch/dasc-qwen36-ascend-20260915/dense-align-prefix-control-v10`
directory did not by itself support the README's dense-control claim. The
stopped container
`dasc_qwen36_dense_align_prefix_v10_20260915` still existed and was audited
without restarting it. Container metadata proves image
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
physical NPU4-7 mapped to logical 0-3, TP4, Mamba align mode, 9 GiB manual cache,
and `FULL_DECODE_ONLY` capture sizes 1, 2, 4, 8, and 16. It exited 0 and had no
DASC repository or plugin mount.

The retained Docker log proves all five captures completed, the service became
ready, ACL graph replay occurred, and one chat-completion request returned HTTP
200. It does not contain the client response body. Therefore graph/service
success is verified, while the historical exact-`OK` output claim is not.
Recovered raw files and hashes:

- `container-inspect.recovered.txt`:
  `f7a23feab93e80d6586ff7aba19073031f92a9dcd7b746e80e4e41a5d8925162`
- `service-log.tail250.recovered.txt`:
  `c504ca2f489d2c819866af229b979bd3e72bb35dee1dc6e8ff4fb9087fbc97c1`

This closes the narrow question of whether the dense stack can capture the
five graphs. It does not prove response-content equivalence, DASC correctness,
performance, or quality.

## 2026-09-16 graph-stable workspace refactor

The v12r5 failure was narrowed beyond the rejected cache-group ordering theory.
The physical bridge dynamically replaced `self.kv_cache`, cloned/replaced GDN
metadata, and created remapped index tensors inside each model forward. Those
object and address changes are unsafe assumptions for ACL graph capture/replay,
even though eager transactional tests pass.

The first successor step now permanently binds each GDN module to one full-size,
fixed-address dense workspace tuple while the bridge and vLLM cache registry
retain the scheduler-owned compact tensors. Restore populates only the active
workspace prefix; checkpoint writes only that prefix back. The module no longer
changes cache tuple or tensor addresses per forward, including after a native
operator exception. The complete DASC plugin suite passes in the pinned v0.23.0
image: 42 tests; `git diff --check` also passes.

This is a code-level gate, not NPU graph, performance, or accuracy evidence.
The successor now wraps `NPUModelRunner._model_forward`, which is outside the
wrapped model's ACL graph. It prepares global-to-local state mappings, restores
compact persistent rows into fixed dense workspaces, calls the captured or
replayed model, then checkpoints the updated retained heads. GDN native forward
no longer owns this lifecycle. State-index tensors use fixed buffers keyed by
path/shape/dtype/device, so prefill, decode, and different graph sizes retain
separate stable addresses. A replay-style test changes scheduler block ids
between two calls and verifies unchanged workspace/index pointers plus correct
updates to the newly selected persistent rows.

The complete pinned-image suite now passes 45 tests with only the 16 known
upstream Torch/read-only-cache warnings, and `git diff --check` passes. This is
still not target-device evidence. Before an NPU launch, commit this stage and
recheck live NPU4-7 ownership, container declarations, port 8030, immutable
result-root absence, and the controller/plugin snapshot provenance.

## 2026-09-16 v12r11-v12r16 numerical localization

The head-dimension blocker was bypassed with a plugin-owned head-256 prefill
fallback. v12r11 then reached service readiness with the W64 DASC selector and
passed activation/allocation checks, but three identical long-prefix requests
produced different nonsensical continuations. That result is not performance
or quality evidence.

An exact plugin-disabled dense control, v12r13, used the same 1,938-token
prompt, system message, seed, temperature, output length, and prefix-cache
sequence. It produced `VERIFIED` three times, had
`identical_replays=true`, and observed 3,072 prefix-hit tokens. Its artifact
SHA256 is
`715aba4ddf6b9f35259034c96ea17051d66d350f20c71be83c54df48d20ce2d8`.
This excludes the base head-256 fallback and ordinary prefix cache as the
source of nondeterminism.

v12r14 and v12r15 were control-plane failures, not numerical experiments.
v12r14 exposed that the mixed attention/Mamba grouping path incorrectly
admitted only heterogeneous Mamba pages. v12r15 fixed that admission and
proved all 192 GDN cache bindings, but copied an obsolete canary script that
did not recognize the all-head diagnostic flag. Both immutable roots are
retained and must not be rerun.

v12r16 used the commit-current canary and retained all 12 local GDN heads in
all 48 layers on every TP rank. All 192 physical bindings had exact actual
bytes equal to the compact spec. The service initialized and the short response
body was `OK\n\n`, but the strict short gate was false; do not describe it as
exact. The three identical 1,938-token long-prefix requests
still diverged:

- `VERDICT: VERDICT: The user wants a summary of a response`
- `- 0 ... The "onnxr" field is not a`
- `[alright, there's no other way, this is a must]`

Prefix-cache hits increased by 4,608 tokens, so this is specifically a
cache-hit lifecycle failure. The all-head geometry removes DASC selection and
zero-filled omitted heads from the causal path. The current defect is in the
request-owned recurrent-state restore/continue bridge or its block/slot
mapping. Physical-canary SHA256 is
`9159d380fbaaf0778d7a7e82b8c6e92345f5345de9a25d842d5f537a8827fcfa`;
evidence SHA256 is
`a8e69ee0618268a9cca37a481a4fafe0cb65a9fd1495481b3c68292e74daa184`;
service-log SHA256 is
`e6e4e22c0661497fda2c5f2484c764168498149b6f0226fbd96fe58854b16ed3`.
The owned container stopped and NPU4-7 returned to the 2,868 MiB idle floor.

Do not benchmark or run E2E quality next. Instrument the first cache-hit token
boundary and compare plugin-disabled dense lifecycle with all-head bridge:
request identity, global/local block mapping, compact source row, active dense
slot, and state checksums before restore, before native recurrent execution,
and after checkpoint. Require exact first-token/logit equivalence and stable
multi-step state evolution before reintroducing pruning.

## 2026-09-16 v12r17 bridge bypass and v12r18 lifecycle correction

v12r17 kept the all-head physical layout but bypassed the request-owned bridge,
metadata remapping, and active-state workspace completely. All 192 native cache
bindings and TP geometry checks passed and no `request_active_state` event was
emitted. Nevertheless, the three identical prefix-hit replays still diverged.
Physical-canary SHA256 is
`19f8197ea40c247cc0931d3a2d3eb9b48520a6de28826dacd508cc2377df7262`;
evidence SHA256 is
`68996138c90ec276601d2b840b05fddbef632517e6bcf1ee837ec6913006a4ce`;
service-log SHA256 is
`16ab48cc1051d0c5821f0eb2dea0e2c7978e9f8b270a67d35aae49bad05f3b7f`.
This disproves the bridge as the sole cause.

The next source audit found a lower, cache-hit-specific lifecycle defect. The
worker aggregate is a mixed `UniformTypeKVCacheSpecs`, but vLLM 0.23's
`KVCacheConfig.has_mamba_layers` inspects only the outer group spec. It therefore
returned false, disabling both scheduler `_mamba_block_aligned_split` and
`needs_kv_cache_zeroing`. At the same time, scheduler config reduces the
aggregate to its first inner attention spec and accepts a full 1,536-token
prefix block. A 1,938-token unsplit prefill need not leave a valid recurrent
state at that boundary, explaining why both bridge and native controls resume
from invalid state.

The v12r18 plugin patch makes `KVCacheConfig` detect inner Mamba specs only
while DASC physical mode is enabled. It restores the native block-aligned split
and zeroing without changing upstream sources, selector geometry, or the
attention-first physical dispatch. Focused tests pass 15/15 and the plugin plus
controller suite passes 90/90 in the pinned v0.23.0 image. This is source-backed
software evidence only. Commit/push it, then run the immutable v12r18 native
all-head control once on physical NPU4-7. Do not benchmark performance or run
E2E quality until the strict replay canary passes.

## 2026-09-17 takeover-ready scheduler-chain checkpoint

The earlier property-only implementation at `a36a432` was incomplete: it
fixed worker configs but not the scheduler config after upstream first-inner
reduction. Preserve it through
`checkpoint/dasc-qwen36-property-only-v12r18-20260917`; do not execute those
bytes. The reconciled successor is
`7aa733eddbcc9e7365fe2ea861d5372ba933833c`. It keeps the a36 controller and
v12r17 evidence while adding the scheduler reducer wrapper, explicit lifecycle
marker, import-order-safe alias handling, and detached-alias failure gate.

Validation from the pinned `quay.io/ascend/vllm-ascend:v0.23.0` image:

- focused physical monkeypatch file: 17 passed;
- complete DASC plugin suite: 61 passed;
- v12r18 controller tests: 2 passed;
- Python compilation, `git diff --check`, and all 26 maintainer skills passed.

These are pinned-software results only. No new NPU numerical, performance, or
quality result exists. The previous 15/15 and 90/90 wording above describes the
property-only checkpoint and is superseded for execution by this checkpoint.

Physical NPU4-7 were actively occupied during the latest orientation. Live
device PIDs mapped through cgroups to container `vllm_main_au`. Its process
tree ran `/cache/austinov/deltalog/scripts/run_config.sh pkg_on`, serving
`/cache/austinov/Qwen3.8-27B` with TP4 on port 8251. Each card reported about
29,461 MiB HBM. The container has no owner label, so do not infer a person and
do not stop, restart, or share the workload.

The first push of the reconciled branch and recovery tag failed because the
target host could not connect to GitHub port 443 for about 130 seconds. The
worktree is clean and two commits ahead of the public branch. Retry the same
non-force push only after network reachability returns; do not amend, squash,
or recreate either commit.

While GitHub is unreachable, the offline recovery bundle is kept at
`/cache/cch/dasc-qwen36-ascend-20260915/recovery/dasc-qwen36-handoff.bundle`.
Run `git bundle verify` before using it and compare its advertised branch tip
with this handoff; regenerate it after any later local-only checkpoint.

Resume in this order:

1. verify branch `HEAD` is the reconciled commit and inspect
   `git status --short --branch`;
2. push the workstream branch plus the property-only recovery tag, then verify
   the remote refs;
3. re-orient NPU4-7, container mappings, device PIDs, HBM, port 8030, and the
   immutable v12r18 result-root absence;
4. only when the lane is genuinely free, run
   `run_v12r18_mixed_lifecycle_fix_control.py` once;
5. require the scheduler-preservation event, exact first resumed token,
   identical repeated continuations, positive prefix-hit delta, owned cleanup,
   and released resources.

A pass permits restoring the all-head bridge and then W64 pruning. A failure
closes this scheduler-awareness treatment and moves localization to the actual
checkpoint materialization boundary. It does not permit performance or quality
testing.

## 2026-09-17 publication and live-resource recheck

GitHub connectivity recovered. The workstream branch was pushed and remotely
verified at f5ada8a6d3d499a7fc433482602ee5acb07b9828. The annotated recovery tag
checkpoint/dasc-qwen36-property-only-v12r18-20260917 was also pushed and
verified at tag object 27b07e5bdeea73f77bbe58f506c4e1678bbdefcd, dereferencing to
the intentionally non-runnable property-only commit
a36a432933c8ee7c8f6f5354880cc7c0ff35423f.

Do not infer NPU availability from one process-free npu-smi sample or from
static Docker device declarations alone. The corrected PID-to-cgroup audit
mapped the live TP4 workers to container vllm_26_au on physical NPU0-3, where
each card held about 29.9-30.7 GiB HBM. Its Qwen3.8-27B service used port 8261.
Physical NPU4-7 had no device process and remained at the 2868-2869 MiB idle
floor. The earlier Qwen3.5 workers in container vllm-ascend had exited; its
current process tree contained only bash/vim. This matters because privileged
containers may expose mappings or visible-device values that do not establish
which cards their live workers actually own.

The operator additionally authorized physical NPU0-3 when they are genuinely
idle, but they were not idle at this audit. The current v12r18 controller stays
pinned to physical NPU4-7. Port 8030 was free and the actual immutable result
root
/cache/cch/dasc-qwen36-ascend-20260915/mixed-lifecycle-fix-all-heads-v12r18
was absent.

The next action remains exactly one
run_v12r18_mixed_lifecycle_fix_control.py attempt after a fresh live-process,
HBM, container-tree, port, lock, image, repository, and immutable-root
preflight. No new DASC NPU numerical, performance, or quality result was
created by this recheck.

## 2026-09-17 v12r18 result and v12r19 readiness

The single authorized v12r18 attempt ran on physical NPU4-7. Model load,
TP4 worker ownership, graph compilation/capture, API readiness, all 192 native
all-head cache bindings, and cleanup passed. The scheduler reducer emitted
`has_mamba_layers=true` and `needs_kv_cache_zeroing=true`, and the repeated
long prompt accumulated 4,608 prefix-cache-hit tokens. This proves the
configuration path and physical allocation were active.

The numerical gate still failed. The short output was
`OK, I will \"wo\" to`, and the three identical long-prefix requests produced
different nonsensical continuations. Therefore `identical_replays=false`,
`replay_exact_verified=false`, and `short_exact_ok=false`. The current
scheduler-awareness treatment is rejected. Do not benchmark it, do not run
E2E quality, and do not rerun the same bytes or immutable root.

Authoritative artifacts are under
`/cache/cch/dasc-qwen36-ascend-20260915/mixed-lifecycle-fix-all-heads-v12r18`:

- `physical-canary.json`: `e3b4825e1ae8991ae894569c7488ab92eba2612ffa9e2184e40aed87b2f230bd`;
- `evidence.jsonl`: `957ee11b0ce14214ab5c83ed37184a00a3198dbaa4b197934d62b450c1ac8b2f`;
- `service.log`: `16580897d3e3f6c7ca45e11459ee36c4eac944c40a02c9f54bc0f9e75a1f3c97`;
- `container-inspect.json`: `1947d3115455b30dcd41c0c3dc133c367d016df32c77f2798395e50c8bb93284`.

The owned container exited and physical NPU4-7 returned to the driver-only
2,867-2,871 MiB floor with no device processes. No performance or E2E quality
result was created.

The decisive observability gap is now explicit: a true lifecycle property is
only precondition evidence. v12r18 did not record whether the scheduler's
aligned-split branch, its new-block zeroing branch, or the Mamba state-copy
branch actually executed with the expected material inputs. v12r19 is prepared
as an observability-only all-head control. It adds bounded branch-local events,
does not alter scheduling or copy decisions, and uses the new immutable root
`branch-evidence-all-heads-v12r19`. Its focused pinned-image test gate passes
20/20; the full plugin plus v12r19 controller gate passes 64/64. Run it once
only after commit/push and a fresh resource/root preflight.

Interpret the v12r19 evidence before changing code again:

- missing scheduler initialization or split events means the live scheduler
  class/alias was not patched as assumed;
- a split event whose scheduled count is not changed to the required boundary
  means the restored flag is insufficient for the actual request shape;
- no nonempty zeroing event means the block pool did not materialize blocks for
  the worker zeroing path, even if the property was true;
- no heterogeneous Mamba copy event means the aggregate group still bypassed
  the state-copy lifecycle;
- if all three branches execute with expected values and outputs still diverge,
  move below configuration/lifecycle selection to physical row materialization,
  per-layer byte offsets, and the exact first resumed-token state boundary.

The post-commit preflight found a new resource state: physical NPU4-7 were
occupied by live TP workers at about 30.7 GiB HBM per card, while physical
NPU0-3 had no device process and were at the 2.869-2.872 GiB driver floor.
Because the operator explicitly authorized NPU0-3 when a live audit proves
them idle, an alternate controller entry point is prepared at
`run_v12r19_npu0_3_branch_evidence_control.py`. It changes only the physical
device tuple and immutable root/container identity; candidate bytes and canary
remain identical. Re-run its own preflight immediately before launch because
the idle observation is not a reservation.

## 2026-09-17 v12r19 one-shot readiness hardening

A final pre-NPU audit found four execution-readiness gaps and repaired them
without running the candidate:

- the earlier wrapper did not create a structured branch verdict when the
  strict numerical canary exited nonzero;
- verdict files written after base-controller cleanup were not covered by the
  final artifact hash manifest;
- a first-call-only split marker could be consumed by the 40-token short
  request and hide the later material split of the 1,938-token prefix;
- the controller checked resources before launch but did not re-attribute
  target-device PIDs to the owned container after service readiness.

The v12r19 controller now writes `branch-evidence-verdict.json` on both the
pass and numerical-failure paths, preserves the original failure, refreshes
`artifacts.sha256.json` without self-hashing, records the first split invocation
plus the first changed split, and writes
`post-readiness-ownership.json`. The ownership gate requires live processes on
all four selected physical devices and rejects any target-device PID outside
the owned container before the numerical request.

Validation in the pinned `quay.io/ascend/vllm-ascend:v0.23.0` image with the
model configuration mounted read-only passed all 160 DASC plugin and workstream
tests. The 26-skill maintainer-tree validator, Python AST parsing, and
`git diff --check` also passed. This is software and controller evidence only;
no v12r19 NPU, performance, or quality result exists yet.

The one-shot interpretation is now encoded rather than left to manual log
reading. Missing/invalid scheduler initialization, a non-material aligned
split, empty zeroing, or fewer than four worker copy PIDs each produce a
distinct decision. If all lifecycle branches pass but the numerical canary
fails, the recorded next boundary is physical row materialization, per-layer
offsets, and the exact first resumed token. Performance and E2E quality remain
forbidden until this strict all-head control passes.

## 2026-09-17 v12r19 admission race

The remote workstream and public branch were verified at
`fc02263efc9015b7aa7175f26172f04f29a3b4d5`. A fresh standalone v12r19
preflight then found physical NPU4-7 process-free at the 2,869-2,870 MiB driver
floor and passed every repository, image, port, and immutable-root gate.

Before the launch controller could admit the DASC run, an unrelated workload
started TP4 workers on the same four cards. The controller's own fail-closed
preflight rejected the launch with PIDs 31337-31340. Their parent PID 28520
mapped through `/proc/28520/cgroup` to container
`fd2be986b54d2ac96d30b5c3fbc5785ba7c1f9703d812275d0fa0d48204622b5`
(`alltoall-dedup-ep4_nk`). No DASC container or result root was created and no
foreign process was stopped.

This is `not_run/resource_race`, not a v12r19 numerical failure and not DASC
algorithm evidence. The successful part is the two-stage admission gate: it
prevented a collision despite a stale-in-seconds idle observation. The failed
assumption is that a standalone process-free sample or repository lock reserves
shared hardware; unrelated workloads need not honor that lock.

Resume only after a fresh live audit proves NPU4-7 idle. Use a new AWMCP
control-plane idempotency key because the previous launch key has a completed
admission-failure result. The immutable v12r19 experiment identity and result
root may remain unchanged only after confirming that root is still absent.
Then let the launch controller perform its own final occupancy check; do not
insert performance or E2E quality work ahead of the strict numerical canary.

## 2026-09-17 v12r19 branch evidence result

The fresh v12r19 admission succeeded on physical NPU4-7 using commit
`ced591b55a7ff1ab91892d91a59a452db8670286`. Post-readiness ownership
attributed one TP worker to each selected physical device and found no foreign
target-device PID. The service completed the canary, the owned container exited,
the controller stopped, and NPU4-7 returned to the 2,868-2,869 MiB driver-only
floor with no device processes. NPU0-3 were not touched.

The observability treatment succeeded:

- scheduler lifecycle initialization recorded all required flags;
- the aligned split materially changed the request to the 1,536-token block
  boundary;
- zeroing produced a nonempty block set;
- the Mamba copy branch executed in all four TP workers;
- all 192 native all-head cache bindings and the positive 4,608-token
  prefix-cache-hit delta were retained.

The strict numerical canary still failed. The short exact gate was false, the
three identical long-prefix replays diverged, and
`replay_exact_verified=false`. Therefore the candidate is not eligible for
performance or E2E quality testing. This result rejects the remaining
configuration/lifecycle-selection hypothesis; it does not reject DASC itself.
The next localization boundary is below lifecycle selection: physical state-row
materialization, request/global/local block and slot mapping, per-layer byte
offsets, and exact state evolution around the first resumed token.

Authoritative immutable artifacts are under
`/cache/cch/dasc-qwen36-ascend-20260915/branch-evidence-all-heads-v12r19`:

- `branch-evidence-verdict.json`:
  `5c890e85cdfa09dd8ca1fff184d6fb1e37bbb35b93a33484a1b14813cb131786`;
- `physical-canary.json`:
  `3d76f7e011f3888d85469ba2661e82767a51a16cfe3a2de8026349c4ebe0f786`;
- `post-readiness-ownership.json`:
  `c865a218bbf117ef00d3b3aee2fed66d955e91123c734460d2fceb9e1b2326e6`;
- `evidence.jsonl`:
  `b719eeb982ea72cc5a0c0e38993b2553b6fd010127e13525206a6a186b4afaa1`.

Do not rerun v12r19 or reuse its immutable root. Build the next one-variable
diagnostic around the first cache-hit resume token and retain the all-head
control until exact multi-replay equivalence passes. Only then reintroduce head
pruning and later enter matched performance and E2E quality gates.

## 2026-09-17 v12r20 state-index control prepared

Source mapping below the proven lifecycle branches found one bounded, testable
hypothesis. In v12r19 the real Mamba copy moved every layer's state from logical
block index 0 to logical block index 1, while the native GDN metadata for an
aggregate attention/Mamba group is constructed from block-table column 0. The
aggregate attention table can therefore retain the old source row even after
the Mamba lifecycle has materialized the new running-state row.

The plugin now has an explicit
`physical-cache-native-all-heads-state-index` mode. It keeps all heads, dense
state geometry, the v12r19 scheduler decisions, and the existing Mamba copy
unchanged. Its sole behavioral change is to route every known Ascend GDN state
index path from the old physical row to the copied destination row using stable
metadata buffers captured during dummy/graph execution. It emits bounded
source/destination fingerprints before copy, after copy, immediately before
the native model forward, and immediately after it. The old source row must not
change; the destination row must change on every TP worker.

The immutable controller is
`run_v12r20_state_index_control.py`, with result root
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-all-heads-v12r20` and
container `dasc_qwen36_state_index_v12r20_20260917`. The focused plugin tests
passed 27/27, the complete plugin suite passed 65/65, and the controller tests
passed 5/5 in the pinned v0.23.0 image. The safe no-model workstream run passed
101/103; the only two unavailable cases required the local model config, and
both pure resource-budget assertions passed when executed directly on the host
without exposing that config to a container. These are software gates only;
v12r20 has not run on NPU and has no performance or quality result.

At the preparation audit all eight physical NPUs were active. NPU0-3 held
VLLMWorker_TP PIDs 267654-267657 at about 28.67 GiB each. NPU4-7 held PIDs
351355-351358 at about 27.07 GiB each, attributed to foreign container
`dreamy_meitner`. Do not stop or share either workload. Run v12r20 once only
after a fresh audit proves a complete four-card lane idle, the immutable root
absent, port 8030 free, and post-readiness ownership exclusive to the DASC
container. Performance and E2E quality remain prohibited until the strict
all-head numerical canary passes.

## 2026-09-17 v12r20 terminal resource-race result

v12r20 launched once from committed head
`6fbb2f19474bb4a961f4f5a4ca498f4208cf0722` after both preflight and the
immediate prelaunch audit showed physical NPU4-7 process-free at idle HBM.
The owned service never reached readiness. During the plugin's TP alignment
collective, all workers failed HCCL initialization because NPU network socket
port 16666 was already bound.

The conflicting NPU4-7 worker PIDs were attributed through cgroups to foreign
container `alltoall-dedup-ep4_nk`
(`fd2be986b54d2ac96d30b5c3fbc5785ba7c1f9703d812275d0fa0d48204622b5`).
That container was already running with `privileged=true`, no explicit Docker
device mapping, and no visible-device declaration, so the old claim parser
could not assign it a lane. It activated TP workers during the DASC startup and
later held about 28.2 GiB on each of physical NPU4-7.

Classify v12r20 as `not_run/resource_race_before_readiness`. It emitted no
state-copy, metadata-remap, lifecycle, or numerical-canary events. Therefore
the state-index hypothesis remains untested; this is not a DASC algorithm,
numerical, performance, or quality result. The owned container exited and was
not restarted.

Immutable artifact root:
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-all-heads-v12r20`.
Key SHA256 values: service log
`da466cdf0b05c9d842cf7fb69fafcf49efd644526a9cdea64b1f469845763ae8`,
evidence
`a6c4ccf8e7ea6e367703bc11db058b8772fe24d3e268b60b69dd63b0215f7b13`,
state-index verdict
`c4629b3dd0ad3506298f89debb39254c734a73e36641daf62be310b3470ffaef`,
and prelaunch audit
`e5aeb8603bfc2749cfcc89db4f73cba990104479b21f3af59cf69e1f2782206e`.

Do not reuse the v12r20 root or idempotency key. A later v12r21-style attempt
may reuse the same one-variable code only in a new immutable root after the
entire lane is exclusive through readiness. Treat any running privileged
Ascend-capable container with unprovable device scope as a wildcard contender,
and monitor ownership continuously from final admission through readiness.
At the terminal audit, NPU0-3 and NPU4-7 both had foreign TP workers; do not
stop or share them.

## 2026-09-17 v12r21 startup guard prepared

The next controller is
`run_v12r21_startup_guard_control.py`. It preserves v12r20's all-head,
dense-geometry, state-index-only treatment and changes no DASC algorithm
variable. Its immutable root is
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-startup-guard-v12r21`;
its container name is
`dasc_qwen36_state_index_v12r21_20260917`.

The controller now blocks a running privileged container when neither explicit
Docker device mappings nor a valid `ASCEND_RT_VISIBLE_DEVICES` declaration can
prove its physical scope. Such a container is recorded as
`unknown_device_scope/wildcard_npu_contender`. After the owned container is
created, every readiness iteration also compares NPU4-7 PIDs with the owned
container process tree. A foreign activation writes
`startup-resource-race.json` and terminates only the owned launch as
`not_run/resource_race`.

The v12r21 and v12r20 controller suites passed 13/13 in the pinned
vLLM-Ascend v0.23.0 image; Python compilation and `git diff --check` passed.
A live `--preflight-only` proof exited 2 as designed: NPU4-7 had active TP
workers near 31 GiB HBM, and `Maxon4ick_torch_910_dev` plus
`alltoall-dedup-ep4_nk` were running privileged with unknown physical-device
scope. The repository was also intentionally dirty with the uncommitted
controller at that moment. No result root was created and no NPU experiment
started.

Do not run v12r21 until a committed clean-tree preflight returns `ok: true`.
Do not weaken the wildcard gate or use a different HCCL port to share cards;
exclusive NPU ownership through readiness is part of the numerical ruler.
Once admitted, v12r21 remains a single NPU numerical attempt. Performance and
E2E quality stay prohibited until the row gate and exact replay canary pass.

## 2026-09-17 v12r21 decisive row-gate hardening

A source audit against the pinned v0.23.0 Ascend GDN metadata builder found
that the original v12r20 verdict was weaker than the instrumentation. It could
accept one exact copy and one before/after boundary per TP worker even if the
other state family or one representative layer was absent. That would make a
partial trace look like a complete state-row proof.

The verdict now requires, on every one of four TP workers, both state indices
0 and 1 across the first and last representative GDN layers. The set of exact
copy keys must equal the sets of before-native and after-native boundary keys,
without duplicate-key collapse. Every worker's mapping event must cover all 48
GDN layers and contain two complete representative mappings. The existing
source-row-unchanged, destination-row-updated, and strict numerical canary
requirements remain unchanged.

The pinned v0.23.0 image, with no device mapping and no network, passed 81
plugin/controller tests. A focused metadata and controller run passed 24
tests, including graph-padded remapping of every reviewed Ascend temporal and
causal-convolution index path while preserving buffer addresses.

The current live NPU4-7 snapshot is device-process-free at about 2868-2869 MiB
HBM per card, but v12r21 is still not admitted. Running privileged container
`Maxon4ick_torch_910_dev` has no provable physical-device scope and is being
used interactively by a bash plus opencode process. The clean committed
preflight rejected it as a wildcard contender. Do not stop, share, or
allowlist it; rerun preflight only after its live claim disappears or its owner
provides an authoritative narrower device scope. No NPU numerical,
performance, or quality result was produced in this preparation turn.

## 2026-09-17 checkpoint inventory and reusable gate audit

The target model inventory was re-derived instead of copied from the paper.
`/cache/efim/Qwen3.6-27B/config.json` declares 64 hidden layers with the
repeating `linear_attention, linear_attention, linear_attention,
full_attention` pattern, which yields 48 linear-attention/GDN layers. The
pinned selector manifest independently reports `layer_count: 48`. Therefore
the controller's expected count of 48 is correct for this checkpoint even
though the paper discusses a different Qwen-GDN inventory. Future controllers
must derive this value from the exact checkpoint and cross-check the selector
manifest and live activation rather than copying a paper-level count.

The row verdict review also exposed a general false-positive pattern: checking
the sets of observed ranks, state indices, and layers independently does not
prove that every required combination exists. The hardened verdict now treats
rank, state index, and representative layer as one composite key and requires
the exact copy/before/after key sets without duplicate collapse. This rule is
now part of the maintainer tuning skill and its transformation eval.

The controller no longer trusts a hard-coded count even though 48 was correct.
Before preflight or launch it now derives the linear-attention layer IDs from
the exact checkpoint configuration, verifies the selector manifest's config
hash, count, length, and ordered layer IDs, and records both source hashes in
the state-row verdict. A mismatched or stale selector fails before accelerator
mutation. Unit tests cover both a matching inventory and a manifest from the
wrong checkpoint.

## 2026-09-17 v12r21 committed preflight result

Read-only preflight operation `exec-00000000000019e9` ran from clean pushed
commit `b66c8a4`. It first derived and printed the exact 48 GDN layer IDs from
the 64-layer checkpoint and verified both the model-config and selector
manifest hashes. Resource admission then exited 2 as designed. Physical
NPU4-7 had no device process and were at the 2868-2869 MiB idle floor, port
8030 was free, and the immutable v12r21 root was absent, but two running
privileged containers had unknown physical-device scope:
`Maxon4ick_torch_910_dev` and the restarted historical competitor
`alltoall-dedup-ep4_nk`.

The latter currently contains only `sleep infinity`, but v12r20 already
proved that the same container can receive a later worker launch without a new
Docker mapping and race HCCL startup. The former still contains an active
opencode session. Do not stop, share, or silently allowlist either container.
The preflight created no DASC container and no result directory; therefore it
is readiness evidence only, not numerical, performance, quality, or algorithm
evidence.

## 2026-09-18 operator-authorized idle coexistence

The operator subsequently and explicitly instructed this workstream to use
physical NPU4-7 while the cards are process-free and at their idle HBM floor.
The repository default remains fail-closed. v12r21 accepts only an exact-name,
per-launch `MST_DASC_ALLOW_IDLE_UNKNOWN_SCOPE` list for
`alltoall-dedup-ep4_nk` and `Maxon4ick_torch_910_dev`. The exception neither
stops nor reconfigures those containers. Their identities remain in every
preflight and startup verdict, and any NPU4-7 PID outside the owned DASC
container terminates only the owned launch as `not_run/resource_race`.

## 2026-09-18 v12r21 physical NPU4-7 result

The operator-authorized single run used commit
`680f5cb2500978662ca8212469a340b2ded86c7d` and the pinned v0.23.0 image on
physical NPU4-7. Preflight passed with no target-card processes, HBM at the
approximately 2.87 GiB idle floor, port 8030 free, and no result-root
collision. Post-readiness ownership was exact: one owned TP worker on each of
physical NPU4-7, no foreign PIDs, and no startup-resource-race artifact.

The run is a strict numerical failure, not a resource failure. Lifecycle
branch evidence passed on all four TP workers. Sixteen physical state-copy
events and sixteen before/after native-boundary pairs covered both recurrent
states and the two representative layers on all four workers; the old source
rows remained unchanged and destination rows were updated. However, all four
`gdn_running_state_indices_remapped` events recorded source and destination
indices as `[12]` for both representative layers. The attempted remap was
therefore a no-op (`12 -> 12`) even though the physical copy used source block
2 and destination block 3.

The strict replay gate failed: the three 16-token replays were non-identical,
the short exact gate failed, and the variant response was not exact. Prefix
cache hits were positive (delta 4608), activation evidence was present, and
the service returned successful HTTP responses, so none of those facts may be
reported as numerical correctness. The authoritative decision is
`running_state_index_not_changed_on_all_workers`; performance and quality
remain not run. Evidence root:
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-startup-guard-v12r21`.

Do not repeat v12r21 unchanged. The next implementation slice must prove the
request-state object used by `collect_mamba_copy_meta` is the same live object
later read through `model_runner.requests[owner]`, or carry the destination
row through an explicit runner-owned mapping. Add a fail-closed assertion that
source and destination state indices differ before launching the next NPU
run.

## 2026-09-18 v12r21 evidence correction and v12r22 preparation

The previous paragraph's `12 -> 12` diagnosis inspected the first mapping
event, which was emitted before the prefix-hit copy. The before-native
boundary events are later and authoritative for the resumed token: all four
workers recorded raw GDN metadata source `25`, remapped destination `3`,
while the exact physical copy used source manager block `2` and destination
manager block `3`. The request-state object did carry the destination
correctly.

The pinned v0.23.0 input-batch implementation explains the mismatch. The
synthetic aggregate is attention-first, so a 1536-token scheduler block is
virtually split into twelve 128-token attention-kernel blocks. The shared GDN
builder consumes that expanded block table, while recurrent state tensors and
the Mamba copy lifecycle remain indexed by unsplit manager blocks. Thus raw
metadata `25` corresponds to manager block `2`, and the earlier ordinary
metadata value `12` corresponds to manager block `1`. The plugin had been
writing GDN state to raw kernel-block rows and later copying a different,
still-zero manager row.

v12r22 normalizes every live GDN metadata id by the runner-owned
`blocks_per_kv_block` before native execution, then applies a copy
destination when present. It fails closed if the scale cannot be resolved or
is non-positive. Evidence now records raw source, normalized source,
destination, scale, and whether a copy remap is active. The verdict ignores
the earlier pre-copy identity event and requires each exact copy boundary to
match its normalized metadata source and destination. Tests cover both
ordinary `25 -> 2` normalization and resumed-copy `25 -> 2 -> 3`
normalization/remapping. The focused plugin/controller gate passed 34 tests.

Next immutable run:
`.agents/workstreams/dasc-qwen36-ascend-piercing-20260915/run_v12r22_kernel_block_normalization_control.py`;
result root
`/cache/cch/dasc-qwen36-ascend-20260915/kernel-block-normalization-v12r22`.
Do not run performance or quality until this strict numerical canary passes.

## 2026-09-18 v12r22 startup race

Commit `239c4c5` passed 189 software tests, `git diff --check`, and the
26-skill maintainer-tree validation. A fresh preflight showed physical NPU4-7
process-free at the idle HBM floor, while NPU0-3 remained occupied by an
unrelated service. v12r22 was launched with only physical NPU4-7 mapped.

The startup guard stopped the owned container before readiness when NPU4-7
reported PIDs `3194485, 3194486, 3194487, 3194495`, while Docker top reported
the owned set as `3177121, 3190947, 3190948, 3198791-3198794`. The four NPU
PIDs disappeared after the owned container stopped, so the evidence does not
yet distinguish a real concurrent claimant from a PID-attribution gap during
vLLM multiprocessing startup. The authoritative status is
`not_run/resource_race`: no numerical request, performance test, or quality
test ran. Evidence root:
`/cache/cch/dasc-qwen36-ascend-20260915/kernel-block-normalization-v12r22`.

v12r23 preserves the same algorithm and fail-closed ownership rule but records
`/proc/<pid>/status`, command line, cgroup, and executable for any unowned
target-card PID before aborting. Its immutable result root is
`/cache/cch/dasc-qwen36-ascend-20260915/kernel-block-normalization-race-guard-v12r23`.

## 2026-09-18 v12r23 attributed startup race and v12r24 preparation

v12r23 again terminated before readiness, but its enriched evidence closed the
attribution gap. Foreign host PID 3277916 was
`python3 /tmp/opencode/repro_foreach.py`, with cgroup
`/docker/321c36f70aac...`, executable
`/usr/local/python3.12.13/bin/python3.12`, and exact container identity
`Maxon4ick_torch_910_dev`. It appeared on physical NPU4. Therefore the event
was a real foreign claimant, not an owned vLLM multiprocessing PID omitted by
`docker top`. The authoritative v12r23 status remains
`not_run/resource_race`; no numerical request, performance test, or quality
test ran.

The operator explicitly authorized stopping containers that occupy physical
NPU4-7. A fresh audit found NPU4-7 process-free and NPU0-3 still occupied by
an unrelated service. The exact proven interfering container was stopped
without deletion and verified as `exited false 0`; NPU0-3 and all other
containers were left untouched. v12r24 keeps the v12r23 algorithm and strict
fail-closed gates, changes only the immutable result root and container
identity, and must be launched with only the still-running idle
`alltoall-dedup-ep4_nk` allowlisted. Result root:
`/cache/cch/dasc-qwen36-ascend-20260915/kernel-block-normalization-exclusive-v12r24`.

Before v12r24 launch, Docker container creation failed with ENOSPC despite
about 912 GiB free and 3% inode use. Kernel evidence identified the real
cause: dockerd's mount namespace had approximately 98,486 mounts against the
vendor kernel `mount-max=100000`, while the v0.23 image required about 1,514
additional mounts. Restarting Docker would risk the unrelated NPU0-3 service.
v12r24 therefore uses a fail-closed existing-container path, not a relaxed
resource gate. It accepts only exact container ID `fd2be986...`, exact pinned
image ID, a writable `/cache` bind, privileged/no-explicit-device layout,
and an exact sole `sleep infinity` process tree. The service is launched
with per-exec `ASCEND_RT_VISIBLE_DEVICES=4,5,6,7`; every startup NPU PID must
still belong to that container, and cleanup stops it. This is an experiment
harness workaround only and is not part of the DASC deployable plugin.

The existing-container workaround above was prepared and software-tested but
was not used for an NPU experiment. A competing control run and then a
treatment run repeatedly entered `alltoall-dedup-ep4_nk` and occupied all of
physical NPU4-7. The operator had explicitly authorized terminating such
occupants; their exact workload was terminated, and the container was
subsequently stopped without deletion. Stopping it released enough dockerd
mount budget for a fresh no-device v0.23 container to start successfully.
Therefore v12r24 reverted to the safer dedicated-container design with exact
physical 4-7 mappings. No shared-container mount injection, rename, or NPU
service launch occurred.

## 2026-09-18 v12r24 native field mismatch and v12r25 plan

The dedicated v12r24 launch passed physical NPU4-7 ownership and reached all
four TP workers. It then failed closed during graph capture before readiness:
the plugin requested upstream BlockTable.blocks_per_kv_block, while the pinned
Ascend v0.23 vllm_ascend.worker.block_table.BlockTable exposes
blocks_per_phys_block. The native implementation defines it as
physical_block_size divided by logical_block_size; for the aggregate 1536/128
layout this is exactly 12, matching the earlier raw-row 25 to manager-row 2
analysis. No strict numerical request, performance test, or quality test ran.
Evidence root:
/cache/cch/dasc-qwen36-ascend-20260915/kernel-block-normalization-exclusive-v12r24.

v12r25 resolves the ratio from both recognized field names and independently
from physical/logical block geometry when available. Every available source
must be positive and agree exactly; a missing, malformed, non-divisible, or
conflicting source still fails closed. Evidence records the exact resolution
sources. This is a cross-version compatibility fix in the plugin, not an
upstream framework modification. Next immutable result root:
/cache/cch/dasc-qwen36-ascend-20260915/ascend-block-scale-v12r25.

## 2026-09-18 v12r25-v12r26 result and v12r27 graph-boundary control

Commit `420c385` passed 196 software tests and fixed the native Ascend block
scale lookup. v12r25 did not cross the experiment start boundary: the
auto-restarted privileged `Maxon4ick_torch_910_dev` container triggered the
strict unknown-scope admission guard. It is `not_run/resource_race`, not DASC
numerical evidence.

Commit `0cb6f84` added only an exact-name idle-container coexistence wrapper;
live NPU4-7 PID ownership remained fail-closed. v12r26 reached readiness on
physical NPU4-7 with one owned TP worker per card and no foreign device PID.
The physical row gate passed: all four ranks, both state families, and both
representative GDN layers had exact source-to-destination copies; source rows
remained unchanged and destination rows changed after native execution. The
strict numerical gate nevertheless failed. The short output was `OK,`, and
the three deterministic long-prefix continuations were not identical. This is
an all-state integration-correctness failure. Performance and E2E quality were
not run. Immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/ascend-block-scale-idle-scope-v12r26`.

A pinned-source audit rejects splitting causal-convolution and recurrent
metadata into different row mappings. Ascend `gdn_attn_builder.py` derives both
from the same gathered Mamba block table in align mode, while `gdn.py` consumes
both against state tensors whose leading dimension is the allocated physical
cache row. The next one-variable diagnostic therefore keeps the v12r26 plugin
and physical-row mapping unchanged and changes only graph execution mode.
`run_v12r27_eager_boundary_control.py` launches with `--enforce-eager`, omits
the decode graph compilation contract, and writes a new immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-eager-boundary-v12r27`.

Interpret v12r27 narrowly. Exact eager replay would localize the remaining
defect to graph-captured metadata/state binding. Eager failure would close that
route and keep localization in physical state semantics or cache lifecycle.
Neither outcome is performance or GSM8K evidence. Do not alter pruning,
retained-head selection, cache capacity, or serving workload in this control.

## 2026-09-18 v12r27 startup race and v12r28 retry

v12r27 passed preflight from clean pushed commit `774fe05` with physical
NPU4-7 process-free at the approximately 2.87 GiB idle floor. The four owned
TP workers loaded the model and reached the final API warmup. During startup,
a new privileged wildcard container named `combine-code-read-tmp_nk`
appeared. The ownership guard stopped only the owned DASC container before
any numerical request and classified the attempt as
`not_run/resource_race`. Inspection showed that the contender contained
only `sleep infinity`; it was removed by its creator before an explicit stop
could be applied. No performance or quality test ran. The immutable v12r27
root remains evidence of the aborted attempt.

v12r28 is a resource retry only. It imports the exact v12r27 eager control and
changes only the immutable result root and owned container name. Its root is
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-eager-boundary-v12r28`.
It must still pass the same preflight and continuous ownership checks; do not
allowlist transient `combine-*` containers. Interpret its numerical result
with the same eager-vs-graph discriminator as v12r27.

## 2026-09-18 v12r28 eager result and v12r29 dense-eager control

v12r28 reached readiness on physical NPU4-7 with exact post-readiness
ownership: one owned TP worker per card and no foreign device PID. The complete
physical row gate passed on all four ranks, both state families, and both
representative GDN layers. Sixteen exact copies matched sixteen before/after
native-boundary pairs, source rows remained unchanged, destination rows
changed, and the mapping covered all 48 checkpoint-derived GDN layers.

The strict eager numerical gate failed. The short output was
`OK,\n\n!$MOKET`; the three long-prefix continuations were not identical and
were not exactly `VERIFIED`. Prefix-cache hits increased by 4608 tokens.
Therefore graph capture is not sufficient to explain the treatment failure,
but the discriminator is not yet closed because the prior exact dense control
v12r13 used graph mode rather than eager mode. Performance and E2E quality
remain prohibited. Authoritative hashes:

- `physical-canary.json`: `a4201d9b8faa1d0956e1cf545ac77943bba1b4183378867311f783bca32fa17c`
- `state-index-verdict.json`: `8e727298182db6f4185f944ab162cc67512e6bd5220153f4ff2d269154ddc8f2`
- `branch-evidence-verdict.json`: `4fc87df30e0c9f9ce33ad788d9e0aa703146e70385e26bad5b987866a9927eb6`
- `post-readiness-ownership.json`: `69a2bd13a7a9548d3a8f5e02861d614b9f3ac5c98735972d2b30c4610a06db80`
- `evidence.jsonl`: `922a4c3721c2ae92cdb423e264368a66e77918f5740f317874e9e526dd7ac62a`

v12r29 is the required matched dense eager control. It reuses the latest
resource/ownership controller, changes the plugin mode to the same
`compat-head256` dense treatment used by v12r13, keeps `--enforce-eager`, and
requires three exact stopped `VERIFIED` responses plus a positive prefix-hit
delta. DASC treatment-only allocation/row/branch verdicts are disabled while
the latest resource guards remain active. Immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/dense-eager-exact-prefix-control-v12r29`.
The pinned v0.23.0 image passed the complete 204-test DASC workstream/plugin
suite with 14 upstream deprecation warnings; JSON parsing, `git diff --check`,
and the 26-skill Maintainer Skill Tree validation also passed.

Interpretation is fail-closed: if v12r29 passes, eager mode itself is cleared
and the remaining defect stays inside DASC physical-state/cache-lifecycle
semantics. If v12r29 fails, the eager branch is inconclusive and v12r26 remains
the authoritative graph-mode DASC failure against the exact graph-mode v12r13
dense control. Neither outcome is performance or GSM8K evidence.

## 2026-09-18 v12r29 matched dense eager result

v12r29 completed successfully on physical NPU4-7 from clean pushed commit
`f2c4683`. Exact post-readiness ownership passed with one owned TP worker on
each target card and no foreign target-card PID. All three long-prefix
cache-hit replays returned exactly `VERIFIED`, used `finish_reason=stop`, had
no reasoning output, and were byte-identical. The prefix-cache-hit counter
increased by 3072 tokens. The first request took 76652.44754 ms while the two
replays took 1153.42293 ms and 1155.0572 ms; these are diagnostic latencies,
not a formal performance comparison.

This closes the eager discriminator: eager execution itself is numerically
sound under the matched dense control. Because v12r28 used the same eager
execution mode and workload but failed only with DASC all-state integration,
the remaining fault domain is DASC physical-state or cache-lifecycle semantics,
not graph capture and not eager mode. Performance and GSM8K remain prohibited.

Authoritative root and hashes:

- root: `/cache/cch/dasc-qwen36-ascend-20260915/dense-eager-exact-prefix-control-v12r29`
- `dense-eager-replay-control.json`: `e9d032771228a1fa9a178cfbe701ff7922757a0a6809f92a0ad4cf856bf1aafc`
- `post-readiness-ownership.json`: `96a5d5a3dbbf4820d7ffdc9d4f969ce35448469d8e28e947bb5aea30e3a37d57`
- `evidence.jsonl`: `95cc4f8d6e92eafc9ec07295727be7ba31860ce4d9a6df91c576f94f55dca667`
- `artifacts.sha256.json`: `f19ca1244521302f769f7b1b16b6c527a1318b6cffe9dd98500ea992798c2050`

The next bounded diagnostic is a v12r30 expansion of the exact first-resumed-
token copy/native-boundary evidence from the current first/last representative
layers to all 48 checkpoint-derived GDN layers, both state families, and all
four TP ranks. It must keep the v12r28 algorithm, mapping, workload, and eager
execution unchanged. The expected Cartesian gate is 4 ranks x 48 layers x 2
state families = 384 exact copy keys, each with exactly one before/after native
boundary pair. This is a one-off correctness diagnostic only; its host-transfer
overhead must not be reported as serving performance.

## 2026-09-18 v12r30 full-layer diagnostic preparation

v12r30 is prepared as a diagnostic-only extension of v12r28. The plugin now
accepts the fail-closed boolean environment switch
`MST_DASC_FULL_STATE_ROW_DIAGNOSTICS=1`. Without that switch, the established
first/last-layer evidence scope is unchanged. With the switch, the first
cache-hit transition records exact full-row digests for every checkpoint-
derived GDN layer and includes every layer in the state-index mapping event.
No pruning threshold, head selection, state mapping, request sequence, cache
capacity, or eager execution setting changes.

The v12r30 verifier derives the canonical 48-layer inventory from the pinned
checkpoint and selector manifest. It requires exactly 384 unique physical-copy
keys and exactly 384 matching before and after native-boundary events across
four ranks, 48 layers, and two state families. It additionally requires exact
source-to-destination copy digests, normalized metadata rows matching the copy
rows, every old source row remaining unchanged, and every destination row
changing after native execution. Numerical replay remains a separate gate.

Software evidence in the pinned v0.23.0 image:

- focused configuration, physical patch, v12r28, and v12r30 tests: 41 passed;
- complete DASC plugin/workstream suite: 212 passed;
- `git diff --check`: passed.

The first complete-suite invocation exposed a harness-only failure because
historical result roots were deliberately mounted read-only and an older test
writes a verdict beside fixture evidence. The authoritative rerun used a
container-local tmpfs results tree plus a read-only bind of only the selector
manifest; all 212 tests passed and no historical result was modified. Preserve
this pattern for future full-suite validation.

Next immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/state-index-eager-all-layers-v12r30`.
Run it only after the standard fresh physical NPU4-7, port, Docker identity,
checkpoint, selector, and root-absence preflight passes. This diagnostic is not
performance evidence; performance and GSM8K remain prohibited.

## 2026-09-18 v12r30 full-layer diagnostic result

v12r30 completed on physical NPU4-7. Its complete state-row gate passed:
four TP workers x 48 checkpoint-derived GDN layers x two state families yielded
exactly 384 unique copy keys, 384 before-native rows, and 384 after-native rows.
Every full-row copy digest matched, every old source row remained unchanged,
and native execution updated every copied destination row. Exact ownership also
passed and the owned container exited normally; NPU4-7 returned to the idle
floor.

The strict numerical gate nevertheless failed. The short result was not exact,
the third long-prefix replay diverged from the first two, and none of the long
responses returned the requested exact stopped token. Prefix reuse was real
(`prefix_cache_hit_delta=4608`), so this is a cache-hit semantic failure rather
than a missed test path. Performance and GSM8K were not run.

Authoritative root and hashes:

- root: `/cache/cch/dasc-qwen36-ascend-20260915/state-index-eager-all-layers-v12r30`
- `full-layer-state-verdict.json`: `aa6592f164d8e584bf034e66291dc4400bea933c2181ea547f6d811a4af3aec7`
- `state-index-verdict.json`: `ce2ef4c572e885972a24b6bb976190105bb8f606893e6d56d29c47f72ef41206`
- `physical-canary.json`: `f0ae4a4e3a1931b2678c682a1224da28d2e16f6502393044b05dc2927368554a`
- `evidence.jsonl`: `312856a8597f481cd70bf612a64e2bd9c892cbb325e05b24992db1920edbed43`
- `post-readiness-ownership.json`: `a314e4e9ebca4743b46ed4670bb47d6c3ff448d86be9dbc40f6f80077e8878e0`

This closes missing middle-layer copy coverage and copied-row/native-consumer
identity as explanations. Do not expand the same trace again. The remaining
fault domain is above or beside those rows: state production, aggregate cache
lifecycle, attention KV, or physical page geometry.

## 2026-09-18 v12r31 dense-page-padding identity preparation

A source audit found that v12r30 retained every local GDN head but still cleared
the original `page_size_padded`. Its all-head payload was 801792 bytes per GDN
page while the dense reservation was 1588224 bytes. Thus v12r30 was a state-
content identity control, not a physical-page identity control.

v12r31 adds the fail-closed diagnostic switch
`MST_DASC_PRESERVE_DENSE_PAGE_PADDING=1`. It is legal only with enabled
`physical-cache-native-all-heads-state-index` mode and all local heads retained.
The same eager execution, cache-hit workload, state-index normalization, and
384-key full-layer diagnostics remain active; only the dense page reservation
is restored. The verifier requires 192 unique TP-worker/layer cache-binding
rows, exact dense reservation fields, and a positive padding gap on every row.

Software evidence in the pinned v0.23.0 image:

- focused configuration, physical patch, v12r30, and v12r31 tests: 46 passed;
- complete DASC plugin/workstream suite: 219 passed;
- source was mounted read-only and historical result roots were replaced by a
  tmpfs with only immutable model-config and selector inputs bound read-only;
- `git diff --check`: passed.

Next immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-identity-v12r31`.
If its strict numerical canary passes, compact page geometry or aggregate
offsets are implicated. If it fails, close page padding and test attention-KV
or aggregate-lifecycle semantics as the next single variable. Neither branch
admits performance or GSM8K until exact repeated replay passes.

## 2026-09-18 v12r31 environment-race result and v12r32 retry

v12r31 did not reach readiness, worker initialization, plugin activation, or a
numerical request. The service process failed during Ascend
`rtGetSocVersion`/`aclInit` with `Resource_Busy`. The immutable root is
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-identity-v12r31`;
its container exited 1 without OOM. This is `not_run/resource_race`, not DASC
numerical evidence, so dense page padding remains untested.

The first live audit found a privileged Docker container with unknown device
scope actively building a CANN operator and briefly calling `torch_npu`; it
was stopped without deletion after it ceased to satisfy the operator-authorized
idle-coexistence exception. Device access still failed because a separate
containerd namespace was invisible to `docker ps`: `dias/dias-cont-1` launched
a Qwen3.5-27B vLLM service whose four workers were proven by cgroup and parent
chain on physical NPU4-7. Its environment declared all eight devices. SIGTERM
to the task and all child processes was ignored; the operator-authorized
SIGKILL stopped the task while preserving the container definition. NPU4-7
then returned to the idle floor, and the pinned v0.23.0 image successfully
allocated and read tensors on all four mapped devices.

v12r32 is an immutable retry of the exact v12r31 treatment. It adds no algorithm
or cache-layout change. Its controller additionally enumerates the `dias`
containerd namespace before launch and during every readiness poll, failing
closed if any DIAS task is RUNNING. Docker inventory alone is not sufficient
on this host. The new root is
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-identity-retry-v12r32`.
The v12r32 retry preparation passed the complete read-only pinned-image software
suite: 223 tests passed with the plugin source provided through `PYTHONPATH` and
only the immutable Qwen3.6 model config mounted from the model tree. Maintainer
Skill Tree validation passed for all 26 skills, `task.json` parsed successfully,
and `git diff --check` passed. This remains software evidence only; it does not
claim an NPU numerical, performance, or quality result.

## 2026-09-18 v12r32 external restart and v12r33 paused guard

v12r32 passed preflight with NPU4-7 at the 2868 MiB idle floor, no target-card
PIDs, no running DIAS task, no wildcard container, and port 8030 free. During
the readiness window an external actor explicitly restarted
`Maxon4ick_torch_910_dev`. Its Docker `RestartPolicy` was `no` and
`RestartCount` was zero, so this was not daemon auto-restart. The startup
ownership guard observed the exact container id and stopped only the owned DASC
service. No readiness, plugin activation, state-row event, numerical request,
performance run, or quality run was reached. Keep v12r32 classified as
`not_run/resource_race_during_startup`.

Authoritative v12r32 evidence:

- root: `/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-identity-retry-v12r32`
- operation: `exec-0000000000001d02`
- `startup-resource-race.json`: `e64c3b9eced7a175c0c5b000396de9412c39f6d70c4616551307bc440cf9be37`
- `controller-error.txt`: `482525b73d8cd6ac063820f7475da5a544c9b2456ba7c80012af0577bd3b9ca1`
- `artifacts.sha256.json`: `d7679604a540214aa7c2b81b5d8b953c34477f9fd87089037d3c59a6304545d9`

v12r33 keeps the exact v12r31/v12r32 dense-padding treatment. Its only new
variable is stronger environmental isolation: the exact foreign container id
must remain running but paused at preflight, every readiness poll,
post-readiness, and continuously during the physical canary. Any identity or
pause-state transition stops the owned service and remains resource-race
evidence. The controller restores the foreign container with `docker unpause`
in `finally`; it neither deletes nor reconfigures it. Its immutable root is
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-paused-guard-v12r33`.
Focused v12r31-v12r33 tests passed 14/14, and the complete pinned-image suite
passed 228/228.

## 2026-09-18 v12r34 NPU0-3 guarded-lane preparation

The v12r33 controller had one pre-NPU defect that its earlier mock coverage did
not expose: the base post-readiness ownership validator writes its verdict but
returns `None`, while the v12r33 wrapper attempted to mutate that return value
as a dictionary. The wrapper now reloads the written verdict when the base
validator returns `None`, rejects any other non-mapping return, and has a
regression test. Do not launch the older uncorrected v12r33 bytes.

Physical NPU4-7 are currently occupied by the live `dias-cont-1` Qwen3.5
service. Physical NPU0-3 have no device-side processes and remain at the idle
HBM floor. v12r34 therefore preserves the exact v12r31-v12r33 dense-padding
treatment and changes only the execution lane and resource-isolation policy:

- physical NPU0-3 with a distinct cooperative lock;
- a new immutable result root and owned container identity;
- the exact Maxon container must remain paused and is unpaused in `finally`;
- only the already-running `dias-cont-1` task may coexist on non-target NPU4-7;
- its namespace/task/root-PID/status identity must remain stable;
- any DIAS or other foreign PID on NPU0-3 fails closed;
- after readiness, every NPU0-3 process must belong to the owned container and
  per-card HBM growth is monitored continuously through the physical canary.

The focused v12r30-v12r34 suite passed 27/27. The complete read-only pinned
v0.23.0 image suite passed 235/235 with 14 upstream torch.jit deprecation
warnings. Source and historical artifacts remained read-only; the result tree
was a container tmpfs with only the immutable selector manifest and exact model
config mounted as inputs. Maintainer Skill Tree validation passed all 26
skills, task.json parsed, and `git diff --check` passed. Commit/push,
preflight, and the one-shot NPU run remain pending. The planned immutable root is
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-npu0-3-coexist-v12r34`.
This is still a correctness diagnostic. It cannot produce a performance or
GSM8K claim unless the strict repeated-replay gate passes first.

## 2026-09-18 v12r35 live-lane switch

After v12r34 was committed and pushed, the live resource assignment reversed:
the unchanged `dias-cont-1` task moved its four vLLM workers to physical
NPU0-3, at about 28.2 GiB process memory and 30.98 GiB HBM per card. Physical
NPU4-7 returned to the 2.869 GiB idle floor with no device-side process.
Therefore v12r34 must not launch on its now-occupied NPU0-3 lane.

v12r35 reuses the same tested target-lane coexistence controller and changes
only `NPUS`, the cooperative lock, immutable result root, and owned container
identity back to physical NPU4-7. Resource-race artifact schemas and messages
now derive their target from the recorded `physical_npus` field instead of
hard-coding NPU0-3. The exact DASC dense-padding treatment, eager mode,
full-layer state diagnostics, Maxon pause guard, DIAS stable-identity guard,
continuous target-process ownership check, and HBM-growth guard are unchanged.

The focused v12r30-v12r35 suite passed 30/30. The complete read-only pinned
v0.23.0 image suite passed 238/238 with 14 upstream torch.jit deprecation
warnings; no NPU was mapped and historical artifacts remained read-only.
Commit/push, exact live preflight, and the one-shot NPU run remain pending.
Planned immutable root:
`/cache/cch/dasc-qwen36-ascend-20260915/dense-page-padding-npu4-7-coexist-v12r35`.
