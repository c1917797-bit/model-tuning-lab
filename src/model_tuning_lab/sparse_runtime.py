"""Opt-in experimental adapter. Not automatically loaded or model-validated.

Install in the engine process before scheduler creation, with the resolved
scheduler class and SHA256-pinned source paths. Native workers still execute
state copies; this adapter does not claim to have instrumented those copies.
"""
import hashlib
import inspect
from pathlib import Path

from .sparse_checkpoint_plan import publication_mask, split_at_checkpoint


def install(scheduler_class, mamba_class, positions, block_size, source_hashes, emit):
    """Install a frozen, block-aligned plan; return a process-local rollback.

    source_hashes maps exact imported file paths to verified SHA256 digests.
    Caller must separately pin image, model, histogram and checkpoint budget.
    Native eviction/admission/refcounts and same-step readiness remain intact.
    """
    positions = tuple(positions)
    if (type(block_size) is not int or block_size <= 0 or
            any(type(p) is not int or p <= 0 or p % block_size for p in positions) or
            list(positions) != sorted(set(positions))):
        raise ValueError("plan must contain sorted unique positive block boundaries")
    cache_base = next(cls for cls in mamba_class.__mro__[1:]
                      if "reachable_block_mask" in cls.__dict__ and "cache_blocks" in cls.__dict__)
    for cls in (scheduler_class, mamba_class, cache_base,
                scheduler_class._mamba_block_aligned_split):
        path = inspect.getsourcefile(cls)
        if not path or path not in source_hashes:
            raise ValueError("missing imported source fingerprint: " + str(path))
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != source_hashes[path]:
            raise ValueError("imported source fingerprint mismatch")
    if getattr(mamba_class, "_sparse_plan_installed", False):
        raise RuntimeError("sparse plan already installed")
    names = ("_mamba_block_aligned_split", "cache_blocks", "reachable_block_mask")
    owners = (scheduler_class, mamba_class, mamba_class)
    saved = [(cls, name, cls.__dict__.get(name)) for cls, name in zip(owners, names)]
    native_split = scheduler_class._mamba_block_aligned_split
    base_cache = cache_base.cache_blocks

    def split(self, request, num_new_tokens, num_new_local_computed_tokens=0,
              num_external_computed_tokens=0):
        if self.cache_config.block_size != block_size or self.use_eagle:
            raise RuntimeError("unsupported block size or speculative execution")
        native = native_split(self, request, num_new_tokens,
                              num_new_local_computed_tokens, num_external_computed_tokens)
        computed = (request.num_computed_tokens + num_new_local_computed_tokens
                    + num_external_computed_tokens)
        result = split_at_checkpoint(positions, computed, native, request.num_prompt_tokens)
        if result != native:
            emit("checkpoint_split", request_id=request.request_id,
                 position=computed + result, native_end=computed + native)
        return result

    def mask(cls, start_block, end_block, alignment_tokens, kv_cache_spec,
             use_eagle, retention_interval=None, num_prompt_tokens=None):
        if kv_cache_spec.block_size != block_size or use_eagle:
            raise RuntimeError("unsupported cache identity")
        return publication_mask(positions, start_block, end_block, block_size)

    def cache(self, request, num_tokens, retention_interval=None):
        if self.mamba_cache_mode != "align" or self.num_speculative_blocks:
            raise RuntimeError("only native align / MTP-off is supported")
        before = self.num_cached_block.get(request.request_id, 0)
        base_cache(self, request, num_tokens, retention_interval=retention_interval)
        after = self.num_cached_block.get(request.request_id, 0)
        for index in range(before, after):
            block = self.req_to_blocks[request.request_id][index]
            if not block.is_null and block.block_hash is not None:
                self.cached_blocks_this_step.add(block.block_hash)
                emit("checkpoint_published", request_id=request.request_id,
                     position=(index + 1) * block_size, block_id=block.block_id)

    scheduler_class._mamba_block_aligned_split = split
    mamba_class.reachable_block_mask = classmethod(mask)
    mamba_class.cache_blocks = cache
    mamba_class._sparse_plan_installed = True

    def rollback():
        for cls, name, descriptor in saved:
            if descriptor is None:
                delattr(cls, name)
            else:
                setattr(cls, name, descriptor)
        delattr(mamba_class, "_sparse_plan_installed")

    return rollback
