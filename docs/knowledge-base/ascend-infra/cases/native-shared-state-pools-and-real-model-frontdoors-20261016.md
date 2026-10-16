# Native shared state pools and real-model frontdoors

Status: implementation diagnosis; no new technique accepted. HYPIC is historical, not a result of this round.

## Verified failure versus an unverified explanation

DeltaLog101R10 completed 101/101 actual same-image software controls, loaded the isolated opt-in package and native four-device canaries, and reached a real HTTP completion after model startup. It then failed in layer registration before original native prepare or candidate model arithmetic. The parent SSE/count error is secondary to the worker's `registered actual layer arenas must not overlap`. Actual owner result: 3834 bytes, SHA256 `bc9fc23a42be7ad271ac066a34c187a128e98c90f4a33a743a0d83eff2df3c7e`; original files and failures remain retained.

The checked contiguous interval `[data_ptr, data_ptr + numel * element_size)` is not proved to contain an offset error. Actual Ascend allocation source explicitly assigns one raw tensor to all names in `kv_cache_tensor.shared_by`; each Mamba layer then obtains compact conv/state views from that raw buffer. Whole arenas can therefore overlap while different groups use different physical slots. This is a source-supported explanation, NOT proof that the actual collision was harmless.

Before any adaptation accepts sharing, capture the two actual prefixes/groups/objects, storage/data pointers, offset/shape/stride/dtype/device/size, declared shared allocation, static context identity and real request block allocation. Pre-prepare CPU tables must not be called committed metadata. Original native prepare includes H2D/device-buffer work. If a post-prepare observation is needed, use a separately frozen observer that stops unconditionally before model forward. Same-group same-slot overlap, undeclared sharing, wrong layer binding or intersecting live byte footprints must remain hard failures. Recheck retirement/reuse and deferred auxiliary state, not just initial addresses.

This failure means the current integration assumptions require diagnosis. It does not establish an incorrect recurrent kernel, valid model outputs, a paper no-go, or any performance result.

## Test the actual frontdoor, not only a library helper

BOLE131R1 passed its previous patched-Ascend FA source gate and loaded real model weights, then failed because the actual `@contextmanager` wrapper belongs to Python `contextlib.py`, not the wrapped module's basename. The repair binds the exact installed Python3.12.13 standard-library bytes and one known wrapper/body/closure/global/code chain; broad `unwrap` or arbitrary wrapper acceptance is not allowed.

Further actual-source review caught additional deterministic defects before R2 was admitted: the checkpoint architecture is ConditionalGeneration, whose top-level multimodal config does not forward `vocab_size`; the language-model owner and MTP carry the real text config. Native multimodal preprocessing can pass pure text as `input_ids=None` plus `inputs_embeds`, and the real runner token-ID buffer is int32. Do not delete the guard or pretend converted IDs were the original input. Preserve the actual native call, recover the IDs from the source-bound current runner/request, prove pure text and exact positions/count/value identity, and record the real input mode/dtype. Handcrafted tree IDs are a separate ABI.

A cold probe stopping at the first native boundary usefully tests source plumbing but does not cover later real object/configuration contracts. Review those contracts against the installed allocator/model/preprocessor constructors and capture live facts where a static source cannot decide them. These are specific adapter failures, not evidence against BOLE's mechanism.

## Source composition and validation cost are separate gates

The prepared106R7 production receiver referenced a helper absent from the exact101R10 source. A real declared-file/frontdoor test caught the inevitable KeyError.106R8 owns the original replayable helper bytes itself and does not fabricate a file in the model source. Small helper tests prove that seam only; actual R4 full160 recovery and model receipts are still mandatory.

Static call-graph audit also found repeated complete raw-index/blob hashing in worker registration, common plugin and live snapshot validation. This is a startup/validation engineering risk, not a measured model slowdown. A future source-bound host PRE/POST certificate must tie the actual full verification to the run/lease/source/index/owners/DSOs and retain the complete final data/source/storage fence; PRE grants only execution and never final success. A free Boolean cache or omitted final fence is not a repair.

## Reusable decisions

* Separate a parent process/HTTP failure from the first worker fault and its real operands.
* Keep native allocation/group/lifecycle semantics in an independent interface contract. Whole-buffer assumptions are not universally portable safety invariants.
* Test the real entry, complete declared source and configuration/input mode before another expensive model load; keep mathematical tests independent.
* Instrument an unresolved fault before weakening a guard. Capture only the missing bounded evidence; do not repeat an unchanged deterministic failure.
* Software/ABI repairs, component passes and reports do not qualify as whole-model performance or task accuracy, and do not activate the conditional extension.

Current original cutoff remains2026-10-17T07:02:13Z. The single conditional extra24h is authorized but unused. Only physical NPU4–7; external0–3 workloads were observed and left untouched. Exact R10 CPU/model CIDs were independently confirmed exited/Pid0/noExec/noOOM in op0f69. See the adjacent workstream checkpoint for immutable refs, current handles and missing gates.
