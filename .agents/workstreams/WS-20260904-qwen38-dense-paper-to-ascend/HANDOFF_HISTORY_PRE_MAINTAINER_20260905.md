# Workstream Handoff — WS-20260904-qwen38-dense-paper-to-ascend

Read `COMPLETION_AUDIT.md` first for the requirement-by-requirement
distinction between reusable tooling and real experiment completion.

## Active: employee historical-ruler HYPIC reproduction

The operator reopened the Hypic line after identifying that the completed
experiment used the wrong denominator for comparison with the employee
measurements. The old PDC-only versus PDC+Hypic evidence remains valid and
immutable for that question, but it is not the employee experiment.

The active experiment runs Qwen3.6-27B TP4 on host NPU0-3 and CPU112-191.
Both arms disable native prefix caching. The only algorithm switch is
`VLLM_ASCEND_HYPIC_ENABLE`: arm G1 is no-cache/Hypic-off and arm G3 is
HYPIC-only. Performance uses the supplied historical ruler exactly:
32768 input tokens, 16384 shared-prefix tokens, 1024 fixed output tokens,
40 requests, concurrency 16, two warmups and three repetitions. Each arm is
then stopped and restarted before three LongBench-v2 and three GSM8K quality
runs. CEval remains excluded by operator decision. NIAH+ is not substituted
because its authoritative files did not exist on the source host.

The controller owns only these exact containers:

- `qwen36_hypic_nocache_baseline_npu0_3`
- `qwen36_hypic_only_npu0_3`

The workstream is paused by operator request. Controller operation
`exec-00000000000005b0` is terminal after its exact controller process was
sent SIGTERM at 2026-09-05T18:16:20Z. Both exact containers passed image,
CPU-set, host-device and HYPIC-switch inspection before the baseline was
started. Superseded operation
`exec-0000000000000505` was deliberately stopped before any benchmark
request: a post-launch audit found that its NPU-empty parser selected the
separator column instead of the process-id column. The cleanup trap stopped
only the exact baseline container and NPU0-3 were verified empty; the parser
was corrected and the full no-side-effect self-test passed before operation
`exec-000000000000050d` launched.

Operation `exec-000000000000050d` completed with exit 2 at
2026-09-05T16:57:49Z after the restarted baseline service had reached
`Application startup complete`, but before the first quality request. The
generated quality CLI contained eleven literal `+` arguments where Bash
continuation backslashes were intended, so `hypic_quality_eval.py` rejected
the command during argument parsing. The same generation defect was also
repaired in the not-yet-reached final SHA256 command. No quality score was
emitted, and cleanup stopped only the exact baseline container.

After repair, `bash -n`, a literal-plus regression scan, static input
hashes, the no-side-effect controller self-test and `git diff --check` all
passed. NPU0-3 were empty, the baseline container was exited and the treatment
container remained created/unstarted. Operation `exec-0000000000000562`
then resumed; it verifies and skips all three completed baseline performance
artifacts before restarting the baseline quality phase.

Live verification at 2026-09-05T17:11:43Z: operation
`exec-0000000000000562` was running, the isolated baseline quality service
had reached `Application startup complete`, and LongBench-v2 repetition 1
had queued the complete 127-sample dataset with concurrency 32. The evaluator
argv contained the intended dataset, data path, model, output directory,
run id, seed, timeout and retry values and no stray arguments. Its atomic
checkpoint interval is 20 completed samples; no checkpoint, summary or
failure had yet been emitted at this early observation.

At 2026-09-05T17:21:30Z the first atomic LongBench-v2 checkpoint was
independently parsed: 20/127 rows were present, all 20 requests were
successful, none failed, 14 scored correct, and all 20 ended with `stop`.
The service-side success counter had already advanced beyond the checkpoint,
so the same evaluator and controller remain live and continue the queue.

At 2026-09-05T17:30:11Z the second atomic checkpoint independently validated
40/127 rows, all request-successful, zero failed and 22 correct. Finish
reasons were 32 `stop` and 8 `length`. The same controller and evaluator
remain live; this is progress evidence, not a completed run summary.

At 2026-09-05T17:41:48Z the third atomic checkpoint independently validated
60/127 rows, all request-successful, zero failed and 29 correct. Finish
reasons were 40 `stop` and 20 `length`. The same operation continues;
completion still requires the controller-generated 127/127 summary.

At 2026-09-05T17:51:07Z the fourth atomic checkpoint independently validated
80/127 rows, all request-successful, zero failed and 37 correct. Finish
reasons were 47 `stop` and 33 `length`. The original evaluator and
operation continue without retry or parameter change.

At 2026-09-05T18:02:15Z the fifth atomic checkpoint independently validated
100/127 rows, all request-successful, zero failed and 44 correct. Finish
reasons were 58 `stop` and 42 `length`. The controller remains on the original
evaluator process and operation. A latent verifier mismatch was also corrected
in the on-disk recovery script: the evaluator summary emits `requests`, not
`total`. The already-running shell parsed the old verifier at startup, so it is
expected to stop safely after this run writes its complete summary; resume only
after independently validating 127/127, using the corrected script so run1 is
skipped rather than repeated.

At 2026-09-05T18:10:11Z baseline LongBench-v2 run1 completed with 127/127
successful requests, zero failures, 57 correct and 44.881890% accuracy. Finish
reasons were 75 `stop` and 52 `length`; all 127 response hashes were unique.
An independent audit parsed all details, matched the details SHA256
`bae9efdf3193861066b8bff5e0ccabefcc8a4945a37defaf2ddfb0e1b1c36853`
to the summary, and confirmed its counts and score. As predicted, operation
`exec-0000000000000562` then exited 1 because its in-memory verifier still
expected `total`. Cleanup stopped only the exact baseline container and all
four owned device nodes were empty. The corrected no-side-effect self-test
passed, and operation `exec-00000000000005b0` resumed at 18:11Z. It accepts
and skips run1, starts only the exact baseline container and proceeds to
LongBench-v2 run2.

At operator request the resumed operation was paused while that isolated
baseline service was still initializing for run2. Its EXIT cleanup stopped
only `qwen36_hypic_nocache_baseline_npu0_3`; the treatment container remains
created and was never started. No controller or evaluator process remains,
port 8223 has no listener, all NPU0-3 device nodes have no users, and no
LongBench-v2 run2 artifact exists. All validated run1 and performance files
are preserved. The `hypic-historical-reproduction` heartbeat is also paused,
so it cannot restart the workload. To resume exactly from the next incomplete
unit:

```bash
cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh --self-test
bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh
```

The controller will verify and skip the three baseline performance artifacts
and LongBench-v2 run1, then restart at LongBench-v2 run2. Do not launch the
last command until the operator explicitly resumes the workstream.

