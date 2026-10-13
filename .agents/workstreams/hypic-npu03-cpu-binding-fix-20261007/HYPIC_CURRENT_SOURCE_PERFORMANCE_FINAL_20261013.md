# HYPIC 4429e35 — same-source three-pair performance supplement

Status: final descriptive performance supplement; quality REJECT_OR_QUALIFY.
Campaign: current4429-performance-20261013. Date: 2026-10-13 UTC.
This closes the authorized six-phase speed measurement, not all Paper-to-Ascend
or 29-Skill acceptance. This is scoped direction/magnitude evidence, not
absolute-number reproduction of a colleague's different-source experiment.

## Step 0. Environment and identity

Host chicaihong01/ma; physical Ascend 910B4 NPU0–3 only; TP4/DP1;
CPU112–191, CPU binding disabled; port8223. Physical mapping, four worker
namespace identity, continuous isolation and exact owned release passed the
independent per-phase audit. Final read-only snapshot02f5 found no physical
0–3 process and no8223 listener. No foreign task or physical4–7 was modified.

Model /cache/efim/Qwen3.6-27B, BF16; model index SHA256
a8ad2c26fb707ff8c245806315b03e3b4b74595528492423af5dae0ce39b4d9b.
This is an index identity, not a newly computed hash of all weight bytes.
Image sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1.
Runtime source /cache/cch/hypic_vllm_ascend-hotproof-20261008 at
4429e35177979c874bf053ab29789e4773f39b22, byte-attested in every arm.
Controller frozen e94ca151; read-only statistics checkpoint b21ff6ea.
Work branch work/hypic-npu03-cpu-binding-fix-20261007.
No runtime source or frozen measurement helper was edited during this supplement.

Per-arm contract.json and source-attestation.json retain runtime and launch
identity. CANN path cann-9.1.0 is explicit in retained serving environment;
final host npu-smi displayed25.2.0. A full independent tokenizer-byte,
driver/firmware/toolchain matrix is not established by this supplement;
do not invent it from image names or today's snapshot. No MTP/speculation
treatment was introduced. New profiling and diagnostic-observer work are
explicitly out of scope; timing includes the existing common evidence setup,
whose isolated overhead is not separately measured.

## Step 1–3. Baseline, treatment and sequential protocol

G1 no-cache and G2 hypic-only use the same mounted source/image/model/common
serving flags. Normalized six-phase specs match; the declared treatment switch
is VLLM_ASCEND_HYPIC_ENABLE=0/1. Per-arm names/result paths are identifiers,
not scientific variables. Prefix caching remains disabled.

Context41984, memory fraction0.85, material cache3584MiB/10segments.
Synthetic input32768 tokens, shared prefix16384, explicit segment ends
[16384,32768], concurrency16; 40 scored requests plus2 concurrent one-token
warmups per arm/round. Fixed output1024, ignoreEOS, temperature0/seed0.
The served alias contains '2048' and inherited fingerprint.max_output_tokens
is2048 for quality; actual performance benchmark_config.output_tokens and
all response counts are1024. No LongBench/GSM8K was rerun by this campaign.

Frozen order:
no-cache/screen → hypic-only/screen → hypic-only/repeat2 →
no-cache/repeat2 → no-cache/repeat3 → hypic-only/repeat3.
Every preceding phase was independently accepted as valid before the next.
Six distinct containers/roots; 240 scored responses and12 warmups,42 unique
IDs per phase. No failed/excluded scored request appears in the accepted
matrix. This is not a claim about unrecorded transport retries.
1006 continuous isolation samples were clean.
All120 candidate scored requests have boundary joins and four-worker hot proof.
This proves activation for these performance requests, not r19 quality requests,
full tensor equivalence, distributedC3, or a numerical allocation of time saved.

### Exact historical entry commands (do not rerun completed roots)

