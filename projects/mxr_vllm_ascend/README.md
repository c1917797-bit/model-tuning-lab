# MXR vLLM-Ascend Plugin

This is the plugin-owned delivery area for the MXR triangular-inversion
workstream. It is disabled by default. The workstream reached a terminal
`no-go` for the frozen service objective: the official candidate was correct
and locally faster on real Ascend hardware, but its measured service share was
below the predeclared integration gate. The plugin therefore preserves the
configuration, runtime identity, and v0.23/v0.27 adapter contract without
installing the rejected candidate into service. It must not be used for a gain
claim.

The core/backend interface is version independent. Runtime-specific adapters
may only route the prefill call:

- v0.23: replace the imported chunk-GDN callable after exact source validation.
- v0.27.x: delegate to the upstream fused CANN path by default. An experimental
  override requires `MST_MXR_ALLOW_V027_OVERRIDE=1` and must pass its own NPU
  comparison before service use.

Activation requires `MST_MXR_ENABLE=1`, an absolute
`MST_MXR_EVIDENCE_PATH`, `MST_MXR_BACKEND_MODULE`, and an exact
`MST_MXR_EXPECTED_GDN_SHA256`. Unknown versions and source identities fail
closed, including later release lines such as v0.28. Unset `MST_MXR_ENABLE` to
roll back.

The official source archives are reference inputs during the NPU gate. No
unverified or ambiguously licensed MegaGDN source has been copied here.
