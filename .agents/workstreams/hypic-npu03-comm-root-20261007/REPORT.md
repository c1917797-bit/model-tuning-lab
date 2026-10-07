# NPU0–3 HYPIC Decode communication diagnosis (2026-10-07)

## Verdict boundary

The apparent 0–3 Decode "slow communication" is principally a downstream synchronization wait, not demonstrated HCCS bandwidth saturation. In a sampled graph-on full-service step, rank 2 waits before its attention kernel and reaches the small AllReduce about 22.7 ms after the other ranks on raw profiler clocks. A fresh eager-service control changes which rank waits, yet makes request TPOT worse. The producer/condition of the graph-on pre-attention notification and the source-level cause of cross-rank skew are **not yet proven**; this workstream is diagnostic-inconclusive rather than an accepted optimization. No NPU2-only static card configuration or fault was found.

The three-round frozen 0–3 no-cache TPOT weighted mean was 413.10 ms/token and HYPIC-only 399.41 ms/token. The corresponding historical 4–7 numbers were 74.51 and 60.36 ms/token. HYPIC absolute savings were 13.69 and 14.15 ms/token respectively. Do not conflate this near-equal method effect with the common 0–3 Decode floor.

## Critical-path evidence

Raw source: `/cache/cch/hypic-qwen36-e2e-2048-20261006/profiles/no-cache/decode`. The diagnostic capture used 4 requests × 128 output tokens with profiling overhead; it is not the formal 40 × 1024 timing result.

- In exported rank-0 task timeline, a trimmed 110-step Decode sample has 387.89 ms median step spacing and 356.10 ms median communication timeline union, about 91.8% of spacing. HYPIC-only is 387.90 and 356.13 ms, respectively.
- The last 30 seconds of rank-0 no-cache trace have 10,022 AIV AllReduce tasks: 8,647 under 0.1 ms (sum 0.087 s) and 1,243 from 10 to 30 ms (sum 27.255 s). The latter have median about 22.05 ms. Approximately sixteen such calls occur per Decode step. The model has sixteen full-attention layers; exact operator-to-layer mapping is still a hypothesis.
- Three CSV-exported ranks (0, 1, 3) start sampled slow collectives within 7–14 microseconds of each other on their raw clocks and each spends about 22 ms. AllReduce task timing may include synchronization wait; cross-device timestamps require clock-offset calibration before comparing absolute start times.
- Rank 2 CSV export was incomplete, but its existing raw `msprof_20261006155326.db` has the task rows. In the same sampled interval, rank 2's 40 KB AllReduce starts 22.666 ms after rank 0's slow-call start and lasts 0.0086 ms. Rank 2 stream 45 repeatedly executes `MEM_WAIT_VALUE` for that interval, while its stream 46 has a roughly 23 ms `EVENT_WAIT`. Thus rank 2 is a late entrant at this collective, but its upstream wait may itself depend on other ranks; do not label NPU2 faulty from this trace.
- The earliest observed divergence in that sampled step is between `reshape_and_cache` and `FusedInferAttentionScore`, **before** the collective. Rank 0/1/3 each run `reshape_and_cache` in about 3 microseconds, `MEM_WAIT_VALUE` in about 1–2 microseconds, and attention in about 0.21–0.22 ms; their subsequent AllReduce is charged about 22.7 ms. Rank 2 runs `reshape_and_cache` in about 3.58 microseconds, polls `MEM_WAIT_VALUE` roughly 7,665 times over 22.4 ms, then runs attention in about 0.216 ms and the subsequent AllReduce in about 0.009 ms. This is timing/ordering evidence, not proof that the notification originates locally on rank 2.
- The rank-2 raw database's trailing-30-second 40 KB AllReduce tasks have median 0.00925 ms, P95 0.01375 ms, and no task over 10 ms. The other ranks' slow duration is wait-dominated. The matching HCCL task metadata records size 40,960 bytes, BF16, algorithm `MESH-RING-NHR`.
- In that same raw rank-2 sample, stream 5 performs `MEM_WRITE_VALUE` about 22.414 ms after the sampled rank-0 collective start, releasing the stream-45 `MEM_WAIT_VALUE`. The linked CANN_API `aclrtValueWrite` is submitted by a host thread at about 22.152 ms. This identifies the release action but does not establish why host submission was late.

## Is NPU2 configured differently?

Read-only per-card checks found the same Ascend 910B4 V1, BoardID `0x34`, BOM `1`, firmware `7.7.0.3.220`, HCCS lane mode `4`/lanes `1111`/speed `224`, and zero HCCS retries/errors, PCIe TX/RX/LCRC/ECRC/retry errors, and HBM ECC errors on physical NPU0–3. Their mutual topology is HCCS. This is evidence against an NPU2-only static hardware or link setting, not a loaded-link stress test or proof of perfect hardware.

