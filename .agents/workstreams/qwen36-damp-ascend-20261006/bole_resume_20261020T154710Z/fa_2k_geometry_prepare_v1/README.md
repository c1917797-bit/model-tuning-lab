# Native2k FA geometry and private three-node view

Source preparation only. No NPU, Docker, authority, SOURCE_BOUND, allocation or
observed page count has been created. The131 source and inverse remain intact.

## Actual mechanism

The original model_entry._fa and actual service_bridge._fa gather ceil((L+2)/128) native publication pages.
The unchanged adapter.prepare allocates ceil((L+3)/128) PRIVATE pages and puts
root/left/right at L,L+1,L+2. Commit writes only root or root+one child to native
positions L or L,L+1. For2048 input/1024 output, MAX_BEFORE3070 therefore needs
24 native publication pages but25 private scratch pages. The extra private page
does not imply a third native1536 block. Two actual native1536 blocks would be
enough if native prefill really allocates them; that observation is still absent.

fa_native_geometry.bind_all is an actual native-after-prefill hook using source
identities, real NPU input/cache objects, all16 FA layer contexts, original
fa_prefill131r10.mapping, full CPU/GPU/metadata tables, every2048 slot destination,
and strong request/group/table/storage objects. It is defaultOFF behind
BOLE_NATIVE_2K_GEOMETRY_ENABLE=1. JSON, an arithmetic plan, CPU buffers or guessed
page counts cannot substitute for NativeGeometry. Registration.attach passes
the same strong binding to the actual cache registry. Every later check refuses
request/slot reuse, alias rebound, native table changes or insufficient
accepted-path capacity. No native allocation/growth is implemented or inferred.

render_geometry.adapt changes only eight existing source files plus the new
geometry helper. It routes real model staging, service FIA shapes and live owner
allocation checks through the observed native geometry for2k, while keeping the
original131 path, adapter mathematics, independent references, TP consensus and
transactions byte-for-byte. All native scratch mask/table/padding checks and
FIA argument values remain. The original metadata observer retains its2MiB
limit; no bucket or raw budget is increased. The model native-ar sequential
controls and independent numerical consumer remain separate and unqualified.

The service installer replaces Bridge._fa with service_bridge._fa. Both paths
must check the same live native geometry and attach it to the actual prepared
trial before ServiceFiaBoundary construction. Merely fixing model_entry._fa
does not reach the production override. The original2635546 preparation lacked
that override propagation and is retained as history, not a validated2k route.

The native-after-prefill service callback now contains the actual bind_all call.
This component deliberately does NOT remove the rest of the131 input/GDN/source
contracts. Current whole-source/runtime entry is therefore NOT ready:2k routing,
GDN prefill/tail binding, all independent2k consumers, source producer/authority
and real first/current/failed raw+checkpoint joint budget still need composition.
Changing those assertions alone is not a valid integration.

## Checks and minimal real observation

test_geometry uses explicit synthetic metadata/lifetime objects only. It checks
full table/slot joins, insufficient-page rejection before indexing,24 versus25,
all allowed publication indices, stale request/table/storage refusal, defaultOFF,
unknown geometry refusal, complete inverse and unchanged algorithm/oracle bytes.
No test fabricates a numerical PASS or a native allocation receipt.

The production override control executes the actual install_methods AST,
the actual rendered service_bridge._fa and the actual ServiceFiaBoundary
constructor with explicitly synthetic tensor objects and live-type predicates.
It proves trial geometry propagation and missing/wrong-source rejection for
2048 and3070, plus the original131 route without new geometry. It stops before
the native delegate; no tensor mathematics or NPU behavior is inferred.

For the next legitimate native2k NPU observation, the existing original
after_prefill callback must reach the new bind_all hook with actual returned
2048 input/positions and native metadata, then the existing bounded
fa_prefill131r10.capture should save its full integer operands. Inspect all4 ranks
and16 FA layers: ratio/physical size, allocated physical IDs and expanded kernel
table, cache shape/dtype/alias, complete slot destinations and request epoch.
Do not enter candidate staging unless the live registration and its capacity
checks pass. If native allocation is insufficient or differs, stop and preserve
the actual metadata; do not manufacture24/25 pages or silently permit growth.

Read-only preparation checks (default without arguments is OFF):
python3 -I -B render_geometry.py --check
python3 -I -B test_geometry.py --check
