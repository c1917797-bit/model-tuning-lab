# Native2k snapshot/publication capacity repair

Source preparation only. No authority, SOURCE_BOUND, Docker, NPU, native
allocation observation or numerical PASS is created. Frozen geometry/numeric
and old131 sources are not edited.

The actual service_runner._snap retains ALL native-owned FA pages and called
G2.capacity(length,len(pages)). The original function both rejected2k by its131
domain and required L+3 inside native capacity. That incorrectly charged the
third PRIVATE branch row to native publication at L3070:3073>24*128.

render_capacity.adapt changes exactly two source files. The original131
capacity function is retained as _capacity_131 with its complete AST, domain,
defaults and checks unchanged. The public capacity function delegates every
legacy value to it. The2k branch requires the already reviewed
fa_native_geometry.NativeGeometry, calls its real strong C1 request/table/cache
lifetime check, verifies the SAME output budget and EXACT allocated native count,
then separately checks:

- Native accepted-path publication ends at L+2, fitting the actual native table.
- Private three-node scratch ends at L+3 with ceil((L+3)/128) required pages.

At L3070 an actually bound24-page native allocation can therefore coexist with
25 PRIVATE required pages. The helper explicitly reports
private_scratch_allocation_proven=False: actual scratch tensor/operator checks
remain in the existing FIA/numerical path. It neither allocates nor asserts that
the required private scratch has already been executed.

The actual _snap call passes binding.get('native_geometry') before gathering
native pages. Unknown JSON/plan, changed request/slot/storage, other batch,
insufficient native capacity or wrong geometry/budget still refuses. No
capacity assertion is removed, no budget is increased and growth remains false.

## Limited software evidence

test_capacity executes the actual derived _snap AST and G2.capacity using
explicit INTERNAL synthetic metadata objects only. This is not a native
observation, real Torch tensor computation, same-image test or NPU numeric PASS.
Ten finite controls cover original131 AST/result/error equivalence,
L2048/L3070 native24/private25, insufficient count/unknown geometry, batch and
storage/request lifetime refusal, independent private requirement, real
_snap-to-capacity ABI, and complete two-file inverse.

## Explicit new2k metadata, not a mathematical permit

Only the derived g2_contract.scope prefix operand becomes2048. All other
scope fields,1024 output limit, original caps and _capacity_131 remain unchanged.
Frozen131 sources are not edited. service_runner worker BOOT, g2_stream_owner
host/worker/channel binding, g2_channel.contract and g2_consumer entry all use
the exact same source-owned G2.SCOPE. A mixed legacy131 channel or consumer
manifest is rejected. No new schema or caller-selected prefix switch is added.

The software scope control executes the actual channel contract only until
the original host-ownership verifier (a deliberate test stop, NOT acceptance),
and the actual consumer's first scope predicate. It does not create a host
proof, ACK, numerical result or usable channel.

## Integration remains pending

Apply geometry then this capacity delta, then the separate native input ABI
delta; the snapshot seam is independent of its after_prefill edits. That
separate callback delta changes registration/Owner/input ABI, not this one.
Fixing capacity and metadata does NOT make whole2k source ready:
g3_validate still has an explicit131 SCOPE/profile that a new whole-source
validator must handle through a complete source derivation/inverse.
The historical g2_state.open_rank and g2_numeric.consume_step also retain131;
they are not the current FAST sink's direct numerical route and their length
restrictions are not claimed to block that direct route.
The control actually executes the original open_rank first registration gate
and proves a2048 owner remains rejected; renaming metadata cannot qualify math.
Those legacy validators/consumers are NOT edited here. A reviewed whole2k
producer/validator must explicitly bind the actual sink to independent
fastpath_numeric_consumer.consume_frame with numeric_prefix_2k and native
prefill identity, prove that routing and
the complete source contract, rather than reuse historical math by label.
Actual live native prefill, full source/review/authority, independent numerical
checks and a measured complete joint raw/wire/decoded/checkpoint/failed-frame
budget remain required. The numeric2k runtime hard refusal is unchanged.

Default commands do not execute a preparation check. Read-only checks:
python3 -I -B render_capacity.py --check
python3 -I -B test_capacity.py --check
