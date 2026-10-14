"""Canonical public-request selector and C1 material sink for worker integration."""
from independent_segment_selection import token_digest
from independent_hybrid_material import MaterialIdentity
from independent_linear_material_pool import LinearMaterialPool,identity_key
from independent_runner_context import CURRENT_PROMPT_TOKENS

class CanonicalPublicStage:
    def __init__(self,*,model_identity,code_identity,public_tokens,capacity_bytes,
                 boundary_tokens=8,allow_public_tail=False):
        if type(allow_public_tail) is not bool:raise ValueError("explicit public-tail boolean required")
        self.allow_public_tail=allow_public_tail
        if not model_identity or not code_identity:raise ValueError("frozen source identities required")
        self.tokens=tuple(public_tokens);self.digest=token_digest(self.tokens)
        if boundary_tokens<3 or len(self.tokens)<=boundary_tokens:
            raise ValueError("public segment/live boundary invalid")
        self.model=model_identity;self.code=code_identity;self.boundary=boundary_tokens
        self.store=LinearMaterialPool(capacity_bytes)
    def identity(self,layer,rank):
        return MaterialIdentity(self.model,self.code,layer,rank,self.digest,
                                len(self.tokens),self.boundary)
    def select_public(self,layer,requests):
        if len(requests)!=1:return None
        request=requests[0];prompts=CURRENT_PROMPT_TOKENS.get()
        tokens=prompts.get(request.request_id) if prompts is not None else None
        if not self.is_public_prompt(tokens):return None
        if request.computed_tokens!=0 or request.scheduled_tokens!=len(tokens):return None
        identity=self.identity(layer.prefix,request.rank)
        with self.store.pool.lock:
            if identity_key(identity) in self.store.pool.entries:return None
        return identity
    def is_public_prompt(self,tokens):
        if tokens is None:return False
        tokens=tuple(tokens)
        return tokens==self.tokens or (self.allow_public_tail and
            len(tokens)>len(self.tokens) and tokens[:len(self.tokens)]==self.tokens)
    def publish(self,material):
        expected=self.identity(material.identity.layer,material.identity.rank)
        if material.identity!=expected:raise ValueError("public producer identity mismatch")
        return self.store.publish(material)
    def install(self,*,enabled=False):
        from independent_public_gdn_hook import install_public_gdn_producer
        return install_public_gdn_producer(enabled=enabled,
            select_public=self.select_public,publish=self.publish)
