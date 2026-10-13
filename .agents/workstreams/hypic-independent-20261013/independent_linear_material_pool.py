"""Canonical identity-bound C1 public material cache and pinned private leases."""
from contextlib import contextmanager
from dataclasses import asdict
import hashlib,json
from independent_c1_reference import SegmentAffine
from independent_hybrid_material import validate_material
from independent_linear_reuse import LinearPublicBody
from independent_public_pool import PublicPool

def identity_key(identity):
    validate_material(identity,identity)
    return hashlib.sha256(json.dumps(asdict(identity),sort_keys=True,
                                      separators=(',',':')).encode()).hexdigest()

class LinearMaterialPool:
    def __init__(self,capacity_bytes):
        self.pool=PublicPool(capacity_bytes)
    def publish(self,material):
        identity=material.identity
        validate_material(identity,identity)
        if material.core_outputs.shape[0]!=identity.length-identity.boundary_tokens:
            raise ValueError("public body coverage mismatch")
        return self.pool.publish(identity_key(identity),{
            "transition":material.affine.transition,
            "zero_state":material.affine.zero_state,
            "core_outputs":material.core_outputs,
            "conv_tail":material.conv_tail})
    @contextmanager
    def acquire_private(self,identity):
        with self.pool.acquire_private(identity_key(identity)) as (generation,data):
            yield generation,LinearPublicBody(identity,
                SegmentAffine(data["transition"],data["zero_state"]),
                data["core_outputs"],data["conv_tail"])