From /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007:
```bash
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm no-cache --phase screen --action run
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm hypic-only --phase screen --action run
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm hypic-only --phase repeat2 --action run
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm no-cache --phase repeat2 --action run
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm no-cache --phase repeat3 --action run
TMPDIR=/cache/cch python3 -B current_source_performance_20261013.py --arm hypic-only --phase repeat3 --action run
```
These checked-in entries own service startup, warmup, benchmark, continuous
guard and exact release; full serving command/environment and benchmark
arguments are retained in each contract.json and benchmark-command.json.
They require fresh ma/direct route proof and actual physical0–3/8223 admission.
Every existing root is exclusive and cannot be overwritten or resumed by rerun.
No new starts after2026-10-13T08:47:14Z.

## Measured performance

All values below are current4429e35 measurements, not historical references.
P95 uses the benchmark's nearest-rank estimator within each40-request run.
Weighted TPOT and batch throughput are independently recalculated from raw rows.

| Round | G1 TPOT ms | G2 TPOT ms | TPOT relative change | G1 TTFT P95 s | G2 TTFT P95 s | G1/G2 throughput token/s |
|---|---:|---:|---:|---:|---:|---:|
| screen | 75.6181 | 58.3311 | -22.8610% | 88.5053 | 45.0214 | 100.6443 / 134.4750 |
| repeat2 | 74.7410 | 58.4195 | -21.8374% | 89.4044 | 45.0163 | 102.1759 / 134.6307 |
| repeat3 | 74.7991 | 58.2802 | -22.0844% | 89.4104 | 45.4714 | 102.0650 / 134.2829 |

| Metric | G1 mean ± sample SD | G2 mean ± sample SD | G1 median | G2 median | Median relative change |
|---|---:|---:|---:|---:|---:|
| Weighted TPOT (ms/token) | 75.0528 ± 0.4905 | 58.3436 ± 0.0705 | 74.7991 | 58.3311 | -22.0163% |
| TPOT P95 (ms/token) | 111.6639 ± 0.8433 | 78.2584 ± 0.0766 | 111.7113 | 78.2506 | -29.9529% |
| TTFT P95 (s) | 89.1067 ± 0.5208 | 45.1697 ± 0.2613 | 89.4044 | 45.0214 | -49.6429% |
| Output throughput (token/s) | 101.6284 ± 0.8541 | 134.4629 ± 0.1742 | 102.0650 | 134.4750 | 31.7543% |
| Batch duration (s) | 403.0561 ± 3.4034 | 304.6197 ± 0.3947 | 401.3130 | 304.5919 | -24.1012% |

Relative change=(candidate/baseline−1)×100; negative latency is improvement.
SD is across three run summaries, not a confidence interval. Median of run
P95 is not a pooled percentile. TPOT reductions range21.8374–22.8610%;
three repeats do not establish population statistical significance.

## Existing same-source quality, separately retained

r19 max2048, naturalEOS quality was completed before this supplement.
LongBench-v2 local127×3:227/381→219/381,59.5801%→57.4803%,
−2.0997percentage points; per-round74/77/76→73/70/76; length stops49→67.
Frozen decision REJECT_OR_QUALIFY and deployment_allowed=false remain.
This is net8 response losses (23 regressions,15 improvements), not8 independent
failed questions. See HYPIC_R19_QUESTION_LEVEL_INTERPRETATION_20261013.md.
Question-level variation and truncation association are not a proven cause.
GSM8K off-path1319×3:3838/3957→3840/3957; this does not validate HYPIC hot-path quality.
See HYPIC_R19_FINAL_QUALITY_REPORT_20261012.md for original evaluator,
datasets/scorers, commands, repetitions and quality boundaries. Its older
'unmeasured same-source performance' status is superseded ONLY by this supplement;
do not edit the hash-pinned historical report or change its quality decision.
Quality audit SHA256:
40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b.

## Historical comparison and interpretation

The previous r13/c12060c speed result is a different source, not a denominator
for this report. Colleague TP2/other model/card results are likewise historical.
No paper or colleague number is copied into the current tables.
Current same-source three-pair measurements support a speed improvement under
this one workload. They neither refute the paper nor prove lossless deployment.

| Decision | Status |
|---|---|
| Feasibility and scoped activation | Six valid phases;120/120 four-worker hot requests |
| Descriptive performance | TPOT median−22.0163%;TTFT P95 median−49.6429%;throughput median+31.7543% |
| Quality safety | Existing r19 REJECT_OR_QUALIFY; not overridden |
| Kernel/profile attribution | No new profile; component-level saved-time cause unproven |
| Adoption | Not approved |
| Generalization | Other models,traffic,precision,topology not established |
| Full29-Skill acceptance | Not complete;9 bounded verified/20 partial retained |

