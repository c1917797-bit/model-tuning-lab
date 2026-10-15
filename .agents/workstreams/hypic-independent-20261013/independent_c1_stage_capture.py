"""Bounded CPU-only samples for one failed integrated C1 shadow group.
No activation, algorithm changes, cache writes, or device admission here.
"""
import hashlib,json,os,re
from pathlib import Path
import numpy as np
import torch

LAYER="language_model.model.layers.0.linear_attn"
STAGES=("inputs","prefix_terminal","cached_composition","suffix_seed","final")
REQUIRED={
    "inputs":{"q","k","v","g","beta","initial"},
    "prefix_terminal":{"state"},
    "cached_composition":{"transition","zero_state","state"},
    "suffix_seed":{"state"},
    "final":{"state","conv","output"},
}
MAX_BYTES=64*1024*1024
MAX_RECORDS=32

def validate_identity(identity):
    if (not isinstance(identity,dict) or identity.get("rank")!=0
            or type(identity.get("rank"))is not int or identity.get("layer")!=LAYER
            or type(identity.get("pid"))is not int or identity["pid"]<=0
            or type(identity.get("step"))is not int or identity["step"]<0
            or not re.fullmatch("[0-9a-f]{64}",identity.get("manifest_sha256",""))):
        raise ValueError("exact source/rank0/layer0/step/PID identity required")
    requests=identity.get("requests");generations=identity.get("generations")
    if (not isinstance(requests,list) or not 1<=len(requests)<=2
            or any(not isinstance(x,str) or not x for x in requests)
            or len(set(requests))!=len(requests) or not isinstance(generations,dict)
            or set(generations)!=set(requests)
            or any(type(v)is not int or v<1 for v in generations.values())):
        raise ValueError("one bounded exact hot group and producer generations required")
    return json.loads(json.dumps(identity))

class FirstDivergenceCapture:
    """Caller must explicitly select a group. Passed calls create no files."""
    def __init__(self,identity,*,max_bytes=MAX_BYTES,max_records=MAX_RECORDS):
        self.identity=validate_identity(identity)
        if (type(max_bytes)is not int or not 1<=max_bytes<=MAX_BYTES
                or type(max_records)is not int or not 1<=max_records<=MAX_RECORDS):
            raise ValueError("frozen capture limits required")
        self.max_bytes=max_bytes;self.max_records=max_records
        self.records=[];self.keys=set();self.bytes=0;self.closed=False

    def add(self,*,side,request_id,stage,window,source_start,source_end,tensors):
        if self.closed:raise ValueError("capture closed")
        if (side not in ("packed","serial") or request_id not in self.identity["requests"]
                or stage not in STAGES or window not in ("prefix","suffix","body")
                or type(source_start)is not int or type(source_end)is not int
                or not 0<=source_start<source_end<=40960
                or not isinstance(tensors,dict) or set(tensors)!=REQUIRED[stage]):
            raise ValueError("exact paired stage/window coordinates and fields required")
        key=(side,request_id,stage,window)
        if key in self.keys:raise ValueError("duplicate actual stage")
        if len(self.records)>=self.max_records:raise ValueError("record bound")
        snapshots={};cost=0
        for name,value in tensors.items():
            if self.bytes+cost+value.numel()*4>self.max_bytes:
                raise ValueError("byte bound before CPU snapshot allocation")
            # Explicit detached CPU FP32 clone. The caller selects head0 before
            # entering here; an accelerator tensor is never serialized directly.
            value=value.detach().to(device="cpu",dtype=torch.float32).clone().contiguous()
            array=value.numpy()
            if (array.dtype!=np.float32 or array.ndim>5 or array.size==0
                    or not np.isfinite(array).all()):
                raise ValueError("finite nonempty bounded sampled tensor required")
            cost+=array.nbytes
            if self.bytes+cost>self.max_bytes:raise ValueError("byte bound")
            snapshots[name]=array.copy()
        self.records.append(dict(side=side,request_id=request_id,stage=stage,window=window,
            source_start=source_start,source_end=source_end,tensors=snapshots))
        self.keys.add(key);self.bytes+=cost

    def discard(self):
        self.records.clear();self.keys.clear();self.bytes=0;self.closed=True

    def seal_failure(self,root,*,failed_request_id):
        if self.closed or failed_request_id not in self.identity["requests"] or not self.records:
            raise ValueError("nonempty actual failed group required")
        root=Path(root)
        if not root.is_absolute() or not root.parent.is_dir() or root.parent.is_symlink():
            raise ValueError("absolute existing non-symlink capture parent required")
        root.mkdir(mode=0o700,exist_ok=False)
        manifest=dict(schema="hypic-first-divergence/v1",identity=self.identity,
            failed_request_id=failed_request_id,sampling="declared head0 only; not full tensor equivalence",
            max_bytes=self.max_bytes,max_records=self.max_records,payload_bytes=self.bytes,records=[])
        for i,record in enumerate(self.records):
            meta={k:v for k,v in record.items() if k!="tensors"};meta["tensors"]={}
            for name,array in record["tensors"].items():
                filename=f"{i:02d}-{name}.npy";path=root/filename
                with path.open("xb") as stream:
                    np.save(stream,array,allow_pickle=False);stream.flush();os.fsync(stream.fileno())
                meta["tensors"][name]=dict(file=filename,sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                    shape=list(array.shape),dtype="float32",nbytes=int(array.nbytes),file_bytes=path.stat().st_size)
            manifest["records"].append(meta)
        raw=(json.dumps(manifest,sort_keys=True,separators=(",",":"))+"\n").encode()
        with (root/"manifest.json").open("xb") as stream:
            stream.write(raw);stream.flush();os.fsync(stream.fileno())
        fd=os.open(str(root),os.O_RDONLY)
        try:os.fsync(fd)
        finally:os.close(fd)
        digest=hashlib.sha256(raw).hexdigest();self.discard()
        return dict(root=str(root),manifest_sha256=digest,records=len(manifest["records"]),
                    payload_bytes=manifest["payload_bytes"])

def selected_capture(identity,*,enabled=False):
    if type(enabled)is not bool:raise ValueError("explicit diagnostic switch required")
    return FirstDivergenceCapture(identity) if enabled else None
