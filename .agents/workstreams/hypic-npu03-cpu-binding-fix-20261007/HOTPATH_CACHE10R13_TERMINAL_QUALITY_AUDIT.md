# r13 full paired quality: valid evidence, negative outcome

2026-10-09 UTC. Frozen LongBench-v2 127 samples × 3 scored responses,
max output 2048, c8, explicit `[boundary, prompt_tokens]` segments,
Qwen3.6-27B TP4 on physical NPU0–3, source `c12060cd47e7575ead059983d7a8bb4704165c98`.
The only serving-arm differences were HYPIC enablement and evidence path.

## Terminal provenance and isolation

- Baseline controller `exec-0000000000001a76` exited 0; its contract/arm-result
  SHA256 are `79ef620ab90a1f5925e6155b03b30de3c396ba1cb2e379108ec593f3a4661d23` /
  `d348af20d07dab5d34dfa3b2fbf68d310f716f1a9e6aecf91e1d467ad63a5449`.
- Candidate controller `exec-0000000000001bb1` exited 1 after all 127/381;
  its exact error is `RuntimeError: candidate scored boundary/hot coverage incomplete`.
  Its contract/arm-result SHA256 are `d7a169d11e8ddfaf7c3e865cc86874b5609c6b175863b25c4a3548443622ed9a` /
  `f4ef1e4f3c2367b41121a6f49209d4d229adaa8eecdb52b050cfad1ebc97329a`.
- The independent frozen `audit_arm` rechecked every sample identity, payload,
  output hash and score, source attestation, identical environment fingerprint,
  998/1080 clean baseline/candidate lane-guard probes, and exact owned
  container/NPU/port release. No foreign NPU0–3 process was recorded.
- Frozen dual audit raw receipt:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-quality-cache10r13-dual-audit.json`,
  SHA256 `f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b`.

## Two predeclared conclusions

- All-request deployed quality: baseline 230/381 (60.3675%), candidate
  219/381 (57.4803%), delta **−2.8871 percentage points**. Paired outcomes:
  19 improved, 30 regressed; repetition correct counts 77/74/79 versus
  69/73/77. Candidate `length` finishes 60 versus baseline 48. Easy and
  short strata fell below the baseline run range. Frozen decision:
  `REJECT_OR_QUALIFY`, not a quality pass.
- Strict four-worker request-ID hot path: 368/381 scored requests proven,
  13 cold. Frozen decision `FAIL`; strict quality `NOT_ACCEPTED_HOT_COVERAGE`.
  The 369 aggregate repair counter is not the 368 unique scored request-ID
  coverage and must not be substituted for it.
- The cold cohort had 7/13 candidate versus 4/13 baseline correct, while
  the hot cohort had 212/368 versus 226/368. These post-hoc strata are
  descriptive, not causal attribution; the quality drop cannot be assigned
  solely to cold fallback.

## Bounded mechanism diagnosis and next gate

`diagnose_material_eviction_sequence.py` classified all 13 cold scored IDs:
each candidate material was once ready, then its last prior materialization
transition was `evicted`; at planner rejection, ready hashes were empty and
`computed_tokens > 0` with `computed_prefix_not_reusable_boundary`.
This establishes an observed eviction → unavailable material → native
partial-prefill sequence for these 13 requests. It does not isolate why
hot-request answers differ from baseline or prove a safe fix. The immutable
r13 roots remain negative; no post-hoc warm-only pass or root reuse.

The prospectively frozen six-phase performance follow-on may quantify
deployment effect because the paired quality *evidence* gate is valid, but
favorable speed cannot override this quality rejection or C3, which remains
unimplemented. First no-cache/screen controller: `exec-0000000000001c05`.
No main or remote integration is claimed.
