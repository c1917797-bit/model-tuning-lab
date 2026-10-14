# C2 compact query implementation checkpoint

Independent query planner88f34998 now has cache binding and request-local
official paged-attention metadata construction. Source inspection0075/0076
confirmed PrefillCacheHit uses paged KV, per-request block tables and logical
seq_lens_list. Only queries and their newly written slot_mapping are compact.

CPU checks:0077 passed18 C2 tests including5 cache-binding controls and an
independent FP64 dense-attention oracle. Two windows exactly reproduce the
full causal attention retained queries on identical Q/K/V; a single compact
bottom-right causal window fails the negative control.0079 passed2 metadata
tests covering native-object/request isolation, live table drift and mixed
batch rejection. Fixture tests do not prove actual official metadata dispatch.

Write ownership remains explicit: cache association alone cannot grant a lease.
Binding rejects aliased scheduled writes, writes into computed-prefix slots,
unleased slots and request/rank/step drift. No runtime hook is enabled by these
modules. No new device job was launched.

Next: connect compact hidden/residual rows through decoder layers and install
body KV using real native cache mapping/ownership before submitting the two
window calls to the source-bound backend. Independently validate C1 seam/body
state handoff and all-layer material readiness; do not allow false native
fallback success. Then freeze one integrated27B TP4 request/device contract.
Formal performance/quality and lifecycle remain pending for this new path.
