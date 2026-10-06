"""CPU-only exact byte-footprint contracts. No serving/NPU success is issued."""
from dataclasses import dataclass
from math import prod

class Pending(ValueError):
    """Required actual native evidence is absent or unsupported."""

def require(ok, message):
    if not ok:
        raise Pending(message)

def integer(value):
    return type(value) is int

def ids(values):
    require(isinstance(values, (tuple, list)) and all(integer(x) and x >= 0 for x in values)
            and len(set(values)) == len(values), "exact unique nonnegative block IDs required")
    return tuple(values)

@dataclass(frozen=True)
class View:
    layer: str
    region: str
    kind: str
    group: int
    storage: int
    storage_bytes: int
    offset: int
    shape: tuple
    strides: tuple
    item_bytes: int
    dtype: str
    device: str

    def validate(self):
        require(isinstance(self.layer, str) and self.layer and self.region and
                self.kind in ("fa", "gdn") and integer(self.group) and self.group >= 0,
                "layer/group/region identity missing")
        require(all(integer(x) for x in (self.storage, self.storage_bytes, self.offset, self.item_bytes))
                and self.storage > 0 and self.storage_bytes > 0 and self.offset >= 0 and self.item_bytes > 0,
                "actual storage geometry missing")
        require(len(self.shape) >= 2 and len(self.shape) == len(self.strides)
                and all(integer(x) and x > 0 for x in self.shape + self.strides),
                "positive typed block geometry required")
        expected = 1
        for i in range(len(self.shape)-1, 0, -1):
            require(self.strides[i] == expected, "noncontiguous inner cache region")
            expected *= self.shape[i]
        require(self.strides[0]*self.item_bytes >= self.width, "overlapping cache blocks")
        require(self.offset+(self.shape[0]-1)*self.pitch+self.width <= self.storage_bytes,
                "typed region leaves actual storage")
        return self

    @property
    def pitch(self):
        return self.strides[0]*self.item_bytes

    @property
    def width(self):
        return prod(self.shape[1:])*self.item_bytes

    def blocks(self, block_ids, owner, write):
        self.validate()
        require(type(write) is bool and isinstance(owner, str) and owner, "access identity missing")
        result = []
        for block in ids(block_ids):
            require(block < self.shape[0], "block leaves actual typed cache")
            begin = self.storage+self.offset+block*self.pitch
            result.append(Span(begin, begin+self.width, owner, write, self.kind))
        return tuple(result)

@dataclass(frozen=True)
class Span:
    begin: int
    end: int
    owner: str
    write: bool
    kind: str

def check_spans(spans):
    """Absolute addresses catch aliased storages, not just equal data_ptr/slot IDs."""
    active = []
    for cur in sorted(spans, key=lambda s: (s.begin, s.end, s.owner)):
        require(all(integer(x) for x in (cur.begin, cur.end)) and 0 < cur.begin < cur.end
                and cur.owner and type(cur.write) is bool, "invalid byte footprint")
        active = [s for s in active if s.end > cur.begin]
        require(all(s.owner == cur.owner or not (s.write or cur.write) for s in active),
                "cross-owner live byte read/write alias")
        active.append(cur)
    return True

def physical_to_logical(block_ids, ratio):
    require(integer(ratio) and ratio >= 1, "invalid physical/kernel ratio")
    return tuple(p*ratio+i for p in ids(block_ids) for i in range(ratio))

def fa_blocks(block_ids, block_size, computed, query):
    require(all(integer(x) for x in (block_size, computed, query))
            and block_size > 0 and computed >= 0 and query > 0, "invalid native FA token range")
    blocks = ids(block_ids)
    needed = (computed+query+block_size-1)//block_size
    require(needed <= len(blocks), "insufficient real FA blocks")
    read = blocks[:needed]
    write = tuple(dict.fromkeys(blocks[t//block_size] for t in range(computed, computed+query)))
    slots = tuple(blocks[t//block_size]*block_size+t%block_size
                  for t in range(computed, computed+query))
    return read, write, slots

def zero_spans(segments, page_bytes, block_ids):
    require(integer(page_bytes) and page_bytes > 0 and page_bytes % 4 == 0,
            "actual int32 zero page width missing")
    result = []
    for view, address in segments:
        require(isinstance(view, View) and view.kind == "fa" and integer(address)
                and address == view.storage+view.offset, "cold native zero segment drift")
        for block in ids(block_ids):
            begin = address+block*page_bytes
            require(view.storage <= begin and begin+page_bytes <= view.storage+view.storage_bytes,
                    "zero writer leaves actual raw storage")
            result.append(Span(begin, begin+page_bytes, "zero:"+view.layer+":"+view.region, True, "zero"))
    return tuple(result)

def prompt_only(request):
    require(getattr(request, "prompt_embeds", None) is None and not getattr(request, "mm_features", None),
            "unverified multimodal/embedding request")
    mask = getattr(request, "prompt_is_token_ids", None)
    tokens = getattr(request, "prompt_token_ids", None)
    require(isinstance(tokens, list) and tokens and all(integer(x) and x >= 0 for x in tokens),
            "native token-only prompt required")
    require(mask is None or (isinstance(mask, list) and len(mask) == len(tokens)
                            and all(type(x) is bool and x for x in mask)),
            "invalid native prompt_is_token_ids mask")
