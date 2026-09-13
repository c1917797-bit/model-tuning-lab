# T31 bounded-prefill warm rerun

## Decision

Reject the unchanged bounded prefill-only MMAR candidate. It does not pass the
fresh steady-state c1 gate and must not enter the full concurrency matrix.

## Runtime identity

- Image: unchanged official `quay.io/ascend/vllm-ascend:v0.23.0`
- Model: Qwen3.5-27B, BF16, TP4
- Physical devices: NPU0-3 only
- MTP/speculative decoding: disabled
- Delivery seam: one read-only Python monkeypatch mount; no source overlay
- Variant: `candidate-prefill`
- Activation audit: passed, with one TP worker per target NPU

## Evidence

Artifact root:
`/cache/austinov/qwen35-candidate-prefill-service-20260913-v15`

| Evidence | SHA256 |
|---|---|
| activation-report.json | `6712cf7ce54fa7351e9b37a73a7c80db0f051d0d124f51ff35d2e2cff234f7ae` |
| warmup-c1/c1-r1.json | `034ceeade183d3fa02e12c04d20ec771db24667798a93d6d3262cf116bef5ee1` |
| failfast-candidate-prefill/c1-r1.json | `1b9d6f77dd9b95af8166ac289daa803dd71f2136489c106b8464f1c3ee3ec289` |
| service.log after stop | `cacb23b11525e1b106d5357ee6695cfa1ff8fc8fc86ee73883d273ca09b9e2ec` |

The first warmup covered all 32 frozen query-rewrite prompts. It completed
32/32 requests with zero errors and natural EOS. Its TTFT P95 was 6605.294 ms,
confirming that first-use prefill/Triton compilation materially contaminates a
cold c1 run.

The formal c1 fail-fast then ran on the same live service with an independent
cache-salt prefix:

| Metric | Fresh v14 control median | Candidate | Required maximum | Result |
|---|---:|---:|---:|---|
| TTFT P95 | 841.073 ms | 850.068 ms | 672.858 ms | fail; 1.07% regression |
| TPOT P95 | 28.909 ms | 31.342 ms | 26.018 ms | fail; 8.41% regression |

The formal cell completed 32/32 requests with zero errors and natural EOS.
Performance failure alone is sufficient to reject it; the full accuracy gate
and c5/c8/c16 matrix were intentionally not run.

## Durable lesson

The historical T20 result (TTFT 6310.576 -> 808.224 ms) compared a cold control
with a warm candidate and therefore does not establish a steady-state
optimization. Every future prefill candidate must receive a non-evidence
warmup on the exact live treatment service before its c1 admission run.

Do not combine this candidate with a decode optimization merely to mask its
regression. A stack component must contribute independently under the current
fresh-control protocol.
