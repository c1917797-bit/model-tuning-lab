"""Explicit scheduler entry point for a bounded mechanism canary, not release."""
import json
import os
from pathlib import Path
from vllm.v1.core.sched.async_scheduler import AsyncScheduler
from vllm.v1.core.single_type_kv_cache_manager import MambaManager
from .sparse_checkpoint_plan import plan_checkpoints
from .sparse_runtime import install


class SparseCanaryScheduler(AsyncScheduler):
    def __init__(self, *args, **kwargs):
        # Synthetic predeclared training histogram, not measured future traffic.
        # One checkpoint at1536 deliberately differs from native final boundary.
        histogram = [0] * 3073
        histogram[1536] = 1
        positions = plan_checkpoints(histogram, 1536, 1)
        if positions != [1536]:
            raise RuntimeError("unexpected canary plan")
        root = "/vllm-workspace/vllm/vllm/v1/core/"
        hashes = {
            "/vllm-workspace/vllm-ascend/vllm_ascend/patch/platform/patch_mamba_manager.py": "f39b28a75509ff5b8617104a00c73e6bd21b8b7acd43f81b50c57ea7c474815e",
            root + "sched/async_scheduler.py": "0022e12f356fd46406f6e6d3c82755daf7287ca2d86e2000c27b05bb8d9621cc",
            root + "sched/scheduler.py": "9ae1491f57a6294e32416b93ef2ea68107fa0d65c3a4d7f745f1261012f735e9",
            root + "single_type_kv_cache_manager.py": "dc425e1e87b6157f3e5c46be2bfee54076ccb020b86c5a8aaa3d9901c75e46ef",
        }

        def emit(kind, **data):
            event = dict(kind=kind, pid=os.getpid(), **data)
            with Path("/output/sparse-events.jsonl").open("a") as stream:
                stream.write(json.dumps(event, sort_keys=True) + "\n")

        self._sparse_rollback = install(AsyncScheduler, MambaManager, positions,
                                        1536, hashes, emit)
        super().__init__(*args, **kwargs)
        if self.cache_config.block_size != 1536 or self.use_eagle:
            raise RuntimeError("unsupported canary runtime")
        emit("engine_constructed", positions=positions, budget=1,
             scheduler=type(self).__module__ + "." + type(self).__qualname__)
