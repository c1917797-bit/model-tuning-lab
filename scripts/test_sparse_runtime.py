"""Adapter contract tests with fake objects; no device activation claim."""
import hashlib
import sys
from pathlib import Path
from types import SimpleNamespace as NS
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from model_tuning_lab.sparse_runtime import install


class Scheduler:
    cache_config = NS(block_size=1536)
    use_eagle = False

    def _mamba_block_aligned_split(self, request, n, local=0, external=0):
        return n


class Base:
    @classmethod
    def reachable_block_mask(cls, **kwargs):
        return None

    def cache_blocks(self, request, num_tokens, retention_interval=None):
        count = num_tokens // 1536
        mask = self.reachable_block_mask(0, count, 1536, NS(block_size=1536), False)
        self.req_to_blocks[request.request_id] = [
            NS(is_null=False, block_hash=i if keep else None, block_id=i)
            for i, keep in enumerate(mask)]
        self.num_cached_block[request.request_id] = count


class Mamba(Base):
    mamba_cache_mode = "align"
    num_speculative_blocks = 0

    def cache_blocks(self, *args, **kwargs):
        raise AssertionError("native wrapper must be replaced")


request = NS(request_id="a", num_computed_tokens=0, num_prompt_tokens=5000)
events = []
path = str(Path(__file__).resolve())
hashes = {path: hashlib.sha256(Path(path).read_bytes()).hexdigest()}
original = Mamba.cache_blocks
undo = install(Scheduler, Mamba, [1536, 4608], 1536, hashes,
               lambda kind, **data: events.append((kind, data)))
assert Scheduler()._mamba_block_aligned_split(request, 4608) == 1536
m = Mamba()
m.num_cached_block, m.req_to_blocks, m.cached_blocks_this_step = {}, {}, set()
m.cache_blocks(request, 4608)
assert m.cached_blocks_this_step == {0, 2}
assert [e[1]["position"] for e in events if e[0] == "checkpoint_published"] == [1536, 4608]
undo()
assert Mamba.cache_blocks is original
assert "reachable_block_mask" not in Mamba.__dict__
assert Scheduler()._mamba_block_aligned_split(request, 4608) == 4608
print("PASS adapter split, sparse publication, readiness bookkeeping and rollback; fake objects only")