Baseline performance repetition 1 completed at 2026-09-05T16:05:21Z and
passed the controller's strict artifact gate: 40/40 requests succeeded, all
finished by length, all produced the requested 1024 tokens, and the aggregate
output count was 40960. Its metrics are 1407.618124 s benchmark duration,
48417.823470 ms mean TTFT, 415.443010 ms weighted TPOT, and 29.098801 output
tokens/s.

Baseline performance repetition 2 completed at 2026-09-05T16:28:40Z and
passed the same strict gate: 40/40 requests succeeded, all 40 finish reasons
were `length`, output was 40960/40960 tokens, and fixed-output verification
was true. Its metrics are 1378.745924 s benchmark duration, 42207.405621 ms
mean TTFT, 410.681258 ms weighted TPOT, and 29.708157 output tokens/s. The
controller then advanced automatically to baseline repetition 3.

Baseline performance repetition 3 completed at 2026-09-05T16:51:54Z and
passed the same strict gate. Its metrics are 1373.611011 s benchmark
duration, 41949.867842 ms mean TTFT, 409.593527 ms weighted TPOT, and
29.819214 output tokens/s. Across the three validated baseline repetitions,
the means are 1386.658353 s duration, 44191.698977 ms TTFT, 411.905932 ms
weighted TPOT, and 29.542057 output tokens/s. The controller then stopped and
began restarting the baseline service before quality collection, as required
by the lifecycle contract.

It uses port 8223 and output root
`/cache/cch/hypic-qwen36-historical-reproduction-20260905`. It never starts
both arms together, validates the exact host device mapping before use, and
stops only its current exact container on an error. NPU4-7 and their workload
remain forbidden.

Validation and launch:

    cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
    bash -n .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh
    python3 -m py_compile .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_hypic_historical_reproduction.py
    python3 -m json.tool .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic-historical-reproduction-contract.json >/dev/null
    bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh --self-test
    bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_historical_reproduction.sh

The last command is resumable: completed, fully validated run artifacts are
skipped; an invalid summary is archived with a timestamp before retry. Monitor
`controller-status.json` and `controller.log` in the output root. Final
results are rendered to `historical-reproduction-summary.json` and
`HISTORICAL_REPRODUCTION_REPORT.md`.

This is a workload reproduction on the operator-selected Qwen3.6-27B TP4
target. The employee result used Qwen3.5-27B TP2, so identical absolute
latency/throughput is not a valid completion requirement. The final report
must state whether the four performance directions reproduce and show both
sets of exact deltas.

## Completed Hypic v0.8.5 piercing on Qwen3.6-27B

This is an independent experiment inside the historical Paper-to-Ascend
workstream. Do not reinterpret the older Dk64 decision below as the Hypic
decision.

Current state (2026-09-05): the formal PDC-only and PDC+Hypic performance
arms, all three quality repetitions per available dataset and arm, both active
semantic canaries, both rank0 native profiles and the final strict evidence
audit are complete. Controller operation `exec-00000000000004c6` exited zero
at 12:57:03Z. All four exact Hypic experiment containers are exited and no
owned controller, evaluator, benchmark or profiler process remains. Profile
clones used the same image, effective argv, mounts, host NPU0-3 devices,
CPU112-191 and HYPIC switch as their source; their only environment delta was
`PROFILING_MODE=dynamic`. NPU4-7 is externally owned and forbidden: do not
enter, stop, restart, or otherwise modify its workload. Never run two Hypic
experiment containers together.

Formal 32768-input/1024-output, 40-request, concurrency-16 result:

- PDC-only: 1371.8533 s, 29.8574 tok/s, mean TTFT 50346.6553 ms,
  weighted TPOT 401.7438 ms.
- PDC+Hypic: 1357.6341 s, 30.1701 tok/s, mean TTFT 41843.4805 ms,
  weighted TPOT 401.4442 ms.
- Treatment delta: duration 1.0365% better, throughput 1.0473% better,
  TTFT 16.8893% better, TPOT 0.0746% better/effectively flat.

The intended C1/C2 hot path activated, including materialization,
PDC+Hypic combined hits and complete hybrid repair. Full coexistence is not
verified: `mixed_decode_latency_protection` and
`mixed_decode_grouped_reclaim` signals are missing. Paper C3 distributed
scatter/transfer is outside this single-instance implementation. The final
decision therefore rejects adoption of this configuration; it is not
deployable, paper-complete, or proven accuracy-lossless.

Previous real practice is context, not a same-ruler A/B. It used
Qwen3.5-27B, TP2 and Hypic-only versus prefix-cache-disabled baseline; the
reported deltas were TTFT -46.6%, TPOT -18.4%, throughput +38.5% and batch
duration -27.8%. Current Qwen3.6 uses TP4 and PDC+Hypic versus PDC-only.
Compare relative deltas only; absolute latencies and scores are not
interchangeable.

The user-supplied source (SHA256
`c07f0c5b5193377a6ad11d4519a3caf5390d3b3acece9e6e5c50a9ba3ee84504`)
reported these absolute prior values: TTFT 49389.7 -> 26395.3 ms, TPOT
89.87 -> 73.30 ms, output throughput 102.27 -> 141.63 tok/s and batch
duration 400.5 -> 289.2 s. Its reported three-run quality comparison was
NIAH+ 92.50% -> 92.50%, LongBench-v2 54.33% -> 55.38%, GSM8K 98.67% ->
98.50% and CEval 32.47% -> 32.59%. These numbers are preserved as external
reported evidence in `hypic-previous-practice-reference.json`; they were not
regenerated on the current checkpoint and must not be pooled with the current
Qwen3.6 scores.

Primary records:

- `experiment-hypic-qwen36.json`
- `evidence-hypic-qwen36.json`
- `decision-hypic-qwen36.json`
- `hypic-previous-practice-reference.json`
- `hypic-current-vs-previous-comparison.json`
- final strict audit:
  `/cache/cch/hypic-qwen36-piercing-20260904/final-evidence-audit.json`
  (SHA256 `078d0626afe615debb5eae829b754c4c30844740dad667155f5a81bfce20bf1c`)
- baseline artifact:
  `/cache/cch/hypic-qwen36-piercing-20260904/pdc-baseline/native_prefix_baseline.run2.json`
  (SHA256 `98ad182273fb0affe2ae88fcbbfc4e0ac4659af6e8f0a626922ae335cb756adc`)
- treatment artifact:
  `/cache/cch/hypic-qwen36-piercing-20260904/pdc-hypic/pdc_hypic_treatment.run1.json`
  (SHA256 `aa2420bed5712813ddfff6744fb5c870deaf56f135a2ffd6b3bd35886ebe9b61`)

