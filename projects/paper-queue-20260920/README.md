# Ascend paper piercing queue (2026-09-20)

This directory is the queue-level audit for the ten-paper campaign on
Qwen3.6-27B and Ascend.

The acceptance target is deliberately stricter than a paper reproduction:

- plugin/monkeypatch delivery for vLLM-Ascend;
- physical NPU4-7 only;
- at least 10% end-to-end output-throughput improvement against the matching
  baseline, with TTFT and TPOT reported separately;
- LongBench-v2 and GSM8K must not regress;
- numerical correctness must precede performance claims.

The ordered queue is complete. See [QUEUE_SUMMARY.md](QUEUE_SUMMARY.md) for the
human-readable result and [evidence/queue-audit.json](evidence/queue-audit.json)
for the machine-readable evidence index.

The queue completion does **not** mean that the general acceptance target was
met. HYPIC crossed the performance threshold for a shared-prefix workload, but
its measured quality deltas were slightly negative. The other nine candidates
did not produce an accepted end-to-end candidate.
