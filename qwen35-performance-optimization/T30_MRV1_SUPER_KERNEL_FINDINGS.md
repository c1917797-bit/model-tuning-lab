# T30: upstream MRV1 Super Kernel live findings

Status: rejected on the target stack before service readiness.

## Pinned candidate

The runtime monkeypatch backports vLLM-Ascend commit
`7ab47e73d005756963e3c6dd0e491296401b1f19` / PR `#15059` into the
unchanged official `quay.io/ascend/vllm-ascend:v0.23.0` image. The launch
used Qwen3.5-27B BF16, TP4, physical NPU0-3, npugraph-ex, static kernel, and
Super Kernel. MTP, speculative decoding, and quantization remained disabled.

## Live result

All four TP workers logged both exact upstream backport activation markers.
Static-kernel compilation completed its initial torch.compile phase, then
`aclgraph.super_kernel_optimize` called CANN `AclskOptimize` and failed
with ACL error `500001`. The engine terminated before the service became
ready, and the supervised one-shot container was removed.

Evidence:

- artifact root:
  `/cache/austinov/qwen35-mrv1-super-kernel-service-20260913-v1`;
- service log SHA-256:
  `70ed038d322c40ac6000f4df0e2e67f41fa38c49571c59d614e68ce68ad3a750`;
- `service.exit-code=1`;
- repository commit at launch:
  `496165c`.

No benchmark or accuracy result exists for this candidate because the
optimized service never became available.

## Upstream applicability audit

The pinned upstream PR reports unit coverage but does not report a
Qwen3.5-27B BF16, TP4, Ascend 910B4 end-to-end run. Current upstream Qwen3.5
deployment guidance uses FULL_DECODE_ONLY and does not enable static or Super
Kernel. Upstream main through
`d4d2957e5208c2f464d4625c05920bd29ea233cb` contains no follow-up fix or
revert for this Super Kernel path.

## Decision

Do not catch, ignore, or downgrade the optimizer exception while claiming
Super Kernel is active. That would silently benchmark a different treatment.
Retry is allowed only if a pinned upstream change or official compatibility
requirement explains and fixes the target-stack failure. Otherwise MRV1
remains closed and immediate rollback is
`QWEN35_ASCEND_SUPER_KERNEL=0` plus removal of static-kernel enablement.