The frozen service container has CPU cpuset `112–191`, while the topology's recommended CPU affinity is `144–191` for NPU0/1 and `96–143` for NPU2/3. Consequently NPU2/3 get only `112–143` of their local recommended range, unlike NPU0/1. This is a **pairwise host-CPU affinity asymmetry**, not a unique NPU2 card configuration; NPU3 shares it without the same graph-on pre-attention wait. All four worker processes were allowed CPUs `112–191` with no rank-2-only pin. CPU-affinity causality remains untested; no CPU setting was changed.

## Controlled NPU0–3 probes

Only physical devices `/dev/davinci0` through `3` were mapped. The exact pinned service image digest `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`, TP4, AIV expansion, CPU set 112–191, and matching driver mounts were used. Preflight found no NPU0–3 processes. The pre-existing all-card-declaring sleep container was not touched; NPU4–7 had no diagnostic mapping or process.

1. `hccl_allreduce_probe.py`, operation `exec-0000000000000892`: 80 measured calls/rank after warmup. At 40 KB, four-rank medians were 0.260–0.262 ms; at 160 KB, 0.246–0.247 ms. All ranks completed.
2. `hccl_graph_probe.py`, operation `exec-00000000000008b8`: 48 measured graph replays/rank after warmup, each replay containing sixteen 40 KB AllReduce calls. Whole-replay medians were 0.216–0.218 ms. All ranks completed.
3. Both unique diagnostic containers ran with `docker --rm`, exited successfully, and a subsequent `npu-smi info` showed no NPU process. No 4–7 card was used.

These two isolated probes reject the broad claims that physical NPU0–3 HCCS is intrinsically too slow for 40 KB collectives or that any AIV graph replay inherently reproduces the service stall. They do **not** eliminate a vLLM-specific graph, inter-stream dependency, rank-mapping, or workload-specific HCCL interaction.

## Fresh full-service graph-on versus eager control

The same pinned image/source/model, TP4 AIV, physical NPU0–3, `32768` input/`16384` prefix and 2 warmups + 4 requests × 128 output were used in separate fresh containers. The sole serving CLI change was `--enforce-eager`, which in this runtime disables both compilation and graph capture; this comparison cannot isolate NPUGraph alone. Both arms returned 4/4 valid responses with exactly 128 output tokens. These are profiled short diagnostic requests, **not** the frozen formal 40 × 1024 benchmark.

| Arm | Weighted TPOT | TPOT P95 | TTFT P95 | Throughput |
| --- | ---: | ---: | ---: | ---: |
| Graph-on control | 499.00 ms/token | 593.23 ms | 32638.87 ms | 6.2670 token/s |
| Eager (`--enforce-eager`) | 616.44 ms/token | 707.20 ms | 31880.53 ms | 5.3120 token/s |

Eager TPOT was **117.43 ms/token worse (+23.53%)**, so disabling the compiled/graph path globally is not a fix. Graph-on rank-2 raw capture was about 2.1 GB; its full CSV export did not complete under the bounded parser. Four raw ranks and workload results remain saved. Eager raw rank-0/2 traces were exported to SQLite; the bounded capture guard skipped an oversized whole-file JSON parse, so the overall profile manifest is conservatively marked incomplete despite valid requests and usable SQLite.

The eager rank-0/2 task tables have no `MEM_WAIT_VALUE`, `MEM_WRITE_VALUE`, or `aclrtValueWrite` rows. In their trailing 30 seconds, 40 KB AllReduce medians are 0.0083 ms on rank 0 (0 of 7,769 over 10 ms) and 2.4658 ms on rank 2 (311 of 7,569 over 10 ms). Crucially, pairing **the same named collective sequence** gives 654 long rank-2 calls with median duration 12.4182 ms and a matching rank-0 duration of only 0.0077 ms. Rank-0 start minus rank-2 start, minus the rank-2 duration, is a stable roughly **1.5165 ms inter-device profiler clock offset** (5th–95th percentile 1.5154–1.5171 ms). After offset alignment, rank 2's long collective ends just as rank 0 enters it: in eager, **rank 2 waits for rank 0**. The graph-on example had the opposite rank-order symptom. A long NPU2 collective timer therefore does not prove slow NPU2 HCCS or a special NPU2 throttle.

Evidence root: `/cache/cch/hypic-npu03-comm-root-20261007/{graph-on,eager}`. Both named diagnostic containers were removed, NPU0–3 had no remaining process, port `8223` was free, and no NPU4–7 workload or setting was touched.

## Next discriminating experiment

On NPU0–3 only, first trace the host call site and scheduling dependency that submits graph-on rank 2's delayed `aclrtValueWrite`, and align per-rank profiler clocks before declaring entry order. A follow-up one-variable test could alter rank-to-physical mapping **within 0–3** or test CPU-affinity symmetry in an isolated container, preserving the pinned service and diagnostic stimulus. Predeclare the mapping/affinity and safety checks; capture all four raw timelines and request-level TPOT. Require the suspected wait and E2E TPOT to change together before claiming a cause or fix. Do not change drivers, firmware, clocks, shared HCCS settings, or the frozen formal benchmark. Do not repeat global `--enforce-eager` as an optimization candidate: it already worsened TPOT here.
