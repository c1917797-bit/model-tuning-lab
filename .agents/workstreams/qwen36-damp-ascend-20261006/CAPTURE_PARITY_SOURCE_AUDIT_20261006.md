# Capture parity: source and admission audit — 2026-10-06

Status: **source audit complete; root cause unproven**. This records a failed native capture's noninterference gate, not DAMP compression accuracy, a task score, performance, or a paper-wide no-go. The companion JSON carries exact paths, hashes, seams and scope.

## Observed result and authority

MAIN's MA `exec-0000000000000455` completed exit1 after all36 requests produced4096 tokens. Existing arrays have7 identical outputs and29 different outputs; all36 prompt hashes agree. First differing token indices range11–895. The original failure and stopped owned container remain retained. No valid full SOURCE_LOCK or192 calibrated plans exist.

The read-only diagnostic is:
`/cache/cch/qwen36-damp-20261006/capture-parity-failure-analysis-v1/RESULT.json`
SHA256 `be0721d46f5ed9e5a8bcc6574bc104bde5308f452870640663dd92f6e72c9bc4`.

This agent's original read-only operations were MB `exec-00000000000003cd` and `exec-00000000000003ce`, both completed exit0 through `force_direct/tpc`, `routeDecision=peer_direct`, target `lgw_53d59c2f73ef4b81ba3cc0e00c2f8d35`. These MB handles must not be polled against MAIN's MA peer. They read existing bytes; they did not execute Torch/NPU, modify frozen source, or mutate Git.

## What source proves — and does not prove

Frozen collector `damp_capture/patch.py` SHA256
`3b1791ec12d072ce03c07a952984308b34adf1c3a64020d69cf2384c93e4ea78`:

- Lines87/147 call the saved native model forward; lines172/196 call the saved native GDN core; line157 calls the saved native gating function. Each active path calls once with original arguments and returns the original result. The donor/actual Qwen receiver alias helper preserves the native callable before binding. No collector recurrence/gating recomputation or direct write to original state was found.
- Line136 copies native positions to CPU; lines181–184/190 copy layer indices/boundaries/lengths. Line166 copies the actual gate output to CPU **before the original GDN core resumes normalization and recurrence**. Line206 copies selected native state at anchors. These are blocking diagnostic transfers and change host/device overlap.
- The writer requires CPU FP32 state, serializes CPU bytes, and accumulates RMS with CPU FP64 non-inplace operations. This source does not write back those tensors to NPU state. Source inspection still is not actual before/after numerical equality proof.

The actual native GDN snapshot has SHA256
`d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816`;
its original image path is `/vllm-workspace/vllm-ascend/vllm_ascend/ops/gdn.py`.
Line313 gates; lines423–424 normalize; line427 invokes native recurrence. Thus unchanged arithmetic source is compatible with changed synchronization timing; the latter is a candidate cause, not an established causal finding.

The earliest token difference is11, while the first full-mode state anchor is update256. Consequently anchor/RMS serialization alone cannot explain every early difference. Metadata/gate copies and changed request admission remain relevant before that anchor.

## Real ON scheduling was not fixed batch4

The rank0 original event file:
`/cache/cch/qwen36-damp-20261006/full-reference-resume-v1-on/rank-0/events.jsonl`
SHA256 `92b8b36c83d8d5393bf8982d7d925a7b27ce1a257a16d6e668ae8287ec27c206`.

It records these native admission sequences, using source-bound external IDs:

| TRAIN group | Actual ON turns |
|---|---|
| math-fit | First ID0 alone,1024 prefill tokens; then IDs0–3 with3073 tokens and computed counts[1025,0,0,0]: **1 → 4**, mixed decode/prefill |
| math-tune | First ID4 alone; then IDs4/5 with1025 tokens,[1024,0]; then IDs4–7 with2050 tokens,[1025,1024,0,0]: **1 → 2 → 4** |
| general-tune | The same **1 → 2 → 4** admission pattern |

`run.py` lines61–64 submits each four-row group to `llm.generate`; a client group/max_num_seqs is not a native model-forward barrier. Gate transfers could change when additional asynchronous requests become available, which can change prefill/mixed kernel shapes. This is an evidence-supported hypothesis, not proof that this was the actual OFF/ON cause.

**OFF native turn shapes were not captured. We do not infer them from ON.** Client logical IDs, external-ID order0–35 and prompt hashes agree across arms. Internal randomized IDs legitimately differ. No output zip mismatch or blind suffix recovery is claimed.

