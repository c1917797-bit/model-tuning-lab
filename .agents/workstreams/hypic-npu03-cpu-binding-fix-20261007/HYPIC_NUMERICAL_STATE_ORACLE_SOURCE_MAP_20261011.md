# Direct state oracle: source map and offline comparator (2026-10-11)

Status: comparator implemented; **capture adapter not implemented, no device
experiment admitted**. This is diagnostic infrastructure, not a HYPIC repair,
numerical-equivalence result, quality acceptance, or a replacement for r19/r22.

## Frozen evidence and source

r22 paired audit was rehashed unchanged:
23568b259c3bff7b3da562db0532a817c1705972ac283af55f8245d197185e1a.
The clean source examined is /cache/cch/hypic_vllm_ascend-hotproof-20261008,
commit 4429e35177979c874bf053ab29789e4773f39b22.
- context.py SHA256 c95550602542a30a09dd2979e6e58c1d1bd17d653ff05880347d96aaf2a4aac0
- patches/attention.py SHA256 0e13fbf953f40d3e6103fc7e4b1858755d8992d108d8b1763659aa29fb502876
- patches/gdn.py SHA256 72d58fdf03a4317ee4493ac475cd4b059ae3ed7f9138243446737a860537623d

Read-only source findings are not runtime causes:
- HypicForwardContext is allocated per execute_model forward. Staging keys
  intentionally reuse same-shaped scratch. GDN material stage names include
  the segment hash (gdn.py 937–980), so shape-only aliasing between distinct
  segment hashes is not established by context.py alone.
- PI KV replay consumes canonical K/V then applies anchor RoPE before writing
  actual cache slots (_repair_position_independent_kv). Compare destination
  slots, not merely the source tensors passed to reshape_and_cache.
- GDN replay composes T @ incoming_state + S, then transposes/casts into the
  request's actual state slot (gdn.py 1177–1248). Conv history is independently
  stored at the state index (985–1082). Source presence/shape checks cannot
  establish numerical correctness.
- Producer materialization uses zero-start public segments, while native
  full-context execution has a different attention context. Raw native-vs-PIC
  tensor inequality is not automatically an implementation defect.

## Comparisons that must remain separate

1. Storage integrity: producer snapshot versus retrieved same-generation
   canonical K/V, conv tail, S and T. Match dtype and exact coordinates;
   retained CPU snapshots must own their bytes, not alias mutable buffers.
2. Replay correctness: canonical K relocated with independently computed
   RoPE versus actual destination K slots; canonical V versus destination V;
   independent T @ incoming_state + S (including output cast/layout) versus
   actual GDN state slot; reconstructed conv tail versus destination tail.
   Do not use the production output as its own reference.
3. Position correctness: request logical positions, compacted physical rows,
   block table slots and GDN state indices, checked against the frozen plan.
4. Native-versus-PIC semantic difference: matched token prefix and per-layer
   input/output captures only after 1–3 are valid. Report error magnitude and
   first divergent layer, not a bitwise-equality quality gate. Distinguish
   within-arm numerical variation and PIC's context approximation.

The comparator numerical_state_oracle.py reports absolute/RMS/relative RMS,
coordinate coverage, and identity mismatches separately for each component.
It rejects mismatched request/rank/layer/step/segment/generation/coordinates,
nonfinite values, invalid positions and missing rows. Zero reference norm is
reported as null relative error, not an artificial pass or infinity.
Synthetic perturbation tests only establish comparator behavior.

## Capture admission still outstanding

Implement a disabled-by-default removable observer in a separate source
revision; do not edit or relaunch frozen r19/r22 sources/roots. Capture exact
request IDs on all four TP workers and join them to independently audited
HYPIC hot receipts. Record source/image/weights, tensor dtype/layout,
generation, coordinate selection, full tensor shape, capture stage and raw
hashes. Sampled coordinates cannot certify full tensor equality.

Use one prospectively chosen request with known serial hot behavior to verify
capture coverage first. This is not a new full suite or independent GDN task.
Do not repeat r22's entire c32 wave merely to hope sample082 becomes hot.
Any later concurrency-stress diagnosis needs its own falsifiable source
hypothesis and bounded request schedule. Instrumented timings are not
performance results. A later corrected-source full 127x3/max2048 pair remains
required for adoption; preserve r19 REJECT_OR_QUALIFY.

Before any device admission: source observer host tests, comparator negative
controls, exact fresh roots, fresh ma/direct-route, physical NPU0–3 and8223
idle, continuous isolation and exact owned cleanup. NPU4–7 and foreign tasks
remain untouched. No numerical tolerances are yet frozen; no device launch
is authorized by this document alone.
