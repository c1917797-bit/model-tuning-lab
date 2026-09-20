# Ascend paper piercing queue (2026-09-20)

This directory is the queue-level audit for the ordered ten-paper list on
Qwen3.6-27B and Ascend. HYPIC is a historical successful piercing used as the
reference sample; it was not re-pierced or produced as a new result in the
current campaign. The current campaign contributes nine new paper decisions.

The acceptance target is deliberately stricter than a paper reproduction:

- plugin/monkeypatch delivery for vLLM-Ascend;
- physical NPU4-7 only;
- at least 10% end-to-end output-throughput improvement against the matching
  baseline, with TTFT and TPOT reported separately;
- LongBench-v2 and GSM8K must not regress;
- numerical correctness must precede performance claims.

The ordered evaluation is complete: nine new piercings plus the preserved HYPIC
historical reference. See [QUEUE_SUMMARY.md](QUEUE_SUMMARY.md) for the
human-readable result and [evidence/queue-audit.json](evidence/queue-audit.json)
for the machine-readable evidence index.

The queue completion does **not** mean that the current campaign met the general
acceptance target. The earlier HYPIC work crossed the performance threshold for
a shared-prefix workload and serves as the benchmark for a valid Ascend
piercing. The nine newly evaluated candidates did not produce an accepted
end-to-end candidate.