Correctness-first progression was not silently declared passed: the human
explicitly authorized this speed-only supplement after the quality rejection.
No speed threshold was used to delete a slow run. Cold/startup,boundary
concurrency,soak,power and memory optimization are outside this supplement,
not zeros or automatically satisfied requirements.

## Failures, release and evidence

Six admitted phases passed; no phase was retried or raw root reused in this
campaign. Earlier campaigns remain separately rejected/failed/inconclusive.
Expired connector handles were resolved through terminal raw evidence, not
treated as permission to restart. The app heartbeat disappeared; it was not
recreated without clarification. Active-session continuation completed the
sequence. No claim of continuing background monitoring is made.
Unchanged GitHub authentication was not retried; local commits are not
main/remote synchronization.

Independent final phase audit02f1 exit0, aggregate/statistics02f3 exit0.
Final controller02d6 exit0; exact last service release07:42:23UTC.
Aggregate /cache/cch/hypic-npu03-cpu-binding-fix-20261007/current4429-performance-20261013-audit.json
SHA256 67ba6cf14fc9bed993acbdf421eb438f22d56957f3e56baad170a4bb871e53fe.

Each root below retains contract.json,performance.json,arm-result.json,
benchmark-command.json and ARM/{source-attestation.json,worker-namespace-map.json,
lane-guard.json,service-stop.json,hypic-evidence.jsonl}.
The aggregate binds each full root,container,contract/performance/result/event
digest,counts and metrics. All raw evidence remains outside Git.

| Phase | Guard samples | arm-result SHA256 |
|---|---:|---|
| no-cache/screen | 170 | 6a1fde522523c9482bc681bfd1116fb4742064db3315a048c5448ff38af57fed |
| hypic-only/screen | 164 | f263c1122102ccb993ddd720de077aab5307572178908a0675a977692fcaf68e |
| hypic-only/repeat2 | 162 | e15b83bb61b0f923f3901a7126e6957f6161f0bd1d5028eaedb4471c0c2a88bb |
| no-cache/repeat2 | 172 | 428d8440b6d03919e65016206583c07fd3c8ce7a528a2fc5cb2f8c22e7019f5d |
| no-cache/repeat3 | 176 | a5ee696aed9edeae45066b1c790674dda0879135ce0cc79733c30eec65dc11cb |
| hypic-only/repeat3 | 162 | 8524b9797d3e0bbdd902e83ef2a79ab984377ab958ef073a8dcce92ecb6f9f1f |

Raw prefix: /cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-context-41984-current4429-performance-20261013-
Append each arm-phase exactly as the aggregate root field records.

## Read-only replay and recovery

```bash
cd /cache/cch/model-tuning-lab-hypic-e2e-20261006/.agents/workstreams/hypic-npu03-cpu-binding-fix-20261007
TMPDIR=/cache/cch python3 -B summarize_current_source_performance.py
python3 -B -m unittest test_summarize_current_source_performance.py
python3 -B current_source_performance_20261013.py --arm hypic-only --phase repeat3 --action audit-phase
npu-smi info
ss -lntp
docker inspect 8925e0c5693d21999fe282d9bf736df430ae1e1584a277d7f2b91853109e8a26
```
The exact last container should be absent; independent service-stop/guard
receipts are historical release proof. Do not stop any current foreign owner.
No cleanup or NPU resume is necessary. audit-all already created its exclusive
aggregate; do not run that writer again. The read-only summary is the replay.
Next: retain these results in Skill evidence and complete remaining applicable
exact-main obligations offline; integration requires working authorization/
authentication. No additional performance or quality run is authorized here.

Allowed: bounded same-source speed improvement and retained quality regression.
Forbidden: losslessness,quality pass,deployability,all29Skills verified,or
main/remote synchronization. Remaining unproven: quality causality,full
lifecycle recovery/generalization and unfulfilled Skill obligations.
