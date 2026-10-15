"""Private packed convolution windows; omitted body rows are never gathered."""
from dataclasses import dataclass
import torch

@dataclass
class PackedWindows:
    projected: object
    b: object
    a: object
    conv: object
    starts: object
    host_starts: tuple

def pack_windows(layout,projected,b,a,incoming_conv,cached_conv):
    n=len(layout.request_ids)
    if projected.ndim!=2 or b.ndim!=2 or a.ndim!=2 or b.shape!=a.shape:
        raise ValueError("projected/gating matrix ABI required")
    if b.shape[0]!=projected.shape[0] or incoming_conv.shape!=(n,3,projected.shape[1]):
        raise ValueError("complete private conv/input coverage required")
    if any(x.device!=projected.device for x in (b,a,incoming_conv)):
        raise ValueError("one packed input device required")
    if not layout.windows:raise ValueError("native1-only layer has no packed windows")
    expected={key for chain in layout.chains for kind,key in chain if kind=='cached'}
    if set(cached_conv)!=expected:raise ValueError("exact cached convolution coverage required")
    for tail in cached_conv.values():
        if tail.shape!=incoming_conv.shape[1:] or tail.device!=projected.device:
            raise ValueError("cached conv layout/device mismatch")
    sources=[];tails=[];starts=[0]
    for number,window in enumerate(layout.windows):
        chain=layout.chains[window.request_row]
        action=chain.index(('live',number))
        if action==0:tail=incoming_conv[window.request_row]
        else:
            if chain[action-1][0]!='cached':raise ValueError("suffix must follow cached body")
            tail=cached_conv[chain[action-1][1]]
        if not 0<=window.source_start<window.source_end<=projected.shape[0]:
            raise ValueError("packed source window outside compact stream")
        sources.extend(range(window.source_start,window.source_end))
        tails.append(tail)
        starts.append(starts[-1]+window.source_end-window.source_start)
    if starts[-1]!=layout.packed_tokens or len(set(sources))!=len(sources):
        raise ValueError("packed window overlap/count drift")
    index=torch.tensor(sources,dtype=torch.long,device=projected.device)
    conv=torch.stack(tails).to(projected.dtype).clone().contiguous()
    # Inputs and real native cache slots remain untouched by the backend.
    return PackedWindows(projected.index_select(0,index).contiguous(),
        b.index_select(0,index).contiguous(),a.index_select(0,index).contiguous(),conv,
        torch.tensor(starts,dtype=torch.int32,device=projected.device),tuple(starts))
