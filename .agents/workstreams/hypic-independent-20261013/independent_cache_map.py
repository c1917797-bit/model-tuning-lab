"""Read-only per-request KV slot association. Never grants write ownership."""
from dataclasses import dataclass
@dataclass(frozen=True)
class CacheSlice:
    request_id: str
    rank: int
    step: int
    group: int
    row: int
    block_size: int
    block_ids: tuple
    slots: tuple

def freeze_cache_slices(requests, tables, live_slots, *, block_sizes, row_counts,
                        cp_world_sizes):
    """Compare CPU table-derived positions with actual device slot mapping.
    CP partitioning is unsupported; reject rather than invent local ownership.
    Shared prefix blocks may legitimately alias: this is observation only.
    """
    requests=tuple(requests)
    if not (len(tables)==len(live_slots)==len(block_sizes)==len(row_counts)==len(cp_world_sizes)):
        raise ValueError("cache group coverage mismatch")
    result=[]
    for group,(table,actual,size,counts,cp) in enumerate(zip(
            tables,live_slots,block_sizes,row_counts,cp_world_sizes)):
        if cp!=1 or size<=0:
            raise ValueError("unsupported CP or block size")
        table=tuple(tuple(int(v) for v in row) for row in table)
        actual=tuple(int(v) for v in actual)
        counts=tuple(int(v) for v in counts)
        for req in requests:
            if req.row>=len(table) or req.row>=len(counts):
                raise ValueError("cache row missing")
            count=counts[req.row]
            if count<0 or count>len(table[req.row]):
                raise ValueError("cache block count invalid")
            ids=table[req.row][:count]
            if any(v<0 for v in ids):
                raise ValueError("negative allocated block")
            expected=[]
            for position in range(req.computed_tokens,
                                  req.computed_tokens+req.scheduled_tokens):
                index,offset=divmod(position,size)
                if index>=count:
                    raise ValueError("scheduled position beyond allocated blocks")
                expected.append(ids[index]*size+offset)
            observed=actual[req.token_start:req.token_end]
            if len(observed)!=req.scheduled_tokens or tuple(expected)!=observed:
                raise ValueError("device slot mapping disagrees with request/table")
            result.append(CacheSlice(req.request_id,req.rank,req.step,group,
                                     req.row,size,ids,observed))
    return tuple(result)
