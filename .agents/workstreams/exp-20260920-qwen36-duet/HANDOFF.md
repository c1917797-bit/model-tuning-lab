# DUET — Qwen3.6/Ascend piercing

## Status

- Stage: completed / rejected at hardware-expression and plugin-delivery gates.
- Start: 2026-09-20.
- Hard timebox: 24 hours.
- Queue position: 10, after the previously completed DASC no-go at position 9.
- Resource lane if needed: physical NPU4-7 only.

## Paper fidelity boundary

The paper proposes disaggregated hybrid Mamba-Transformer serving with
prefill-specific and decode-specific hardware packages. The official repository
is an architecture-level simulator: configurable systolic PE and vector-unit
arrays, simulated tics, estimated clocks and FLOP-based throughput.

Qwen3.6 is a hybrid GDN/full-attention model, not the paper's evaluated
Mamba-Transformer. More importantly, the target is fixed Ascend 910B hardware
and plugin/monkeypatch delivery. A simulator result or imagined array
configuration cannot establish an Ascend runtime candidate.

## Predeclared gate

1. Inventory the official repository's executable surfaces and separate
   numerical reference code from architecture simulation.
2. Map each claimed gain to custom hardware, a fixed-hardware software
   scheduling choice, or an existing vLLM-Ascend feature.
3. Abort if the gain requires replacing/configuring PE or VU arrays unavailable
   through CANN/operator/plugin APIs.
4. Abort if no distinct software-only production mechanism remains.
5. Only after a real plugin seam exists may an NPU numerical canary run.
6. Simulator clocks, tics, FLOP/s and CPU/PyTorch comparisons never count as
   NPU performance evidence.

## Final mechanism audit

- The paper's Prefill package uses systolic-array chiplets plus off-package
  memory for matrix multiplication and long-sequence SSM work.
- Its Decode package uses vector-unit arrays plus high-bandwidth in-package
  memory for token SSM and vector-matrix work.
- Those distinct compute arrays and memory systems are the optimization.
- The official repository implements them as `PE_ARRAY` and `VU_ARRAY`
  architecture simulators. Timing is reported as tics, estimated clocks and
  FLOP/s, not device measurements.
- No CANN operator, torch_npu kernel, vLLM integration, device binary or
  software-only scheduler that reproduces the package properties is present.

## Decision

Reject DUET for plugin delivery on unchanged Ascend 910B. A CANN operator can
choose tiling and fuse software work, but cannot turn fixed 910B silicon into
the paper's separate systolic/off-package and vector/in-package accelerator
packages. Running the simulator or a generic NPU kernel would not pierce the
paper's claimed mechanism.

No NPU service was launched. The 10-paper queue is complete; next work should
aggregate all evidence and resume only a still-actionable lossless candidate.
