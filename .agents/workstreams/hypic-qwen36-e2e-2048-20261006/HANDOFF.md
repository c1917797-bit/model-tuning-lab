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

## Current state

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
