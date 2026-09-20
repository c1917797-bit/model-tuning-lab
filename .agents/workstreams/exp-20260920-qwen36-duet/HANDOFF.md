# DUET — Qwen3.6/Ascend piercing

## Status

- Stage: planned / hardware-expression applicability gate.
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

## Immediate next action

Audit the official source tree and paper mechanism table. Do not launch NPU
work until a real software-selectable 910B path is named and bounded.
