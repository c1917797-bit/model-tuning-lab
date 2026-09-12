"""Pinned-image native cache metadata test; no NPU tensors or model proof."""
import json
from types import SimpleNamespace as NS
import torch
from vllm.v1.core.block_pool import BlockPool
from vllm_ascend.patch.platform.patch_mamba_manager import AscendMambaManager as MambaManager
from vllm.v1.core.sched.async_scheduler import AsyncScheduler
from vllm.v1.kv_cache_interface import MambaSpec
from model_tuning_lab.sparse_runtime import install

root = "/vllm-workspace/vllm/vllm/v1/core/"
hashes = {
    "/vllm-workspace/vllm-ascend/vllm_ascend/patch/platform/patch_mamba_manager.py": "f39b28a75509ff5b8617104a00c73e6bd21b8b7acd43f81b50c57ea7c474815e",
    root + "sched/async_scheduler.py": "0022e12f356fd46406f6e6d3c82755daf7287ca2d86e2000c27b05bb8d9621cc",
    root + "sched/scheduler.py": "9ae1491f57a6294e32416b93ef2ea68107fa0d65c3a4d7f745f1261012f735e9",
    root + "single_type_kv_cache_manager.py": "dc425e1e87b6157f3e5c46be2bfee54076ccb020b86c5a8aaa3d9901c75e46ef",
}
events = []
undo = install(AsyncScheduler, MambaManager, [1536, 4608], 1536, hashes,
               lambda kind, **data: events.append(dict(kind=kind, **data)))
pool = BlockPool(16, True, 1536)
spec = MambaSpec(block_size=1536, shapes=((1,),), dtypes=(torch.bfloat16,),
                 mamba_cache_mode="align")
manager = MambaManager(spec, pool, enable_caching=True, kv_cache_group_id=0,
                       scheduler_block_size=1536)
request = NS(request_id="test", num_prompt_tokens=5000,
             block_hashes=[bytes([i]) * 32 for i in range(1, 4)],
             num_computed_tokens=0, num_tokens=5000)
engine = object.__new__(AsyncScheduler)
engine.cache_config = NS(block_size=1536)
engine.use_eagle = False
assert engine._mamba_block_aligned_split(request, 4608) == 1536
manager.req_to_blocks["test"] = pool.get_new_blocks(3)
manager.cache_blocks(request, 4608)
assert pool.get_cached_block(request.block_hashes[0], [0]) is not None
assert pool.get_cached_block(request.block_hashes[1], [0]) is None
assert pool.get_cached_block(request.block_hashes[2], [0]) is not None
hit = manager.find_longest_cache_hit(request.block_hashes, 3072, [0], pool,
                                      spec, alignment_tokens=1536, drop_eagle_block=False)
assert len(hit[0]) == 1
assert manager.get_num_blocks_to_allocate("other", 2000, hit[0], 1536, 2000) == 17
manager.new_step_starts()
manager.free("test")
assert pool.get_cached_block(request.block_hashes[0], [0]) is not None
assert pool.get_num_free_blocks() == 15
undo()
print(json.dumps({"passed": True, "scope": "native metadata only; no model tensors",
                  "events": events}, sort_keys=True))
