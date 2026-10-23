"""Request-local metadata for the official paged PrefillCacheHit path.

All cached KV must be installed before this metadata is submitted. Construction
does not activate a hook or certify that installation has happened.
"""
from dataclasses import replace
import torch


def window_metadata(native, window, *, request_row, cache_hit_state,allow_mixed=False,
                    block_table_reader=None, request_identity=None):
    if (not native.causal or (not allow_mixed and (native.num_decodes or native.num_decode_tokens))
            or native.prefill is not None or native.decode_meta is not None
            or native.kvcomp_metadata is not None):
        raise ValueError("C2 window requires ordinary causal pure prefill")
    if allow_mixed and (native.num_decode_tokens!=native.num_decodes or
                        native.num_decodes<0 or native.num_prefills<1):
        raise ValueError('unsupported mixed decode/prefill metadata')
    if native.block_tables is None or not 0<=request_row<native.block_tables.shape[0]:
        raise ValueError("request block-table row missing")
    n=len(window.logical_positions)
    if n==0 or len(window.write_slots)!=n:
        raise ValueError("nonempty retained query/slot coverage required")
    if window.logical_positions!=tuple(range(window.kv_end-n,window.kv_end)):
        raise ValueError("query window is not right-aligned to logical KV endpoint")
    if block_table_reader is None:
        ids=tuple(int(x) for x in native.block_tables[request_row,:len(window.block_ids)].detach().cpu().tolist())
    else:
        if not callable(block_table_reader):
            raise ValueError("explicit C2 block-table reader required")
        ids=block_table_reader(native,request_row,len(window.block_ids),
                              request_identity=request_identity)
        if (not isinstance(ids,tuple) or len(ids)!=len(window.block_ids)
                or any(type(x) is not int for x in ids)):
            raise ValueError("complete integer block-table snapshot required")
    if ids!=window.block_ids:
        raise ValueError("live block table changed after cache binding")
    def tensor(values,template):
        if template is None:raise ValueError("native metadata tensor missing")
        return torch.tensor(values,dtype=template.dtype,device=template.device)
    # Row and counts are copied. The native object remains available to other
    # requests/layers; it is never temporarily overwritten in forward context.
    return replace(native,attn_state=cache_hit_state,
        num_actual_tokens_pcp_padded=n,num_actual_tokens=n,
        num_decode_tokens=0,num_prefills=1,num_decodes=0,
        seq_lens=tensor([window.kv_end],native.seq_lens),
        seq_lens_cpu=tensor([window.kv_end],native.seq_lens_cpu),
        seq_lens_list=[window.kv_end],actual_seq_lengths_q=[n],
        query_start_loc=tensor([0,n],native.query_start_loc),max_query_len=n,
        block_tables=native.block_tables[request_row:request_row+1].clone(),
        slot_mapping=tensor(window.write_slots,native.slot_mapping))
