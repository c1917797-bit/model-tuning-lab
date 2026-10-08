# cache10r9 baseline-reuse audit — old full control is not the matched denominator

The 2026-10-08 `quality-context-41984-hotpath-full-baseline` no-cache arm is a complete standalone LongBench-v2 run: 127 unique sample files with exact indexes 0–126, three scores per file (381 rows), no arm error, no foreign NPU0–3 guard observations or probe errors, and an exact owned-service release receipt. Its existence does **not** make it a comparable control for `cache10r9`.

| Identity field | Old completed no-cache arm | cache10r9 HYPIC arm / planned no-cache control |
| --- | --- | --- |
| Qwen3.6-27B weights, image/source, physical NPU0–3, CPU-binding-off, context 41984 | Same frozen fingerprints | Same |
| LongBench-v2 sample/prompt identities; 2048 output cap; natural EOS; seed 0; temperature 0; thinking off; concurrency 8; 3 scored repetitions | Match | Match |
| `--gpu-memory-utilization` | `0.9` in frozen no-cache launch command | `0.85` in live r9 container and r9 arm launcher |
| HYPIC material-cache cap / maximum segments | Original 1536 MiB / 4 (inactive in no-cache arm) | 3584 MiB / 10 (candidate treatment settings) |

The common GPU-memory-utilization setting differs. The old arm's `contract.json` fingerprint omits this field, while the r9 fingerprint records `0.85`; the deterministic launch seam leaves the frozen source at `0.9` for the old arm and changes **both** r9 arms to `0.85`. This is a material serving/capacity identity difference, even though the sample identities match. Under `ascend-benchmark-evidence` and `ascend-model-quality-evaluation`, **do not reuse or pair the old 0.9 arm**. Once the live r9 candidate has completed and released cleanly, use the already-declared fresh `quality-context-41984-hotpath-cache10r9-full-baseline` root with the same 0.85 common setting. That root was absent at this audit; never start it concurrently on NPU0–3 or while a foreign process is present.

The new contract also serializes `split_shard` and `clean_set_receipt_sha256` as null; the old contract omits these inactive split-only fields. The focused read-only replay normalizes only this absent-versus-null schema extension, then verifies every substantive workload field, raw hash, sample count, isolation receipt, and the 0.9/0.85 launch commands:

`python3 -B .agents/workstreams/hypic-npu03-cpu-binding-fix-20261007/verify_hotpath_baseline_reuse.py`

Read-only evidence:

| Artifact | SHA-256 |
| --- | --- |
| Old `contract.json` | `73e2f5ae76e5fcaf7b623791e68d5b0e62030ac6fa828534b72ae227bc542336` |
| Old `arm-result.json` | `856b33bf897187bdc5351d63b165cb7067fca794b65eea99bf501c6411f9c898` |
| Old 127-file `sha256sum samples/*.json` manifest stream | `d289db3f3e9ceb627d48ad2b01925d37a41954f915bdcdf6b7aaf8589fe29a6f` |
| Old `no-cache/service-start.json` | `9e9d2c8f676b0a8fbce3f256078ba9aae381f87ca9f7cea6b9ffe480bc1ac601` |
| Old `no-cache/lane-guard.json` | `a523cc0f1ad1a89604c75a4e561429d8ddcc931419e8e74b5b1ebffef5d7c432` |
| Old `no-cache/service-stop.json` | `b4c7e0582db71a62d6f9e1e25df2cbaca7a4b26e259bfa5daeae687ff93ab540` |
| Live r9 `contract.json` | `89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48` |

The old `arm-result.json` deliberately leaves `quality_pass_claim=false`: a complete control alone cannot prove paired quality. No r9 quality or performance verdict is inferred here.
