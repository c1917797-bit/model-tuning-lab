# Independent C1 derivation and scope

New mathematical reference follows paper equations2/6 using a key-major state.
A direct dense per-token recurrence is the oracle; the accumulated tuple uses
low-rank erasure updates. Tests cover a nonzero incoming state, segment order,
associativity, empty segments, wrong naive addition, grouping and configured
TP4 dimensions(Hk4/Hv12/D128). FP64 tolerance1e-10 is a local arithmetic test,
not a BF16/NPU or task-quality threshold.

Source: https://arxiv.org/html/2607.01299v2
No existing HYPIC module, source or kernel is imported/copied. Official Torch
operations are reused. This code is an equation reference, not yet a runtime
patch, native GDN comparison, graph correctness or performance result.
Gate before production implementation: establish identity-matched nativeTP4
baseline and serving source contract. C2/conv/seam remain pending.
