# R19 LongBench quality uncertainty (post-hoc, read-only)

The frozen repaired-source max-2048/c32 LongBench-v2 pair remains
`REJECT_OR_QUALIFY`: no-cache 227/381 correct versus HYPIC-only 219/381,
an observed difference of -2.0997 percentage points. The independent paired
audit is immutable (SHA256
`40ce887336be3446aa87a8e552fb50d366234fc10006ad5a3140f3dc0df16d9b`).
This note does **not** change its preregistered quality gate.

To check how much of the eight-response difference could reflect finite-sample
variation, read the three `correct` flags from each arm's already audited
`samples/000.json` through `samples/126.json`. Keep each sample's three
repetitions together as one paired cluster. For sample `i`, calculate
`d_i = sum(candidate_correct) - sum(control_correct)`; the 127 differences
sum to -8. Their histogram is: -3: 1 sample, -2: 2, -1: 10, 0: 106,
+1: 7, +2: 1, +3: 0.

An exploratory 20,000-draw paired cluster bootstrap used Python
`random.Random(20261010)`, sampled 127 sample IDs with replacement in each
draw, and calculated `sum(d_i)/381*100` percentage points. The percentile
2.5–97.5 interval was **[-5.2493, +1.0499] pp**; 89.32% of draws were
negative and 2.905% exactly zero. The interval includes zero. Repeated
responses for one sample are correlated, so a response-level independent
binomial test would overstate precision.

The benchmark's 127 samples were not established here as a random sample of
a broader task population; this bootstrap is a sensitivity description, not
a formal population confidence guarantee. The correct claim is that the
frozen quality gate rejects the observed pair and that the measured score is
lower, **not** that this experiment proves HYPIC necessarily causes a quality
loss. Conversely, uncertainty does not prove quality preservation or permit
adoption. Any future noninferiority/equivalence margin and statistical rule
must be chosen prospectively with a matched source and independent audit;
do not rewrite the r19 gate or reuse its roots.