Quality is deliberately separate from the native-position active canary.
LongBench-v2 and GSM8K use the exact delivered prompts/postprocessors with
temperature 0, seed 0, thinking disabled, EOS honored and three repetitions
per arm. CEval is excluded by operator decision. NIAH+ is blocked because the
authoritative expected NeedleBench data files were not delivered; do not
synthesize or substitute them. Generic quality requests do not carry PIC
metadata and therefore test off-path quality regression, not active Hypic
correctness. The active semantic canary warms one public segment at position
zero and reuses it at a relocated position, with the exact prompt and hashes
preserved by `hypic_semantic_canary.py`.
Both active canaries passed and returned `ZEBRA-41729`. The baseline artifact
SHA256 is
`9193e45cf414bcb380676bdc872b0e59063166e90e6fcff52a73d478c59e3cbc`;
the treatment artifact SHA256 is
`d3e7128978a887a75cd376e087fbbd8fbcb94cfb8813f736fd8f6513e3e50b66`.
Their 32768-token prompt, relocated public segment and response-text SHA256
values are identical.

PDC-baseline three-run quality is complete with zero failed requests:

- LongBench-v2: 44.094488%, 44.881890%, 46.456693%; mean 45.144357%,
  population standard deviation 0.982062pp, range 2.362205pp.
- GSM8K: 96.209249%, 96.057619%, 96.512509%; mean 96.259793%,
  population standard deviation 0.189116pp, range 0.454890pp.

PDC+Hypic LongBench-v2 completed three 127/127 zero-failure runs at
48.031496%, 44.094488%, and 44.881890%. Run1 details and summary SHA256 are
`4fa3bd52a3767a713688c12c1205a34972f2d4b33444cbc941e0ba36ab4cb454`
and `f6b05215981c3bfd1a5f6f61cbc00d09d66a1e6ce32cef102256874b9e5e9cfc`.
Run2 details and summary SHA256 are
`dca7acb5b93d772a5bd9a3cf8e85ecd487a8a5ce4087df59bd0a166cbafb1971`,
and `c611b31a890119f2089a0104e6fbfe8d275272d84c5875e1662e9cbe1d9b6b7c`.
Run3 details and summary SHA256 are
`08cae3155c1bf19dcbadf69e9396e8ab9c4d9058bff54e02474e27cbf255a841`
and `c5c8391d0da62ed32a10da494f14e0e27cf93e8154da0d59eae219873dbb011d`.
The treatment mean is 45.669291%, population standard deviation 1.700982pp,
and range 3.937008pp. Its +0.524934pp mean delta is only 22.2% of the
baseline three-run range; matching-run deltas are +3.937008pp, -0.787402pp,
and -1.574803pp. This is noise-compatible, not a demonstrated quality gain.

PDC+Hypic GSM8K run1 completed 1319/1319 with zero failures, 1271 correct and
96.360879% accuracy. Its details and summary SHA256 are
`8beba588a38cb9c3d721015c28ba4b1a19978479721ee4404406acea9dee2223`
and `19458d4064d49a113c13932397c60248c55017061cc207ebe8a63be3b6412494`.
Run2 also completed 1319/1319 with zero failures, 1267 correct and
96.057619% accuracy. Its details and summary SHA256 are
`588af4ca94f2798525abe594c5d2417158e0133574245ac4f7fa8cf6c833011d`
and `6c956557c5e67fd9086aecf8fca6340529f1b3a76f4d1ba9e6c534abdeceba07`.
Run3 completed 1319/1319 with zero failures, 1264 correct and 95.830174%
accuracy. Its details and summary SHA256 are
`86c05189a09e5d121f1a4d76a967247a6e4b1511e2aa88c6a33d6158b9203c7f`
and `920634e74427174a552fd8cbf89ebb31328539b4fda2062bc6919af0062554cc`.
The treatment mean is 96.082891%, population standard deviation 0.217395pp
and range 0.530705pp. It is -0.176902pp versus the baseline mean, within the
baseline 0.454890pp run range; matching-run deltas are +0.151630pp,
0.000000pp and -0.682335pp. This is noise-compatible aggregate evidence,
but the run3 excursion and missing NIAH+ forbid an accuracy-lossless claim.

The verified PDC-only rank0 native profile manifest SHA256 is
`f1ec0d5d7a8257f8e7033e61233edc1975ac5a7d7cc47a0312f641232c79aa5b`;
profiler/workload both exited zero and 228 non-empty payload files totaling
175150491 bytes were preserved. The verified treatment manifest SHA256 is
`3adbf72f2da13a25d37796b30e873abb46e5d79503dac89624bb62a0142623f6`;
the profiler exited zero, all 4 fixed-output traffic requests succeeded, and
234 non-empty payload files totaling 184536157 bytes were preserved. Its raw
benchmark exit remains 1 because coexistence acceptance is false. The
capture-stimulus gate is deliberately separate and does not turn those missing
algorithm signals into a pass.

Evidence integrity is checked by `verify_hypic_evidence.py` (SHA256
`b0953f455877e91f0a4117eb3ce30dbf32faa4e91fcef1a6fb0dd8c6be3d813d`).
After all producers stopped, runtime-event SHA256 was frozen as
`32f2135dd2099ef87847d8cc7cad3fbee0e263628e727fbc390eb15935b18e2b`.
The strict audit ran without `--allow-volatile` and passed: 37 inventory
files, 228 baseline profile payloads, 234 treatment profile payloads, zero
errors and no volatile evidence.

Exact recovery/resume commands (run from the worktree):

The validated continuation controller is
`resume_hypic_piercing.sh` (SHA256
`568395006663e448b63d0851e05abb35778aa575c89b0a21cb6cec700bec4939`).
Operation `exec-00000000000004c6` completed the treatment profile and exited
zero. Operation `exec-00000000000004ec` then proved the finalized controller
is idempotent: it verified existing evidence, left every container stopped and
exited zero. If a future profile is invalid, the controller atomically archives
that exact phase directory before retrying so raw failure evidence is not
overwritten. Its log and exclusive lock paths are
`/cache/cch/hypic-qwen36-piercing-20260904/resume-hypic-piercing.log` and
`/cache/cch/hypic-qwen36-piercing-20260904/resume-hypic-piercing.lock`.
The four fail-closed attempts, preserved artifacts and exact recovery
rationale are in `profile-failure-20260905.json`.

Final-state self-test and idempotent resume (both exit zero without starting a
service while the recorded artifacts remain valid):

    cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
    bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_piercing.sh --self-test
    bash .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/resume_hypic_piercing.sh

