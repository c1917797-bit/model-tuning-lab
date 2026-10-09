# Model-quality Skill: r13 terminal negative real-task case

This case exercises the exact current-main `ascend-model-quality-evaluation`
contract against a terminal HYPIC NPU0–3 task. It does not upgrade the Skill
to a portable pass: the main reference lacks the branch's request-ID/four-worker
join, this ruler contains LongBench-v2 only at c8 (not the Skill's default
LongBench-v2+GSM8K/c32), and short deterministic canary equality has not been
accepted for this source. Those are explicit scope gaps, not reasons to
relabel the completed 127×3 paired result.

- Frozen c8, natural-EOS, max-2048, no-thinking, seed/temperature 0,
  explicit-boundary LongBench-v2 baseline/candidate used identical data,
  scorer, image, source, model, physical NPU0–3 and service fingerprint; only
  HYPIC enablement/evidence path differed.
- Both arms independently passed all 127 samples/381 scored responses,
  per-sample output-hash/scorer replay, source attestation, continuous
  isolation (998/1080 clean guard probes) and exact owned release. Candidate
  controller exit 1 was the predeclared strict coverage failure, not missing
  data or an invalid environmental pair.
- The frozen dual audit at external SHA256
  `f66b9760bfb4f9391863cd386658211c58ab07d0dfc2de58ea2091ed4d2c9b7b`
  reports 230/381 baseline versus 219/381 candidate (−2.8871 percentage
  points), paired 19 wins/30 losses, and easy/short category cliffs.
  Therefore the all-request quality decision is `REJECT_OR_QUALIFY`.
- The request-ID/four-worker strict gate is separately `FAIL`, 368/381.
  All 13 missing IDs have material ready → evicted → partial-prefill
  rejection ordering under the frozen 10-segment cache. The aggregate
  complete-repair counter 369 is not 368 scored-ID proof.
- Hot-request quality also declined descriptively, 226/368 to 212/368;
  cold-request quality moved 4/13 to 7/13. These post-hoc cohorts do not
  isolate why output answers changed; cold fallback alone cannot explain
  the aggregate regression. Candidate length-limit count 60 versus 48
  baseline is another diagnostic signal, not proof of causation.

The exact local report is `HOTPATH_CACHE10R13_TERMINAL_QUALITY_AUDIT.md`.
The independent frozen dual auditor and the separate eviction-sequence
diagnostic are replayable; the latter is descriptive, not an acceptance gate.
Performance may be measured under its predeclared evidence-valid entry gate,
but speed cannot turn this quality rejection into a pass. Before upgrading
this Skill case, integrate and replay the request-level proof requirement on
main, assess the absent default-ruler dataset/canary requirements, and test
any proposed quality repair against a new same-identity control.
