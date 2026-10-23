# Independent 2k prefix numerical preparation — NOT runtime ready

Own scope only. No old131/frozen source is changed, no source/authority is bound, and no Docker/NPU/HTTP is run. This is not a performance or numerical result.

## Actual independent path and changes

The existing FAST consumer uses original oracle112.sequential, independent_model.old112, g2_numeric.conv_math/fa_owner/equal and source-derived independent_model.attention. Existing generalized_attention already replaces the old131/two-page lookup with actual owner length while retaining the same FP64/FP32 softmax formula and pointwise .001+.01*abs(reference) bound. GDN state/output/P/U thresholds and the independent sequential oracle are unchanged.

render_numeric_2k.adapt applies a complete reversible source delta to this actual consumer and its existing qualification taps. It adds actual2048 prefix guards with an explicit source-pinned8/160/1024 qualification budget, full actual private scratch/mask/table validation and fixed native allocation continuity. The complete qualification declaration must exactly match the actual performance-profile input/output, with unchanged logical cap and formal_performance=False. Owner maximum length is2048+B-2, version maximum B-2 and remaining publication count2048+B-1-L for that SAME budget B, not an assumed1024. All original64-layer/128-write, GDN full state/wide-conv, native FA full before/after page, accepted-path indices, state digest and outside-table-pending checks remain. It does not call the old131-only independent_model.consume or g2_numeric.consume_step; those separate public paths are NOT claimed generalized here.

numeric_prefix_2k.prefill verifies the actual int32[2048] native ID tensor, actual_CPU_token_ids and strong-request prompt IDs, plus unchanged runtime sources and optional native BF16[2048,5120] embedding lookup. This function is prepared; actual producer/join to the first observed frame is still pending and cannot be replaced with a declared input length.

## Native publication is NOT private scratch

Owner length2048..3070 requires publication ceil((L+2)/128), at most24 pages. Three PRIVATE branch slots require ceil((L+3)/128), at most25 pages. Child2 is private scratch positionL+2, but if selected, commits to native positionL+1. No25th native page is invented or demanded. Frame guards also enforce remaining output budget; atL3070 only one new token is allowed.

The old FAST observer retained q/k/v/output but did not retain actual operator scratch arguments. New qualification-only taps observe the actual service FIA kwargs, not a reconstructed candidate trial:
- Full BF16 scratch K/V, bool mask and int32 table before conversion.
- Full BF16 query digest joined to the existing same-frame actual q.
- Full FP16 query/K/V and original-dtype bool mask/int32 table digests immediately before and after the REAL delegate call.
- Completed boundary/source/owner/layer and event-stage join.

The independent CPU consumer reconstructs scratch from the retained native preimage and actual post-RoPE rows, validates every byte, private sibling mask and padding, then reconstructs the FP16 cast and compares all delegate-operand digests. FP16 duplicate tensors are not persisted. These are observations only: candidate arithmetic, native delegate call, cast and permanent writes are not replaced.

## Budget is not guessed

AtL3070 the added retained logical capture is exactly52,584,000 bytes per frame across16FA layers (two BF16 scratch tensors + actual mask/table). Maximum single CPU digest payload is1,638,400 bytes, NOT a peak-RSS claim: the actual helper holds a CPU tensor plus its byte copy, at least3,276,800 bytes before allocator/serializer overhead; measured peak RSS is pending. Existing logical operands, actual serialized current wire bytes, retained first raw, checkpoints, combined metadata and retained failed-frame bytes remain separately required. Failed-frame bytes must explicitly be zero only if the actual lifecycle proves none retained. The current retained-byte subtotal does NOT account for simultaneous decoded/current logical CPU tensors, temporary digest copies or serialization/allocator overhead; their lifecycle overlap and a complete joint budget are still unbound. The original384MiB frame and1GiB joint caps are unchanged. A nominal or partial sum never returns fit_proven or runtime_admitted.

Both observer installation and consumer begin with an UNBOUND hard refusal. Fresh actual live native geometry, actual prefill/first-frame identity and a source-reviewed measured joint raw/wire budget consumer must be connected in a new reviewed source revision before execution. Boolean PASS, CPU geometry arithmetic or old131/short8 results cannot open this gate.

These are distinct qualification scopes, not formal-performance modes. An8 or160 result cannot qualify1024; complete profile/source/coverage must be separately bound. Formal performance without qualification remains fixed1024 in the service entry. The existing short8/160 whole-source builders and validators still require a reviewed2k composition; accepting the correct budget in these two components does not create that whole-source or execution authority.

## Software evidence boundaries

Host /usr/bin/python3 has neither torch nor numpy (0a5c). Controls therefore cover source/inverse/actual tap placement, independent scalar prefix/sibling discrimination, exact24-vs25 geometry and native indices, owner/output budget/page metadata, and cap rejection. Real tensor scratch/digest/prefill execution and original FP64/FP32 tensor threshold controls remain PENDING for same-image no-device preparation and then actual NPU evidence. No synthetic software result is an NPU numerical PASS.

Read-only default-OFF commands:
python3 -I -B render_numeric_2k.py --check
python3 -I -B test_numeric_2k.py
