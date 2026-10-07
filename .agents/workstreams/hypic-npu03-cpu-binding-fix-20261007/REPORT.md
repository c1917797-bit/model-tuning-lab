# NPU0-3 Decode CPU-binding repair result (2026-10-07)

The measured no-cache Decode floor on physical NPU0-3 is repaired by one supported vLLM-Ascend switch: `--additional-config '{"enable_cpu_binding":false}'`. The opt-in launcher leaves the official image, model, source, TP4 AIV, FULL_DECODE_ONLY graph mode, container cpuset `112-191`, workload, and physical card mapping unchanged. It never changes the shared service or NPU4-7. The upstream CPU allocation algorithm itself was **not** patched.

The frozen baseline and candidate both use Qwen3.6-27B BF16, 32768 input tokens/16384 prefix, 40 requests x 1024 fixed output, c16, two warmups, three fresh service lifecycles, and no profiler. All six runs completed 40/40 exact-length outputs with zero failures. The three candidate contracts agree byte-for-byte on serving command, image digest, source commit, benchmark SHA256, cpuset, and physical devices.

| Run | Binding enabled TPOT | Binding disabled TPOT | Candidate TPOT P95 | Candidate TTFT P95 | Candidate output throughput |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 417.54 ms/token | 77.56 ms/token | 117.50 ms | 80.78 s | 117.29 token/s |
| 2 | 410.86 ms/token | 77.83 ms/token | 118.65 ms | 81.81 s | 115.40 token/s |
| 3 | 410.90 ms/token | 77.01 ms/token | 117.88 ms | 78.93 s | 117.32 token/s |
| Median | 410.90 ms/token | 77.56 ms/token | 117.88 ms | 80.78 s | 117.29 token/s |

Median weighted TPOT fell **81.12%**; the median of per-run TPOT P95 fell **73.63%** (447.08 to 117.88 ms). Throughput median was **3.94x** the frozen baseline (29.74 to 117.29 token/s), and fixed-batch duration median fell **74.64%** (1377.15 to 349.21 s). TTFT P95 median did not regress (81.14 to 80.78 s). Candidate TPOT across three runs ranged 77.01-77.83 ms/token. These are same-lane, same-protocol comparisons; the historical fast NPU4-7 result is context, not the denominator.

An additional unprofiled 4 x 128 smoke completed 4/4 with weighted TPOT 141.05 ms/token. Its deterministic 32768-token semantic canary matched the frozen no-cache token IDs and response text hash exactly. Service logs parsed `enable_cpu_binding=False` and emitted no CPU allocation plan. Each candidate container was explicitly identified, removed, and followed by NPU0-3/port 8223 release checks. NPU4-7 and the pre-existing sleep container were not touched.

Decision: `partial-component`. The no-cache **performance** repair is verified for this physical lane and frozen protocol. This is not a claim that the upstream overlapping-pool allocation algorithm was fixed, that HYPIC-enabled service performance has been revalidated, or that production quality/adoption passed. The prior complete 2048-token paired LongBench-v2/GSM8K quality ruler was not available for this candidate; do not replace it with the short canary. The opt-in repair remains on this work branch, disabled by default. A production change requires a feasible new paired quality plan, HYPIC-enabled formal A/B when claiming paper reproduction, and explicit integration review.

Evidence: external artifact root `/cache/cch/hypic-npu03-cpu-binding-fix-20261007`; immutable original baseline root `/cache/cch/hypic-qwen36-e2e-2048-20261006/no-cache`. Exact SHA256 values and operation IDs are in `../../experiments/exp-20261007-hypic-npu03-cpu-binding-fix.yaml`. The guarded launcher is `binding_off_service.py`.
