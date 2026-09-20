# DUET — Ascend piercing report

## Current decision

- Paper: arXiv:2603.15530.
- Official source: AlishKanani/DUET.
- Target: Qwen3.6-27B on four fixed Ascend 910B4 devices.
- Delivery boundary: explicit opt-in vLLM-Ascend plugin/monkeypatch.
- Status: rejected at the hardware-expression and plugin-delivery gates.

## Initial evidence

The official repository exposes an architecture-level simulator, not a CANN,
PyTorch-NPU or vLLM implementation. Its `PE_ARRAY` and `VU_ARRAY` model
configurable systolic and vector-unit hardware; reported tics, estimated clocks
and FLOP/s are simulated quantities.

## Mechanism boundary

The paper's speedup is produced by two different accelerator packages:

- Prefill uses systolic-array chiplets with off-package memory.
- Decode uses vector-unit arrays with high-bandwidth in-package memory.

These are physical compute-array and memory-system properties. The official
repository models them in Python and supplies a PyTorch numerical comparator,
but no CANN operator, torch_npu implementation, vLLM integration, device binary
or deployable runtime scheduler.

## Final decision

Reject DUET for the current fixed-hardware plugin objective. CANN kernels and a
vLLM monkeypatch can alter software execution on 910B; they cannot reproduce the
paper's two custom accelerator packages or their memory placement. No distinct
software-only mechanism remains after excluding the hardware contribution.

No NPU run, performance result or accuracy result was produced. Simulator tics,
estimated clocks and FLOP/s were intentionally not treated as Ascend evidence.
This does not dispute the paper's architecture result; it states that the
result is not portable as a vLLM-Ascend plugin on existing 910B cards.
