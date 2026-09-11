# Ascend reproduction: verified lessons from sparse-prefix work

Read for model-identity drift, disposable-container startup failures, or repeated
resource blocking. These are scoped lessons, not proof the paper works on Ascend.

## Evidence boundaries
- Author DP versus exhaustive oracle passed 868 cases, zero failures:
  /cache/austinov/sparse-prefix-cpu-sRpewC/author-dp-oracle.json
  SHA256 be5528e45ca6df64dfad944aada7d9c897ecf4786a8cc728f7ef9c1bda9d8ead.
  This proves tested planner cases only, not cache restoration or model quality.
- Model config/weight identity must come from mounted files and hashes, not
  served model aliases, architecture names, directory labels or worktree names.
  Qwen3.8 weights were advertised with a Qwen3.5 service alias in old evidence.
  A user-approved model change permits a new question, never relabeling results.
- Reuse requested historical TP4 cells only after reading raw data and matching
  model, image, TP/topology, prompt, sampling, warmup and cache semantics.
  Missing concurrency/repetition cells remain missing. Do not silently rerun a
  full baseline against the user's request; explain any required additional arm.
- Per-request unique cache_salt disables reuse. A sparse-cache/no-reuse comparison
  is not evidence of incremental benefit over native caching.
- Startup success, HTTP success, natural EOS, planner correctness, paired output
  fidelity and task accuracy are separate claims. Empty dataset answers do not
  provide task-quality ground truth.

## Narrow diagnostic ladder
Use the smallest check that can falsify the current hypothesis:
host ownership -> disposable device count -> worker/model load -> request smoke
-> cache-state restoration -> paired quality -> clean performance.
Do not restart full model loading while an earlier gate still fails.

Observed outcomes in this host/image configuration:
- Docker rejected a 16-CPU request; six fit the reported seven-CPU limit.
  Query current limits; do not hardcode six as a universal requirement.
- Triton could not map npu_utils.so from noexec tmpfs. Explicit exec on disposable
  build tmpfs cleared that error. Do not make host or image source writable.
- Making the entire disposable root writable did NOT solve DCMI -8020.
- Host npu-smi showed no compute while container device_count was zero and DCMI
  reported device-used -8020. Temporarily stopping the specifically authorized
  binding container, then preserving physical4-7 device nodes with logical
  ASCEND_RT_VISIBLE_DEVICES=0,1,2,3, yielded DEVICE_COUNT4.
  This is configuration-specific evidence, not a universal mapping prescription.
- When the external container restarted, -8020/device_count0 recurred:
  /cache/austinov/sparse-prefix-smoke-RLFnK6/run.log
  SHA256 94e0f961c085f80dff9b3ed4fd525748339e0c8cb13bf6b75517c485f61e0b5e.
- Later full smoke failed at ParallelOpenMP.cpp:64, Invalid thread pool, after
  multithreaded fork. Pinned image envs.py supports spawn; commit b5ce821 selects
  it. This is an UNVERIFIED correction, not a passed four-rank model test.

## Ownership and retry decisions
- Report actual NPU processes separately from running container bindings.
  An idle utilization sample does not prove device initialization will succeed.
  Conversely, declarations alone do not prove compute occupancy when the user
  explicitly permits use based on actual processes.
- Recheck immediately before acquisition; a previous idle sample became four
  external VLLM workers on physical0-3 during this incident.
- A restarted external container is a new live state: inspect owner and current
  processes; do not reuse a past temporary-stop authorization as indefinite
  permission. Record and fulfill any agreed restoration responsibility.
- Observation timeout is not execution failure. Poll the same operation handle
  or inspect its exact container before another launch.
- On a repeated, unchanged resource blocker, retain one evidence record and one
  requested user action. Use supported wait/monitor/blocked lifecycle behavior;
  do not repeatedly ask the same question or produce commits for identical state.
  Status polling and documentation alone are not algorithmic progress.
- If independent algorithm implementation or CPU correctness work can advance
  the actual goal, do that while hardware is blocked; do not label the entire
  project blocked solely because accelerator access is unavailable.

## Delivery and handoff discipline
Keep one current-status section: scope, last accepted gate, failed gate, owned
resources, external dependencies, next executable action, and evidence paths.
Move superseded narratives under clearly historical headings rather than
accumulating contradictory current instructions. Keep transient PIDs/occupancy
out of reusable skill rules.

Before spending another substantial run, state what decision it will change.
Prefer a bounded implementation/validation stage over repeated environment
orientation. Count a paper reproduction complete only with the actual mechanism
implemented and exercised, matched performance evidence, and the declared quality
gate; never substitute smoke scripts or planner-only tests for that end state.

