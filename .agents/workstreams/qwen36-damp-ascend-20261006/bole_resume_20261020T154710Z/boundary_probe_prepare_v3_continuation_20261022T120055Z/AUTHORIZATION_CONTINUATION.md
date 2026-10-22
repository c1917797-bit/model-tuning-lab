# Explicit continuation authority, recorded 2026-10-22 12:00:55 UTC

The user explicitly said: “可以继续穿刺一直到成功”. This is new permission to
continue the Qwen3.6-27B paper-to-Ascend task after the prior result window. The
record time identifies this continuation checkpoint; it is not a claim that
the chat message has an independently verified second-level timestamp.

The previous window keeps its hard report deadline of **2026-10-22 12:38:41
UTC**. Its source, authority, results, failures, and output directories remain
immutable. This document does not extend or rewrite that old ticket.

For the first continuation diagnostic, MAIN chooses a finite internal batch
envelope from **2026-10-22 12:00:55 UTC** through **2026-10-22 18:00:55 UTC**.
This six-hour bound is an execution limit selected under the user's continuing
permission; the user did not promise a separate six-hour result window. Each
new owner retains the existing 3600-second phase and 180-second cleanup budgets.
The whole 3780-second preparation/admission allowance must fit before this
batch's cutoff; no phase, cleanup, or numerical threshold may be shortened to
obtain admission.

## First admitted scope, only after separate gates

- Model: `/cache/efim/Qwen3.6-27B`; physical Ascend 910B4 NPU 4–7 only, TP4.
  Physical NPU 0–3 remain protected. Visibility variables and requested device
  mappings do not establish actual ownership.
- Candidate: BOLE diagnostic path, explicit opt-in and default disabled.
  Observe two genuine requests with 131 input tokens and 8 output tokens each,
  plus the existing native retirement/lifecycle barrier. Trace the actual
  layer-0 projection caller between the already observed norm return and
  out-projection return; do not split fused kernels or add new GEMMs,
  collectives, writes, or model computations.
- This batch can establish diagnostic observations. It cannot pass the old
  ON/OFF pair, establish whole-model numerical qualification, authorize formal
  performance, or count as final task accuracy merely by completing requests.
- Before any NPU owner, MAIN must finish and independently review exact source
  closure, fresh same-image software controls, numerical preconditions, fresh
  topology/process/container/device mapping/RAM/disk/output checks, the MAIN
  serialization lock, and prior owner termination and resource release.
- Use new source and exclusive output identities. A failed invocation is
  preserved; only its evidenced cause may be repaired in another version.

## Unchanged completion criteria

Deliver one non-HYPIC, training-free, explicit opt-in vLLM-Ascend monkeypatch
plugin. Before performance, pass true-NPU numerical, multistep-state, and
lifecycle gates without weakening their tolerances. Full-model dense/candidate
performance must use the same configuration and fixed 1024 output tokens, with
three matched formal pairs and at least 10% throughput improvement, reporting
TTFT and TPOT separately. Final GSM8K, HumanEval, and MMLU use thinking off,
`max_tokens=2048`, normal EOS, and the user's allowed 1% accuracy loss; report
both percentage-point and relative changes. HYPIC and component/CPU-only
results cannot satisfy this goal.

Current facts remain: the corrected short-pair reader failed on the unequal
complete frame-key sets (ON 36, OFF 32); the boundary diagnostic localized the
first observed cross-generation difference to the layer-0 out-projection
return after equal captured norm outputs. Its cause is not established. No
formal 1024-token speedup, formal TTFT/TPOT, or final task-accuracy acceptance
has been obtained.

## No automatic admission

This authority record grants no resource owner and contains no fabricated
source-freeze, MAIN review, CPU PASS, NPU PASS, or equality claim. Any later
batch receives its own finite identity and gates under the user's continuing
instruction, preserving this batch's original limits and failed evidence.
