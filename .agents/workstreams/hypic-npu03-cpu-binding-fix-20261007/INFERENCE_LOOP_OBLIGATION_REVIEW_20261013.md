# Inference-loop obligation review — 2026-10-13

Scope: historical CPU-binding-off no-cache case, not a new HYPIC experiment.
Exact-main Skill commit ead80810b7019bdc9ae410ebe883fc5dfbd8f0c2,
blob 010d1a8bd5ab21fcdff6c50e3bad74f974ccae8d.
Inspection: mc operations0030–0033; repaired replay0034 exit0.
Host Euler, worktree model-tuning-lab-hypic-e2e-20261006.
No new NPU work, runtime edit, deployment or main integration.

## Seven stages against retained evidence

| Stage | Retained evidence | Conclusion / boundary |
| --- | --- | --- |
| planned | d8a5a936bf6ae342caec4708d20da64398730c4a introduces the44-line experiment contract | Hypothesis, one variable, source/image/workload, baseline hashes, numerical thresholds, progression and cleanup precede the tracked launcher. This is Git ancestry evidence, not proof of every unrecorded action. |
| baselined | The initial plan names three frozen baseline hashes; existing independent verifier reads all three | Baseline reuse is real and hash-replayed; no need to repeat it. Full software/tokenizer environment identity and original baseline-stage push chronology are not established by this review. |
| attempted | 3a1c554a6e65bbd74045cd2a351d1fea318b2a54 is a direct child of planned | Isolated opt-in launcher changes enable_cpu_binding only. A supported configuration treatment, not a novel monkeypatch or proof of an internal CPU-pool subcause. |
| verified | e12651173c6334170910ddac9eb0798cc867244e records semantic/service smoke | Retained semantic/activation claims are source-scoped. This review's raw verifier checks performance contracts and cleanup, not every semantic token or pre-edit runtime import; those are not promoted from text alone. |
| measured | 85410c78b542f5e8a2ea7fc947502999bfa8e83f;5977e56523decba485d100230943de9512e558b8;090892bc43dbcdc9a0db76815fd83651f6cc698c | Three candidate repetitions, six raw performance hashes, exact workloads and three releases replay. First-screen arithmetic repaired below. |
| decided | 090892bc records partial_component and separates performance from quality/adoption | Bounded performance result is valid; incomplete binding-on/off quality is not repaired by later HYPIC comparisons with binding off in both arms. Negative/incomplete outcomes are valid workflow outcomes. |
| recovered | Exact owned container/NPU/port release receipts for all three candidates; opt-in launcher retained | Resource recovery is proved by the receipts. It is not disable-uninstall-restart serving proof or proof of the entire branch's integration safety. |

The six named commits form a direct-parent chain; the experiment file later
accumulates source-scoped HYPIC extensions rather than seven literal status
labels. Chronological sections are evidence of local progression, not evidence
that every stage was immediately pushed. At inspection HEAD23685bf9 was140
commits ahead of its cached upstream eec5b9581403c6718ac72d29dca5a342ecc34e44.
No fresh remote equality or historical push timing is claimed; authentication
is unchanged, so no repeated failed push was attempted.

## Actual replay defect and repair

The old verifier compared the three-repeat median against a20% threshold and
called it the predeclared fail-fast gate. The initial plan instead specifies
the FIRST screen against the frozen baseline MEAN. Later fast repeats could
therefore mask a failing first screen in a general regression fixture.
The verifier also omitted the screen's TTFT P95 no-more-than10% regression
check. Repaired code preserves the descriptive median but checks the actual
first-screen TPOT denominator separately.

The original TTFT statement does not name a baseline aggregation. We did NOT
retroactively select or freeze one: the replay reports each baseline's P95,
their mean and their median. It only claims an unambiguous historical TTFT
pass when all these retained rulers agree; disagreement is explicitly
ambiguous, not an invented historical failure or a replacement device gate.

Raw replay0034:
- baseline TPOT mean413.0985279535679ms;
- screen TPOT77.5640789833808ms:81.22383070023939% reduction, pass;
- screen TTFT P9580775.48966999166ms;
- baseline TTFT P95 mean84881.72581999486ms, median81137.27383999503ms,
  individual values92633.5489799967/81137.27383999503/80874.35463999282ms;
- all five retained TTFT comparisons pass the original10% limit;
- descriptive three-repeat TPOT median reduction remains81.12318290741513%.

Eight negative/boundary tests passed: first-screen failure despite potentially
fast later repeats, mean-versus-median distinction, inclusive thresholds,
TTFT failure, ambiguous ruler, invalid metrics, missing metric, missing runs.
No original raw file, experiment contract, threshold or outcome was changed.
Retry14 remains an environmental zero-score failure with exact owned release.

## Remaining original obligations

The initial opportunity estimate is a profiled short-run difference of about
358ms/token, explicitly not an unprofiled formal bound. A full pre-edit exclusive
wall-time/call-count/shape/coverage opportunity calculation and pre-edit runtime
object proof are not established by the inspected records. They cannot be
created retrospectively. Neighbor-resource acceptance is not proved just by
owned-container cleanup. Every-stage upstream equality, full recovered-tree
integration and fresh-main execution remain unproved.

Thus the existing planned/measured/decided/recovered review is complete, but
the Skill remains partial-evidence. Do not repeat old device phases, history
inspection or the same raw replay solely to raise the count. Future genuinely
needed work should retain these missing facts prospectively; remote integration
requires restored authentication and its separate review. The current4429
performance supplement and r19 quality rejection are unchanged.

Replay from repository root:
python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_inference_tuning_loop_case.py
Tests:
python3 -B -m unittest discover -s .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007 -p test_inference_screen_thresholds.py
