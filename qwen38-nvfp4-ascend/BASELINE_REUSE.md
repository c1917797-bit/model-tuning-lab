# Baseline reuse audit — 2026-09-13

Historical audit scope at creation: Qwen3-32B BF16 versus Qwen3.5-27B BF16.
The user subsequently selected Qwen3.8-27B explicitly; SWITCH_VALIDATION.md and
the latest HANDOFF supersede this model-selection scope, not the raw cell facts.
Actual PERF_RUNNER inspection confirms /v1/completions with a raw prompt.
The service's no-thinking chat-template default does not transform that prompt.
Keep those cells only as original-protocol evidence.
Keep Qwen3.8 evidence separate; architecture/served aliases do not prove weight identity.
Do not rerun valid cells merely because the containing controller failed.

## Qwen3-32B completed historical cells

Artifact root:
`/cache/austinov/eval-runs/qwen3-32b-comparison/qwen3-32b-bf16-tp8-20260912T051439Z`

All three `performance/cells/*.json` sidecar hashes reverified in
`exec-0000000000000ba6`. TP8, repeat 1, 357 completed requests each, zero
request errors. The controller is terminal failed; c16 has a log but no
completed JSON in this root. It is not a running job to wait on.

| Cell | TTFT P95 ms | TPOT P95 ms/token | stop / length |
|---|---:|---:|---:|
| c1-r1 | 360.831440 | 44.862442 | 355 / 2 |
| c5-r1 | 637.836912 | 47.445713 | 357 / 0 |
| c8-r1 | 629.781294 | 51.210223 | 355 / 2 |

SHA256, respectively:
```
0f3047406c5f29f2667f15a6ff5c569341be5a27a83204d2ef44c462b8faa44e
e2205f4c978185ee2b775394f8ed67b9980fa90317a001e4b536617a1a15d922
8da144f5e650f8864e0376ce2cf37dab9ad440eeae15a990317f6c10c13ad9c4
```

The preserved protocol amendment accepts up to two context-limit exceptions;
these are not natural EOS. If resuming the identical protocol, skip these cells
and run only missing cells after resource/identity gates. If the desired protocol
changes, retain them as historical evidence rather than pooling measurements.
`protocol.txt` records quality_enable_thinking=false but does not establish the
performance thinking setting. Audit the actual request runner/launch parameters
before admitting these cells to a no-thinking comparison. Context limit is 40960;
the old Qwen3.8 comparison used 133000. Quality protocol was LongBench-v2/GSM8K,
not a complete MMLU/GSM8K/HumanEval result.

## Other historical evidence

Qwen3.5-labelled TP4/TP8 baselines under
`/cache/austinov/eval-runs/exp-20260904-qwen35-query-rewrite-3x-e2e/baselines/`
have c1/c5/c8/c16 x three repeats, but only 32 requests per cell. Preserve them
as historical screening evidence. Complete launch/weight identity matching before
admission; do not equate this population with 357 requests or TP8 with TP4DP2.

Qwen3.8 full baseline and Qwen3-vs-Qwen3.8 sentinel results are not evidence for
the Qwen3.5 replacement decision. No complete matched standard-quality score set
has been verified yet.

## Standard-task offline preflight

`preflight_standard_tasks.py` inspects the pinned lm-eval v0.4.13 upstream YAML
without resolving `!function` imports, then validates local DatasetDict inputs.
The returned configurations are intentionally NOT executable evaluator configs.
It preserves upstream prompt/scoring descriptions but proves only data readiness.

First attempt (`exec-0000000000000b9e`) failed during HumanEval function resolution:
upstream utils imports code_eval and runs a sample at import time. The corrected
inspection uses resolve_func=False and asserts HumanEval utils were not imported.
No claim is made that HumanEval runtime scoring is now wired or complete.

Corrected test `exec-0000000000000bad`: exit 0, 59 task configurations,
15525 test rows (MMLU 14042, GSM8K 1319, HumanEval 164), no Hub loader calls.
Network disabled, no NPU devices, read-only root/source/data, dropped capabilities,
no-new-privileges, 2 CPUs, 4 GiB RAM, 256 PID limit, temporary 512 MiB /tmp.
Fixed image ID:
`sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
Harness: `/cache/austinov/eval-tools/lm-evaluation-harness-v0.4.13`.
Python: `/cache/austinov/eval-tools/lm-eval-v0.4.13-venv/bin/python` inside image.
Inputs: `/cache/austinov/eval-data/general` mounted read-only as `/data`.

Next: prove executable task construction and sandboxed offline HumanEval scoring;
freeze model-specific template/thinking and performance protocol before deciding
which historical cells are comparable. No new NPU workload was launched here.
