"""Actual native conv/chunk + DAMP ops seam. Default OFF; not serving acceptance.

Only caller-owned transient prefill state exists. Torch, torch_npu, native gdn
and explicit independent candidate ops are INJECTED after proper image init.
No direct load, Docker/NPU execution or global-op reassignment at import.
"""
from dataclasses import dataclass
from .core import require
DECODE_NAMESPACE="qwen36_damp_all_batch_v3"
PACK_NAMESPACE="qwen36_damp_selected_prefill_v1"
GDN_SHA="d6ec29919268178f5bf6e70e689c1d273d04b1cb1d84dc94efa7bbbc35490816"
@dataclass
class Cold:
    plan: object
    inv_pk: object
    cache_identity: tuple
    plan_identity: tuple
    decode_T: frozenset
    prefill_P: frozenset
class TorchBackend:
    def __init__(self,torch,torch_npu,gdn,decode_ops,pack_ops,plans,identity,sink,
                 enabled=False,formal_perf=False):
        require(enabled is True,"backend default OFF")
        # Readiness MUST be enforced before installation by the source-bound
        # service authority. This checked source cannot admit formal timing.
        require(formal_perf is False,"checked backend is NOT formal performance; pending async failure/lifecycle gates")
        self.t,self.npu,self.gdn=torch,torch_npu,gdn
        self.decode_ops,self.pack_ops,self.plans=decode_ops,pack_ops,plans
        self.identity,self.sink=identity,sink
        self.cold={}
        require(decode_ops.decode.default._schema.name.startswith(DECODE_NAMESPACE+"::"),
                "explicit frozen all-batch namespace required")
        require(pack_ops.pack.default._schema.name.startswith(PACK_NAMESPACE+"::"),
                "explicit NEW selected-pack namespace required")
    def nd(self,x):
        result=self.npu.npu_format_cast(x.contiguous(),2)
        if result.data_ptr()%32:
            result=self.npu.npu_format_cast(result.clone(),2)
        require(result.is_contiguous() and self.npu.get_npu_format(result)==2 and
                result.data_ptr()%32==0,"actual ND32B operand required")
        return result
    def prepare_layer(self,layer):
        # Called only AFTER source-bound allocator/plan admission and cache
        # initialization; never inside model forward/capture.
        t=self.t;conv,hi,lo,sc=layer.kv_cache
        require(hi.shape[0] >= 16, "actual allocator needs at least16 distinct slots for the admitted C16 cap")
        plan=self.plans.get(layer.tp_rank,layer.layer_idx,hi.device)
        pk_cpu=plan.pk.detach().cpu() # static cold data only, no recurrent state
        require(tuple(pk_cpu.shape)==(12,128) and pk_cpu.dtype==t.int32,
                "cold plan logical INT32 per-Hv Pk required")
        for h in range(12):
            require(t.equal(pk_cpu[h].long().sort().values,t.arange(128,dtype=t.int64)),
                    "Pk bijection required before inverse construction")
        inv_pk=self.nd(pk_cpu.long().argsort(dim=1).to(dtype=t.int32,device=hi.device))
        # Prepared keys independently cover true1..16 P/T, no fake padded16.
        for n in range(1,17):
            q=self.nd(t.zeros((n,4,128),dtype=t.bfloat16,device=hi.device))
            self.decode_ops.prepare(q,hi,plan.pk,plan.pv,plan.inv_pv,plan.sr)
            dense=self.nd(t.zeros((n,12,128,128),dtype=t.float32,device=hi.device))
            ix=self.nd(t.arange(n,dtype=t.int32,device=hi.device))
            self.pack_ops.prepare(dense,hi,lo,sc,plan.pk,plan.pv,plan.sr,ix,False)
            # prepare validates static ABI/keys only; these indices are not a dynamic metadata gate.
            # dense/q/ix are local cold validation scratch, not retained.
            del q,dense,ix
        self.cold[layer.prefix]=Cold(plan,inv_pk,self.identity.cache(layer.kv_cache),
            self.identity.plan(plan),frozenset(range(1,17)),frozenset(range(1,17)))
    def resource(self,layer):
        require(layer.prefix in self.cold,"missing cold prepared actual layer")
        r=self.cold[layer.prefix]
        require(r.cache_identity==self.identity.cache(layer.kv_cache) and
                r.plan_identity==self.identity.plan(r.plan),"native cache/static-plan pointer identity changed")
        return r
    def require_cold(self,layer,turn):
        r=self.resource(layer)
        require(self.gdn.get_pcp_group().world_size == 1,
                "native PCP>1 conv gather/state path is outside this exact local TP4 seam")
        require(not turn.num_decodes or turn.num_decodes in r.decode_T,"true decode T cold key missing")
        require(not turn.prefill_rows or len(turn.prefill_rows) in r.prefill_P,"true prefill P cold key missing")
    def metadata(self,prefix):
        all_md=self.gdn.get_forward_context().attn_metadata
        if all_md is None:return None
        require(isinstance(all_md,dict) and prefix in all_md,"native actual metadata required")
        return all_md[prefix]
    def conv(self,layer,md,turn,mixed_qkv):
        require(md.spec_sequence_masks is None and md.num_actual_tokens==turn.starts[-1],
                "spec/padded native GDN metadata unsupported")
        all_input=mixed_qkv[:md.num_actual_tokens]
        weights=layer.conv1d.weight.view(layer.conv1d.weight.size(0),layer.conv1d.weight.size(2))
        has_prefill=bool(turn.prefill_rows)
        metadata=(md.non_spec_prefill_metadata if has_prefill else md.non_spec_decode_metadata).causal_conv1d
        out=self.t.empty_like(all_input)
        # With ANY prefill, native causal metadata belongs to ALL rows.
        self.t.ops._C_ascend.npu_causal_conv1d_custom(
            out,all_input,weights.transpose(0,1),conv_state=layer.kv_cache[0],
            bias_opt=layer.conv1d.bias,query_start_loc_opt=metadata.query_start_loc,
            cache_indices_opt=metadata.cache_indices,
            initial_state_mode_opt=metadata.initial_state_mode if has_prefill else None,
            num_accepted_tokens_opt=None,activation_mode=1 if layer.activation else 0,
            pad_slot_id=self.gdn.PAD_SLOT_ID,run_mode=0 if has_prefill else 1)
        return out
    def project(self,layer,convolved):
        return layer.rearrange_mixed_qkv(convolved)
    def gating(self,layer,a,b,tokens):
        return self.gdn.DeviceOperator.fused_gdn_gating(layer.A_log,a[:tokens],b[:tokens],layer.dt_bias)
    def decode(self,layer,md,turn,qkv,gating):
        n=turn.decode_tokens;r=self.resource(layer);_,hi,lo,sc=layer.kv_cache
        q,k,v=qkv;g,beta=gating
        q=self.gdn.l2norm_fwd(q[:,:n]).squeeze(0)
        k=self.gdn.l2norm_fwd(k[:,:n]).squeeze(0)
        # Clone native suffix/prefix metadata only if ND alignment requires it.
        # Values/count remain actual T: no fake slots/PAD or GPU->CPU receipt.
        operands=tuple(self.nd(x) for x in (q,k,v[:,:n].squeeze(0),
                       g[:,:n].squeeze(0),beta[:,:n].squeeze(0)))
        indices=self.nd(md.non_spec_state_indices_tensor[:turn.num_decodes].contiguous())
        lengths=self.nd(md.non_spec_decode_metadata.actual_seq_lengths)
        return self.decode_ops.decode(*operands,hi,lo,sc,r.plan.pk,r.plan.pv,
                r.plan.inv_pv,r.plan.sr,lengths,indices).unsqueeze(0)
    def unpack_selected(self,layer,md,turn,positions):
        # Return only P-prefill key-major transient native initial states.
        t=self.t;r=self.resource(layer);_,hi,lo,sc=layer.kv_cache
        p=len(turn.prefill_rows)
        initial=t.zeros((p,12,128,128),dtype=t.float32,device=hi.device)
        if not positions:return initial
        pos=t.tensor(positions,dtype=t.int64,device=hi.device) # tiny CPU scheduling positions H2D, not D2H
        ids=md.prefill_state_indices.index_select(0,pos).long()
        selected_hi=hi.index_select(0,ids)
        selected_lo=lo.index_select(0,ids)
        selected_sc=sc.index_select(0,ids)
        for head in range(12):
            # SAME group32 V axis; no BF16 intermediate, no scale floor.
            low=selected_lo[:,head].float()*selected_sc[:,head].repeat_interleave(32,dim=1)
            packed=t.cat((selected_hi[:,head].float(),low),dim=-1)
            original=packed.index_select(1,r.plan.inv_pv[head].long()).index_select(
                              2,r.inv_pk[head].long())
            original=original*r.plan.sr[head][None,:,None] # original-V FP32 SR
            initial[:,head].index_copy_(0,pos,original.transpose(-1,-2).contiguous())
        # Fresh rows remain ZERO; continuing rows alone are reconstructed.
        # Every selected temporary dies before return/end-of-layer. No S-state.
        return initial
    def prefill(self,layer,md,turn,qkv,gating,positions):
        t=self.t;r=self.resource(layer);_,hi,lo,sc=layer.kv_cache
        n=turn.decode_tokens;p=len(turn.prefill_rows)
        q,k,v=qkv;g,beta=gating
        initial=self.unpack_selected(layer,md,turn,positions)
        out,last=self.gdn.chunk_gated_delta_rule(
            q=q[:,n:],k=k[:,n:],v=v[:,n:],g=g[:,n:],beta=beta[:,n:],
            initial_state=initial,output_final_state=True,cu_seqlens=md.prefill_query_start_loc,
            prebuilt_meta=md.non_spec_prefill_metadata.chunk,head_first=False,
            use_qk_l2norm_in_kernel=True)
        # Native prebuilt suffix metadata/order is preserved, not regenerated.
        final=self.nd(last.transpose(-1,-2).contiguous())
        require(tuple(final.shape)==(p,12,128,128),"native final state P/axes drift")
        indices=self.nd(md.prefill_state_indices)
        status=self.pack_ops.pack(final,hi,lo,sc,r.plan.pk,r.plan.pv,r.plan.sr,indices,False)
        # CHECKED experiment only: validation sync/D2H is exposed, not smuggled
        # into instrumentation-free formal performance. All guarded status kept.
        self.sink.pack_status(status,layer.prefix,turn)
        return out
    def merge(self,decode,prefill):
        return self.t.cat((decode,prefill),dim=1) if decode is not None and prefill is not None else (
            decode if decode is not None else prefill)
    def validate_output(self,out,prefix,turn):
        self.sink.output(out,prefix,turn)
    def publish(self,target,out,tokens):
        target[:tokens]=out.squeeze(0)