Rank0 counts are36 request bindings,36,882 complete turns,10,368 anchors,10,368 futures and1,728 layer completions. Counts alone do not check all artifact bytes or all four ranks. No full capture PASS follows.

## Why the full result remains failed

Frozen validator SHA256
`2daf0cefe7311431baf9bb0a2aa1dbebe62543598ddcec0bada55796d4be4b8c`
rejects token output parity at line40 before reading rank artifacts at line53. Completed generation therefore does not establish the full state/decay evidence chain. Preserve the failed result; do not fit or sign a successful calibration identity from it.

Temperature0/seed0 are sampling settings, not an independent proof of native eager determinism. OFF/OFF repeatability, identical native batch shapes and a same-input local numerical comparison are missing. Neither speculative blame nor relaxation of the output gate is justified.

## Narrow short diagnostic proposal — NOT implemented or launchable

Only after MAIN review, prepare a NEW `projects/damp-ascend/tools/fixed_admission_capture_v1/` packet. Do not change frozen collector or the frozen shared-lifecycle13 files.

1. Derive one explicitly **smoke/not-calibration** manifest from the exact existing TRAIN `math-fit-02` row:1024 input token IDs, fingerprint `3221d44cf06bc8c752a03a0c895d5a5fb82ef73ab7fe714efd67b29fe427522d`. Keep source provenance; no padding, new data, final-eval borrowing or author-sample claim. Use33 fixed outputs, anchor24, future2, no thinking/normalization change. The frozen corpus contract allows smoke output at most33; do not silently call128 outputs a supported smoke.
2. Run fresh sequential OFF-A/OFF-B/ON arms, TP4 on physical4–7, **one request only**, eager, prefixOFF, chunked-prefillOFF. No queued second request or speculation is permitted. This fixes admission without pretending a multi-request queue barrier has already been proven.
3. Apply the same NEW diagnostic observer to all three arms. Proposed observation is a native Python code-object profile callback, not replacement arithmetic or rebinding GDN core methods. Verify actual source/frame/callable identity and exception behavior before NPU. Record every4rank×48 native GDN call, actual CPU query-start/computed/slot identities and native argument/return/state evidence. All corresponding prefill1024 and32 one-token native turns must match the declared shape.
4. Compare native inputs and before-state **before** comparing after-state/output. Locate the earliest available GDN seam difference. This does not establish independent FA/matmul/logit arithmetic. If all GDN evidence matches but tokens differ, report that narrower fact instead of inventing a GDN cause.
5. Retain bounded raw inputs/state/outputs before assertions. Save initial/after-state frames once; verify each before-state hash against the preceding after-state for the same slot. Retain raw-before on mismatch/missing prior state. Hard total cap20GiB; no all-token Fraction oracle or persistent dense sidecar.
6. Stop at the first failed gate. If OFF/OFF drifts, do not continue ON or attribute causality to capture. Whole budget45min including three cold starts, ordinary-RAM floor64GiB and unchanged8GiB reserve, disk floor40GiB, fresh physical/cgroup/ownership proofs and exact owned stop-retain finally. MAIN exclusively executes Docker/NPU. No automatic retries.

The **existing, source-verified inner CLI** for each future smoke arm is:

```text
/usr/local/python3.12.13/bin/python3 -B -m damp_capture.run
  --manifest /cache/cch/qwen36-damp-20261006/calibration-inputs/fixed-admission-source-diag-v1.json
  --output-dir /cache/cch/qwen36-damp-20261006/fixed-admission-source-diag-v1/off-a
  --capture off --batch-size 1 --memory-utilization 0.80
```

OFF-B changes only the arm basename; ON also sets `--capture on`. **The manifest, common observer, source manifest and controlling launcher do not exist yet.** This is a bounded design/argv specification, not permission or a ready command to execute. MAIN must review the exact NEW source closure, actual immutable-image callback/CLI tests, new input hashes and fresh admission first. Output roots must be absent; never reuse/overwrite the failed full capture.

A successful B1/33 experiment would establish only that short fixed-admission scope, not full36/4096 noninterference. A short failure is not DAMP task loss or paper-wide no-go. If it passes, a source-proven C4 pause/queue barrier can be reviewed separately; do not blindly repeat the full expensive pair.

## Integrity boundaries

- Original failed files, frozen collector source, shared-lifecycle13 and native runtime/image remain unchanged.
- No valid SOURCE_LOCK,192 plan, compressed serving, graph, end-to-end gain or task accuracy is asserted.
- Existing source-only observations and hypothetical explanations stay separated.
- MAIN may publish these two audit files at the next coherent checkpoint; this agent performs no Git mutation.
