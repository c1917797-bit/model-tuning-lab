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


def _npu_runtime():
    import torch
    return torch.npu


@contextmanager
def transfer_private_material(data,*,device,asynchronous=False,quarantine=None):
    """Keep private CPU sources alive until the exact copy stream completes.

    The opt-in changes host blocking only, not tensor values, ownership or math.
    A failed event falls back to stream completion. If both fail, retain all
    references in the owning pool and fail closed; never assume copies stopped.
    """
    if type(asynchronous) is not bool:
        raise ValueError('explicit asynchronous material transfer boolean required')
    if not asynchronous:
        yield {k:v.to(device=device) for k,v in data.items()}
        return
    target=str(device)
    if target!='npu' and not (target.startswith('npu:') and target[4:].isdigit()):
        raise ValueError('asynchronous compact material transfer requires NPU target')
    if quarantine is None:
        raise ValueError('owning transfer quarantine required')
    runtime=_npu_runtime()
    with runtime.device(device):
        stream=runtime.current_stream()
        event=runtime.Event()
        private={};started=False;recorded=False
        try:
            with runtime.stream(stream):
                for key,value in data.items():
                    started=True
                    private[key]=value.to(device=device,non_blocking=True)
                event.record(stream)
                recorded=True
            yield private
        finally:
            if started:
                try:
                    if recorded:event.synchronize()
                    else:stream.synchronize()
                except BaseException:
                    try:stream.synchronize()
                    except BaseException as failure:
                        quarantine.append((data,private,event,stream))
                        raise RuntimeError('material copy completion unknown; sources quarantined') from failure
                    raise


class CompactLinearMaterialPool:
    def __init__(self,capacity_bytes,*,async_material_transfer=False):
        if type(async_material_transfer) is not bool:
            raise ValueError('explicit asynchronous material transfer boolean required')
        self.pool=PublicPool(capacity_bytes)
        self.async_material_transfer=async_material_transfer
        self._quarantined_transfers=[]
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
        if self._quarantined_transfers:
            raise RuntimeError('material pool blocked after unknown copy completion')
        with self.pool.acquire_private(identity_key(identity)) as (generation,data):
            with transfer_private_material(data,device=device,
                    asynchronous=self.async_material_transfer,
                    quarantine=self._quarantined_transfers) as private:
                yield generation,CompactLinearBody(identity,
                    SegmentAffine(private['transition'],private['zero_state']),private['conv_tail'])
