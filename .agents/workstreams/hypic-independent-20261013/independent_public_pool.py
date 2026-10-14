"""Independent bounded public-material pool; not yet a serving integration."""
from collections import OrderedDict
from contextlib import contextmanager
import threading
import hashlib,json
def complete_material_copies(tensors):
    # Conservative first implementation: finish each producing device before
    # another request/stream can observe cloned material. Optimize only after
    # event-based readiness has its own device evidence.
    devices={v.device for v in tensors.values() if v.device.type=="npu"}
    if devices:
        import torch
        for device in devices:torch.npu.synchronize(device)
def material_key(model_identity,implementation_identity,token_ids,public_context_identity):
    if not model_identity or not implementation_identity or not public_context_identity or not token_ids:
        raise ValueError("complete identity and nonempty tokens required")
    return hashlib.sha256(json.dumps([model_identity,implementation_identity,list(token_ids),public_context_identity],separators=(',',':')).encode()).hexdigest()
class PublicPool:
    def __init__(self,capacity_bytes,*,on_eviction=None):
        if on_eviction is not None and not callable(on_eviction):raise ValueError("eviction observer must be callable")
        self.on_eviction=on_eviction
        if capacity_bytes<=0:raise ValueError("positive capacity required")
        self.capacity=capacity_bytes;self.used=0;self.entries=OrderedDict();self.lock=threading.RLock();self.generation=0
    def publish(self,key,tensors):
        size=sum(v.numel()*v.element_size() for v in tensors.values())
        if not tensors or size>self.capacity:raise ValueError("material exceeds pool")
        # Public data cannot alias the producer's private write buffers.
        data={k:v.detach().clone() for k,v in tensors.items()}
        complete_material_copies(data)
        with self.lock:
            if key in self.entries:raise ValueError("immutable material already published")
            need=self.used+size-self.capacity;victims=[]
            for candidate,e in self.entries.items():
                if need<=0:break
                if not e['pins']:victims.append(candidate);need-=e['size']
            if need>0:raise BufferError("all capacity pinned; publication unchanged")
            for candidate in victims:
                victim=self.entries.pop(candidate);self.used-=victim['size']
                if self.on_eviction is not None:
                    self.on_eviction({'key':candidate,'generation':victim['generation'],
                                      'size_bytes':victim['size']})
            self.generation+=1
            self.entries[key]={'data':data,'size':size,'pins':0,'generation':self.generation}
            self.used+=size
            return self.generation
    @contextmanager
    def acquire_private(self,key):
        with self.lock:
            entry=self.entries[key];entry['pins']+=1;self.entries.move_to_end(key)
        try:
            # Request relocation/composition must never write into public tensors.
            private={k:v.clone() for k,v in entry['data'].items()}
            complete_material_copies(private)
            yield entry['generation'],private
        finally:
            with self.lock:entry['pins']-=1
