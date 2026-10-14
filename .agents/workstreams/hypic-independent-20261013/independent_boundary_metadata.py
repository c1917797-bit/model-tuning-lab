"""Request-local official Ascend prebuilt metadata for live GDN windows."""
from types import SimpleNamespace
import torch

def boundary_builder_config(length,total_value_heads,tp_size):
    if any(type(x) is not int or x<1 for x in (length,total_value_heads,tp_size)):
        raise ValueError('positive integer boundary geometry required')
    if total_value_heads%tp_size:raise ValueError('nondivisible TP head geometry')
    config=SimpleNamespace(
        model_config=SimpleNamespace(hf_text_config=SimpleNamespace(linear_num_value_heads=total_value_heads)),
        parallel_config=SimpleNamespace(tensor_parallel_size=tp_size))
    return SimpleNamespace(vllm_config=config),torch.tensor([0,length],dtype=torch.int32)

def build_boundary_metadata(layer,length,device):
    from pathlib import Path
    import hashlib,inspect
    from vllm_ascend.ops.gdn_attn_builder import _build_non_spec_chunked_prefill_metadata
    fn=_build_non_spec_chunked_prefill_metadata
    if hashlib.sha256(Path(inspect.getfile(fn)).read_bytes()).hexdigest()!='42cc0284b57193112b8a8ad19704aa3401f02294f0c36333c307d748f462fe16':
        raise ValueError('official Ascend boundary metadata source drift')
    builder,starts=boundary_builder_config(length,layer.num_v_heads,layer.tp_size)
    meta=fn(builder,starts,device)
    if meta.cu_seqlens_host!=(0,length) or meta.chunk_indices_chunk64 is None:
        raise ValueError('boundary native chunk metadata coverage missing')
    return meta
