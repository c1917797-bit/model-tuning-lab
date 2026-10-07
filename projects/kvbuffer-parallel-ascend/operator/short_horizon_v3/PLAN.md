# KVBuffer short-horizon adaptation — pre-registered 2026-10-07

Hypothesis: the independently observed incoming-state reconstruction drift,
not only the current-step reduction, caused the original BF16 midpoint crossing.
Shortening the deferred materialization lifetime may reduce that history error
while retaining the paper mechanism: FP32 base is written only once per eight
live updates, not every token. This is a distinct Ascend adaptation, not a
claim that the paper's reported configuration or performance is reproduced.

Primary variable: materialization interval16 ->8. Retain LOG_CAPACITY16,
all DMA/UB layouts, sixteen-lane/four-level vector tree reductions, native
current-step arithmetic, metadata stride32, FP32 state, BF16 input/output,
dead-lane mask-before-exp, active-only native output domain, original native
library/source pins and OUT_LIMIT=.00303 / STATE_LIMIT=2e-6.
Do not simply set LOG_CAPACITY8: the existing four-level TreeFold result
location and sixteen-lane DMA contracts would then differ.

Independent namespace qwen36_kvbuffer_short_horizon_v3; independently named
ASC kernel/wrapper/tiling/torch exports. Default OFF; no vendor registry,
runtime, image, existing candidate source, manifest or old result overwritten.
An existing sixteen-step cache is NOT admissible for this new eight-step
protocol; source, algorithm identity, lifecycle and graph keys must bind
the interval. Existing cache allocation bytes are unchanged, not savings.

Predeclared progression: actual no-device compile/export/load/schema/Meta;
full B16 160-step eager1 + changing-feedback graph3 with19slots, inactive
rows, untouched slot/log/input checks, resets64/112, complete/per-head FP32
state, original gates, guards and pointers. Retain first complete raw failure;
no automatic retry or threshold adjustment. If B16 passes, continue complete
B1..16 native gates and actual48layer/4rank lifecycle before model candidate.
No single saved step, sample, CPU or microbenchmark substitutes for these.

Formal E2E remains fixed1024 output, same stack/common optimizations dense,
>=10% throughput plus separate TTFT/TPOT, and final thinkingOFF/max2048
LongBench-v2/GSM8K. Latest user <=1% task loss must be reported in both
percentage-point and relative form, alongside original no-loss audit.
All E2E/task/serving claims are pending. No throughput inferred from lower
state writes or numerical tests.

Physical4-7 only; protect0-3 and actual outside HYPIC. Numerical stages use
only a fresh scoped owned card with summed ordinary-RAM/CPU/disk budget and
unchanged reserve; preregistered within-paper shards can use all four only
after joint admission. TP4/formal timing is exclusive. Stop/retain only exact
owned containers; no rm, hugepage resizing or outside process interference.

KVBuffer cutoff 2026-10-08T08:29:54Z; portfolio cutoff
2026-10-09T11:17:31Z; neither reset by this adaptation.
Actual compile/load/NPU source-bound receipts must precede promotion.
Rollback is simply never enable or disable this explicit experimental opt-in,
preserving the attempted source, first error, raw and Git history.