Fresh state inspection:

    cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
    docker inspect -f '{{.State.Status}} {{.HostConfig.CpusetCpus}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' qwen36_hypic_pdc_baseline_npu0_3
    docker inspect -f '{{.State.Status}} {{.HostConfig.CpusetCpus}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}} {{range .Config.Env}}{{if eq . "PROFILING_MODE=dynamic"}}PROFILING_MODE=dynamic{{end}}{{end}}' qwen36_hypic_pdc_baseline_profile_npu0_3
    docker inspect -f '{{.State.Status}} {{.HostConfig.CpusetCpus}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}}' qwen36_hypic_pdc_treatment_npu0_3
    docker inspect -f '{{.State.Status}} {{.HostConfig.CpusetCpus}} {{range .HostConfig.Devices}}{{.PathOnHost}} {{end}} {{range .Config.Env}}{{if eq . "PROFILING_MODE=dynamic"}}PROFILING_MODE=dynamic{{end}}{{end}}' qwen36_hypic_pdc_treatment_profile_npu0_3
    for hypic_dataset in longbenchv2 gsm8k; do for hypic_run in run1 run2 run3; do hypic_file=/cache/cch/hypic-qwen36-piercing-20260904/quality/pdc-baseline/${hypic_dataset}.${hypic_run}.jsonl; printf '%s ' "$hypic_file"; test -f "$hypic_file" && wc -l < "$hypic_file" || echo 0; done; done
    ps -eo pid,etimes,args | grep '[h]ypic_quality_eval.py'
    pgrep -af '[r]esume_hypic_piercing.sh'
    tail -n 40 /cache/cch/hypic-qwen36-piercing-20260904/resume-hypic-piercing.log

Live evidence audit while the exact producer above is still running:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_hypic_evidence.py --evidence .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/evidence-hypic-qwen36.json --worktree-root "$PWD" --allow-volatile

Final evidence audit after every Hypic producer is stopped and the final
runtime-event SHA256 has replaced its volatile marker:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_hypic_evidence.py --evidence .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/evidence-hypic-qwen36.json --worktree-root "$PWD" --output /cache/cch/hypic-qwen36-piercing-20260904/final-evidence-audit.json

Do not relaunch a quality run while its process exists. After a run exits,
rerun these exact commands safely: the evaluator resumes missing samples and
re-scores persisted responses with the exact dependency-free AIS scorer.

    test -z "$(pgrep -af '[h]ypic_quality_eval.py')" || { echo 'quality evaluator already running; do not relaunch'; exit 1; }
    for hypic_run in run1 run2 run3; do python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py --dataset longbenchv2 --data /cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json --base-url http://127.0.0.1:8221 --model qwen36-hypic-piercing --output-dir /cache/cch/hypic-qwen36-piercing-20260904/quality/pdc-baseline --run-id "$hypic_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2 || exit; done
    for hypic_run in run1 run2 run3; do python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py --dataset gsm8k --data /cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl --base-url http://127.0.0.1:8221 --model qwen36-hypic-piercing --output-dir /cache/cch/hypic-qwen36-piercing-20260904/quality/pdc-baseline --run-id "$hypic_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2 || exit; done

The baseline active canary and all baseline quality runs already passed.
Never attach msprof to the original service because it was not started with
`PROFILING_MODE=dynamic`. If the controller is terminal and no Hypic process
exists on NPU0-3, the exact profile-only recovery is:

    sha256sum /cache/cch/hypic-qwen36-piercing-20260904/pdc-baseline/active_semantic_canary_reproducible.json
    test -z "$(pgrep -af '[r]esume_hypic_piercing.sh')" || { echo 'controller already running'; exit 1; }
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_profile_clone.py --source qwen36_hypic_pdc_baseline_npu0_3 --clone qwen36_hypic_pdc_baseline_profile_npu0_3 --expected-hypic disabled
    docker start qwen36_hypic_pdc_baseline_profile_npu0_3
    until curl -fsS http://127.0.0.1:8221/health >/dev/null; do sleep 10; done
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_native_profile.py --container qwen36_hypic_pdc_baseline_profile_npu0_3 --phase pdc-baseline --output-root /cache/cch/hypic-qwen36-piercing-20260904/profiles --duration 300
    docker stop --time 60 qwen36_hypic_pdc_baseline_profile_npu0_3

Then start only the original treatment container, verifying NPU0-3 and
CPU112-191 before continuing:

    docker start qwen36_hypic_pdc_treatment_npu0_3
    until curl -fsS http://127.0.0.1:8221/health >/dev/null; do sleep 10; done
    docker inspect -f '{{json .HostConfig.Devices}} {{.HostConfig.CpusetCpus}} {{.State.Status}}' qwen36_hypic_pdc_treatment_npu0_3
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_semantic_canary.py --base-url http://127.0.0.1:8221 --model qwen36-hypic-piercing --phase pdc-hypic --output /cache/cch/hypic-qwen36-piercing-20260904/pdc-hypic/active_semantic_canary_reproducible.json --timeout 2400

For treatment quality, use these exact same-ruler resumable commands:

    test -z "$(pgrep -af '[h]ypic_quality_eval.py')" || { echo 'quality evaluator already running; do not relaunch'; exit 1; }
    for hypic_run in run1 run2 run3; do python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py --dataset longbenchv2 --data /cache/cch/hhs-aisbench/ais_bench/datasets/LongBench-v2/data.json --base-url http://127.0.0.1:8221 --model qwen36-hypic-piercing --output-dir /cache/cch/hypic-qwen36-piercing-20260904/quality/pdc-hypic --run-id "$hypic_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2 || exit; done
    for hypic_run in run1 run2 run3; do python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_quality_eval.py --dataset gsm8k --data /cache/cch/hhs-aisbench/ais_bench/datasets/gsm8k/test.jsonl --base-url http://127.0.0.1:8221 --model qwen36-hypic-piercing --output-dir /cache/cch/hypic-qwen36-piercing-20260904/quality/pdc-hypic --run-id "$hypic_run" --concurrency 32 --max-out-len 1024 --seed 0 --timeout 2400 --retries 2 || exit; done

Treatment profile requires its own profile-only clone after the original
treatment quality container is stopped:

    docker stop --time 60 qwen36_hypic_pdc_treatment_npu0_3
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_profile_clone.py --source qwen36_hypic_pdc_treatment_npu0_3 --clone qwen36_hypic_pdc_treatment_profile_npu0_3 --expected-hypic enabled
    docker start qwen36_hypic_pdc_treatment_profile_npu0_3
    until curl -fsS http://127.0.0.1:8221/health >/dev/null; do sleep 10; done
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/hypic_native_profile.py --container qwen36_hypic_pdc_treatment_profile_npu0_3 --phase pdc-hypic --output-root /cache/cch/hypic-qwen36-piercing-20260904/profiles --duration 300
    docker stop --time 60 qwen36_hypic_pdc_treatment_profile_npu0_3

Do not invent Git identity and do not push. The final Hypic decision is
`reject-adoption` for the current configuration. Reopen only for a materially
different implementation that restores every coexistence signal, adds
authoritative NIAH+ evidence and repeats the frozen A/B ruler.

## 0. Status

Execution: completed for the Qwen3.6 candidate. Integration: not-ready. Decision: reject.

