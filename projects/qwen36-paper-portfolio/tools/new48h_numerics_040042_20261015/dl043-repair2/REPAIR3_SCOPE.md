# repair3: exact installed Ascend copy bootstrap, not DeltaLog math

Actual repair2 aborted compiling generic vLLM batch_memcpy_kernel with pointer
casts inside the loop. MAIN found complete B1/B16 mixed16 and4 deadflush raw,
but zero copy raw. This is bootstrap/compiler failure, NOT numerical no-go.
The normal actual worker __init__ imports patch_mamba_utils (3949B/
11002e315e93b2534d1fa4e859cf5bdcfbb22caaae370a26f29fbf586144cfb6).
The fixture had omitted it and retained the generic descriptor kernel.

copy_bootstrap source-loads the COMPLETE exact installed official patch file by
path, without importing the full worker parent package. It records official
preprocess/postprocess assignments too; these are not exercised in this fixture.
On910B, actual patch assigns mu.batch_memcpy and batch_memcpy_kernel; do_copy
remains original and dynamically resolves the new batch global. New checks prove
all callable identities and actual source paths before DeltaLog captures it.
The official Ascend kernel moves uint8 pointer casts outside the loop and uses
BLOCK_SIZE8192. Neither kernel source nor DeltaLog arithmetic is rewritten.

Host readset includes byte-exact dependencies/native_patch_mamba_utils.py and
native_ascend_batch_memcpy.py snapshots; /vllm-workspace paths are verified ONLY
inside the actual image, not presented as host-mountable Ref3s. Actual snapshot
SHA equals actual loaded source SHA. No fake sys.modules or invented operator.

Same-image Devices[] CPU preflight now source-loads the actual patch in an
isolated subprocess before granting CPU stage PASS. If it imports/device-probes
unsafely without devices it FAILS and requires real diagnosis; no silent skip.
The independent CPU oracle parent does not import torch_npu.

Durable stage markers use exclusive file creation/write/fsync/close, so mixed,
copy and bootstrap before/after stages survive SIGABRT. These are diagnostic
only, not timing measurements or numeric PASS.

All old candidate/kernel/math/source pins, original input seed/B1+B16 steps,
16smoke-before160, original FP64/output/state/guard/aux/copy gates, resources,
hostCPUassignment, singleton5, fixed cutoff and stop-retain owner are unchanged.
New identity/root/output only. Old repair2 and failed raw remain unchanged.
Full-model/PDC/graph/performance qualification remains FALSE.
