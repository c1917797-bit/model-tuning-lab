# Build-v2 source repair — preserved failures and later build-v3

The first real build in the immutable v0.23/CANN9.1 image failed at the ASC
wrapper: a braced initializer list mixed const input tensor pointers and a
mutable local tiling pointer. Compiler phase1 exited2. Preserve
/cache/cch/qwen36-damp-20261006/production-integer-compaction-build-v1,
including source receipt, phase0/1 logs, inspect records and failed receipt.
This is a compile-time implementation failure, not paper no-go or NPU evidence.

The new wrapper uses an explicitly typed const Tensor-pointer array for the
same output-disjointness checks. No check was removed.

Separately, MAIN read the actual CANN9.1 SDK snapshot from that same image:

- include/adv_api/pad/broadcast.h SHA
  ac4b048ba75b1c31e965db2a169ec6b75c1586310abde929ae6da758a12d24fd;
- broadcast_common_impl.h SHA
  9647011f4ed228acc22b07dde321247271a24e3f88688e965c0ba4aee603acb8;
- broadcast_v220_impl.h SHA
  37b17be5a6023ad3e5bccf11c5b6b30159bc3d9472ec41e8763c94c0fa977cc8.

The old four-argument API implicitly obtains LCM workspace. Its allocation
capacity/address was not proven. The public five-argument API instead receives
scratchB_ reinterpreted as bytes. That existing region has8192B at work offset
71680, separate from broad_ and delta_. Its LoadState conversion has completed
before UpdateReadout; PackStore initializes its next use after UpdateReadout's
final vector barrier. For the actual2201 [32,1] to [32,128] FP32 path, the SDK
uses at most1024B temporary storage;8192B is sufficient without new explicitUB.

No recurrence, reduction, scale, quantizer, gate or precision policy changes.
The source contract permits exactly this workspace substitution and still
requires every other UpdateReadout byte plus ten other native method bodies
to match the frozen source. ExplicitUB remains141312B. This removes this
particular implicit broadcast allocation; it does NOT prove compiler stack,
TPipe hardware allocation, numerical correctness, graph support or throughput.
Original v4, goldens, helpers, collectors and failed build artifacts stay intact.

Use a new non-overwriting build-v2 output/container. Hash all9 compilation
dependencies before/after. A successful build must still pass actual defined
symbol, load/Meta, independent certificate/compaction, savedstep45,160step,
generalSR and real service lifecycle gates before E2E admission.

Later actual history: build-v2's harness could not access the preserved SDK
snapshot because its exact directory was not mounted; it failed before any
compiler command. Keep that running-initialized receipt/raw failure unchanged.
MAIN added only that read-only snapshot mount to fresh build-v3, without
changing the nine compilation sources. MA03ac completed0, exported its actual
defined T launcher, and produced SOad6d0106...c92c8b. Actual no-device Meta and
saved-step45 NPU repair subsequently passed. ACTUAL_GATES.md gives full
identities. None establishes final E2E throughput or task accuracy.
