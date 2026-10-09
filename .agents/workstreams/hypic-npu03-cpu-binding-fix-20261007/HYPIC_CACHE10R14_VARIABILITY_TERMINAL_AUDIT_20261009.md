# HYPIC r14 c1 variability diagnostic — terminal audit

2026-10-09 UTC. This is a prospective, selected-sample diagnostic of the
frozen r13 quality symptom. It does not replace the complete r13 LongBench-v2
127×3 c8 quality decision.

## Contract and evidence

- Predeclared source: `HYPIC_CACHE10R14_VARIABILITY_PREREGISTRATION_20261009.md`,
  workstream commit `3b62ae1a983fa58d56fdf7abe5d84f2093a04c4f`, independently
  checked against the remote workstream ref before launch. The historical
  controller and service files were left byte-identical; the r14 adapter
  selected new roots and c1 only in memory.
- Pinned Qwen3.6-27B BF16 TP4, official image
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`,
  plugin source `c12060cd47e7575ead059983d7a8bb4704165c98`, context
  41984, 0.85 GPU-memory fraction, 3584-MiB/10-segment material cache,
  physical NPU0–3, max-2048 natural-EOS, seed/temperature 0.
- Three length-selected LongBench-v2 indices `[0,55,48]`, prompt tokens
  `[24616,10352,39642]`; each arm used two one-token warmups and three
  scored responses per sample at client concurrency 1. The only serving
  switch was HYPIC enablement plus its evidence path.
- No-cache controller `exec-000000000000068d` exited 0 with 3/3 samples,
  9/9 scored responses, 134 clean continuous guard samples and exact owned
  release. Its separate preregistered `--baseline-only` audit exited 0.
  Contract SHA256 `157390f6d06bb65849778984072feb5c5a2dd440e432107b9b338c2110bc3847`;
  arm-result SHA256 `bfdb237a524a43b436b1b0584b04c4d76e0726eb72d3668e2b43f6ff70aa1c2f`.
- HYPIC-only controller `exec-000000000000069e` exited 0 with 3/3
  samples, 9/9 scored responses, 149 clean guard samples, exact owned
  release, and 9/9 scored request IDs joined to a boundary and all four
  post-repair hot workers. Contract SHA256
  `09ee4c3637746b0392df379179a2b5ccc9885fb00c4796b731dfea20652bf3c8`;
  arm-result SHA256 `f9ea52e709cf71a2d8a432aa61c49b876a74c146071786b54e3a021ae137c669`.
- The independent paired auditor `audit_cache10r14_variability.py` exited
  0. Immutable external report:
  `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/hotpath-quality-cache10r14-variability-audit.json`,
  SHA256 `c69692be92d70168a58fd896828a1ecadbe9bd4e0177200b728e2f23871b4cf4`.
  It replayed all request hashes, source attestations, scores, continuous
  isolation, exact resource release, and one-switch service commands/binds.
  A post-cleanup live check found no NPU0–3 process or 8223 listener; the
  exact owned containers were absent. NPU4–7 were never mapped by this task.

## Results and interpretation

| Same-sample repetition pairs on indices 0/55/48 | r13 c8 baseline | r13 c8 HYPIC | r14 c1 baseline | r14 c1 HYPIC |
| --- | ---: | ---: | ---: | ---: |
| Exact text | 1/9 | 0/9 | 1/9 | 3/9 |
| Median common prefix | 416 chars | 85 chars | 1229 chars | 1901 chars |
| Same extracted answer | 9/9 | 9/9 | 9/9 | 9/9 |
| Correct responses | 3/9 | 3/9 | 3/9 | 3/9 |

The r13 selected c8 candidate had 9/9 request-level hot proof (none of these
IDs is among its 13 cold issues), as did r14 c1. The r14 c1 candidate does
**not** repeat the excess candidate text variability seen on these same
samples in r13 c8. Index 48 moved from 0/3 exact candidate repetition pairs
at c8 to 3/3 at c1. These selected-sample observations are descriptive:
three pairs from one sample are correlated; natural-EOS output length and
runtime scheduling can differ even with seed 0 and temperature 0.

Changing c8 to c1 also changed the number/order of other live prompts,
service lifecycle time, and cache residency history. The result supports
investigating concurrency/capacity as a *bundled* hypothesis; it does not
isolate concurrency, cache eviction, CANN, HCCL, numerical behavior, or any
single causal root. No full-population quality or paper-success conclusion
follows from 9 responses per arm.

The immutable r13 verdict remains baseline 230/381 versus HYPIC 219/381
(`REJECT_OR_QUALIFY`), with strict four-worker hot coverage 368/381
`FAIL`. The six-phase performance gain remains a separate valid positive
result and cannot compensate for this quality rejection. The main
`ascend-model-quality-evaluation` Skill case remains partial until its
request-level wording is integrated and the missing default GSM8K/c32 and
short deterministic-canary gates are truly verified.

## Recovery and replay

Both r14 roots and the paired report are immutable; do not rerun or overwrite
them. `verify_r14_variability_terminal.py` is a post-run read-only replay
of the preregistered auditor and this fixed-subset comparison. Keep response
texts, model weights, datasets, and raw evidence outside Git.
