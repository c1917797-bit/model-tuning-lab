"""Opt-in ephemeral all-head C1 observations; never changes runtime mathematics."""
import math
import torch
from independent_c1_stage_capture import REQUIRED,MAX_RECORDS
from independent_native_decode_prepare import SHADOW_ATOL,SHADOW_RTOL

MAX_RETAINED_BYTES=256*1024*1024

def residual_selection(actual,expected,reported_max):
    """Select with exactly the frozen FP32 guard; not an independent oracle."""
    if actual.shape!=expected.shape or actual.ndim!=3:
        raise ValueError("head/key/value state geometry required")
    if not bool(torch.isfinite(actual).all()) or not bool(torch.isfinite(expected).all()):
        raise ValueError("finite full states required")
    x=actual.detach().float();y=expected.detach().float()
    scaled=(x-y).abs()/(SHADOW_ATOL+SHADOW_RTOL*y.abs())
    flat=int(scaled.reshape(-1).argmax())
    width_k,width_v=actual.shape[1:]
    head,offset=divmod(flat,width_k*width_v)
    key,value=divmod(offset,width_v)
    maximum=float(scaled[head,key,value])
    if not math.isfinite(reported_max) or maximum<=1 or maximum!=float(reported_max):
        raise ValueError("actual failed frozen guard maximum required")
    return dict(value_head=head,key_coordinate=key,value_coordinate=value,
                reported_max_scaled=float(reported_max),selected_max_scaled=maximum,
                atol=SHADOW_ATOL,rtol=SHADOW_RTOL,
                selection="runtime full-state FP32 argmax; exported head is sampled")

def sampled_head(stage,tensors,value_head,*,key_heads=4,value_heads=12):
    """Inputs are standardized [token,head,...] or [head,key,value]."""
    if (type(value_head)is not int or not 0<=value_head<value_heads
            or key_heads<1 or value_heads%key_heads or set(tensors)!=REQUIRED.get(stage)):
        raise ValueError("exact stage and grouped-head coordinates required")
    result={}
    for name,tensor in tensors.items():
        if name=="conv":
            if tensor.ndim!=2:raise ValueError("full conv tail geometry required")
            result[name]=tensor
        elif stage=="inputs" and name in ("q","k"):
            if tensor.ndim!=3 or tensor.shape[1] not in (key_heads,value_heads):
                raise ValueError("native or expanded Q/K geometry required")
            index=value_head//(value_heads//key_heads) if tensor.shape[1]==key_heads else value_head
            result[name]=tensor[:,index]
        elif (stage=="inputs" and name in ("v","g","beta")) or name=="output":
            expected_ndim=2 if name in ("g","beta") else 3
            if tensor.ndim!=expected_ndim or tensor.shape[1]!=value_heads:
                raise ValueError("value-head token geometry required")
            result[name]=tensor[:,value_head]
        else:
            if tensor.ndim!=3 or tensor.shape[0]!=value_heads:
                raise ValueError("head-first state geometry required")
            result[name]=tensor[value_head]
    return result

class DeferredHeadCapture:
    """One-call owned clones, bounded before allocation, default-off factory."""
    def __init__(self,*,max_bytes=MAX_RETAINED_BYTES,max_records=MAX_RECORDS):
        if (type(max_bytes)is not int or not 1<=max_bytes<=MAX_RETAINED_BYTES
                or type(max_records)is not int or not 1<=max_records<=MAX_RECORDS):
            raise ValueError("frozen deferred bounds required")
        self.max_bytes=max_bytes;self.max_records=max_records
        self.records=[];self.keys=set();self.bytes=0;self.closed=False

    def add(self,*,side,request_id,stage,window,source_start,source_end,tensors):
        try:
            self._add(side=side,request_id=request_id,stage=stage,window=window,
                      source_start=source_start,source_end=source_end,tensors=tensors)
        except BaseException:
            self.discard()
            raise

    def _add(self,*,side,request_id,stage,window,source_start,source_end,tensors):
        if self.closed:raise ValueError("deferred capture closed")
        if (side not in ("packed","serial") or not isinstance(request_id,str) or not request_id
                or window not in ("prefix","suffix","body")
                or type(source_start)is not int or type(source_end)is not int
                or not 0<=source_start<source_end<=40960
                or not isinstance(tensors,dict) or set(tensors)!=REQUIRED.get(stage)):
            raise ValueError("exact deferred coordinates and stage required")
        key=(side,request_id,stage,window)
        if key in self.keys:raise ValueError("duplicate deferred stage")
        if len(self.records)>=self.max_records:raise ValueError("deferred record bound")
        # Validate all geometry/bytes BEFORE the first clone, including later fields.
        sampled_head(stage,tensors,0)
        cost=0
        for value in tensors.values():
            if not isinstance(value,torch.Tensor) or not value.is_floating_point() or value.numel()==0:
                raise ValueError("nonempty floating stage tensors required")
            cost+=value.numel()*value.element_size()
        if self.bytes+cost>self.max_bytes:raise ValueError("deferred byte bound before allocation")
        snapshots={}
        try:
            for name,value in tensors.items():
                snapshots[name]=value.detach().clone().contiguous()
        except BaseException:
            snapshots.clear()
            self.discard()
            raise
        self.records.append(dict(side=side,request_id=request_id,stage=stage,window=window,
            source_start=source_start,source_end=source_end,tensors=snapshots))
        self.keys.add(key);self.bytes+=cost

    def flush_to(self,capture,value_head):
        if self.closed:raise ValueError("deferred capture closed")
        try:
            for record in self.records:
                meta={k:v for k,v in record.items() if k!="tensors"}
                capture.add(**meta,tensors=sampled_head(record["stage"],record["tensors"],value_head))
        finally:
            self.discard()

    def discard(self):
        self.records.clear();self.keys.clear();self.bytes=0;self.closed=True

def selected_deferred_capture(*,enabled=False,**limits):
    if type(enabled)is not bool:raise ValueError("explicit diagnostic switch required")
    return DeferredHeadCapture(**limits) if enabled else None
