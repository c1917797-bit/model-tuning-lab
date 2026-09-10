# Algorithm audit and claim boundary

> Historical audit: factual selector/proxy observations below remain evidence,
> but its blanket closure of heterogeneous/rank-budget research and claim that
> a specific runtime mechanism is the only allowed next branch are superseded
> by EXTENDED_RUNTIME_RESEARCH.md and the user's algorithm-first steering.
> A proxy is not an accuracy or end-to-end impossibility bound. See
> RANK_BUDGET_48_80.md for the new representative NPU width admission.

## Decision

The load-time tensor slicing and the official-raw selector structurally match the
pinned upstream implementation, but the currently measured Dk64 candidate uses
energy-kernel. That selector is an experimental joint normalized Q/K energy
top-k method, not Strong RRQR. Historical plans remain immutable; their
top-level provenance.method = DRRQR label is too broad and must not be used to
claim paper-exact DRRQR.

New plans now record both an objective-specific method and
paper_exact_selection. Only official-raw sets the latter to true.

## What was checked

- Pinned reference commit: 919d8667d951c385e08510bc1267c2e7049a4f56.
- Pinned reference rrqr.py SHA-256:
  fa4bacf516011ba1c88f2e0e92957bbe4513cc1bb6634912fdb0d06ba7821a62.
- Official path: concatenate post-convolution Q and K, reshape by head, run
  Strong RRQR independently per head, and slice the matching Q/K projection and
  convolution rows.
- Plugin path: the same topology and slicing for official-raw, adapted to TP4
  by selecting each rank's local heads and rebuilding the global per-head map.
- Official launcher uses 16 batches, batch size 1, sequence length 2048, seed
  42, and FineWeb-Edu sample-10BT.
- Delivered adaptation uses 16 LongBench-v2 non-evaluation rows of 2048 tokens.
  Its manifest proves zero evaluation-ID overlap, but it is not the paper's
  calibration corpus.

## Selector stability probe

The frozen 16-row capture was audited on representative linear-attention layers
0,12,25,38,50,62, every TP rank and every local head, using four-fold heldout
joint normalized Q/K energy.

For Dk64:

- median heldout oracle regret: 0.187284 percentage points;
- P95 heldout oracle regret: 1.469821 percentage points;
- median train-vs-heldout coordinate overlap: 92.1875%;
- median train-vs-full coordinate overlap: 98.4375%.

This passes the predeclared stability gate (median regret <= 1 pp and P95 <= 2
pp). It does not prove cross-domain representativeness or downstream accuracy,
but it rejects simple within-sample coordinate instability as the primary cause.

Report:
/cache/cch/state-reduction-qwen38-drrqr-aligned-20260908/dk64-energy/preflight/calibration-stability-representative-v1/report.json

Report SHA-256:
9e896c0f83e938cf9c2d5c64b665209ca5208ded33fd09be964a89d5186456c1

## Accuracy and performance boundary

The energy selector improves the frozen in-calibration proxy versus
official-raw (QK score RMSE 0.0231973 versus 0.0359613) but that proxy is not a
downstream accuracy result. Its available LongBench-v2 preflight remains below
the unpruned baseline.

A later all-48-layer frozen proxy also compared energy-Dk64 with the supported
kernel-normalized StrongRRQR Dk64 selector. Energy remained at RMSE
0.0231972667 while kernel-normalized StrongRRQR reached 0.0343228833, a
47.960894% worsening. It therefore failed its predeclared NPU-admission gate
and no native teacher replay was run. This rejects that selector candidate,
not DRRQR or a recurrence-aware coordinate objective. Report SHA256:
71d2a657f6fd8c9fb5b1392f0ea13eef086aba1434b9f297011d4f23e4453305.

A subsequent causal-interaction-energy selector used only calibration captures
0-11 for coordinate selection and reserved captures 12-15 for its deciding
proxy. It ranked each coordinate by the squared diagonal contribution from
historical keys to later queries. On the held-out captures, Dk64 normalized-QK
RMSE worsened from 0.022558974 for energy-Dk64 to 0.079352171, or 251.754350%.
The causal selector retained only 0.535215 mean Q energy versus 0.777442 mean K
energy. It therefore failed before NPU replay. This rejects the diagonal causal
surrogate, not covariance-aware or direct state-sensitivity selection. Report
SHA256: 77e08035e819c6d680da929687cb8b65d5ce5a45df3784b4914c90c34df5bad9.

A bounded follow-up started from the frozen energy-Dk64 map and optimized the
exact causal normalized-QK score under per-head 98% Q/K marginal-energy floors.
On six representative layers and all 96 local heads, four train-only exchanges
per head improved mean train RMSE by about 11.7% and 67/96 heads improved on
held-out captures. Aggregate held-out RMSE improved only 2.163152%
(0.027786426 to 0.027185363), below the frozen 10% gate, and three heads
worsened by more than 5%. It was therefore rejected before NPU replay. The gap
between train and held-out evidence points to excessive search capacity or
insufficient training-token coverage, not a proven endpoint or state-fidelity
gain. Report SHA256:
32ce108ce430e81e221547b6b9244d47a9971ddab5d54cad4ae9bc500dd1b38a.

The predeclared regularized check then increased training coverage from 16 to
64 tokens per calibration capture and limited the search to one swap per head.
It improved 82/96 held-out heads, had no head regression over 5%, and kept every
Q/K energy ratio above 0.991. Nevertheless aggregate held-out RMSE improved
only 2.268935% (0.027786426 to 0.027155970), still far below the 10% admission
gate. This reduces the likelihood that the prior failure was merely too little
training data or too many swaps. Further Q/K-only selector tuning is not the
next branch; direct recurrent state/post-RMS sensitivity on non-evaluation
calibration inputs is required. Report SHA256:
c110a0dc37b7b0eed976dc81c5f0bfc2ab873f738f9fb4f3cac1f239b2fb6300.

Changing the coordinate selector while keeping Dk64 leaves all runtime tensor
shapes unchanged. Therefore it may recover accuracy but cannot close the
measured performance gap from +4.752041% to the required >=10% throughput.
The paper's own workflow explicitly places LoRA fine-tuning after pruning to
recover performance; a no-training, no-accuracy-loss result at 50% pruning is a
stronger requirement than the published workflow.

An exact mixed-layer energy-budget audit also rejected heterogeneous Dk as a
current no-training prototype. At the same average Dk64 budget, the best
allocation over Dk32/Dk64/Dk128 improves mean retained energy by only0.097074
percentage points and changes just6/48 layers. It is not supported by the
current global-Dk model/cache contract and has no lower aggregate Q/K
arithmetic than uniform Dk64. See `LAYERWISE_ENERGY_BUDGET.md`.

## Bounded conclusion

- Do not label energy-kernel results as paper-exact DRRQR.
- Do not start a large calibration sweep: the representative stability gate
  passed and selector changes have zero performance headroom.
- Do not run formal three-round performance or final accuracy for a candidate
  still below the throughput gate.
- Do not implement heterogeneous per-layer Dk from the current proxy: its exact
  same-budget gain is only0.097074pp and it cannot supply missing throughput.
- The present same-stack, no-LoRA branch has not met the joint target.
- Historical conclusion, superseded: this audit previously required the next
  branch to be a Dk64-specific runtime mechanism. That restriction is not
  current project policy and must not be used to block algorithm-first selector,
  rank-budget, or recurrence-compensation work.
- Current boundary: test a named DRRQR algorithm change first. Modify cache or
  operators only when the change enables that concrete candidate or addresses
  its measured Ascend bottleneck; then prove the integrated path and paired
  endpoint headroom before final task-accuracy testing.
