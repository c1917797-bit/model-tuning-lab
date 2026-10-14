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

def install_private_kv_parts(key_cache,value_cache,private_keys,private_values,slots,owned_slots):
    """Write native separate paged cache tensors without stacking/copying caches."""
    if (key_cache.ndim!=4 or value_cache.shape!=key_cache.shape
            or not key_cache.is_contiguous() or not value_cache.is_contiguous()
            or key_cache.device!=value_cache.device or key_cache.dtype!=value_cache.dtype):
        raise ValueError('matching contiguous native paged K/V parts required')
    if key_cache.device.type=='npu':
        import torch_npu
        if any(torch_npu.get_npu_format(t)!=2 for t in (key_cache,value_cache)):
            raise ValueError('native KV parts require physical ND format')
    if (private_keys.ndim!=3 or private_keys.shape!=private_values.shape
            or private_keys.shape[1:]!=key_cache.shape[2:]
            or len(slots)!=private_keys.shape[0]):
        raise ValueError('private KV part row/head coverage mismatch')
    if private_keys.device!=key_cache.device or private_values.device!=key_cache.device:
        raise ValueError('private KV part device mismatch')
    limit=key_cache.shape[0]*key_cache.shape[1]
    if len(set(slots))!=len(slots) or any(type(x) is not int or not 0<=x<limit or x not in owned_slots for x in slots):
        raise ValueError('aliased, invalid or unleased KV part slot')
    index=torch.tensor(slots,dtype=torch.int64,device=key_cache.device)
    key_cache.view(limit,*key_cache.shape[2:]).index_copy_(0,index,private_keys.to(key_cache.dtype))
    value_cache.view(limit,*value_cache.shape[2:]).index_copy_(0,index,private_values.to(value_cache.dtype))
