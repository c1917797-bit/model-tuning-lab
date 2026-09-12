# T22 retired-prefetch ablation

## Decision

Remove the two weight-prefetch monkeypatch hooks from any final candidate.
The no-prefetch ablation preserved successful execution and produced no
material end-to-end loss or gain relative to T20. The upstream retirement
audit and the target measurement therefore agree: this mechanism is not a
credible component of the Qwen3.5-27B optimization.

## Exact evidence

- Artifact root:
  `/cache/austinov/qwen35-t22-candidate-prefill-no-prefetch-20260911`.
- Official image ID:
  `sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1`.
- Runtime form: read-only Python monkeypatch mount, no framework source
  overlay, no custom image, and no custom operator mount.
- Scope: BF16 TP4 on physical NPU0-3 only. NPU4-7 were not mapped.
- Activation report SHA256:
  `3554b47e9c429003b62ebbf9530b404c504fa774bbe4c7b6c6a1106017cf16a7`.
- Weight-prefetch hook marker counts: gate-up `0`, RMSNorm postprocess `0`.
- Smoke: 1/1 completed, zero errors, natural EOS.
- Warmup: 32/32 completed, zero errors, natural EOS.
- Measured run:
  `failfast-candidate/c1-r1.json`, 32/32 completed, zero errors, natural EOS,
  TTFT P95 `822.561976 ms`, TPOT P95 `28.306571 ms`.

T20 with the retired prefetch hooks enabled measured TTFT P95 `808.224 ms`
and TPOT P95 `28.282 ms`. The differences are only +1.77% TTFT and +0.087%
TPOT for no-prefetch, which is not evidence of a useful prefetch effect and is
far below the required TPOT improvement. No full matrix or expensive accuracy
run is authorized for this rejected component.

## Trust boundary

The query-rewrite file has empty reference answers, so its response hashes are
not an accuracy oracle. A future performance-passing stack must additionally
pass the reference-backed GSM8K no-regression gate: three complete paired
repetitions against a fresh identity-matched official control, zero request
failures, and candidate accuracy greater than or equal to control in every
repetition and in the median. Performance never overrides this gate.

## Next admission

Keep the bounded-prefill component only as a TTFT candidate. Audit and measure
a decode treatment that starts from accepted upstream code, preserves BF16
semantics, and clears the exact c1 TPOT budget before service integration.
MTP, speculative decoding, quantization, retraining, source overlays, and a
custom final image remain out of scope.
