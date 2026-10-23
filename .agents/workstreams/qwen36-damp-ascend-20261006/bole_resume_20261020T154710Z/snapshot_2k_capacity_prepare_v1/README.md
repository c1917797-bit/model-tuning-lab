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
Seven finite controls cover original131 AST/result/error equivalence,
L2048/L3070 native24/private25, insufficient count/unknown geometry, batch and
storage/request lifetime refusal, independent private requirement, real
_snap-to-capacity ABI, and complete two-file inverse.

## Integration remains pending

Apply geometry then this capacity delta, then the separate native input ABI
delta; the snapshot seam is independent of its after_prefill edits. The old
geometry renderer still passes registry length=131 next to native_geometry and
the rest of the131 input/GDN/source contracts remain. Fixing _snap alone does
NOT make whole2k source ready. The native input author owns that callback/owner/
registry composition; this scope does not relax those gates or modify numeric
sources. Actual live native prefill, full source/review/authority, independent
numerical checks and measured joint raw/wire/checkpoint budget remain required.

Default commands do not execute a preparation check. Read-only checks:
python3 -I -B render_capacity.py --check
python3 -I -B test_capacity.py --check