Final Qwen3.6 A/B result: the Dk64 treatment loaded and served on NPU0-3,
but it did not improve the performance gate. Baseline versus treatment median
TPOT was 369.1616 versus 369.1632 ms/token on the identical forced-length
361-input/32-output warm7 workload. Median TTFT changed from 2575.79 to
2519.81 ms and median E2E from 14019.80 to 13971.92 ms, but decode TPOT—the
target metric—was unchanged. The treatment container was stopped, leaving
NPU0-3 free. Native profiling and DRRQR quality work were not run because a
candidate with no decode gain cannot become adoptable through quality work.
No accuracy-lossless statement is permitted.

Operator scope change (2026-09-04): stop the Qwen3.5-27B line and optimize
`/cache/efim/Qwen3.6-27B` instead. Its index, all 15 shards and all 1199
safetensors keys were verified complete. Qwen3.5 download/restart operations
were cancelled and any partial files were preserved. The Qwen3.6 baseline
container is `qwen36_27b_hypic_baseline_npu0_3`, port 8211, host NPU0-3,
CPU112-191. CEval remains excluded. NPU4-7 remains forbidden.

Latest execution evidence: the Qwen3.6 baseline loaded all 15 shards and
served successfully. The valid forced-length 361-input/32-output warm7 run is
`qwen36-baseline-361in-32out-warm7.json`; median TTFT was 2575.79 ms, median
TPOT 369.16 ms/token and median E2E 14019.80 ms. Fixed seed did not make all
output hashes identical. An earlier run without `ignore_eos=true` is invalid
because several requests emitted EOS at one token and the summarizer rejected
the incomplete cell.

The Qwen3.6 Dk64 speed oracle now exists at
`/cache/efim/Qwen3.6-27B-gdn-dk64-speed-oracle`. Conversion atomically rewrote
6 shards and 96 tensors. Offline validation proved 48 QKV plus 48 conv tensors
at packed width 8192 versus source width 10240; both indexes contain 1199
tensors. This is performance-feasibility treatment only, not quality evidence.

After baseline shutdown, an externally created container
`qwen35_query_rewrite_tp4_dev` took host NPU0-3 and CPU96-191. It must not be
stopped or modified. Treatment launch is waiting for that lane to become free;
the thread heartbeat `resume-qwen3-6-optimization` checks every 10 minutes and
stays quiet while occupancy is unchanged.

Superseded blocker (2026-09-04): the previously selected baseline was
`/cache/efim/Qwen3.5-27B`, but its index declares 11 safetensors shards while
only shards 00001-00006 exist. Shards 00007-00011 were not found elsewhere
under `/cache`; vLLM therefore fails closed with uninitialized checkpoint
weights. The failed container was `qwen35_27b_hypic_baseline_npu0_3` on the
authorized NPU0-3 lane. It produced no benchmark evidence. CEval is explicitly
excluded from this run by operator decision. This blocker is no longer on the
active path because the operator selected the separately verified Qwen3.6-27B
checkpoint. Do not substitute `/cache/austinov/Qwen3.8-27B`.

Hardware feasibility is established for GDN Dk 128->64, with a repeatable positive speed signal. Adoption is not justified: the fixed-channel checkpoint is a speed oracle only, and the data-free L1 checkpoint passed only 13/20 initial micro-quality cases. True paper-aligned DRRQR remains undone.

Worktree: /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
Branch/base: work/WS-20260904-qwen38-dense-paper-to-ascend at 222677fc719c7014879b161ed1dd3ed3276d7a5d.

Dirty state intentionally includes workstream records, two offline converter scripts, and an experiment-only opt-in Q/K capture change in vllm_ascend/ops/gdn.py. No commit exists because mtuser has no configured Git identity. Do not invent one and do not push.

Last read-only observation: qwen38_paper_baseline_npu0_3 was running on host NPU0-3 / CPU112-191; qwen38_gdn_fused_candidate was running on host NPU4-7 / CPU0-95. This consolidation changed no workload.

## 1. North Star

Determine whether paper-derived Q/K channel reduction can reduce dense Qwen3.8-27B inference cost on Ascend 910B4 without unacceptable quality loss, using real weights, identical warm A/B conditions, and native profiling.

## 2. Current Focus

Move from the proven Dk64 hardware speed oracle to a quality-qualified DRRQR treatment. Keep performance feasibility and model-quality claims separate.

## 3. Successful Results and Evidence

- Model match: 64 text layers = 48 GDN + 16 full attention; 16 key heads, Dk=128; 48 value heads, Dv=128; conv width 4.
- Packed Q/K/V width is 2048 + 2048 + 6144 = 10240. Dk64 becomes 1024 + 1024 + 6144 = 8192.
- Runtime is shape-driven; recurrent Triton supports K<=256. Baseline selected Triton/FLA prefill, so Dk64 did not discard the active prefill path.
- Offline conversion preserved the source and atomically replaced destination shards. Both manifests record 16 changed shards and 96 changed tensors over all 48 GDN layers.
- Real-weight Dk64 serving reached head_k_dim=64.
- Dk64 warm 361-input/32-output median TPOT was 34.38 ms/token over 7 samples, mean 35.18. Comparable profiler-enabled baseline observations were about 36.4-38.4 ms/token: roughly 8-10% positive hardware signal, not quality evidence.
- Theoretical per-rank saving at max-seqs16: about 288 MiB GDN state pool plus about 240 MiB Q/K weights, roughly 528 MiB/rank.
- Baseline rank0 native profile: MatMulV2+V3 about 70.9% of operator time, but the largest component is unaffected MLP. GDN decode projection 5120->4096 appeared 1824 times (48x38). Recurrent/chunk/conv GDN kernels contributed roughly another 10%, only part scaling with Dk.

Evidence paths:
- /cache/austinov/Qwen3.8-27B-gdn-dk64-speed-oracle/speed_oracle_manifest.json
- /cache/austinov/Qwen3.8-27B-gdn-dk64-l1/l1_pruning_manifest.json
- /cache/austinov/qwen38-paper-profiles/baseline
- /cache/austinov/qwen38-paper-profiles/dk64
- /tmp/qwen38_paper_dk64_warm7.txt
- /tmp/qwen38_quality_l1.json
- /tmp/qwen38_paper_l1_warm7.txt
- /cache/austinov/eval-runs/exp-20260904-qwen38-gdn-native-state-layout/baseline/correctness32.json

Reusable fixed-ruler assets:

