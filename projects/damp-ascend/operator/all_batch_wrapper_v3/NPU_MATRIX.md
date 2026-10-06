# Required all-T acceptance matrix — not executed

MAIN owns source review, no-device compile/export/load, fresh fail-closed
physical NPU4–7 and new non-overwriting outputs. This candidate is not enabled.

1. Verify newcompiled9, image, OPP9.1 identity, library SHA, symboldefined and
   actual Ascend910B4/device mapping. No-device schema/Meta positives for all
   T1..16, negative T0/17/wrongshape/dtype. Record inherited Meta layout limits.
2. Anchor the new SO at T1/T16 against original v1/arena numerical receipts,
   including saved-step45. Do not reuse an old SO or mark receipt by rename.
3. Every new T2..15: S=T+3, first/last/changing unique indices, original160-step
   changing-input own-feedback independent packed golden. Per-Hv permutations,
   SR1/power2 and general positive FP32 SR; independent native-derived reference
   anchors where the protocol requires. No production/helper self-reference.
   Same-arena zero-gap and64B guards must retain fullraw/conv/padding bytes.
4. Complete selected/allstate/untouched slots, output finite/shape/dtype,
   raw high/low/scales bitwise under the applicable original protocol, state
   relativeL2<=1e-5/output<=.00303, inputs/plans/meta unchanged, stable
   data/storage/offset/shape/stride identities. Save rawactual before assertions.
5. T2/T7/T8/T9/T15 are explicit metadata-pad boundaries; no special-case skip.
   For each T, reject indices<0/>=S and duplicate (whenT>1), firstlength!=0,
   active lengths0/2. Entire rawarena unchanged and NaN output required.
   This is original pre-writer validation, not rollback of internal pack errors.
6. Only after eager acceptance: separate cold prepare/key/graph for EACH T.
   Changed inputs/indices in place across160replays and three reset identical
   trajectories; fullraw guards/untouched/input/pointers. Invalid metadata
   replay also unchangedstate. Hold complete rawarena/views throughout graph.
   No padded T16 shortcut with fake unused slots or zero-length PAD acceptance.
7. On failure retain CPU fixture/before/golden, original dispatch error,
   nullable copied outputs/after and secondary D2H errors before assertion.
   Any partial internal pack failure retires all touchedslots/worker; no retry,
   native fallback or silent shape switch.

Only after these actual receipts may a NEW opt-in service adapter admit1..16
pure-decode rows at max_num_seqs16. It must source-bind actual48 receivers,
validate four-region typedarena/shared_by lifetime, use initialized/stable slot
leases, build cold/graph entries for each real activeT, reject mixed/continuation
prefill and MM/softprompt/encoder routes at request layer, and preserve atomic
turn publication or permanent slot/worker retire on execution errors.

A working operator is not proof of actual scheduler boundary correctness or
whole model192plans/prefill-pack/timing/quality. Final C16 protocol, common dense
optimizations, fixed1024 performance and2048normalEOS task gates remain unchanged.
