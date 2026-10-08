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

The successor explicit-segment r12 stress is a different experiment
identity (0.85 utilization, cache10, c8/max2048, source c12060c).
Its independent auditor ended negative after 19/19 prompts, 57/57
scored answers, 52/57 request-level four-worker hot proofs, 279 clean
guard probes, and exact owned release. One cold request had a
short-first-prefill-chunk boundary; four were scored producer paths.
No matching no-cache control or full paired quality/performance result
exists for that source. Neither the old clean2 scores nor the old
1024-output performance rows may be substituted for this missing pair.

The main reproduction Skill's separation of scientific question,
one-switch denominator, activation, quality, isolation, and independent
audit yields a correct fail-closed boundary in this case. It has not
completed its own full completion gate: current explicit-boundary
mechanism coverage, same-identity control, complete 2048-token quality,
repeated current performance, and final adoption audit remain open.
Therefore long-term acceptance is partial-evidence, not paper success
or main-version behavioral verification. A correct negative decision
is valuable evidence; it is not a fabricated successful reproduction.

Replay with
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_paper_to_ascend_reproduction_case.py.
The verifier pins main/branch blobs and the historical performance and
natural-quality artifact hashes, then replays r12's raw strict negative.
After the prospective deployed-effect versus all-hot decision rule is
fixed, a new same-identity pair may run only on actually idle physical
NPU0–3 with continuous foreign-process guard. Keep 4–7 and foreign
containers untouched; integrate no unaccepted candidate into main.
