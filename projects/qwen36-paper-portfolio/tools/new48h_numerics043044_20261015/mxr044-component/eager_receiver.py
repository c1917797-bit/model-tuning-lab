"""Independent, default-OFF eager seam; no model/performance admission.

Caller must verify actual pinned solve signature, chunk scope, component receipt,
Event receipt, full-GDN/state/length qualifications and source/libs before binding.
The metadata certificate must originate from the validated scheduler/chunk input,
not a candidate's own output. Missing certificates take the real native path.
"""
import inspect
def make_receiver(native_solve, torch, solver_for_device, pool_for_device,
                  backend_for_device, in_original_gdn_scope, metadata_certificate,
                  graph_query, enabled=False):
    signature=inspect.signature(native_solve)
    counts={'candidate':0,'native':0}
    def fallback(args,kwargs):
        counts['native']+=1
        return native_solve(*args,**kwargs)
    def solve(*args,**kwargs):
        if not enabled or not in_original_gdn_scope() or graph_query():
            return fallback(args,kwargs)
        bound=signature.bind(*args,**kwargs);bound.apply_defaults();x=bound.arguments
        A=x['A'];cu=x.get('cu_seqlens');indices=x.get('chunk_indices_bt');dtype=x.get('output_dtype')
        if (A.device.type!='npu' or A.dtype!=torch.float32 or A.ndim!=4
            or A.shape[0]!=1 or tuple(A.shape[2:])!=(12,64) or not A.is_contiguous()
            or dtype != torch.bfloat16 or cu is None or indices is None):
            return fallback(args,kwargs)
        # This callback supplies prevalidated CPU-known geometry plus immutable
        # tensor/storage identities. No .cpu/.item, per-call finite scan or new
        # scheduler assumption is hidden in the timed solve.
        proof=metadata_certificate(A,cu,indices,dtype)
        if proof is None:return fallback(args,kwargs)
        if (cu.dtype not in (torch.int32,torch.int64) or cu.device!=A.device or not cu.is_contiguous()
            or indices.device!=A.device or not indices.is_contiguous()
            or proof.get('validated_length')!=A.shape[1]
            or proof.get('chunks')!=indices.shape[0]
            or proof.get('cu_pointer')!=cu.data_ptr()
            or proof.get('index_pointer')!=indices.data_ptr()
            or proof.get('qualified_length')!=A.shape[1]):
            return fallback(args,kwargs)
        device=str(A.device);solver=solver_for_device(device)
        pool=pool_for_device(device)
        bytes_required=A.numel()*8+cu.numel()*cu.element_size()+solver.minus_identity.numel()*solver.minus_identity.element_size()
        if bytes_required>pool.max_bytes:return fallback(args,kwargs)
        from block_refine import eager
        cu32=cu if cu.dtype==torch.int32 else cu.to(torch.int32)
        out=eager(solver,A,cu32,int(indices.shape[0]),dtype,pool,backend_for_device(device),proof['host_boundaries'])
        counts['candidate']+=1
        return out
    return solve,counts
