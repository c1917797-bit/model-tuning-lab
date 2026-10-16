"""Canonical material production and complete-layer compact model admission."""
from contextlib import contextmanager,ExitStack
from independent_public_stage import CanonicalPublicStage
from independent_compact_material_pool import CompactLinearMaterialPool
from independent_public_pool import PublicPool
from independent_linear_material_pool import identity_key
from independent_segment_selection import select_segment
from independent_c2_query_plan import plan_c2_queries
from independent_compact_model_hook import CompactModelSelection


@contextmanager
def pin_complete_material(linear_pool,kv_pool,linear_keys,kv_keys):
    """Lock both pools in one fixed order while validating and pinning all layers.

    Pin public entries themselves; private device copies are made by each layer.
    Never clone all-layer material for this readiness guard.
    """
    pinned=[]
    with linear_pool.lock:
        with kv_pool.lock:
            try:
                for pool,keys in ((linear_pool,linear_keys),(kv_pool,kv_keys)):
                    for key in set(keys):
                        entry=pool.entries[key];entry['pins']+=1;pinned.append((pool,key,entry))
            except BaseException:
                for pool,key,entry in pinned:entry['pins']-=1
                raise
    try:yield
    finally:
        with linear_pool.lock:
            with kv_pool.lock:
                for pool,key,entry in pinned:
                    if pool.entries.get(key) is not entry:
                        raise RuntimeError('pinned material generation replaced')
                    entry['pins']-=1


class CompactCanonicalStage(CanonicalPublicStage):
    def __init__(self,*,model_identity,code_identity,public_tokens,
                 capacity_bytes,boundary_tokens=8,kv_capacity_bytes=536870912,
                 enable_mixed=False,allow_public_tail=False,allow_public_chunks=False,
                 c1_async_material_transfer=False,c1_async_material_verify=False):
        if type(enable_mixed) is not bool:raise ValueError('explicit mixed boolean required')
        self.enable_mixed=enable_mixed
        super().__init__(model_identity=model_identity,code_identity=code_identity,
            public_tokens=public_tokens,capacity_bytes=capacity_bytes,boundary_tokens=boundary_tokens,
            allow_public_tail=allow_public_tail,allow_public_chunks=allow_public_chunks)
        self.compact_store=CompactLinearMaterialPool(capacity_bytes,
            async_material_transfer=c1_async_material_transfer,
            verify_async_transfer=c1_async_material_verify)
        self.store=self.compact_store
        self.compact_kv_store=PublicPool(kv_capacity_bytes)
    def layer_inventory(self,model):
        if model.start_layer!=0 or model.end_layer!=64 or len(model.layers)!=64:
            raise ValueError('selected27B single-PP layer inventory mismatch')
        linear=[];full=[]
        for layer in model.layers:
            if layer.layer_type=='linear_attention':linear.append(layer.linear_attn.prefix)
            elif layer.layer_type=='full_attention':full.append(layer.self_attn.attn.layer_name)
            else:raise ValueError('unexpected hybrid layer type')
        if len(linear)!=48 or len(full)!=16 or len(set(linear+full))!=64:
            raise ValueError('selected hybrid layer identities incomplete')
        return tuple(linear),tuple(full)
    def select_compact(self,model,input_ids,positions,intermediate_tensors,inputs_embeds):
        from independent_runner_context import CURRENT_REQUEST_SLICES,CURRENT_PROMPT_TOKENS,CURRENT_RUNTIME_SNAPSHOT
        requests=CURRENT_REQUEST_SLICES.get();prompts=CURRENT_PROMPT_TOKENS.get()
        snap=CURRENT_RUNTIME_SNAPSHOT.get()
        if not requests or prompts is None or snap is None or snap.prompt_logprobs or intermediate_tensors is not None:return None
        if tuple(r.request_id for r in requests)!=snap.request_ids or any((r.rank,r.step)!=(snap.rank,snap.step) for r in requests):
            raise ValueError('runtime snapshot/request identity changed')
        if any(self.is_public_prompt(prompts.get(r.request_id)) for r in requests):return None
        if self.enable_mixed:return self.select_mixed(model,requests,prompts,snap)
        plans=[]
        for req in requests:
            tokens=prompts.get(req.request_id)
            if tokens is None:return None
            try:
                selection=select_segment(tokens,self.tokens)
                plan=plan_c2_queries(req,selection,seam_tokens=self.boundary,public_length=len(self.tokens))
            except ValueError:return None
            if req.token_end-1 not in plan.packed_rows():return None
            plans.append(plan)
        linear,full=self.layer_inventory(model)
        actual_full=tuple(name for _,names in snap.attention_groups for name in names)
        if set(actual_full)!=set(full):raise ValueError('native full-attention inventory changed')
        rank=snap.rank
        lkeys=tuple(identity_key(self.identity(name,rank)) for name in linear)
        kkeys=tuple(identity_key(self.identity(name,rank)) for name in full)
        with self.compact_store.pool.lock:
            with self.compact_kv_store.lock:
                if any(k not in self.compact_store.pool.entries for k in lkeys) or any(k not in self.compact_kv_store.entries for k in kkeys):return None
        return CompactModelSelection(tuple(plans),snap.sampled_rows,False,
            snap.cache_slices,snap.attention_groups,snap.writable_kv_slots,
            pin_complete_material(self.compact_store.pool,self.compact_kv_store,lkeys,kkeys))
    def select_mixed(self,model,requests,prompts,snap):
        from independent_mixed_query_plan import plan_mixed_queries
        linear,full=self.layer_inventory(model)
        if set(name for _,names in snap.attention_groups for name in names)!=set(full):
            raise ValueError('mixed full-attention inventory changed')
        lkeys=tuple(identity_key(self.identity(name,snap.rank)) for name in linear)
        kkeys=tuple(identity_key(self.identity(name,snap.rank)) for name in full)
        with self.compact_store.pool.lock:
            with self.compact_kv_store.lock:
                ready=(all(k in self.compact_store.pool.entries for k in lkeys) and
                       all(k in self.compact_kv_store.entries for k in kkeys))
        if not ready:return None
        selections={}
        for req in requests:
            tokens=prompts.get(req.request_id)
            if tokens is None:continue
            try:selections[req.request_id]=select_segment(tokens,self.tokens)
            except ValueError:continue
        plans=plan_mixed_queries(requests,selections,set(selections),
                                seam_tokens=self.boundary,public_length=len(self.tokens))
        if not any(p.skipped_tokens for p in plans):return None
        return CompactModelSelection(plans,snap.sampled_rows,False,
            snap.cache_slices,snap.attention_groups,snap.writable_kv_slots,
            pin_complete_material(self.compact_store.pool,self.compact_kv_store,lkeys,kkeys))
    def install_producer(self,*,enabled=False,publish=None):
        from independent_public_gdn_hook import install_public_gdn_producer
        return install_public_gdn_producer(enabled=enabled,select_public=self.select_public,
            publish=self.publish if publish is None else publish,compact=True,
            allow_chunks=self.allow_public_chunks)
