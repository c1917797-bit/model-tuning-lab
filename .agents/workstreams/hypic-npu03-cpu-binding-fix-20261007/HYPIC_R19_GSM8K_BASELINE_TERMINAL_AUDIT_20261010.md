# R19 repaired-source GSM8K no-cache baseline terminal audit

The frozen GSM8K max-2048/c32 no-cache arm on chicaihong01 physical NPU0–3
finished in its immutable root
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-baseline`.
Controller `exec-0000000000000433` reached terminal completion after all three
1319-request runs and exact owned-service release. The separate read-only
`audit_arm` invocation from frozen `r19_c32_gsm8k_audit.py`, operation
`exec-00000000000004a0`, exited 0 and replayed every row and score.

| Run | Correct / 1319 | Reached 2048-token cap |
| --- | ---: | ---: |
| 1 | 1280 | 10 |
| 2 | 1274 | 11 |
| 3 | 1284 | 7 |

The independent replay verified 3957/3957 scored rows, dataset and evaluator
hashes, prompt/sample identity, response hashes, receipt hashes, pinned image,
Qwen3.6-27B BF16 TP4 source commit
`4429e35177979c874bf053ab29789e4773f39b22`, 991 clean physical-process
guard samples, and release of only container
`748ff800682d5f085fea77d7cb2b403f7bff18dca9d98bc536b07da9ca48ae98`
and port 8223. No foreign PID or probe error was recorded. The controller
arm-result SHA256 is
`03a2093873b2dbf3a0f675c7d0d47d83cadd0389192e10fb491ca03525ece897`;
contract SHA256 is
`8f76b216800c8f75b293ca91aeeec3422e881126bfe79391484d897aed48b20e`.

This is a valid **control arm**, not a paired GSM8K verdict or HYPIC hot-path
proof. The frozen HYPIC-only arm was admitted only after this audit, its own
root-existence check, a fresh direct-route snapshot showing physical NPU0–3
and port 8223 idle, and the controller's immediate recheck. Its operation is
`exec-00000000000004a3`, rooted at
`/cache/cch/hypic-npu03-cpu-binding-fix-20261007/quality-context-41984-hotpath-cache10r19-c32-gsm8k-hypic`.
Poll that exact live operation; do not restart on slow progress. On terminal,
independently audit all three candidate runs before running the frozen paired
auditor once. GSM8K is off-path runtime-enabled safety and cannot overturn
the r19 LongBench `REJECT_OR_QUALIFY` decision.
