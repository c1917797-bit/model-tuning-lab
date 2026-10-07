# NPU0–3 HYPIC Decode communication diagnosis (2026-10-07)

## Verdict boundary

The apparent 0–3 Decode "slow communication" is principally a downstream synchronization wait, not demonstrated HCCS bandwidth saturation. In a sampled full-service step, rank 2 waits before its attention kernel and reaches the small AllReduce about 22.7 ms after the other ranks. The producer/condition of that pre-attention notification is **not yet proven**; this workstream is diagnostic-inconclusive rather than an accepted optimization.

The three-round frozen 0–3 no-cache TPOT weighted mean was 413.10 ms/token and HYPIC-only 399.41 ms/token. The corresponding historical 4–7 numbers were 74.51 and 60.36 ms/token. HYPIC absolute savings were 13.69 and 14.15 ms/token respectively. Do not conflate this near-equal method effect with the common 0–3 Decode floor.

## Critical-path evidence

Raw source: `/cache/cch/hypic-qwen36-e2e-2048-20261006/profiles/no-cache/decode`. The diagnostic capture used 4 requests × 128 output tokens with profiling overhead; it is not the formal 40 × 1024 timing result.

- In exported rank-0 task timeline, a trimmed 110-step Decode sample has 387.89 ms median step spacing and 356.10 ms median communication timeline union, about 91.8% of spacing. HYPIC-only is 387.90 and 356.13 ms, respectively.
- The last 30 seconds of rank-0 no-cache trace have 10,022 AIV AllReduce tasks: 8,647 under 0.1 ms (sum 0.087 s) and 1,243 from 10 to 30 ms (sum 27.255 s). The latter have median about 22.05 ms. Approximately sixteen such calls occur per Decode step. The model has sixteen full-attention layers; exact operator-to-layer mapping is still a hypothesis.
- Three CSV-exported ranks (0, 1, 3) start sampled slow collectives within 7–14 microseconds of each other and each spends about 22 ms. AllReduce task timing may include synchronization wait.
- Rank 2 CSV export was incomplete, but its existing raw `msprof_20261006155326.db` has the task rows. In the same sampled interval, rank 2's 40 KB AllReduce starts 22.666 ms after rank 0's slow-call start and lasts 0.0086 ms. Rank 2 stream 45 repeatedly executes `MEM_WAIT_VALUE` for that interval, while its stream 46 has a roughly 23 ms `EVENT_WAIT`. Thus rank 2 is a late entrant at this collective, but its upstream wait may itself depend on other ranks; do not label NPU2 faulty from this trace.
- The earliest observed divergence in that sampled step is between `reshape_and_cache` and `FusedInferAttentionScore`, **before** the collective. Rank 0/1/3 each run `reshape_and_cache` in about 3 microseconds, `MEM_WAIT_VALUE` in about 1–2 microseconds, and attention in about 0.21–0.22 ms; their subsequent AllReduce is charged about 22.7 ms. Rank 2 runs `reshape_and_cache` in about 3.58 microseconds, polls `MEM_WAIT_VALUE` roughly 7,665 times over 22.4 ms, then runs attention in about 0.216 ms and the subsequent AllReduce in about 0.009 ms. This is timing/ordering evidence, not proof that the notification originates locally on rank 2.
- The rank-2 raw database's trailing-30-second 40 KB AllReduce tasks have median 0.00925 ms, P95 0.01375 ms, and no task over 10 ms. The other ranks' slow duration is wait-dominated. The matching HCCL task metadata records size 40,960 bytes, BF16, algorithm `MESH-RING-NHR`.

## Controlled NPU0–3 probes

Only physical devices `/dev/davinci0` through `3` were mapped. The exact pinned service image digest `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`, TP4, AIV expansion, CPU set 112–191, and matching driver mounts were used. Preflight found no NPU0–3 processes. The pre-existing all-card-declaring sleep container was not touched; NPU4–7 had no diagnostic mapping or process.

1. `hccl_allreduce_probe.py`, operation `exec-0000000000000892`: 80 measured calls/rank after warmup. At 40 KB, four-rank medians were 0.260–0.262 ms; at 160 KB, 0.246–0.247 ms. All ranks completed.
2. `hccl_graph_probe.py`, operation `exec-00000000000008b8`: 48 measured graph replays/rank after warmup, each replay containing sixteen 40 KB AllReduce calls. Whole-replay medians were 0.216–0.218 ms. All ranks completed.
3. Both unique diagnostic containers ran with `docker --rm`, exited successfully, and a subsequent `npu-smi info` showed no NPU process. No 4–7 card was used.

These two isolated probes reject the broad claims that physical NPU0–3 HCCS is intrinsically too slow for 40 KB collectives or that any AIV graph replay inherently reproduces the service stall. They do **not** eliminate a vLLM-specific graph, inter-stream dependency, rank-mapping, or workload-specific HCCL interaction.

## Next discriminating experiment

On NPU0–3 only, identify the event/memory notification that releases rank 2's `MEM_WAIT_VALUE` between `reshape_and_cache` and `FusedInferAttentionScore`, then run the same short no-cache Decode service workload with one service-level variable changed (graph mode first, or rank-to-physical mapping). Capture all four rank timelines, including rank 2. Require both that wait duration and E2E TPOT to change together before claiming the source-level cause or a fix. Do not change drivers, firmware, clocks, shared HCCS settings, or the frozen formal benchmark.