- test-contract.json: machine-readable dataset, invariant, G1-G4, statistics and quality contract.
- runtime-config.template.json: runtime/load fields that must be filled and frozen.
- result-row.template.json: one JSONL result-row contract.
- freeze_test_contract.py: refuses to freeze unless every required dataset is supplied, then records file/config SHA256.
- summarize_ablation.py: validates G1-G4 switches, one shared frozen/config hash and exactly three warm repetitions before reporting mean/std and deltas.
- The summarizer also rejects a missing G1-G4 cell and fewer than two models by default. Use --expected-models 1 only for its local fixture, never for the final generalization claim.
- evaluate_quality_gate.py: evaluates Conditions A/B/C per model, dataset and treatment; defaults to the exact four-dataset suite, requires at least two models and a hashed repeated-G1 noise evidence file, and emits the permitted lossless wording only when every cell passes.
- render_decision.py: combines valid performance and quality artifacts; it recommends only one group that is uniquely no-worse on every reported metric, clears the minimum gain, and has at least two models. Otherwise it returns iterate.
- run_analysis_pipeline.py: one-shot offline orchestration with separate performance/quality inputs. Production also requires a hash-bound G1-versus-candidate profile manifest; a failed quality/profile gate still renders or rejects an adoption path.
- preflight_piercing.py: read-only, fail-closed readiness gate for frozen inputs, exact lane/image invariants, freshly verified treatment matrix, per-model source-hash-bound DRRQR manifests, and explicit NPU0-3 baseline replacement authority.
- verify_rrqr_capture_hook.py: torch-free host-side executable contract for default-disabled and per-layer/rank-bounded capture behavior.
- RESOURCE_REQUEST.md: exact centralized search/delivery checklist for benchmark assets, missing datasets/configs and true DRRQR resources.
- resource-intake.template.json + verify_resource_intake.py: read-only delivery manifest and canonical file/tree hash verifier; accepts a DRRQR implementation or both model checkpoints.
- lifecycle-plan.template.json + verify_lifecycle_plan.py + execute_lifecycle_plan.py: eight-cell lifecycle plan, validator and default-dry-run one-shot executor for the exact performance-restart-quality sequence. Execute mode is preflight/hash/authorization gated.
- verify_treatment_matrix.py: offline verifier for same-architecture/different-size model inventories, declared config fields, safetensors shard presence, native patch hash/operator identity, and exact G1-G4 orthogonality.
- fixtures/ablation-valid.jsonl: two-model offline positive fixture for the summarizer and decision renderer.

## 4. Failures, Invalid Results, and Traps

- Cold ACL/torch.compile/graph samples of 12-13 seconds are not steady state.
- vllm bench tokenizer/download behavior could stall; direct fixed streaming requests were controllable.
- Literal short-output smoke assertions are unsuitable because reasoning can consume the token budget; compare deterministic tokens/text or task answers.
- Fixed-first-channel is a speed oracle only.
- Per-head data-free L1 is not DRRQR. Its 13/20 result fails the preliminary quality gate but does not falsify DRRQR.
- L1 timing near 0.38 s/token is an invalid/contaminated run until root-caused; do not call it inherent Dk64 performance.
- The opt-in capture hook copies to CPU and torch.save's in the model path. It is now prefill-only, requires both `VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE=1` and `VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR`, and defaults to one capture per layer/rank. It can still destroy benchmark validity when armed; unset both variables for every timing/profile run.
- Compare profiler to profiler and non-profiler to non-profiler; profiler overhead changes latency.
- Container-visible NPU0-3 can map to host NPU4-7. Always inspect host device mappings and CPU sets.

## 5. Decision

Decision: iterate.

Proceed because hardware feasibility is proven. Do not adopt because quality is unresolved. Do not reject because the paper's DRRQR selection has not been tested.

Adopt requires: true DRRQR; real-weight deterministic correctness and broader quality within declared tolerance; clean repeated warm A/B gain; native profile correlation; capture code disabled/removed from the candidate.

Profile evidence is not satisfied by the historical speed-oracle profile.
After the quality winner is known, fill `profile-evidence.template.json`
with G1 and winner native exports for both models, using the same frozen
profile workload and disabled capture, then run:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_profile_evidence.py --manifest /ABSOLUTE/profile-evidence.json --output /ABSOLUTE/profile-verification.json

The manifest points to non-empty regular exported summary files, not merely
msprof directories, and records each file SHA256. A valid report requires the
candidate's target-region operator time to decrease versus G1 on every model.
Real DRRQR profile evidence is still missing; the existing Dk64 speed-oracle
profile must not be substituted.

## 6. Next Actions

1. Preserve the supplied benchmark archive plus the newly hashed LongBench v2 and GSM8K assets recorded in `received-resource-inventory.json`. Provision authoritative NIAH+ data/mapping and the CEval `formal_ceval` tree; code/config alone is not dataset evidence. Do not substitute datasets silently.
2. Freeze prompts, sample IDs/order, lengths, concurrency, request rate, image digest, Docker/serve arguments, seeds and metric parser in test-contract.json.
3. Define G1 baseline, G2 native-only, G3 DRRQR-only and G4 combined so paired comparisons change one switch.
4. Select a second compatible GDN model of a different size for generalization.
5. Read process/container ownership; mutate nothing until NPU0-3 ownership is explicit.
6. In an explicitly authorized calibration-only run, capture representative post-conv Q/K activations with the bounded hook; then unset both capture variables and verify no new files appear during benchmarks.
7. Build and validate a true DRRQR checkpoint from the captured activations.
8. Run every frozen group three times, report each value plus mean/std, and apply aggregate, per-dataset/category and deterministic-canary quality gates.
9. Only after quality passes, profile the best configuration; record adopt/reject and remove capture instrumentation.

The reusable protocol is in PIERCING_LOOP.md. The machine-readable ruler and gap status are in test-contract.json.
The Hypic-practice adaptation for this exact host/image/device layout is in CURRENT_ENV_MANUAL_PIERCING.md. It records the verified live baseline and the present fail-closed blockers; it is not a claim that G1-G4 has run.
The exact G1-G4 treatment identity and both model layouts are in treatment-matrix.json. G2 is the hashed fused-GDN prefill patch; Qwen3.5-4B is the selected second-model candidate. Both still require fresh runtime evidence under this workstream.

Verify those immutable treatment inputs without loading a model:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_treatment_matrix.py --matrix .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/treatment-matrix.json --output /tmp/qwen38-treatment-verification.json

Repeat the bounded, read-only dataset inventory if caches may have changed:

    for root in /cache/cch /cache /home/mtuser/.cache /root/.cache; do
      [ -d "$root" ] || continue
      timeout 12s find "$root" -type f \( -iname '*niah*' -o -iname '*longbench*' -o -iname '*ceval*' -o -iname '*c-eval*' \) -print 2>/dev/null || true
    done | sort -u

Historical result before migration: only the LongBench harness was found. This
is superseded by `received-resource-inventory.json`, which records the newly
supplied benchmark archive, LongBench v2 and GSM8K assets under `/cache/cch`.
CEval data, authoritative NIAH+ data and true DRRQR remain missing.

The successful-practice absolute paths were also checked and are absent on this host. The installed EvalScope CEval adapter identifies `modelscope/ceval-exam` and its upstream archive URL, but no CEval data cache exists. Treat this as an acquisition lead, not a frozen dataset.

