"""Opt-in catalog stage with per-segment all-layer readiness and leases."""
from independent_compact_stage import CompactCanonicalStage,pin_complete_material
from independent_segment_catalog import SegmentCatalog
from independent_hybrid_material import MaterialIdentity
from independent_linear_material_pool import identity_key
from independent_compact_model_hook import CompactModelSelection
from independent_catalog_query_plan import plan_catalog_batch

class CatalogCompactStage(CompactCanonicalStage):
    def __init__(self,*,public_segments,**kwargs):
        if kwargs.get("enable_mixed") is not True:
            raise ValueError("catalog requires explicitly enabled mixed request routing")
        catalog=SegmentCatalog(public_segments,boundary_tokens=kwargs.get("boundary_tokens",8))
        super().__init__(public_tokens=next(iter(catalog.entries.values())),**kwargs)
        self.catalog=catalog
    def identity(self,layer,rank,*,tokens_sha256=None):
        if tokens_sha256 is None:
            raise ValueError("catalog material identity requires explicit digest")
        tokens=self.catalog.tokens(tokens_sha256)
        return MaterialIdentity(self.model,self.code,layer,rank,tokens_sha256,len(tokens),self.boundary)
    def public_digest(self,tokens):
        if tokens is None:return None
        tokens=tuple(tokens);matches=[]
        for digest,public in self.catalog.entries.items():
            if tokens==public or (self.allow_public_tail and len(tokens)>len(public)
                                 and tokens[:len(public)]==public):matches.append(digest)
        if len(matches)>1:raise ValueError("ambiguous canonical catalog producer")
        return matches[0] if matches else None
    def is_public_prompt(self,tokens):return self.public_digest(tokens) is not None
    def public_identity_for_request(self,layer,request,tokens):
        digest=self.public_digest(tokens)
        if digest is None or request.computed_tokens!=0 or request.scheduled_tokens!=len(tokens):return None
        return self.identity(layer,request.rank,tokens_sha256=digest)
    def select_mixed(self,model,requests,prompts,snap):
        linear,full=self.layer_inventory(model)
        if set(name for _,names in snap.attention_groups for name in names)!=set(full):
            raise ValueError("catalog full-attention inventory mismatch")
        ready=set();keysets={}
        for digest in self.catalog.entries:
            lk=tuple(identity_key(self.identity(n,snap.rank,tokens_sha256=digest)) for n in linear)
            kk=tuple(identity_key(self.identity(n,snap.rank,tokens_sha256=digest)) for n in full)
            keysets[digest]=(lk,kk)
            with self.compact_store.pool.lock:
                with self.compact_kv_store.lock:
                    if all(k in self.compact_store.pool.entries for k in lk) and all(k in self.compact_kv_store.entries for k in kk):
                        ready.add(digest)
        plans=plan_catalog_batch(requests,prompts,self.catalog,ready)
        hot=[p for p in plans if p.skipped_tokens]
        if not hot:return None
        lkeys=tuple(k for p in hot for k in keysets[p.tokens_sha256][0])
        kkeys=tuple(k for p in hot for k in keysets[p.tokens_sha256][1])
        return CompactModelSelection(plans,snap.sampled_rows,False,
            snap.cache_slices,snap.attention_groups,snap.writable_kv_slots,
            pin_complete_material(self.compact_store.pool,self.compact_kv_store,lkeys,kkeys))
