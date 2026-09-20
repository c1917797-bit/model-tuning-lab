# DUET — Ascend piercing report

## Current decision

- Paper: arXiv:2603.15530.
- Official source: AlishKanani/DUET.
- Target: Qwen3.6-27B on four fixed Ascend 910B4 devices.
- Delivery boundary: explicit opt-in vLLM-Ascend plugin/monkeypatch.
- Status: hardware-expression applicability gate in progress.

## Initial evidence

The official repository exposes an architecture-level simulator, not a CANN,
PyTorch-NPU or vLLM implementation. Its `PE_ARRAY` and `VU_ARRAY` model
configurable systolic and vector-unit hardware; reported tics, estimated clocks
and FLOP/s are simulated quantities.

This workstream will proceed only if the paper contains a separate
software-only mechanism that can execute on unchanged Ascend 910B hardware.
Otherwise the valid outcome is an early plugin-delivery no-go with no NPU run.