RRQR calibration-only capture settings (never export these in a benchmark shell):

    export VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE=1
    export VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR=/ABSOLUTE/CALIBRATION/OUTPUT
    export VLLM_ASCEND_GDN_RRQR_MAX_TOKENS=256
    export VLLM_ASCEND_GDN_RRQR_MAX_CAPTURES_PER_LAYER=1

Mandatory benchmark cleanup and proof:

    unset VLLM_ASCEND_GDN_RRQR_CAPTURE_ENABLE VLLM_ASCEND_GDN_RRQR_CAPTURE_DIR VLLM_ASCEND_GDN_RRQR_MAX_TOKENS VLLM_ASCEND_GDN_RRQR_MAX_CAPTURES_PER_LAYER
    env | grep 'VLLM_ASCEND_GDN_RRQR_CAPTURE' && { echo 'capture remains armed' >&2; exit 2; } || true

Offline capture-contract replay:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_rrqr_capture_hook.py

Render and validate a filled lifecycle plan without executing any command:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/verify_lifecycle_plan.py --plan /ABSOLUTE/lifecycle-plan.json --output /ABSOLUTE/lifecycle-plan-verification.json

Dry-run the complete one-shot lifecycle (default; executes nothing):

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/execute_lifecycle_plan.py --plan /ABSOLUTE/lifecycle-plan.json

Do not add `--execute` until the filled plan is bound to the current ready preflight report and the operator has supplied the exact NPU0-3 authorization. The executor rejects a stale (default >300 seconds), future-dated or unbound report before the first command. Once a cell service starts, performance/quality commands run under `try/finally`, so an error still attempts the cell's exact stop command.

Execute mode additionally requires a new journal path and refuses to overwrite
an existing journal:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/execute_lifecycle_plan.py --plan /ABSOLUTE/lifecycle-plan.json --preflight-report /ABSOLUTE/preflight.json --journal /ABSOLUTE/lifecycle-journal.json --execute --authorization I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT

If a cell fails, inspect the journal and resume only while the exact same
plan-bound preflight is still fresh:

    python3 -m json.tool /ABSOLUTE/lifecycle-journal.json
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/execute_lifecycle_plan.py --plan /ABSOLUTE/lifecycle-plan.json --preflight-report /ABSOLUTE/preflight.json --journal /ABSOLUTE/lifecycle-journal.json --resume --execute --authorization I_OWN_NPU0_3_AND_AUTHORIZE_BASELINE_REPLACEMENT

`--resume` skips only the exact completed prefix. A plan hash, preflight
hash, ordering or prefix mismatch fails before commands run. If the preflight
is stale, automatic resume is intentionally unavailable: inspect completed
artifacts, generate a new preflight and plan, and use a new journal path.
Offline fault injection verified that failure in cell B leaves only cell A
complete and that resume executes B/C without repeating A.

Plan command surface is intentionally narrow: service names must be unique and start with `paper-`; start/stop argv must exactly target that service; warmup/performance/quality must start with Python or `ais_bench`; health must be loopback HTTP with an explicit port and cannot use protected port 8210.

## 7. Exact Recovery / Resume Commands

Read-only orientation:

    cd /cache/cch/.worktrees/WS-20260904-qwen38-dense-paper-to-ascend
    git -c safe.directory="$PWD" status --short --branch
    git -c safe.directory="$PWD" diff -- vllm_ascend/ops/gdn.py
    cat .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/task.json
    cat .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/HANDOFF.md
    docker ps -a --format '{{.Names}}|{{.Status}}' | grep -E 'qwen38_paper|qwen38_gdn_fused_candidate'
    npu-smi info

Validation:

    python3 -m json.tool /cache/austinov/Qwen3.8-27B-gdn-dk64-speed-oracle/speed_oracle_manifest.json >/dev/null
    python3 -m json.tool /cache/austinov/Qwen3.8-27B-gdn-dk64-l1/l1_pruning_manifest.json >/dev/null
    python3 -m py_compile .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/prune_qwen35_gdn_speed_oracle.py
    python3 -m py_compile .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/prune_qwen35_gdn_l1.py
    python3 -m py_compile .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/freeze_test_contract.py
    python3 -m py_compile .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_ablation.py

Freeze the ruler only after all four exact datasets exist and runtime-config.json has no REQUIRED placeholders:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/freeze_test_contract.py --contract .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/test-contract.json --runtime-config .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/runtime-config.json --output .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/frozen-inputs.json --dataset NIAH+=/ABSOLUTE/FROZEN/NIAH_PLUS --dataset 'LongBench v2=/ABSOLUTE/FROZEN/LONGBENCH_V2' --dataset GSM8K=/cache/austinov/eval-data/general/prepared/gsm8k_test.jsonl --dataset CEval=/ABSOLUTE/FROZEN/CEVAL

Summarize completed JSONL rows:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_ablation.py --results /ABSOLUTE/RESULTS/all-groups.jsonl --output /ABSOLUTE/RESULTS/summary.json --expected-repetitions 3

Evaluate quality only with a threshold derived from repeated G1 runs on the same frozen suite:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/build_g1_noise_evidence.py --quality-results /ABSOLUTE/RESULTS/all-groups.jsonl --output /ABSOLUTE/RESULTS/repeated-g1-noise-evidence.json
    python3 -c 'import json; print(json.load(open("/ABSOLUTE/RESULTS/repeated-g1-noise-evidence.json"))["noise_threshold_pp"])'
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/evaluate_quality_gate.py --results /ABSOLUTE/RESULTS/all-groups.jsonl --output /ABSOLUTE/RESULTS/quality-gate.json --noise-threshold-pp MEASURED_G1_THRESHOLD --noise-evidence /ABSOLUTE/RESULTS/repeated-g1-noise-evidence.json

Start from `noise-evidence.template.json`. Production noise evidence must use
`method: max_within_cell_range_pp`, contain G1 observations for exactly runs
1/2/3 in every model/dataset quality cell, and carry the same
frozen/config/treatment bindings. Compute each cell's `max(score)-min(score)`
in percentage points and set `noise_threshold_pp` to the largest cell range.
The CLI value must equal that recomputed value; a generic 1–2pp constant or a
fixture-only document is rejected. Every observation's model, dataset,
run_index and quality_score must also match the corresponding G1 row in the
quality result JSONL exactly; do not maintain a second independently edited
copy of baseline scores. Generate the document with
`build_g1_noise_evidence.py`; it also binds the byte-level SHA256 of the
complete quality JSONL, so any later edit requires regeneration.

For a real run, every warm quality row must explicitly carry
`deterministic_canary_output_tokens: 512`, a lowercase 64-hex
`deterministic_canary_sha256`, and a finite `quality_score`. Missing token
counts are not defaulted in production. Shorter canaries and symbolic digest
labels are accepted only by explicit `--fixture-mode`, whose output cannot
support a production lossless claim.

