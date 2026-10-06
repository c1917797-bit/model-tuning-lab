# Exact-image selected-prefill source preflight v1

Default OFF; import is stdlib-only. MAIN owns execution. No NPU kernel, Torch
operator, SO load, native context, algorithm call or serving authority is issued.
The synthetic stdlib positive uses explicitly substituted test source pins and
does not prove the immutable image or a loaded native callable.

## Actual failures retained

- Isolated MA0670 rejected a purported bad P1 indices fixture, but shape [1],
  stride [2] is legitimately contiguous. First test the exact image's CPU
  semantics: real P2 indices [2] stride2 is noncontiguous and has two legal slots.
  Keep all57 host rejection entries,134 packing cases and original thresholds.
- Native MA0674 stopped before math because inspect.getsourcefile(decorated
  chunk) observes Torch DisableContext._fn, not the underlying chunk source.
  Do not replace the source SHA or call the unwrapped function.

The original reports, .pt artifacts, terminal receipts, stopped containers and
Git source history are unchanged. The compiled selected wrapper hash is pinned;
this packet does not modify any previously executed gate or SO.

## Commands for MAIN, exact immutable image660ce23a...

Use /usr/local/python3.12.13/bin/python3 -B inside MAIN-owned NO-device image,
RO project and fresh writable output directory, TORCH_DEVICE_BACKEND_AUTOLOAD=0:

    python3 -B projects/damp-ascend/tools/selected_prefill_source_preflight_v1/preflight.py
    python3 -B projects/damp-ascend/tools/selected_prefill_source_preflight_v1/preflight.py --execute --mode fixture_cpu --out /stage-output/fixture.json
    python3 -B projects/damp-ascend/tools/selected_prefill_source_preflight_v1/preflight.py --execute --mode torch_wrapper --out /stage-output/torch-wrapper.json
    python3 -B projects/damp-ascend/tools/selected_prefill_source_preflight_v1/preflight.py --execute --mode native_callable --out /stage-output/native-callable.json

The latter canonical GDN/FLA import may query SoC with no devices. That is a
retained failed/deferred native-import boundary, never a mock architecture or
native-callable PASS. Fixture/Torch modes can finish separately. Native child
must still prove its own actual canonical callable after imports. No algorithm
is called in any mode, including the framework dummy callable, whose body
raises if accidentally invoked. Importing actual GDN may import torch_npu;
the report records this separately, not as mathematical NPU execution.

## Strict reusable proof

preflight.native_proof(torch,gdn,chunk,compiler,decorators,eval_frame,observation)
returns ORIGINAL decorated outer. Before assertion it records observed loaded
source paths, function ids, code/global/closure aliases and wrapper flags.
Source identities include actual Torch compiler/decorators/eval_frame (three
actual stopped-image byte copies), gdn and chunk. Loaded CodeTypes must equal
compile of pinned actual source with this interpreter's optimization setting;
outer code must be the canonical nested DisableContext.__call__ _fn and its
globals must be the same actual module dictionary. __wrapped__, original
backlink and closure fn must be the same single native inner; the context must
be exact DisableContext(callback=None,msg=None,wrapping=True). GDN and canonical
chunk share the exact outer object. No additional wrapper/cycle is admitted.
Source bytes are checked unchanged after proof.

This proof is not a complete Python-global/third-party closure security claim:
the immutable image/runtime gates and loaded SO identity remain independently
necessary. It gives no numeric, graph, allP, cache lifecycle,192plan, performance
or task quality acceptance. A framework-source/alias change fails closed.

## Software checks

    /usr/bin/python3 -B -m unittest discover -s projects/damp-ascend/tools/selected_prefill_source_preflight_v1 -p test_preflight.py -v

Tests are synthetic/stdlb-only. MAIN must separately execute exact-image CPU and
actual callable modes; no result is prewritten here. Output is fresh exclusive
JSON, with original exception/partial observations on failure. Since no dispatch
occurs this is not a numeric failure artifact or a pre-card durable state journal.

Initial host software exec0689 retained 12 passes/3 errors: its Python3.10 lacks
CodeType.co_qualname. The successor resolves the complete lexical CodeType path
on that host; target Python3.12 still uses exact co_qualname. It never falls back
to only a function name. This is a software compatibility finding, not Torch or
native algorithm evidence.
