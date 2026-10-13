"""Independent ND paged KV slot writer; scheduler lease attachment pending."""
import torch
def install_private_kv(kv_cache,private_keys,private_values,slots,owned_slots):
    if kv_cache.ndim!=5 or kv_cache.shape[0]!=2 or not kv_cache.is_contiguous():
        raise ValueError("only contiguous logical ND [2,B,S,H,D] supported")
    if kv_cache.device.type=='npu':
        import torch_npu
        if torch_npu.get_npu_format(kv_cache)!=2:raise ValueError("unsupported physical KV format")
    if private_keys.shape!=private_values.shape or private_keys.ndim!=3:
        raise ValueError("KV material shape mismatch")
    if private_keys.shape[1:]!=kv_cache.shape[3:] or len(slots)!=private_keys.shape[0]:
        raise ValueError("head/row coverage mismatch")
    limit=kv_cache.shape[1]*kv_cache.shape[2]
    if any(not isinstance(i,int) or i<0 or i>=limit or i not in owned_slots for i in slots):
        raise ValueError("invalid or unowned target slot")
    if len(set(slots))!=len(slots):raise ValueError("duplicate target slot")
    if private_keys.device!=kv_cache.device or private_values.device!=kv_cache.device:
        raise ValueError("material device mismatch")
    index=torch.tensor(slots,device=kv_cache.device,dtype=torch.int64)
    kv_cache[0].view(limit,*kv_cache.shape[3:]).index_copy_(0,index,private_keys.to(kv_cache.dtype))
    kv_cache[1].view(limit,*kv_cache.shape[3:]).index_copy_(0,index,private_values.to(kv_cache.dtype))
