"""CPU-only actual frame partition; no scheduling, tensor math or admission.
The original frame stays whole. Indices are native input_batch/query_start_loc
indices, never compact-slot indices or assumed decode-prefix offsets.
"""
def need(value,message):
    if not value:raise ValueError(message)

def partition(frame,prompts,frame_valid):
    frame_valid(frame)
    need(type(prompts)is dict and set(frame["req_ids"])<=set(prompts),
         "actual immutable request prompt lengths")
    rows=[]
    for i,rid in enumerate(frame["req_ids"]):
        prompt=prompts[rid];c=frame["computed_tokens"][i];n=frame["scheduled_counts"][i]
        need(type(prompt)is int and 0<prompt<=32768 and c+n<=prompt+1024
             and ((c<prompt and c+n<=prompt)or(c>=prompt and n==1)),
             "no prefill boundary crossing, speculation or over-cap append")
        rows.append(dict(request_id=rid,batch_index=i,start=frame["query_start_loc"][i],
                         stop=frame["query_start_loc"][i+1],computed=c,scheduled=n,
                         prompt=prompt,kind="prefill"if c<prompt else"decode",
                         complete_prefill=c<prompt and c+n==prompt))
    prefill=tuple(row for row in rows if row["kind"]=="prefill")
    decode=tuple(row for row in rows if row["kind"]=="decode")
    kind="mixed"if prefill and decode else("prefill"if prefill else"decode")
    need(frame["kind"]==kind,"whole Book result matches independently derived row kinds")
    return dict(kind=kind,rows=tuple(rows),prefill=prefill,decode=decode,
                total_tokens=frame["total_tokens"])

def packed_inputs(torch,query,key,value,plan):
    """Only selected real decode tokens, in native request order.
    cat is intentionally charged NPU staging, not host D2H. Pure decode preserves
    the exact original contiguous call inputs; no per-token host tensor indexing.
    """
    total=plan["total_tokens"];rows=plan["decode"]
    need(rows and all(r["stop"]-r["start"]==1 for r in rows),
         "one actual query token for each selected decode owner")
    q=query.reshape(total,6,256);k=key.reshape(total,256);v=value.reshape(total,256)
    if plan["kind"]=="decode":
        return q.contiguous(),k.contiguous(),v.contiguous()
    return tuple(torch.cat([tensor[row["start"]:row["stop"]]for row in rows],0).contiguous()
                 for tensor in(q,k,v))

def merge_decode(output,packed,plan):
    """Exact selected token writeback, never touch any prefill output row."""
    rows=plan["decode"]
    need(tuple(packed.shape)==(len(rows),6,256)
         and tuple(output.shape)==(plan["total_tokens"],1536),
         "whole selected packed and native output sizes")
    for i,row in enumerate(rows):
        output[row["start"]:row["stop"]].copy_(packed[i:i+1].reshape(1,1536))
    return output


def native_prefills(torch,original,context,layer_name,metadata,query,key,value,plan,describe,observer=None):
    """Original public Attention.forward, once per prefill owner in mixed frame.
    Both metadata and slot_mapping are scoped to this exact layer and restored
    even if original native code fails. No native call/cache write for decode.
    """
    from dataclasses import replace
    need(plan["kind"]=="mixed" and type(context.attn_metadata)is dict
         and context.attn_metadata[layer_name]is metadata
         and type(context.slot_mapping)is dict and layer_name in context.slot_mapping,
         "exact eager whole-frame metadata and current-layer slot binding")
    need(metadata.prefill is None and metadata.decode_meta is None
         and metadata.kvcomp_metadata is None and metadata.reshape_cache_event is None
         and metadata.causal is True and metadata.model_runner_type!="pooling",
         "regular non-CP/noncompress/nontransfer causal native subset")
    need(metadata.num_actual_tokens==plan["total_tokens"]
         and metadata.actual_seq_lengths_q==[row["stop"]for row in plan["rows"]]
         and metadata.seq_lens_list==[row["computed"]+row["scheduled"]for row in plan["rows"]],
         "whole actual builder query/KV partition before any subset")
    need(metadata.seq_lens.device.type=="cpu" and metadata.seq_lens_cpu.device.type=="cpu",
         "source80005a builder keeps exact sequence lengths CPU; never subset D2H")
    original_slots=context.slot_mapping[layer_name]
    need(original_slots is not None and callable(describe)
         and describe(original_slots)==describe(metadata.slot_mapping),
         "whole original slot mapping is the exact native tensor alias")
    total=plan["total_tokens"]
    out=torch.empty((total,1536),dtype=query.dtype,device=query.device)
    q=query.reshape(total,6,256);k=key.reshape(total,1,256);v=value.reshape(total,1,256)
    for row in plan["prefill"]:
        i,start,stop=row["batch_index"],row["start"],row["stop"];n=stop-start
        need(n==row["scheduled"] and n>0,"source-qualified actual prefill token span")
        sub=replace(metadata,
            attn_state=(type(metadata.attn_state).PrefillNoCache if row["computed"]==0
                        else type(metadata.attn_state).PrefillCacheHit),
            num_actual_tokens=n,num_actual_tokens_pcp_padded=0,num_decode_tokens=0,
            num_prefills=1,num_decodes=0,seq_lens=metadata.seq_lens[i:i+1],
            seq_lens_cpu=metadata.seq_lens_cpu[i:i+1],seq_lens_list=[row["computed"]+n],
            actual_seq_lengths_q=[n],query_start_loc=metadata.query_start_loc[i:i+2]-start,
            max_query_len=n,block_tables=metadata.block_tables[i:i+1],
            slot_mapping=metadata.slot_mapping[start:stop])
        context.attn_metadata[layer_name]=sub
        context.slot_mapping[layer_name]=original_slots[start:stop]
        try:
            if observer is not None:observer.native_input(row,q[start:stop],k[start:stop],v[start:stop])
            piece=original(q[start:stop],k[start:stop],v[start:stop],output_shape=(n,1536))
            need(tuple(piece.shape)==(n,1536),"whole actual native prefill output")
            if observer is not None:observer.native_output(row,piece)
            out[start:stop].copy_(piece)
            del piece
        finally:
            context.attn_metadata[layer_name]=metadata
            context.slot_mapping[layer_name]=original_slots
    return out

