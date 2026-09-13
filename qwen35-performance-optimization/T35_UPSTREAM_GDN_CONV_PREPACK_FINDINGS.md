# T35: upstream-derived GDN conv-weight prepack findings

## Decision

Reject one-time GDN conv-weight prepacking as a standalone addition to the
retained T32 fused-prefill stack. It preserves the TTFT win and improves TPOT,
but the warmed formal c1/32 TPOT P95 remains above the acceptance threshold.
Do not run this exact treatment through c5/c8/c16 and do not rerun it
unchanged.

## Upstream boundary and project delta

The reusable mechanism comes from current vLLM-Ascend
`vllm_ascend/ops/kimi_kda.py`, traced to commit `826c737af`: store the
depthwise convolution kernel once in the activation-dtype `[W, C]` layout
instead of transposing it in every decode call.

The project delta is limited to the missing Qwen3.5/vLLM 0.23 integration:

- register the derived BF16 parameter on Qwen's GDN attention module;
- materialize it through the original checkpoint weight-loader boundary;
- explicitly mark the derived parameter loaded for vLLM 0.23 strict tracking;
- consume it from the existing Ascend GDN forward path;
- fail closed behind `QWEN35_ASCEND_GDN_CONV_PREPACK=1`.

No convolution, recurrent kernel, collective, quantization, model weight, or
base-image source was reimplemented or replaced.

## Retained integration failures

- v1 reached weight loading, then failed because the derived parameter was not
  included in vLLM 0.23's strict loaded-parameter set.
- v2 failed the source-contract inspection because the return anchor was
  matched before source dedentation.
- v3 corrected both integration defects. All four TP workers logged the
  prepack marker, the activation report passed, and the real request path
  completed.

These failures are retained because startup success is part of the runtime
lifecycle contract, not incidental setup noise.

## Valid v3 evidence

Artifact root:
`/cache/austinov/qwen35-t35-fused-prefill-conv-prepack-service-20260913-v3`

- unchanged official `quay.io/ascend/vllm-ascend:v0.23.0`;
- Qwen3.5-27B BF16, TP4, physical NPU0-3 only;
- one read-only Python monkeypatch mount, no source overlay or custom OPP;
- activation passed on all four workers;
- smoke: 1/1, zero errors, natural EOS;
- independent warmup: 32/32, zero errors, natural EOS;
- formal c1: 32/32, zero errors, natural EOS.

| Metric | Fresh v14 control | T35 v3 | Reduction | Required |
|---|---:|---:|---:|---:|
| TTFT P95 | 841.073 ms | 619.023 ms | 26.401% | >=20% |
| TPOT P95 | 28.909 ms | 27.326 ms | 5.477% | >=10% |

The remaining c1 TPOT deficit is 1.308 ms/token relative to the 26.018 ms
threshold. The measured result is consistent with the T34 budget: eliminating
only the per-layer transpose cannot close the original gap.

Evidence SHA256:

- activation: `b239edce9f5557bf48ecfb05d7c1d499c3f74f167abe74ee45bc927a3cea9798`
- smoke: `2550302b94b2c85292728231403c916a5549a57ecffc1c9978be08873985f2a9`
- warmup: `2c4ccf01f4021c3b6ff1a08f4609dd1cdcb6c0c5415792a50edcb747de2f673b`
- formal c1: `22d84ed832af58d4059fc1344c3909267195bdb19b6c1557bff68f6d7768ad0d`
- stopped service log: `53a0211f2034bbd79522ecb1b17792079fb15588c002b538b0501f5011ba2907`

## Resume point

Keep T32 as the TTFT base, but do not keep T35 as an independently accepted
component. Continue from the profile-proven full GDN transpose-to-recurrent
decode envelope, whose 2.796 ms/token upper bound can cover the remaining
TPOT requirement. Reuse a supported upstream implementation and add only the
Qwen3.5/v0.23 monkeypatch seam plus measurable whole-chain delta.
