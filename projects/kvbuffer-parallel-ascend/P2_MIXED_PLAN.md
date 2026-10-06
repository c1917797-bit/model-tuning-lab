# P2 mixed-lane interface — NOT implemented / NOT P1

Real v0.23 GDN core takes mixed_qkv,b,a,core_attn_out. Non-spec ordering is
decode first then prefill. Causal convolution metadata, gating and l2norm stay
native. Pure decoded lanes may use the new P1 op. Prefill lanes retain the exact
native chunk path and FP32 native recurrent pool.

P1 currently materializes decoded slots and calls the ORIGINAL mixed core.
Do not claim these mixed batches execute buffered candidate recurrence.

A separate P2 change would need:
1. Source-bound CPU proof of decode/prefill boundaries and unique disjoint slots,
   first-token/state initial flags, actual_seq ABI and padded-zero dummy offsets.
2. Materialize only prefill slots which truly require initial state. Native
   full fresh prefill overwrites state; reset only its auxiliary metadata.
3. Reuse native conv/gating/normalize interfaces without double convolution or
   missed conv-state writes. Split the exact Q/K/V outputs at num_decode_tokens,
   not a guessed count; preserve native accepted-token semantics.
4. Candidate decode owns decoded slots, native prefill owns prefill slots; no
   whole-batch flush; prohibit speculative metadata and prefix/migration until
   independent lifecycle/copy/export contracts exist.
5. Full native-off/on numerical/output and state/log footprint validation for
   mixed batches, shrinking batches, slots reused after EOS/cancellation,48layers
   ×4ranks; then model graph capture/replay with zero dummy rows and fixed pointers.
6. Separate new output/source/artifact identities and sole-change performance
   screen. No relabeling serial v5 or combining P1 and P2 results.

P1's kernel graph gate is only an operator ABI proof. It cannot sign off P2
scheduler/model graphs, nor support prefix caching or cache transport.