Real quality rows must also populate the hash-bound fields in
`result-row.template.json`: `frozen_inputs_sha256`,
`invariant_config_sha256`, `treatment_matrix_sha256`,
`checkpoint_manifest_sha256`, `service_config_sha256`,
`deterministic_canary_input_sha256`, and
`per_sample_artifact_sha256`. The first three must be identical across the
entire quality suite; checkpoint identity must be stable per group/model,
service identity per group/model/dataset, and canary-input identity per
model/dataset across all groups and repetitions. Never merge result files
whose ruler hashes differ.

The performance summary independently validates the same three global ruler
hashes. `render_decision.py` compares the performance and quality binding
objects byte-for-byte and returns `iterate` if they differ or if only one
artifact is fixture-scoped. Therefore, never hand-edit summary/gate JSON to
make separately collected experiments appear compatible; regenerate both
from the same frozen result set.

Every warm performance row must contain finite TTFT, TPOT, OTT, throughput and
batch-delay values. Throughput must be positive; latency/delay values must be
non-negative. Each cell must contain exactly one row for run indices 1, 2 and
3. The decision renderer rejects a globally omitted metric and also requires
the performance model/dataset pairs to equal the quality-gate scope.

Production result files are phase-typed: performance rows must declare
`phase: performance`, quality rows `phase: quality`. Within each phase,
checkpoint manifests are stable per group/model and service instance/config
identities are stable per group/model/dataset across runs 1/2/3. The service
instance changes across the required restart, but `service_config_sha256`
must be identical between performance and quality for the same cell.
`checkpoint_manifest_sha256` must likewise match across phases for each
group/model. Both analyzers independently verify the G1-G4
`native_optimization`/`drrqr` truth table; Step 6 rejects either binding
mismatch.

Average speedup is not sufficient for the multi-model generalization claim.
The unique average-dominant group must meet
`--minimum-improvement-percent` in every model/dataset/metric cell. The
decision JSON records both average and worst-case improvement maps. The
minimum must be finite and non-negative; use zero only for control-flow
fixtures, not the production decision.

Render the final decision only from validated artifacts:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/render_decision.py --performance-summary /ABSOLUTE/RESULTS/summary.json --quality-gate /ABSOLUTE/RESULTS/quality-gate.json --profile-verification /ABSOLUTE/RESULTS/profile-verification.json --output-json /ABSOLUTE/RESULTS/decision.json --output-md /ABSOLUTE/RESULTS/DECISION.md --minimum-improvement-percent REQUIRED_MINIMUM

Or run the complete offline analysis after collection (the two inputs may be the same complete JSONL file):

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/run_analysis_pipeline.py --performance-results /ABSOLUTE/RESULTS/performance.jsonl --quality-results /ABSOLUTE/RESULTS/quality.jsonl --profile-evidence /ABSOLUTE/RESULTS/profile-evidence.json --output-dir /ABSOLUTE/RESULTS/final-analysis --noise-threshold-pp MEASURED_G1_THRESHOLD --noise-evidence /ABSOLUTE/RESULTS/repeated-g1-noise-evidence.json --minimum-improvement-percent REQUIRED_MINIMUM

Preferred production one-shot form (builds hash-bound G1 noise evidence and
uses its computed threshold automatically):

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/run_analysis_pipeline.py --performance-results /ABSOLUTE/RESULTS/performance.jsonl --quality-results /ABSOLUTE/RESULTS/quality.jsonl --profile-evidence /ABSOLUTE/RESULTS/profile-evidence.json --output-dir /ABSOLUTE/RESULTS/final-analysis --build-noise-evidence --minimum-improvement-percent REQUIRED_MINIMUM

The verified profile candidate must equal the unique G2/G3/G4 performance
winner, cover the same two models, use the same frozen/config/treatment hashes,
and show lower target-region operator time than G1 on every model. Otherwise
Step 6 remains `iterate`.

Do not combine `--build-noise-evidence` with `--noise-evidence`; the former
writes `final-analysis/repeated-g1-noise-evidence.json`. It is production
only and is rejected with `--fixture-mode`.

Exit 0 means an adoption artifact was produced; exit 2 means fail-closed/iterate or invalid input. Inspect `final-analysis/decision.json` and `DECISION.md` in either case.

Offline tool self-check (does not use NPU):

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/summarize_ablation.py --results .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/fixtures/ablation-valid.jsonl --output /tmp/qwen38-ablation-fixture-summary.json --expected-models 2 --fixture-mode
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/evaluate_quality_gate.py --results .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/fixtures/quality-pass.jsonl --output /tmp/qwen38-quality-pass.json --noise-threshold-pp 1.0 --noise-evidence .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/fixtures/noise-evidence.json --expected-dataset fixture-dataset --fixture-mode

`--expected-dataset` is rejected unless `--fixture-mode` is explicit. Fixture mode can test control flow but emits only a fixture-scoped quality claim and must never be used for the real decision.

Converter replay, only to a new/empty destination after disk/source checks:

    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/prune_qwen35_gdn_speed_oracle.py --src /cache/austinov/Qwen3.8-27B --dst /cache/austinov/Qwen3.8-27B-gdn-dk64-speed-oracle --new-head-k-dim 64
    python3 .agents/workstreams/WS-20260904-qwen38-dense-paper-to-ascend/prune_qwen35_gdn_l1.py --src /cache/austinov/Qwen3.8-27B --dst /cache/austinov/Qwen3.8-27B-gdn-dk64-l1 --new-head-k-dim 64

Do not blindly start/stop containers. Recover exact historical command/device/mount state with:

    docker inspect qwen38_paper_baseline_npu0_3 --format 'Path={{json .Path}} Args={{json .Args}} Image={{json .Config.Image}} Cpuset={{json .HostConfig.CpusetCpus}} Devices={{json .HostConfig.Devices}} Mounts={{json .Mounts}}'
    docker inspect qwen38_paper_dk64_oracle_npu0_3 --format 'Path={{json .Path}} Args={{json .Args}} Image={{json .Config.Image}} Cpuset={{json .HostConfig.CpusetCpus}} Devices={{json .HostConfig.Devices}} Mounts={{json .Mounts}}'
    docker inspect qwen38_paper_dk64_profile_npu0_3 --format 'Path={{json .Path}} Args={{json .Args}} Image={{json .Config.Image}} Cpuset={{json .HostConfig.CpusetCpus}} Devices={{json .HostConfig.Devices}} Mounts={{json .Mounts}}'

## 8. Do Not Do

- Do not operate NPU4-7 workload in any way.
- Do not assume NPU0-3 are free.
- Do not benchmark with capture enabled.
- Do not overwrite/delete source or derived checkpoints.
- Do not equate L1 with DRRQR or speed oracle with quality.
- Do not add global safe.directory, fabricate Git identity, or push.
