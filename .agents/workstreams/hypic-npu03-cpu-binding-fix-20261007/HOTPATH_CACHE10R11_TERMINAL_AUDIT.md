# cache10r11 targeted stress: terminal negative activation and eviction chain

At 2026-10-08 20:49:45 UTC, sole AWMCP controller
`exec-0000000000001830` terminated with exit 1. The immutable root is
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r11-stress-hypic`.
The service mounted plugin source commit
`62b0d4a89234ffaa69855427e0c0dad0ba3e9e41` read-only. Do not rerun or
relabel this root; the later source fix `c12060cd47e7575ead059983d7a8bb4704165c98`
was **not** present in its NPU run.

## Frozen scope and independent result

Physical NPU0-3, TP4, c8, 0.85 GPU utilization, 3,584 MiB/ten-segment
material cache, native prefix-cache read disabled, max output 2,048 with
natural EOS, two one-token observations and three scored requests per sample.
The predeclared 19 distinct LongBench-v2 indexes were 75-91, 107 and 111.
All 19 sample files and 57 scored responses persisted. The independent
`audit_cache10r11_stress.py` verified frozen model/image/source, dataset,
evaluator, payloads, scorer, response hashes, physical PID namespace join,
guard and exact release before returning exit 2. It found 27/57 correct,
45 stop and 12 length finishes in this **single stress arm**. This is not a
paired quality or performance result.

Only 53/57 scored requests had positive skipped-token and post-repair proof
on all four namespace workers. Missing pairs are 77:2, 79:2, 79:3 and 85:2.
All four had unique boundary joins but no worker-hot proof. r10's same 19
sample indexes had 47/57 proof and ten gaps; the source, cache state and
concurrent scheduling differed, so 47-to-53 is a descriptive contrast,
**not** an effect estimate or acceptance of r11. In particular, r10's 86:1-3
were missing and r11's 86:1-3 had proof.

## Request-local diagnosis

- 77:2: hash `5c0fb252aa059de9a68efe3cb586b30b` was reported ready,
  then evicted before this scored request was admitted. The scored request
  became a zero-start replacement producer; its own continuation logged
  `computed_prefix_not_reusable_boundary` with no ready hash. This is a
  cold fallback, not a hot hit.
- 79:2: hash `38d6911f3ca386df7c1e3a8a708500ca` was ready at admission.
  A 77 materialization then evicted it before 79:2's pending request was
  scheduled. 79:2 emitted a replacement `materialization_candidate` but no
  worker-hot proof. The worker later reported that hash ready while the
  scheduler's `materialization_report` recorded `ready=0`: its directory
  entry had been removed by the eviction and was not recreated at ordinary
  materialization commit.
- 79:3: the same hash was absent from the scheduler's ready set at admission;
  this request logged `no_hot_rewrite_or_materialization`. The worker's
  material was later evicted again. The 79:2 directory inconsistency is a
  concrete antecedent, though the full replacement-policy contribution is
  not separately measured.
- 85:2: hash `5c578bad215319848a1cc9615cb7d9f2` was ready then evicted
  before admission. This scored request became a replacement producer and
  logged `computed_prefix_not_reusable_boundary`, with no worker-hot proof.

This is evidence of capacity/eviction-dependent activation under c8, not a
0-3-card communication or external-process fault. Source inspection found
that `_commit_materializations` only updated an existing scheduler cache
entry. The later `c12060c` source change recreates a pending entry when an
eviction removed it between admission and commit; a focused regression was
red before the change and green after it. It addresses the 79:2-to-79:3
directory chain, **not** every cold fallback caused by a ten-segment LRU.
No NPU result exists yet for `c12060c`.

## Isolation, hashes and code checks

The guard sampled 283 times with zero foreign processes/probe errors. The
exact owned container `38745b242a900344daaaea606d94f2ebc6f9f5e3208c707ec07f0bfd6d13470f`
was removed; receipts assert owned NPU/port release, and a subsequent
`npu-smi info` found no NPU0-3 processes while `ss` found no 8223 listener.
NPU4-7 and foreign containers were not modified.

- `contract.json` SHA256: `80241f30394982ec58ff163d73384902ca35eec1ab1580011f074e3999a41bc8`
- `arm-result.json` SHA256: `246bf5c0d5fb324019994206e5aeacb9ef9d474b6a5dbad1d678a69b770653d9`
- `hypic-only/hypic-evidence.jsonl` SHA256: `a9164c287c0d03c4220b404ee130cca5a677f83839882fc0f1da48e456421fcb`
- Ordered sample manifest SHA256: `dd973e7c9134ea4a75b7f4eb18ddf3b5f2db5328cc8309b5204d0b734129d830`
- `hypic-only/lane-guard.json` SHA256: `1ce756ed6c7c648470443bcdcf0da373a78f2c621f46fc18ef56a6cf31e7903f`
- `hypic-only/service-stop.json` SHA256: `31edb411c5ec815d704406765ef30adcc788cd395b61c3e2fd19f43307f7950a`

For the successor plugin source, 13 focused pytest cases and compile checks
passed. The Qwen3.5 single-instance/upstream hot-reuse audits and TP4/DP1
topology passed; upstream-complete/paper-complete/C3 topology correctly
failed because distributed C3 is missing. The host's broad `test_pure.py`
collection remains blocked by system Python 3.9 lacking `itertools.pairwise`;
do not claim a full test-suite pass or hardware validation for the fix.

## Next decision boundary

r11 remains a predeclared strict-activation **fail**. Do not turn it into a
pass after seeing 53/57, rerun it unchanged, or reuse a 0.9 baseline against
the 0.85 service. The next full 2048-token paired ruler must be declared
prospectively: either require every scored request to be hot and solve the
bounded-cache activation problem first, or preserve all original requests
and treat request-level hot/cold activation as a separately reported
stratification of the real deployed treatment. In either case, a new source
needs its own NPU canary, matching control, quality/performance/isolation
audits and Skill acceptance before any HYPIC conclusion.
