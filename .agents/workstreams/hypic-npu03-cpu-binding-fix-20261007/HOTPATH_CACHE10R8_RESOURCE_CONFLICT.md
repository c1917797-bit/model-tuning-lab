# cache10r8 full HYPIC arm — actual NPU3 collision before health

- Target: chicaihong01/ma, physical NPU0–3 only. Original full HYPIC protocol: 127 LongBench-v2 samples × 3 repeats, output cap 2048, concurrency 8. Passive Docker mappings did not veto launch.
- The unique full HYPIC controller `exec-000000000000157a` launched after an actual-idle NPU0–3 and free-port probe. Artifact root: `/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r8-full-hypic`.
- At `2026-10-08T16:54:46.847933Z`, the startup guard observed foreign PID `1762714` on physical NPU3. It was a `kernel_eval.staged_eval` worker in the pre-existing `cannbench_ds` container `efc5e45e8a54690e412cd3e148791f57733385ae0b97f87d0bb3b777e17873f6`; probe errors were empty. The process existed before this arm but only entered NPU3 after launch.
- Guard stopped before service health/scoring: `0/127`. This is environment/isolation-invalid, **not** a HYPIC quality or algorithm verdict. Do not reuse or pair this root.
- Exact owned container `286ec995e2460d8390674dc21d1c8b3ad24291e62cdf9553d7c4fe52ef843aed` was removed. Stop receipt confirms its NPUs and port 8223 released. `lane_available=false` meant the foreign NPU3 process remained; the foreign container was not changed.
- The campaign allowlist/path change passed 37 offline tests and `validate-mst.sh` before launch. Commit `51d403fea571e153453b35eb7e7a266a1ebe0b08` was pushed and independently confirmed on the named remote branch. This does not validate the live quality arm.

Immutable raw-artifact SHA-256:

| Artifact | SHA-256 |
| --- | --- |
| `contract.json` | `89490d2b45967cffe3296242e16292f61004a58005f50e6fab13e7893545fa48` |
| `progress.json` | `abbbd96e4e740528e2034d8891bb4476beeb84eda74d914060ff47b0f604f31e` |
| `arm-result.json` | `62476485edce018c2f1708647e4443d0004cd5d177e10f7ae04f449f2c2ef752` |
| `hypic-only/lane-guard.json` | `816f0357d0a8232ee64bdf289a2450fa2aeac80f5c69ef4b1519a046565544cd` |
| `hypic-only/service-stop.json` | `d133475a661df18f6874ceb839cb6d792c823850da7a103afdfe32b716e843a0` |
| `hypic-only/service.full.286ec995e246.log` | `b2b9c7c81bfa4f1785905f471ec04410b78529240effee92a29ffe53b1f77dbd` |

User choice: continue only when physical NPU0–3 and port 8223 are *actually* idle; do not demand an exclusive reservation, touch NPU4–7, stop foreign processes, or treat container mappings as usage. Each subsequent attempt needs a fresh unique root and the same continuous guard; collision invalidates that arm without changing the technology verdict.
