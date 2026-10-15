"""Bounded per-hook metadata cache, using unchanged official builder."""
from types import SimpleNamespace
import torch

class PackedMetadataCache:
    def __init__(self,builder,*,capacity=8):
        if not callable(builder) or type(capacity) is not int or not 1<=capacity<=32:
            raise ValueError("bounded source-verified metadata builder required")
        self.builder=builder;self.capacity=capacity;self.entries={}

    def get(self,starts,*,total_value_heads,tp_size,device):
        starts=tuple(starts)
        if not 2<=len(starts)<=65 or starts[0]!=0 or any(type(x)is not int for x in starts):
            raise ValueError("bounded integer window starts required")
        if any(a>=b for a,b in zip(starts,starts[1:])) or starts[-1]>40960:
            raise ValueError("positive windows within model budget required")
        if any(type(x)is not int or x<1 for x in (total_value_heads,tp_size)) or total_value_heads%tp_size:
            raise ValueError("valid TP/head geometry required")
        key=(starts,total_value_heads,tp_size,str(device))
        if key not in self.entries:
            config=SimpleNamespace(
                model_config=SimpleNamespace(hf_text_config=SimpleNamespace(
                    linear_num_value_heads=total_value_heads)),
                parallel_config=SimpleNamespace(tensor_parallel_size=tp_size))
            meta=self.builder(SimpleNamespace(vllm_config=config),
                              torch.tensor(starts,dtype=torch.int32),device)
            if tuple(meta.cu_seqlens_host)!=starts or meta.chunk_indices_chunk64_host is None:
                raise ValueError("official packed metadata coverage missing")
            if len(self.entries)>=self.capacity:self.entries.pop(next(iter(self.entries)))
            self.entries[key]=meta
        return self.entries[key]

    def clear(self):self.entries.clear()
