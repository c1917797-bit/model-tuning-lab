"""CPU-resident C1 T/S material; no per-token core outputs are retained."""
from contextlib import contextmanager
from dataclasses import dataclass
from independent_c1_reference import SegmentAffine
from independent_linear_material_pool import identity_key
from independent_hybrid_material import validate_material
from independent_public_pool import PublicPool


@dataclass(frozen=True)
class CompactLinearBody:
    identity: object
    affine: object
    conv_tail: object


class CompactLinearMaterialPool:
    def __init__(self,capacity_bytes):self.pool=PublicPool(capacity_bytes)
    def publish(self,material):
        i=material.identity;validate_material(i,i)
        t=material.affine.transition;s=material.affine.zero_state;c=material.conv_tail
        if (t.ndim!=3 or s.ndim!=3 or t.shape[:2]!=s.shape[:2]
                or t.shape[-1]!=s.shape[-2] or c.ndim!=2 or c.shape[0]!=3):
            raise ValueError('compact state/transition/conv-tail layout mismatch')
        # Blocking transfers establish CPU readiness before immutable publish.
        return self.pool.publish(identity_key(i),{
            'transition':t.detach().to('cpu'),'zero_state':s.detach().to('cpu'),
            'conv_tail':c.detach().to('cpu')})
    @contextmanager
    def acquire_private(self,identity,*,device):
        with self.pool.acquire_private(identity_key(identity)) as (generation,data):
            private={k:v.to(device=device) for k,v in data.items()}
            yield generation,CompactLinearBody(identity,
                SegmentAffine(private['transition'],private['zero_state']),private['conv_tail'])
