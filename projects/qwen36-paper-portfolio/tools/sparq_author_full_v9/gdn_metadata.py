"""Source-bound native writer-domain reconstruction; no Torch at import.
Input is the complete actual metadata snapshot, not a virtual request ledger.
No speculative/context-parallel/cache-align branch is admitted by this packet.
"""
import common as c
def ints(x,name):
 c.require(type(x) is list and all(type(i) is int for i in x),name+" exact integer tensor values")
 return x
def segments(q,name):
 q=ints(q,name)
 c.require(len(q)>=2 and q[0]==0 and all(b>=a for a,b in zip(q,q[1:])),name+" complete nondecreasing offsets")
 return [b-a for a,b in zip(q,q[1:])]
def first_column(x,name):
 c.require(type(x) is list and x and all(type(r) is list and len(r)==1 for r in x),
  name+" actual mamba-cache-none single physical block column")
 return ints([r[0] for r in x],name)
def active(indices,lens,slots,name):
 c.require(len(indices)==len(lens),name+" exact writer row count")
 rows=[]
 for pos,(slot,n) in enumerate(zip(indices,lens)):
  c.require(type(slot) is int and type(n) is int and n>=0,name+" actual slots and positive segment lengths")
  if n:
   c.require(0<=slot<slots,name+" actual live native slot range")
   rows.append(dict(row=pos,slot=slot,query_tokens=n))
 c.require(len({r["slot"] for r in rows})==len(rows),name+" no two live requests share physical state")
 return rows
def plan(raw,conv_slots,recurrent_slots):
 c.require(raw["schema"]=="sparq.GDN-actual-metadata-snapshot/v1" and
  raw["spec_sequence_masks"] is None and raw["num_spec_decodes"]==0 and raw["num_spec_decode_tokens"]==0 and
  raw["mamba_cache_mode"]=="none" and raw["use_context_parallel"] is False,
  "actual original non-spec/no-CP/mamba-none branch")
 d,p=raw["num_decodes"],raw["num_prefills"]
 c.require(type(d) is int and type(p) is int and d>=0 and p>=0 and d+p>0,"actual nonempty native GDN branch")
 qs=raw["non_spec_query_start_loc"];lens=segments(qs,"non_spec_query_start_loc")
 idx=ints(raw["non_spec_state_indices_tensor"],"non_spec_state_indices_tensor")
 c.require(len(idx)==len(lens) and sum(lens)==raw["num_actual_tokens"] and d<=len(idx) and
  raw["num_decode_tokens"]==d and lens[:d]==[1]*d,
  "actual decode-first native metadata ordering/counts")
 conv=raw["conv"]
 c.require(conv["branch"]==("prefill" if p else "decode") and conv["query_start_loc"]==qs,
  "actual conv writer branch consumes complete same original metadata offsets")
 ci=conv["cache_indices"];ci=first_column(ci,"conv.cache_indices") if ci and type(ci[0]) is list else ints(ci,"conv.cache_indices")
 conv_rows=active(ci,lens,conv_slots,"convolution")
 if p:
  pre=ints(raw["prefill_state_indices"],"prefill_state_indices")
  pq=raw["prefill_query_start_loc"];plens=segments(pq,"prefill_query_start_loc")
  # Original builder subtracts d tokens and slices d leading decode rows.
  c.require(pre==idx[d:] and pq==[v-d for v in qs[d:]] and len(pre)==len(plens),
   "actual deployed prefill tail, not recomputed request/synthetic slot")
  recurrent_rows=active(idx[:d],lens[:d],recurrent_slots,"recurrent decode")
  recurrent_rows+= [dict(r,row=r["row"]+d) for r in active(pre,plens,recurrent_slots,"recurrent prefill")]
  # Source writes every prefill-state index on scatter, including a compacted
  # zero-length segment restored to its initial state. Those rows must remain
  # unchanged and therefore stay in the independent inactive byte comparison.
 else:
  c.require(raw["prefill_state_indices"] is None and raw["prefill_query_start_loc"] is None,"decode-only has no prefill writer")
  recurrent_rows=active(idx,lens,recurrent_slots,"recurrent decode")
 c.require(len({r["slot"] for r in recurrent_rows})==len(recurrent_rows),"no cross-branch recurrent slot collision")
 return dict(schema="sparq.GDN-writer-domain/v1",written_slots={
  "conv":sorted(r["slot"] for r in conv_rows),"recurrent":sorted(r["slot"] for r in recurrent_rows)},
  conv_rows=conv_rows,recurrent_rows=recurrent_rows,query_lengths=lens,
  zero_length_rows=[i for i,n in enumerate(lens) if not n],source_branch=conv["branch"])
def observe(meta,runner):
 # Called only before the original model, outside GLOBAL capture. No new H2D.
 c.require(not runner.speculative_config and not runner.use_cp,"exact actual scope")
 def values(t):
  if t is None:return None
  c.require(str(t.dtype) in ("torch.int32","torch.int64") and t.device.type in ("npu","cpu"),
   "actual native integer metadata tensor, not guessed host data")
  return t.detach().cpu().tolist()
 pre=meta.num_prefills>0
 conv=(meta.non_spec_prefill_metadata if pre else meta.non_spec_decode_metadata).causal_conv1d
 return dict(schema="sparq.GDN-actual-metadata-snapshot/v1",spec_sequence_masks=None if meta.spec_sequence_masks is None else "rejected",
  num_spec_decodes=meta.num_spec_decodes,num_spec_decode_tokens=meta.num_spec_decode_tokens,
  num_decodes=meta.num_decodes,num_prefills=meta.num_prefills,num_decode_tokens=meta.num_decode_tokens,
  num_actual_tokens=meta.num_actual_tokens,mamba_cache_mode=runner.vllm_config.cache_config.mamba_cache_mode,
  use_context_parallel=bool(runner.use_cp),non_spec_query_start_loc=values(meta.non_spec_query_start_loc),
  non_spec_state_indices_tensor=values(meta.non_spec_state_indices_tensor),
  prefill_state_indices=values(meta.prefill_state_indices),prefill_query_start_loc=values(meta.prefill_query_start_loc),
  conv=dict(branch="prefill" if pre else "decode",query_start_loc=values(conv.query_start_loc),cache_indices=values(conv.cache_indices)))
