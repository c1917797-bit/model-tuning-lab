# Source selection and baseline lessons

Recorded 2026-09-11. This is a historical case record, not a live baseline,
hardware lease, migration-success claim, or universal performance threshold.

## Reuse the successful experimental method

HYPIC's retained lesson is a named one-switch A/B, complete runtime-chain
activation, capacity accounting, repeatable measurements, and independent raw
artifact review. Its cache-dependent speedup is not transferable to requests
without the required reuse. Existing DRRQR parity lessons remain applicable:
omitting a paper's recovery stage creates a different, possibly infeasible
contract; backend-invalid layouts do not disprove the paper.

## Selection failures identified in review

- Recommending an existing Ascend implementation did not meet the user's
  objective of a new GPU-to-Ascend contribution. Usability and migration
  novelty are different selection criteria.
- PR #15322 describes a FLA Phase6 integration. The reviewed PR page supports
  that integration claim, but no source-level mapping was established that
  proves equivalence to MegaGDN/MXR or multiplication-only inversion. The
  earlier claim that it covered most of a particular paper was too strong.
  Source: https://github.com/vllm-project/vllm-ascend/pull/15322
- Kachua is a competition technical report with public CUDA/Triton code, not
  a main-conference research paper or a validated Ascend migration. The
  separate MSInfer report discusses it; these are different authors/artifacts.
  Preserve publication identity and verify licensing before code distribution.
  Sources: https://github.com/romitjain/kachua-mlsys and
  https://arxiv.org/abs/2607.16831
- Reviewed Kachua decode constants were QK heads=4, V heads=8, D=128.
  Qwen3.5-27B's official config has linear QK heads=16, V heads=48, D=128.
  Head-group ratios are therefore 2 and 3; D128 compatibility alone does not
  prove correctness. Recheck fixed revisions and actual TP-local layouts.
  Sources: https://github.com/romitjain/kachua-mlsys/blob/main/gdn_decode_qk4_v8_d128_k_last/solution/cuda/kernel.cu
  and https://huggingface.co/Qwen/Qwen3.5-27B/blob/main/config.json
- The MSInfer report distinguishes competition-reference speedup from an
  optimized FlashInfer baseline. Neither proves an Ascend service gain.
  Layer count is also not runtime share; require a critical-path opportunity
  estimate before spending time porting a small component.

## T16: retained TTFT component, incomplete final objective

The stored decision `t16-kkt-task-num-despecialization` completed on
2026-09-10 and retained the candidate only as a TTFT component. The paired
TP4 BF16 MTP-off query_rewrite screen used 32 requests per cell, one repeat,
natural EOS and prefix-cache isolation. It was not the full c1/c5/c8/c16
three-repeat matrix or all-357 quality gate.

| Cell | Control TTFT P95 ms | Candidate TTFT P95 ms | Control TPOT P95 ms/token | Candidate TPOT P95 ms/token |
| --- | ---: | ---: | ---: | ---: |
| c1 | 6035.100521 | 850.517368 | 29.001565 | 29.299717 |
| c16 | 18070.055791 | 7624.475079 | 136.799057 | 104.267555 |

The decision records a passed 32-row quality canary and failed c1 TPOT target.
This preserves useful TTFT evidence without declaring the full patch accepted.
The task-count specialization change concerns new-shape compilation behavior;
the table does not establish an equivalent warmed arithmetic acceleration.
Completion-token totals also differ: c1 control/candidate 6865/7720 and c16
7452/6986. Natural-EOS service measurements require this context.

The older t11 c1 frozen denominator (966.3259 ms TTFT P95, 39.0459 ms TPOT
P95) belongs to a different historical comparison. The new control is the T16
iteration denominator, not an automatic replacement of that frozen contract.

Evidence root prefixes on chicaihong01:
`/cache/austinov/qwen35-t16-kkt-{control,candidate}-failfast-20260910`.
Raw files: `c1-r1.json`, `c16-r1.json`; candidate decision: `T16_DECISION.json`.
Expected hashes recorded in that decision:

| Artifact | SHA256 |
| --- | --- |
| c1 control | 57b416378d88ace79b7dcbb1fbf239e1ced721d54a00f7e189bdb1cda5af192b |
| c1 candidate | 55ac01724b5d10f34157df0b1c6b20e07a4251fd7bdab54dc31069a3621d011e |
| c16 control | 4b8be6503794c51463e950888eba177fe1be032246fa7cbd4a3d7a6b4641b7ff |
| c16 candidate | 30723b5b26864070e00f52acf43e8c777e83ee33ede3f672b732c4ea753206de |

## T17: correctness repair did not establish performance

The owning task's 2026-09-11 handoff and
`qwen35-performance-optimization/T17_SMALLM_GEMV_FINDINGS.md` report that a
build-only `libopapi_math.so` shadowed the runtime and caused zero output.
Removing it corrected output without changing the GEMV kernel. Subsequent
opposite-order cold-weight screens still regressed gate-up and qkvz, while
N=3584 was mixed. The aggregate projection opportunity was negative, so the
unchanged AIC GEMV was rejected before service integration.

This is a reported historical decision, not a new rerun. Preserve the binary
and source identities separately; neither the diagnostic binary nor the
disabled source guard is a release artifact. Correctness, performance and
release readiness are separate decisions.
