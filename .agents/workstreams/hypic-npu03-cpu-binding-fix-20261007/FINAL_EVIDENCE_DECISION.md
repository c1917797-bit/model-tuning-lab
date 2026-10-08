# HYPIC NPU0–3 bounded piercing: clean2 evidence decision

Decision (2026-10-07 21:58 UTC): **C1/C2 hot-reuse performance passes; formal 2048-token hot-path quality does not pass; whole-paper reproduction is not established.** This closes the frozen clean2 protocol, not the full research objective. No NPU4–7 workload, unrelated-container change, main merge or production adoption is part of this branch.

## Controlled performance

Both arms used the same Qwen3.6-27B BF16 model, pinned image/source, TP4, physical NPU0–3, cpuset 112–191, HCCL AIV, graph mode and supported `enable_cpu_binding=false` repair. The HYPIC enable flag was the only algorithm-arm variable. The frozen performance run used 32768 input tokens, 16384 shared prefix, 1024 fixed output, c16 and 40 requests, three fresh service lifecycles per arm. All six units were 40/40 with zero failures and exact 1024 output. The independent audit is `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/performance-independent-audit.json` (SHA256 `de2f8af4a12dad9331e675ca1587aed6720aa8adc8aab551f6cfb2065ca78ac1`); it verifies four distinct worker-hot activations in each formal HYPIC run. Median weighted TPOT fell from 77.5641 to 60.2237 ms/token (17.3404 ms, 22.3562% lower); TTFT P95 median fell from 80.77549 to 43.20990 s; output throughput median rose from 117.2930 to 166.8247 token/s (1.4223×).

## Natural quality and strict activation

The natural-EOS protocol used 41984 context, max 2048 output, c32, seed 0, temperature 0, thinking off, LongBench-v2 127 samples and GSM8K 1319 samples, three repeats per dataset and arm. Attempt 1 was invalidated by a foreign physical NPU3 PID and is not pooled. Fresh `clean2` job `exec-0000000000000e15` completed with exit 0 at 21:57:32 UTC. All 12 units have expected indexes, zero failed rows, frozen-scorer recomputation, summary/JSONL/receipt hashes, exact paired/repeated sample/reference/measured prompt-token identity and token accounting. No-cache and HYPIC-only had 752 and 754 uninterrupted clean physical-lane guard samples; both exact containers, owned workers and port 8223 were released, with whole NPU0–3 lane availability proved. Treatment service-stop SHA256: `0d2c44bf5a3da1e64adba919824a299cc3a1472ebb165289e18f8095a9ef4b77`; guard SHA256: `838562b72f87aa7ba397ef2169f2b0fa6aec99a78932844e497006bc79a22a3a`.

| Score | No-cache correct runs | HYPIC correct runs | Mean accuracy delta |
| --- | --- | --- | ---: |
| LongBench-v2 / 127 | 78, 72, 74 | 74, 75, 75 | 0.000000 pp; both 224/381 |
| GSM8K / 1319 | 1278, 1279, 1279 | 1276, 1276, 1282 | -0.050543 pp; 3836 vs 3834 / 3957 |

LongBench easy-category mean is -0.775194 pp and hard +0.396825 pp; its 2048-output-limit rate is -0.787402 pp. GSM8K length-limit rate is unchanged. Three-repeat paired correctness flips: LongBench 13 wins/13 losses, GSM8K 10 wins/12 losses. The two adverse accuracy means are within their corresponding baseline three-run ranges. They are not proven regressions beyond that ruler, but the predeclared all-nonnegative score gate is not met. The valid natural-task comparison is **descriptively inconclusive**, not a formal quality pass.

The unchanged strict `audit_binding_off_quality.py` was run first and exited 1 at its predeclared activation gate: plugin-build and scheduler events existed, but there were **zero distinct `worker_hot_path` PIDs**, versus four required. The separate natural-scope auditor verified all rows, identity, guards and release while retaining `formal_acceptance_claim=false`. Its artifact is `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-clean2/quality-natural-scope-audit.json` (SHA256 `61bcccd926459b8ee57cfc3860a5b30c581c7e7b525fe3b746b52146c2c0dbf0`). The score classifier uses a 1e-9 percentage-point tolerance for adverse and baseline-range tests; an initial floating-point endpoint false alarm was repaired and the entire scoped audit rerun. No raw score or strict gate was changed.

## Root cause and remaining boundary

The pinned natural evaluator sends ordinary chat requests without `vllm_xargs.hypic_segment_ends`; the frozen HYPIC service disables text auto-chunking and has no separator token IDs. Thus its requests cannot form usable segments. GSM8K prompts also measure only 77–242 tokens, below the 4096-token minimum rewrite. This is a protocol/configuration coverage mismatch, not evidence of intrinsic HYPIC quality failure on NPU0–3. The formal performance workload did activate the worker hot path. A separate, prospectively declared 2048-token paired quality supplement would need explicit exact-token boundaries, sufficiently repeated prefix, four-worker scored hot-event preflight, a separate denominator and release audit. Do not retrofit these into clean2 or pool scores.

The source/architecture audit confirms bounded text C1/C2 fit for this Qwen3.5-style hybrid checkpoint, not the paper's distributed C3 or exact upstream SGLang implementation; see `PAPER_ARCHITECTURE_FIT.md`. All 29 archived Skills are classified in `SKILL_VERIFICATION.md`; 29/29 structural validation does not mean 29 behavioral passes. Main and the dirty canonical checkout were not modified.

## Post-freeze repair (2026-10-08; separate evidence)

The frozen verdict above is unchanged. A new explicit-boundary, 2048-max-output
paired single-sample canary used physical NPU0-3 and confirmed four distinct
worker-hot PIDs on the scored HYPIC request (16,376 verified skipped prefix
tokens per worker) against zero baseline worker-hot PIDs. Both arms answered
`A` while the sample reference was `B`, so this one item showed no accuracy
delta but cannot establish aggregate quality. Both services passed clean lane
guards and exact release audits. See `HOTPATH_QUALITY_REPAIR.md` and
`HOTPATH_CANARY_RESULT.md` for the new protocol, receipt hashes, and remaining
full matched-quality acceptance work. Do not pool the canary with clean2.
