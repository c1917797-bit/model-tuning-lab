# Model-quality Skill: r16 full original-source negative case

The prospectively frozen original `3ad0967` no-cache/HYPIC-only
LongBench-v2 max-2048/c8 pair on physical NPU0–3 completed all 127×3
responses per arm. Independent replay verified response/scorer hashes,
matching source/service identity, 999/1078 clean guard observations and
exact owned release. Full report:
`HYPIC_R16_ORIGINAL_SOURCE_FULL_TERMINAL_AUDIT_20261010.md`;
external audit SHA256
`52914becb93266ac4a27e8491b40bf8456b566ee8f828038250098bfec33a4ee`.

Baseline 224/381 fell to candidate 210/381 (−3.6745 pp), with
repetition counts 71/78/75→70/71/69, 16 paired wins/30 losses,
easy/short cliffs and length finishes 52→64. The predeclared quality
gate is `REJECT_OR_QUALIFY`. Candidate controller exit 1 reflects
the separate aggregate hot-coverage shortfall 364/381 *after*
complete scoring; it neither erases the adverse quality observation
nor proves per-request four-worker activation.

Reusable boundary: historical 1024/c32 success is not a matching
baseline for 2048/c8; selected examples and r13 performance cannot
promote this full negative pair. The Skill remains partial for its
default LongBench-v2+GSM8K/c32 and deterministic-canary acceptance,
which this case did not test.
