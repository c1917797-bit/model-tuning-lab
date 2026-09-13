# Qwen3-32B original-input performance: repetition 1

Scope: one control arm, first repetition only. Not a paired model-switch result.
Run completed 2026-09-13 22:34:01 UTC.

- Artifact root: `/cache/austinov/eval-runs/switch12h-qwen3-performance-r1-20260913-iRDuy1`.
- Eight Ascend910B4, TP8/DP1, BF16, no MTP/speculation; original query_rewrite.
- Fixed image digest: `sha256:471744200c5d0c768c1f6c6a6816dcae0fd551de2487d4d129b6fb750024ce6a`.
- Dataset SHA256: `a7a1c93be3a64843d2a4e316f39fbe1bd2c9d4bc7b8bb28776d121e0154b056e`.
- Benchmark SHA256: `5204b7fd92b7610a96fcb86bd010eeb633ed7c0692224f1a15880a80ce93b40c` (v4).
- Natural EOS, cap4096, temperature0, seed1024, thinking off; distinct request cache salts.
- Each cell:357 completed,0 errors,0 empty,0 reasoning,0 prompt-count mismatch,
 357 stop finishes,0 undefined TPOT. This is output validity, not semantic accuracy.
- Lifecycle settings and image identity: `service.start.inspect.json`,
 `image.inspect.json`, `inputs.sha256`, `npu.ready.txt` under artifact root.

| Concurrency | TTFT P95 ms | TPOT P95 ms/token | Wall s | Output tokens |
|---|---:|---:|---:|---:|
| 1 | 364.009888 | 44.242973 | 470.111303 | 8266 |
| 5 | 764.495800 | 108.435290 | 171.458627 | 8291 |
| 8 | 965.979688 | 147.033256 | 144.354363 | 8282 |
| 16 | 1375.014982 | 194.880301 | 98.583170 | 8283 |

Raw summaries and rows under `performance/`:

| Cell | Summary SHA256 | Rows SHA256 |
|---|---|---|
| c1 | dd911bda5b4a4f47ad7b4a02c5c45da8624e2da5af00b8f41528d607f1123dcd | fdf5c0b38c0338f3a5b8f13b412880e8e07c18cb973ecb8e327e411d1765e21f |
| c5 | 44bfbba772083f1681270b81cfa260232e27c612c57a3750678fd359578c98d7 | 63f795d3c6745a3ce7fd2368bf48ecc09d03ec4b91842be3901bec02762c8e46 |
| c8 | 2978f0cfd70ded54c53af660f84f6aeaeeacd3c91f348d0e1055092bc47737a1 | ccbcb749b7b7ff2eac2ba15593b721cfe1d387e276be3136abcfc637ee2d2ec5 |
| c16 | b90ac83840285a77df49c0d647cdd95ba8ef745ab0a8cf78eb80119b6b09eb96 | b9b06dc9b9ec8a6683816c1ccf95e0eede0718bc8c2805be43c2f877b7ce0ee0 |

P50/P99/full extrema and raw SSE remain in these artifacts. c1 maximum TTFT
was6304.655290ms; it was retained, not silently excluded. Three repetitions and
candidate comparison are still required; do not pool historical raw-completion
numbers or normalized-input diagnostics with this original chat protocol.
