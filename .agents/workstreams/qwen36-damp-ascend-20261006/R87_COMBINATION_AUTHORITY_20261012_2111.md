# R87 combination authorization and decision rule

Human authorization on this turn: a single technique need not individually reach 10%; multiple techniques may be combined to achieve the unchanged end-to-end throughput target.

This addendum does not change the frozen R87 authority bytes or its cutoff, 2026-10-13T08:06:34Z. HYPIC remains a historical reference, not a new success in this campaign.

Retain a numerically correct, validly paired positive single-technique candidate even when its measured throughput gain is below 10%. This is a retained candidate, not an accepted deployment. Prefer complementary bottlenecks; reject redundant cache ownership or incompatible state/layout/head mappings before NPU execution. KIVI and SKVQ are alternative low-bit cache routes, not a default double-quantization stack. AdaKV plus one low-bit route is only a hypothesis and requires a unified, explicitly verified cache owner.

Evaluate dense, A, B and A+B under the same stack, inputs, concurrency and common optimizations. Do not add single-technique percentage gains or kernel timing totals. The combination itself must pass independent real-NPU numerical/state/lifecycle correctness before performance admission. Compare A+B directly with the same dense reference; record interactions and plugin dispatch evidence.

Formal performance remains three paired whole-model rounds, output fixed at 1024 tokens, profiling and numerical observers disabled, separate TTFT and TPOT. Final combined LongBench-v2 and GSM8K remain thinking-off, max output 2048 and normal EOS. Report both percentage-point and relative quality losses against the frozen dense reference; the latest human tolerance of 1% applies to task scores, not intermediate tensor errors. If the interpretation differs between percentage-point and relative thresholds, report both and do not silently choose the easier criterion.

Current evidence limitation: AdaKV current dense007 genuinely loaded TP4 weights, but failed during warmup before the measured 1024-token requests. The first recorded exception is evidence.py attention_forward: unsupported graph/attention state; later computed timeline rewind is not yet an independently established primary cause. This is an observer/adapter failure requiring attribution and repair, not evidence that AdaKV has no performance value. No legal dense007 throughput result or new combined acceptance exists.

Preparation runs in parallel; MAIN owns admission and scheduling of physical NPU4-7. Whole-model paired performance has exclusive use. Never manufacture a dummy load to claim utilization, and never lower correctness gates to meet an occupancy target. Research success cannot be guaranteed; invalid implementations must be distinguished from valid measured no-benefit configurations.
