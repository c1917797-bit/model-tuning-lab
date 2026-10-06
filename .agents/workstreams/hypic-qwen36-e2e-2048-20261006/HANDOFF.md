# HYPIC Qwen3.6 TP4 2048-token E2E validation

## Objective

Complete a fresh HYPIC Paper-to-Ascend validation on physical NPU0-3 within
24 hours. The historical 1024-token quality evidence is reference-only; this
workstream owns a new 2048-token baseline and treatment.

## Frozen resources

- Branch: `work/hypic-qwen36-e2e-2048-20261006`
- Clone: `/cache/cch/model-tuning-lab-hypic-e2e-20261006`
- Artifact root: `/cache/cch/hypic-qwen36-e2e-2048-20261006`
- Physical devices: NPU0-3 only
- CPU set: 112-191
- Service port: 8223
- HCCL port range: 27000-27100
- NPU4-7 and their containers are protected.

## Commands

Static no-side-effect gate:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh --self-test
```

Resumable full controller:

```sh
bash .agents/workstreams/hypic-qwen36-e2e-2048-20261006/run_hypic_e2e_2048.sh
```

The controller validates existing units before skipping them. A completed
baseline is reusable only when baseline-contract.json matches and every run
passes its raw-artifact check. Do not delete or overwrite partial JSONL files;
incomplete indexes are the resume boundary.

## Current state — 2026-10-06 14:59 UTC

The first valid controller operation `exec-0000000000000277` is terminal with
exit code 2 (controller-status.json at 14:49:57 UTC). The strict performance
gate rejected the initial HYPIC v0.8.5 candidate after three validated
repetitions per arm, each with 40/40 successful fixed 1024-token requests.
Median TTFT P95 improved 39.40% against a 30% minimum; TPOT P95 improved only
5.90% against 10%, throughput 6.22% against 20%, and total duration 5.86%
against 15%. The raw six run hashes and precise values are in
`/cache/cch/hypic-qwen36-e2e-2048-20261006/performance-gate.json`.
The canary and worker evidence support bounded C1/C2 hot reuse and a TTFT
directional win, **not** whole-service acceptance or paper-complete HYPIC.
The fail-fast controller correctly skipped 2048-token quality; no fresh
quality claim is available. The quality context-capacity preflight below is
also unresolved. No unchanged controller retry is permitted.

The owning controller stopped its treatment service on exit. At 14:59 UTC,
both exact named experiment containers were exited, NPU0-3 had no processes,
and port 8223 was free. The exact-identity disabled-control rollback completed
at 15:04:02 UTC under AWMCP operation `exec-0000000000000452` (exit 0). The
real 32,768-token disabled request passed, its treatment event file stayed
empty, NPU0-3 and port 8223 were released, and the script removed only the
two verified exited experiment containers. The receipt is
`/cache/cch/hypic-qwen36-e2e-2048-20261006/rollback-evidence.json`;
raw canary, event, NPU and port files remain under `rollback/`. The image,
source, benchmark rows, and artifacts remain; only those two container
instances were deleted and can be rebuilt from the pinned command.

Next, preserve the rejected candidate as a partial component and profile the
Decode/service critical path before choosing one new bounded variable. The
three-run conditional Decode-wave proxy is 1270.59, 1269.73, 1269.79 s;
its median 1269.79 s exceeds both the 1147.62 s throughput-equivalent and
1170.57 s duration targets. The reproducible diagnostic is
`decode-opportunity-diagnostic.json` under the artifact root (SHA256
`8d9d6640181cdbce59bbf4ff1f50b21a540119db5482285854794f4553e51680`).
This is a launch-order, unchanged-Decode screening assumption, not a measured
critical path or proof of a kernel cause; verify with target-device profiling.
A changed service max-model-len
for 2048-token quality requires a new matching baseline and explicit user
choice; do not reuse the 40960-context performance denominator as its quality
baseline. Git is local-only ahead of origin because secure HTTPS credentials
are unavailable on this host; keep all commits and raw evidence, and push only
after authentication is restored without exposing tokens.

## Execution log (historical; superseded by current state above)

Running on chicaihong01 through AWMCP direct peer
lgw_a6109c51076a4a2c9d2674ca5a8704a0. Active exec operation:
exec-0000000000000277. The owning controller PID was 1219649 at launch.
Poll that exact operation and controller-status.json; do not start a second
controller while it remains live. Goal deadline is 2026-10-07 11:39:37 UTC;
the timeout wrapper stops the controller about 15 minutes earlier and its
EXIT trap stops its owned container.

The baseline contract was frozen at
219e766d817442471b160598167bcca71191a62399706cf96558921beb147621
for physical NPU0-3 and the 2048-token quality ruler. At 2026-10-06
12:21 UTC both real-weight Canaries passed. They used identical 32,768-token
prompt hashes and returned the same full response with answer ZEBRA-41729.
The canary-gate.json SHA256 is
e539f53b309fd3ec691877d85c5ca13472d140e1579cbe142670c167721850f3.
The disabled-control event file is empty (SHA256
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855);
the enabled event file SHA256 is
2c350a2c58e5f5d6fc87250fcd7e2d81e90f5e100eca4b85da3fbe75569a2bca.
The enabled Canary emitted plugin activation in seven service processes and
an independent segment reuse event. Raw event files are under the artifact
root as no-cache/canary.hypic-evidence.jsonl and
hypic-only/canary.hypic-evidence.jsonl. The current phase is authoritative
only when read from controller-status.json.

At 2026-10-06 12:51 UTC, baseline performance run1 completed with 40/40
successful 1024-token fixed-output requests and no failures. Its JSON SHA256
is 0a3c1740902d769de0240b909423c3b4655b8e334499bfd08d70b49c8c5d5bac.
Run1 TTFT P95 was 92,633.55 ms; TPOT P95 457.29 ms; output throughput
28.94 token/s; benchmark duration 1,415.47 s. This is one measured
repetition, not the three-run baseline denominator. Controller moved to
baseline performance run2 immediately afterward.

At 2026-10-06 13:01 UTC, commit `4387542` was pushed on the workstream
branch. The E2E performance gate now validates all 40 measured request rows,
both warmups, the exact protocol, fixed output lengths, and summary arithmetic
before accepting raw JSON or reusing a run on a future resume. The real run1
passed this validator; a deliberately corrupted in-memory request was rejected.
The running shell controller was not restarted for this code change, so its
already-loaded per-run function is the earlier version; its later on-disk
performance gate will execute the strengthened validator before quality work.
Future controller starts use the strengthened per-run reuse check as well.

At 2026-10-06 13:14 UTC, baseline performance run2 completed and passed the
strengthened validator: 40/40 successful, no failures, every measured request
finished at exactly 1024 output tokens, and the two warmups and protocol matched.
Raw JSON SHA256:
`67bd0b74ee8605e4f5502498ab385d55009cd9581b115bef25f3b700b9120493`.
Run2 TTFT P95 was 81,137.27 ms; TPOT P95 447.08 ms; output throughput
29.74 token/s; benchmark duration 1,377.15 s. These remain individual
repetitions, not the formal three-run denominator. The controller advanced to
baseline performance run3 without restarting the service.

At 2026-10-06 13:37 UTC, baseline performance run3 completed and passed the
strengthened 40-request validator. Its raw JSON SHA256 is
`46e63bc7c3e4b156483a86eedfb0a42a05f606c120ade1516cf91dfd40e1c3a8`.
All three baseline runs were frozen in `baseline-registry.json` under the
experiment artifact root; registry SHA256 at first freeze was
`898f50322900fd24cd0010408824b5f7e6d3ba925eebf4402d7f039105672cd0`.
A second registry invocation returned `MATCH`. Median-of-three baseline values:
TTFT P95 81,137.27 ms, TPOT P95 447.08 ms, output throughput 29.74 token/s,
benchmark duration 1,377.15 s. This is now the formal same-environment
performance denominator for treatment and later candidate iterations; do not
repeat it without fingerprint, raw hash, or live comparability drift.
The controller then stopped the baseline and began starting the treatment
container on the same physical NPU0-3 lane. At 13:40 UTC Docker reported the
expected image, CPU set 112-191, and `/dev/davinci0`–`3` mappings; NPU workers
had not yet appeared, so service readiness remained unproven at that instant.

At 2026-10-06 14:06 UTC, HYPIC treatment performance run1 completed and the
request-level validator accepted all 40 measured 1024-token outputs, both
warmups, exact protocol, and worker hot-path evidence. The raw JSON SHA256 is
`942dc0acf3c83787bc70394c98cd607deb0213412083c798e7bd2f1aafdbb678`.
Run1 TTFT P95 was 51,456.74 ms; TPOT P95 420.43 ms; output throughput
31.42 token/s; duration 1,303.60 s. This is only one treatment repetition;
the pre-registered performance gate uses medians of all three treatment and
baseline runs, so no pass/fail conclusion is yet valid. The same controller
continued into treatment run2 without restarting the service.

At 2026-10-06 14:28 UTC, treatment performance run2 completed and the same
request-level validator accepted 40/40 fixed-output requests and both
warmups. Raw JSON SHA256:
`f2c9df36f23708984645187ea3d354fe2f8c15075dec2ac0d0a43d567e1d8c6e`.
Run2 TTFT P95 was 49,153.90 ms; TPOT P95 420.70 ms; throughput 31.59
token/s; duration 1,296.49 s. These are two of three treatment repetitions,
not a performance-gate verdict. Controller moved into run3 without restarting
the service.

Run1 diagnostic opportunity bound (not a gate decision): subtracting each
request's TTFT from its duration and summing the longest remaining duration
in each of the three measured waves yields 1,270.59 s for treatment run1.
If decode-wave work were unchanged, even zero additional TTFT would not reach
the frozen baseline median's +20% throughput target (1,147.62 s) or -15%
duration target (1,170.57 s). Thus a proposed replay/prefill-only retune has
no plausible E2E opportunity bound under this conditional model. Recompute
after all three treatment runs; profile the decode/service critical path
before selecting the required measured optimization iteration. Do not change
the registered A/B gate or claim impossibility from this one-run estimate.

The final independent 18-unit auditor now recomputes both arms' raw response
SHA256 values, validates per-sample completion-token limits and finish reasons,
reconciles accuracy/token/reason totals, and rejects cross-arm quality protocol
drift. Syntax and the 29-skill maintainer validation passed. It also passed a
regression audit against the separate completed 2026-09-06 1024-token formal
evidence (`audit-regression-formal-1024.json` in this experiment's artifact
root); the incomplete 2026-09-05 corpus correctly failed. These regression
runs do not replace this experiment's pending 2048-token audit.

2048-token quality preflight found a context-capacity blocker before starting
quality traffic. The completed historical formal suite used the same dataset
SHA256 `cdaa9e98deaefbba86f5eadeb287dd2ae90ed8f33313587dc547218b770fa39a`
and evaluator SHA256 `9c8cf4204964220acd31adc8a3f73332374f123e1b8681a522b33eff33504cc0`.
Its LongBench-v2 sample index 48 (`6719b96abb02136c067d4358`) used 39,642
prompt tokens. Requested 2,048 output tokens would total 41,690, exceeding
this experiment's `--max-model-len 40960` by 730. The pinned vLLM source
`vllm/renderers/params.py` validates `max_input_tokens=max_total_tokens-
max_output_tokens` and rejects overlength prompts before the later
`get_max_tokens()` clamp in the chat serving path. This is a source-backed
preflight warning based on historical tokenization, not yet a current-run
HTTP observation. Do not truncate/skip the sample or silently lower its output
cap while claiming the full 2048-token ruler. If the three-run performance
gate passes, the next quality service must provide at least 41,690 context
tokens and use a newly frozen, paired baseline/treatment environment identity;
the existing 40,960 performance baseline cannot be represented as matching
that changed service configuration. If the performance gate fails, preserve
its terminal evidence before selecting a new measured candidate and quality
environment. Keep the active controller untouched while performance runs.

Git checkpoint `949fa6a` is local only: one attempted HTTPS push failed with
`could not read Username for 'https://github.com'`. The branch was one commit
ahead of origin and no credential helper or SSH agent was available. Do not
put tokens in Git or chat; keep device work and local evidence safe, then push
the accumulated commits once secure host authentication is restored.

Baseline artifact registry was added while this controller was already live.
Its running shell will not execute the newly inserted registry commands. After
baseline performance run3 completes, run
`python3 .agents/workstreams/hypic-qwen36-e2e-2048-20261006/baseline_registry.py performance --root /cache/cch/hypic-qwen36-e2e-2048-20261006`
to freeze all three validated raw performance hashes; this performance step
has now been done and independently matched. Once all six baseline
quality summaries and JSONL files complete, run the same command with `quality`
instead of `performance`. Both commands fail closed on missing, invalid, or
changed raw evidence. Future controller starts perform these steps automatically,
and the independent closure audit requires both registry sections.

An initial controller operation, exec-0000000000000263, was stopped before
service readiness after an escaped E2E_GATES variable entered the historical
sequence. It produced no performance or quality result. Its exit code was
124; owned baseline container exited and NPU0-3 were verified process-free.
Commit 9d9acf2 corrected the variable; the active operation above is the
first valid measurement attempt. Do not count the stopped attempt as an
algorithm failure or as a reusable baseline.

The supported vLLM general-plugin entry point is the removable runtime
delivery path; see DELIVERY.md. Final independent audit, rollback exercise,
resource-release proof, optimization iteration, terminal classification and
report are still pending.

After the controller finishes, run the historical 18-unit audit produced by
the wrapper, then record the measured optimization iteration and execute the
post-treatment disabled-control rollback. Store optimization-iteration.json
and rollback-evidence.json plus their raw files under the artifact root.
Use verify_hypic_rollback.py from this workstream with --root pointing at the
artifact root and --canary-script pointing at the historical workstream's
hypic_semantic_canary.py. Run it only after the controller operation is
terminal. The script refuses to proceed while controller.lock is held, checks
the exact two owned container identities and one-switch equivalence, executes
a real disabled request, stops the baseline, and records NPU/port release.
Pass --remove-owned-containers only after all experiment arms are terminal
and their evidence is preserved; it removes only those two named containers.
Finally run audit_e2e_closure.py from this workstream with root
/cache/cch/hypic-qwen36-e2e-2048-20261006 and output
/cache/cch/hypic-qwen36-e2e-2048-20261006/e2e-closure-audit.json.

The closure audit currently reports missing performance, quality, iteration,
and rollback evidence, as expected while the first performance run is live.
Do not treat this partial audit as a failure of the paper technique.
