# DAMP Ascend — current workstream

Activated 2026-10-06T08:48:03Z; hard deadline 2026-10-07T08:48:03Z.
Status: planned, not an NPU/performance/accuracy result.

The previous KIVI closeout and training-free preference were pushed normally
at e63df71 after GitHub HTTPS connectivity recovered. No force push or main
edit occurred. This existing clean target-host checkout is reused on a new
work branch; no ninth worktree is added and all older branches/checkouts are
preserved. Canonical repository remains /opt/host/vnf/austinov/model-tuning-lab.

Primary change: DAMP's offline decay-weighted mixed-precision recurrent-state
storage, not unrelated fusion, MTP, training or distillation. Source is
arXiv 2608.27513v2; no official code link has been verified. Equation-derived
port and project-chosen SR candidate grid must be labeled honestly. Reuse
native Ascend recurrence and existing plugin/operator scaffolds only where
semantics/ABI agree; independently named opt-in code fills the packed-state
update gap if it is proven to exist.

Next: inspect deployed gdn/native schemas and ops-transformer, establish a
nonprivileged physical4 canary, then build output-preserving live state/decay
capture. Freeze full-precision reference trajectories before selecting any
precision mask. Numerical implementation parity uses the same quantization
algorithm as its oracle; quantized-vs-dense drift is a diagnostic, not the
maintainer's 1% task-accuracy tolerance. Require complete state, untouched
slots, changing inputs, multi-step and graph checks before performance.

The maintained goal remains >=10% fixed-1024 E2E output throughput gain,
TTFT/TPOT separately, and final non-thinking max_tokens=2048 normal-EOS
LongBench-v2/GSM8K. Latest explicit user permits up to 1% E2E task loss:
report both pp and relative loss and also audit the original no-loss target.

At orientation NPU4-7 had no compute PIDs, AICore0 and ~2653 MiB baseline
HBM. One external sleep-only container declares 0-7; declaration alone is not
an obstacle. Recheck before every new load. Never stop it without an actual
mapped conflict and applicable narrow authorization. No DAMP load is running.

Artifacts: new non-overwriting /cache/cch/qwen36-damp-20261006 subdirectories;
raw tensors/weights/profiles stay outside Git. Stop and retain only owned
containers after runs. All operation handles must be polled, not relaunched
because an observation times out. Close the current route with scoped
accepted/rejected/failed/inconclusive evidence by its deadline.
