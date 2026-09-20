# DUET on Ascend: Applicability and Piercing Report

## Decision

**No-go under the current plugin/monkeypatch delivery boundary.**

This is not a negative judgment on DUET's hardware proposal. It means the
paper's independent variable cannot be instantiated on the existing Ascend
910B4 devices, so an NPU run would not be a valid reproduction.

## Paper mechanism

DUET is a hardware-architecture paper, not a serving-runtime optimization:

- the prefill package uses custom systolic-array chiplets with off-package
  GDDR, prioritizing dense compute;
- the decode package uses custom vector-unit chiplets colocated with HBM,
  prioritizing bandwidth and token-wise reductions;
- both packages add SSM-specific registers, special-function units, dataflows,
  and control paths;
- KV and recurrent-state caches move between the two packages over a
  package-level interconnect;
- the claimed TTFT, throughput, and TBT gains are evaluated in a cycle-accurate
  full-stack simulator validated against synthesized RTL.

These mechanisms alter compute arrays, memory placement, packaging, and
interconnect topology. They are not software scheduling knobs.

## Source identity and maturity

- Paper: https://arxiv.org/abs/2603.15530
- Official repository: https://github.com/AlishKanani/DUET
- Authors and title match the paper.
- The repository describes itself as an architecture-level simulator and
  exposes `PE_ARRAY`, `VU_ARRAY`, a small Mamba2 comparison harness, and
  simulator statistics.
- Its reported units include architectural `tics`, estimated clocks, and
  FLOP/s derived from simulated clocks. It does not provide CANN kernels,
  vLLM/vLLM-Ascend integration, executable DUET hardware, or service-level
  benchmark tooling.

The paper's evaluated models are Nemotron-H-56B, Zamba2-7B, and Llama3-8B, not
Qwen3.6-27B. Model mismatch is secondary here: even a matching hybrid model
would still require the proposed hardware packages.

## Ascend applicability gate

The authorized target is fixed Ascend 910B4 hardware on physical NPU4-7, with
delivery restricted to a removable vLLM-Ascend plugin/monkeypatch. Such a plugin
can alter graph selection, scheduling, tensor layout, cache lifecycle, custom
CANN operators, and dispatch. It cannot:

- replace Ascend AI Core arrays with the paper's systolic/vector-unit arrays;
- change GDDR/HBM placement or package floorplanning;
- add the paper's PE registers, reduction trees, or special-function rows;
- create the proposed package-to-package physical interconnect.

Therefore the paper mechanism is unreachable in this environment.

## Why no NPU experiment was launched

An NPU experiment must vary the paper mechanism. Running Qwen3.6 on unchanged
910B4 silicon, or porting only the simulator's algebra to PyTorch/CANN, would
test a different hypothesis. Simulator `tics` also cannot be converted into
Ascend TTFT, TPOT, or throughput.

The applicability gate is therefore terminal before numerical and performance
gates. This follows the one-day piercing rule and avoids spending NPU time on a
control-only run with no DUET candidate arm.

## What can still transfer

DUET contributes two useful design principles:

1. measure prefill and decode separately because their bottlenecks differ;
2. use phase-specific implementations when a real runtime exposes a
   software-controllable seam.

Those principles can guide Ascend operator selection, P/D deployment, or
prefill/decode-specific graph policies, but such work must be evaluated as a
new Ascend software hypothesis, not claimed as DUET reproduction.

## Acceptance status

- Mechanism fidelity: failed at hardware reachability.
- NPU numerical correctness: not applicable; no faithful candidate exists.
- Dense A/B performance: not run.
- LongBench-v2/GSM8K: not run.
- 10% end-to-end target: not met and not claimed.

The ten-paper queue can now be considered pierced in order, with DUET closed as
a scoped applicability no-go.
