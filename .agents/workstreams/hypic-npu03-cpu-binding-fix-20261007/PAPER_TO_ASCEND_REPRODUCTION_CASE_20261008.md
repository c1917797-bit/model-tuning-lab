# HYPIC reproduction Skill: exact-main real-task partial case

Tested locally tracked main ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2:
paper-to-ascend-reproduction Skill blob
d0298d9fdf1ce7ba27f1bd711d26834b6bd7b6aa, evidence-contract
reference blob 582852d43b5550594da257b1a274a84103542411, and registry
blob 2611864bbcf719d57920aae03ff9eb85521526b4. The work branch's
Skill body is a different blob, 90fd7d45e7b0630c81c2a0c3694c46e4995131dc:
it adds absolute-versus-percent cross-lane effect decomposition. That
branch-only guidance is not attributed to main.

Real task: reproduce the bounded HYPIC C1/C2 service effect on the
Qwen3.6-named hybrid text checkpoint, with physical NPU0–3 TP4 and an
unchanged official image. The historical frozen performance pair changed
only VLLM_ASCEND_HYPIC_ENABLE, with the supported CPU-binding-off repair
common to both arms. Its independent audit SHA256
de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1
verifies six 40-request/1024-fixed-output c16 units, command identity,
worker activation, release, and a 22.3562% lower median weighted TPOT
for that workload. This is a bounded service-performance decision, not
the later quality protocol or the whole paper.

The separate clean2 natural-EOS 2048-token quality audit SHA256
61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0
proves all 12 units, paired/repeated inputs, the one-switch difference,
752/754 clean lane-guard samples and exact release. It also proves the
predeclared formal activation gate failed: zero distinct worker_hot_path
PIDs, while four were required. Its formal_acceptance_claim is false.
The scores are descriptive ordinary-chat results only; they are not
losslessness or hot-reuse quality acceptance.

The successor r13 experiment has a different frozen identity (0.85
utilization, cache10, source c12060c). Its paired explicit-segment max-2048
quality test completed 127 prompts x 3 repetitions per arm. The no-cache arm
scored 230/381 and HYPIC scored 219/381, a -2.8871 percentage-point delta, so
the deployed quality decision is REJECT_OR_QUALIFY. Quality-path four-worker
coverage was 368/381, so strict mechanism attribution is
NOT_ACCEPTED_HOT_COVERAGE.

The matching performance campaign is also complete. Six independently audited
40-request units use input 32768, output 1024, concurrency 16, physical
NPU0-3, and the same source/image/config except the HYPIC switch. All 120
candidate scored requests have four-worker hot proof. Three-run medians are
74.727578 versus 58.643006 ms weighted TPOT (21.5243% faster), 86.628571
versus 45.759196 seconds TTFT P95, and 1.298735x throughput. The performance
decision is EFFECT_SCREEN_PASS.

The reproduction Skill's separation of scientific question, one-switch
denominator, activation, quality, isolation, and independent audit yields the
correct split conclusion: the bounded HYPIC performance mechanism reproduced
successfully, while unconditional deployment is rejected or must be qualified
because paired quality regressed and universal quality-path attribution was
not proven. This is a completed HYPIC case with a mixed technical verdict, not
a claim that the whole paper or every main Skill is accepted. Main-version
behavioral verification remains partial because this work branch contains
guidance not yet integrated into main.

Replay with
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_to_ascend_reproduction_case.py.
The case verifier pins main/branch blobs and the historical evidence. Replay
the current six-phase raw receipts with
`verify_hotpath_cache10_matched_performance.py`. No completed HYPIC phase
should be rerun. Keep 4-7 and foreign containers untouched; integrate no
unaccepted candidate into main.

## Opportunistic phase-6 retries: environmental, not technical results

After the preceding retry failures, the user authorized monitoring and use of
physical NPU0–3 only while those devices and port 8223 are actually unused.
This did not authorize stopping or altering another workload. Retry19 and
retry20 each began from a fresh idle preflight, then the continuous physical
process guard caught the external `cannbench_ds` container before the owned
service became healthy:

- Retry19 captured PID 1731309 on physical NPU2 (46 guard samples, zero probe
  errors); no benchmark rows or performance metrics were produced. The exact
  retry19-owned service container was removed.
- Retry20 captured PID 1890601 on physical NPU3 (36 guard samples, zero probe
  errors); again there were zero benchmark rows and no performance metrics.
  The exact retry20-owned container was removed. A 14:38 UTC follow-up still
  saw external PIDs 1890601 and 1920829 on NPU3; port 8223 was free.

The external container's human launcher is unknown; its passive device mapping
is not the evidence—the physical NPU process is. Neither event says anything
about HYPIC speed. Do not merge these attempts, reuse their roots, or count
them among the six performance phases. Continue only when a new direct-route
snapshot proves NPU0–3 and port 8223 idle, preserving the r13 quality rejection.
Replay the immutable receipts with `verify_retry19_environmental_failure.py`
and `verify_retry20_environmental_failure.py`.

Retry21 then began from a fresh idle snapshot and completed without a foreign
process entering the lane. It produced 40/40 fixed-output scored rows, 42
unique IDs including warmups, 40/40 request-level four-worker hot proof, and
164 clean guard samples; the exact owned container and port were released.
This valid retry21 measurement filled the sixth phase and enabled the terminal
six-phase audit. See
`HOTPATH_CACHE10PERF_RETRY21_AND_SIX_PHASE_TERMINAL_AUDIT_20261009.md`.
