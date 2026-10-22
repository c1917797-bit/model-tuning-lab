# Saved-input collective replay preparation

This is a default-OFF diagnostic worker for standard single-node four-rank torch.distributed HCCL SUM, using actual full saved BOLE projection partials. It does not run or accept BOLE, task accuracy, or performance. No NPU execution has been performed by this preparation.

MAIN owns source review, finite authorization, same-image preflight, physical NPU4–7 mapping, the global lease, summed host budget, timeout and cleanup. Workers cannot prove physical mapping from logical device environment alone; the manifest includes MAIN's immutable mapping evidence.

Input schema `bole.collective-replay-input/v1` has exactly these keys:

- `worker_ref`: Ref3 of this worker; `variant`: `default` or `deterministic_true`.
- `generation:1`, `iterations:8`, `shape:[131,5120]`, `dtype:"torch.bfloat16"`.
- `physical_to_logical:[[4,0],[5,1],[6,2],[7,3]]`, `mapping_evidence`: immutable Ref3 from MAIN.
- `source_ref`: original producer SOURCE_BOUND Ref3.
- `projection_records`: four actual generation-1 PROJECTION-INTERNAL Ref3 envelopes.
- `inputs`: object keys `"0"` through `"3"`, each exact complete pre_reduce raw Ref3 already joined by its original envelope.

All Ref3 objects contain only absolute path, byte count and whole SHA-256. The worker validates original rank/generation/source/raw hash/shape/dtype joins, every complete raw input, finite BF16 words, ordinary paths and unchanged original files. Input data are little-endian BF16.

The controller creates a fresh output root before torchrun. Each worker exclusively creates `rank-N`; every raw, iteration receipt and RESULT uses exclusive creation. A repeated rank refuses rather than overwriting evidence. Eight iterations reset the same NPU allocation from the original CPU bytes, synchronize and prove the entire NPU pre-image is bitwise the original, then call the actual standard `torch.distributed.all_reduce(SUM, async_op=False)`, synchronize, and retain complete post bytes. Rank0..3 and LOCAL_RANK must match; WORLD_SIZE and LOCAL_WORLD_SIZE must both equal4; rendezvous must be loopback. Input errors persist a first-error RESULT before Torch/NPU import where rank/output admission succeeds.

MAIN's two separate fresh-worker variants must use the same source and inputs: the default variant has HCCL_DETERMINISTIC absent, while the deterministic variant sets exactly `HCCL_DETERMINISTIC=true` before Python starts. Keep other whitelist flags equal. Do not change torch deterministic behavior in the worker. Getter values and the three named environment values are recorded in-process; no complete environment is exported.

Illustrative controller command shape only (not executed):

```text
<same pinned Python> -B -m torch.distributed.run --nproc_per_node=4 --master_addr=127.0.0.1 --master_port=<owned port> replay_collective.py --execute --manifest-ref '<complete manifest Ref3 JSON>' --output <fresh controller-created output root>
```

Logical ASCEND_RT_VISIBLE_DEVICES must be `0,1,2,3` inside MAIN's physical4–7-only container. Never use this command on an unqualified host namespace. No container creation or physical admission is included here.

Per variant post raw is exactly `4*8*131*5120*2 = 42,926,080` bytes, plus small receipts. Reserve at least64MiB output capacity per variant and retain originals. Worker tensors are small but the actual pinned runtime/process RSS and 180-second group init/collective timeout still need MAIN's summed admission and external deadline. A finally block destroys an initialized process group; external timeout handles a crashed peer.

The actual standard Python all_reduce source Ref and callable identity are recorded. /proc/self/maps is filtered only for libhccl/libtorch_npu; their on-disk paths are streamed into hashes. Missing/unreadable observations remain explicit. These observations do not prove mapped inode equivalence, the exact HCCL kernel, internal accumulator precision or reduction order.

MAIN's independent integer consumer can compare exact final BF16 sums and bounded possible BF16 intermediate trees. Per-coordinate tree membership does not establish a single tensor-wide tree; FP32/FP16 and chunked accumulation remain alternative models. Independent replay is causal diagnosis, not production native-AR or BOLE numerical qualification. A matched raw/native control remains necessary before interpreting candidate differences.

Device-free checks:

```text
python3 -B -m unittest discover -s <this directory> -p test_replay_collective.py -v
```

No same-image/NPU result is claimed until its actual receipts exist.

