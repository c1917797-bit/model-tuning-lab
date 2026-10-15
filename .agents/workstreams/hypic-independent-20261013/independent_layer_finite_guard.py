"""Unwired C1 precommit finite gate; never writes inference/cache tensors."""
import torch


class LayerFiniteGuard:
    """Retain private terminal tensors until one scalar precommit decision.

    Same-stream producers must precede validate(). This does NOT establish
    cross-stream dependencies, synchronize cache commits, or prove numerics.
    The runtime must keep material leases alive and perform its final barrier.
    """
    def __init__(self, *, max_tensors=512):
        if type(max_tensors) is not int or not 1 <= max_tensors <= 512:
            raise ValueError("bounded tensor limit required")
        self.max_tensors=max_tensors
        self._tensors=[]
        self._device=None
        self._closed=False

    def collect(self, *tensors):
        if self._closed:
            raise RuntimeError("finite gate already closed")
        if not tensors or len(self._tensors)+len(tensors)>self.max_tensors:
            raise ValueError("empty or excessive finite coverage")
        for tensor in tensors:
            if not isinstance(tensor,torch.Tensor) or tensor.numel()==0:
                raise ValueError("nonempty tensor required")
            if tensor.device.type=="meta":
                raise ValueError("real tensor required")
            if self._device is not None and tensor.device!=self._device:
                raise ValueError("mixed finite-gate devices")
        self._device=tensors[0].device if self._device is None else self._device
        if any(t.device!=self._device for t in tensors):
            raise ValueError("mixed finite-gate devices")
        self._tensors.extend(tensors)

    def validate(self):
        if self._closed:
            raise RuntimeError("finite gate already closed")
        self._closed=True
        tensors=self._tensors
        self._tensors=[]
        if not tensors:
            raise ValueError("missing finite coverage")
        # Reductions remain device-side; exactly one scalar wait for the layer.
        finite=torch.stack([torch.isfinite(t).all() for t in tensors]).all()
        if not finite.item():
            raise ValueError("nonfinite C1 layer before native commit")
        return len(tensors)
