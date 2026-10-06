# Ready-before-resource checkpoint — 2026-10-06

This is a reviewed preparation/source checkpoint, not DAMP service acceptance.
Canonical repository: /opt/host/vnf/austinov/model-tuning-lab.
Branch: work/qwen36-damp-ascend-20261006.
DAMP deadline2026-10-07T08:48:03Z; portfolio cutoff2026-10-09T11:17:31Z.
No new E2E throughput/TTFT/TPOT or GSM8K/LongBench-v2 result is claimed.

## Human rule and actual readiness evidence

Prepare complete algorithm-specific packets before scarce-device admission.
Actual no-device compile/load/schema/Meta and executable CLI checks are required,
not a promise that the first real device attempt cannot reveal a new bug.
MAIN owns all launches; agents prepare source in distinct scopes.

- MA04e0 independently passed14 CPU-dispatch,11 earlier all-T and24 final-plan
  software tests, actual CLI and frozen26 runtime sources.
- MA04fd independently passed97 current software contracts:
  all-T dispatch12, continuous metadata24, CPU dispatch14, final-plan24,
  calibrated admission15 and post-reference8. Three default CLIs actually exited0:
  all-T waiting_MAIN_live_admission, CPU prepared-not-executed and final plan-only.
  AST/current source-manifest checks passed. No Torch/NPU/Docker was started.
  Historical software-v1 receipts are preserved snapshots, NOT current manifests:
  an overbroad audit first rejected their old source pins (MA04fc), then MAIN
  restricted current admission to explicit source/runtime manifests. No source
  or historical evidence was changed to turn that check green.
- The full final-plan aggregate entry point initially shadowed its immutable
  source-manifest variable with a report Path. This was fixed before device
  launch and covered by a real aggregate CLI regression, not only helper mocks.
  Final numerical192, eager/graph, full-state and per-shard evidence remain unrun.
- MAIN no-device CPU canary MA04e8 was refused by Docker: quota8 exceeded actual
  engine NCPU7. No container was created and no NPU was touched. Preserve
  /cache/cch/qwen36-damp-20261006/cpu-selector-preflight-v1/RESULT.json,
  SHA034dc921b976f4902c86c1227cb9ebde18da02ed4a0c45368401b7298e6af342.
- NEW corrected canary MA04ed actually passed import/source/default-CLI in the
  immutable image, no devices, cap4GiB/swap4GiB/quota2CPU, supported
  TORCH_DEVICE_BACKEND_AUTOLOAD=0. Container0ead4c68abac9ba00a34cb978994ecacc54923ad6e623106f760af5ace816a97
  exited0 and is retained, never restarted as fitting. Result
  /cache/cch/qwen36-damp-20261006/cpu-selector-preflight-v2/RESULT.json,
  SHAe5d21c2255e773ea53706e9d2f48485472f39d1c0d95be1aafd309e85c0c70b2.
  selector_executed=false,npu_executed=false; no fitted plans or admission exists.
- All-T future shard quotas are1 CPU each, four together4; optional selector
  quota2 makes6. Require fresh actual Docker info/cgroup/competing CPU evidence,
  not a permanent7-CPU assumption. Four8GiB caps +8GiB reserve require40GiB
  ordinary RAM; overlap with4GiB selector requires44GiB JOINT admission.
  Frozen selector thread count8 is distinct from quota2. Formal timing never
  overlaps numerical shards, fitting, builds or profiling.
- Continuous metadata packet has source-bound native mixed ALL-row convolution,
  decode-prefix/prefill-suffix and q1-continuation ABI, retained pause leases,
  generation/progress checks, actual typed live-byte interval primitives.
  It does NOT install a runtime patch or prove actual shared FA/GDN pages.
  Native _update_states cache-zero can write BEFORE _model_forward; real adapter
  must protect the shared allocation at that earlier writer, not only in the core.
  Fast selected-slot pack/unpack, live mixed/continuation/cache and graph remain open.

## Current hardware collection and successor queue

MA0455 is still the single TP4 ON-only native TRAIN collection; do not duplicate.
Exact owned containerb6e2a1510fb809d0913ee214d28cf0df238930eadd1e39189eba54b0d2f9e1f1,
physical4-7 -> logical0-3, source28 frozen. OFF36 valid outputs are reused.
MA04fe at2026-10-06T15:55:46Z observes8/36 ON completed clients, each4096 tokens;
12 requests bound/rank,3264 anchors/3072 futures/384 layer-complete events per rank,
no capture_failed event. Ordinary MemAvailable38,221,328KiB is below40GiB
four-shard admission; not proof that those successors may launch now.
Protected0-3 remain out of scope; no competing device load was started.

Dependency order after actual terminal success/release:
1. Verify actual parent RESULT/SOURCE_LOCK and native OFF/ON parity. CPU fitting
   uses NEW no-device container/output with immutable source, not the canary.
2. Run admitted four disjoint all-T actual1..16 correctness shards; overlap CPU
   fitting only with joint44GiB/CPU/resource proof, never with TP4 or formal timing.
   The argv planner alone is not an execution controller or fresh-device proof.
3. Verify all192 real calibrated plans/general SR, numerical state+output,
   prefill pack/unpack and actual shared-cache mixed/continuation lifecycle.
4. Only an instrumentation-free, numerical-pass candidate enters matched same-
   stack dense E2E screening and final repeated performance/task validation.
   No hidden persistent FP32 sidecar, fake padding or different common HBM budget.
KVBuffer FP32 parallel-fold B1/B16 correctness is the distinct next packet;
HYPIC remains a previously successful reference, not this project's new success.

## Publication boundary

Reviewed70 files from ten bounded packet directories are enumerated in
READY_SOURCE_SCOPE.json. Current manifest transitive source identities were
checked; existing raw data/binaries/large logs stay outside Git.
This checkpoint preserves previously reviewed wrapper/gate/recovery packages
and new CPU/all-T dispatch/continuous preparation. It changes no live collector,
original runtime, image, model or operator bytes.

Final-plan/calibrated-admission11 files passed current-worktree software checks
but are excluded from this publication: a legacy smoke-loader compatibility test
references an untracked older integration package (fresh-clone closure pending).
No deletion or gate relaxation hides that prerequisite. Evolving service,
prefill pack/probe, controller and other project drafts remain untracked until
MAIN full review and coherent closure. Their existence is not ready-for-service.
Prior4e8dd78c was normally pushed and remote exact-ref verified MA04a9, superseding
the older15:18Z TLS/push-failed paragraph. No force/main/amend operation is allowed.

MA0503 validates20 maintainer skills and the exact bundled skill-creator validator
reports Skill is valid. Exact70 source hashes and staged75-file scope passed.
New governance whitespace passed; the full staged check exited2 only for blank
context lines in the two retained provenance .patch files and an extra EOF blank
in frozen recovery MEMORY_BUDGET.md. These source/provenance bytes are preserved;
there is no blanket full-whitespace PASS claim. No live/NPU source was edited.
