"""Algorithm-specific eager packed batch output seam, default OFF.
No loader/host controller/lease. Actual compiled+owner authority is external.
Capture OFF has no CPU KV snapshots and never invokes original FA.
Capture ON preserves actual pending packed fields for the independent oracle.
"""
import hashlib
import inspect
import json
import os
from pathlib import Path
import tempfile
import traceback

FLAG="QWEN36_KIVI_PACKED_QKAV_OWNED_SEAM"
TIMING_FLAG="QWEN36_KIVI_OBSERVER_OFF_TIMING"
FIELDS=("key_codes","key_scales","key_minima","value_codes","value_scales","value_minima","key_residual","value_residual")
PRE_REFS={"before_bind","actual_format","post_rope","slot_owner"}
CHUNK=1024**2
MAX_POOL=192*1024**2

def need(v,message):
    if not v:raise ValueError(message)

def bound(ref,maximum=8*1024**2):
    need(type(ref)is dict and set(ref)=={"path","bytes","sha256"},"exact3 raw Ref")
    p=Path(ref["path"])
    need(p.is_absolute()and not p.is_symlink()and p.resolve()==p and
         type(ref["bytes"])is int and 0<ref["bytes"]<=maximum and
         type(ref["sha256"])is str and len(ref["sha256"])==64,"actual bounded nonsymlink Ref")
    raw=p.read_bytes()
    need(len(raw)==ref["bytes"]and hashlib.sha256(raw).hexdigest()==ref["sha256"],"actual raw bytes/SHA")
    return raw

def source(module,ref):
    need(Path(module.__file__).resolve()==Path(ref["path"]),"actual loaded module origin")
    bound(ref,1024**2)

def plan_requests(arena,requests,positions,actual_request_type):
    need(type(requests)is tuple and type(positions)is tuple and
         1<=len(requests)==len(positions)<=16,"actual complete batch/positions")
    need(len({r.slot for r in requests})==len(requests),"disjoint actual compact slots")
    rows=[]
    for r,position in zip(requests,positions):
        need(type(r)is actual_request_type and type(position)is int and
             0<=position<33792 and r.length==position and not r.pending,"source-bound live request/one ordered append")
        arena.owned(r)
        need(type(r.slot)is int and 0<=r.slot<16 and type(r.generation)is int and r.generation>=0 and
             type(r.owner)is str and r.owner and type(r.epoch)is int and r.epoch>0,
             "actual assigned owner/slot epoch")
        rows.append({"request_id":r.owner,"slot":r.slot,"epoch":r.epoch,"generation":r.generation,
                     "computed":position})
    return rows

class RawSink:
    """Owned diagnostic streaming publication only, not a resource controller."""
    def __init__(self,root,torch,callback,sequence):
        self.root=Path(root);self.t=torch;self.cb=callback
        need(self.root.is_absolute()and self.root.resolve()==self.root and self.root.is_dir()and
             not self.root.is_symlink()and self.root.is_relative_to("/cache/cch/qwen36-paper-preparation-20261007/lowbit"),
             "actual owned lowbit sink root")
        need(type(sequence)is str and sequence and all(c.isalnum()or c in "-_"for c in sequence),
             "exclusive caller frame name")
        self.sequence=sequence
    def tensor(self,name,tensor):
        total=tensor.numel()*tensor.element_size()
        need(type(total)is int and 0<total<=MAX_POOL and tensor.is_contiguous(),"bounded whole contiguous field")
        flat=tensor.view(self.t.uint8).reshape(-1)
        return self.stream(name,(self.cb.bytes_of(self.t,flat.narrow(0,start,min(CHUNK,total-start)),CHUNK)
                                 for start in range(0,total,CHUNK)),total)
    def stream(self,name,chunks,total):
        need(type(name)is str and name and all(c.isalnum()or c in "-_"for c in name),"actual raw label")
        p=self.root/(self.sequence+"-"+name+".bin")
        need(not p.exists()and not p.is_symlink(),"no overwrite raw destination")
        fd,temp=tempfile.mkstemp(prefix="."+p.name+".pending-",dir=self.root)
        h=hashlib.sha256();count=0
        try:
            with os.fdopen(fd,"wb")as handle:
                for blob in chunks:
                    need(type(blob)is bytes and 0<len(blob)<=CHUNK,"bounded snapshot chunk")
                    handle.write(blob);h.update(blob);count+=len(blob)
                need(count==total,"whole actual field, no selected-byte shrink")
                handle.flush();os.fsync(handle.fileno())
            os.link(temp,p)
            dfd=os.open(self.root,os.O_RDONLY)
            try:os.fsync(dfd)
            finally:os.close(dfd)
        except BaseException:
            # Original partial temp retained; no replacement or experimental deletion.
            raise
        else:os.unlink(temp)
        return {"path":str(p),"bytes":count,"sha256":h.hexdigest()}

class PackedBatch:
    def __init__(self,torch,modules,*,source_refs,device_properties,get_format,qualify,
                 actual_identity,rank,publish,diagnostic=True,model_qualify=None):
        # Pure storage of supplied context. No module import/tensor/kernel/state change here.
        self.t=torch;self.modules=modules;self.refs=source_refs;self.properties=device_properties
        self.format=get_format;self.qualify=qualify;self.identity=actual_identity;self.rank=rank;self.publish=publish
        self.model=None;self.metadata=None;self.arena=None
        need(type(diagnostic)is bool and (diagnostic or callable(model_qualify)),
             "explicit diagnostic mode or independently consumed real model prerequisite")
        self.diagnostic=diagnostic;self.model_qualify=model_qualify
        self.qualified=False;self.qualified_identity=None

    def qualify_boundary(self):
        """Call outside the token loop at installation and native owner changes."""
        self.qualified=False
        self.qualify() # unchanged real compiled/numeric/owned authority
        for name in ("kernel","metadata","lifecycle","callback"):
            source(self.modules[name],self.refs[name])
        ident=self.identity()
        if not self.diagnostic:
            need(os.environ.get(TIMING_FLAG)=="1","separate timing opt-in")
            self.model_qualify() # actual model correctness prerequisite, never made here
        self.qualified_identity=ident;self.qualified=True

    def hot_qualify(self):
        need(self.qualified and self.qualified_identity is not None,
             "real boundary qualification required; no cached default PASS")

    def invalidate(self):
        self.qualified=False

    def append_read(self,arena,requests,query,key,value,positions,*,pre_refs,capture_raw=False,
                    raw_root=None,sequence=None):
        if os.environ.get(FLAG)!="1":return None
        need(os.environ.get("QWEN36_KIVI_PACKED_QKAV_SOURCE_CANDIDATE")=="1","explicit same critical kernel opt-in")
        primary=None;started=False;pub=self.publish
        try:
            need(type(sequence)is str and sequence and all(c.isalnum()or c in "-_"for c in sequence),
                 "actual exclusive layer/frame sequence, never replayed output")
            pub=lambda name,value:self.publish(sequence+"-"+name,value)
            # This actual independent callback must consume compile+numerical+owner lease.
            # It is not permission generated by this source/claimed numeric snapshot.
            if self.diagnostic:self.qualify()
            else:self.hot_qualify()
            k,m,dl,cb=(self.modules[n]for n in("kernel","metadata","lifecycle","callback"))
            if self.diagnostic:
                for name,module in(("kernel",k),("metadata",m),("lifecycle",dl),("callback",cb)):
                    source(module,self.refs[name])
            else:
                need(os.environ.get(TIMING_FLAG)=="1" and capture_raw is False and pre_refs is None,
                     "timing forbids raw snapshots and per-token immutable-file pre_refs")
            need(type(self.rank)is int and self.rank in range(4)and callable(self.identity)and
                 callable(self.publish)and type(capture_raw)is bool,"actual caller identity/sink")
            identity=self.identity() if self.diagnostic else self.qualified_identity
            if self.diagnostic:pub("PACKED-START",{"schema":"kivi.actual-packed-start/v1","rank":self.rank,
                "identity":identity,"source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "query":cb.scalar_tensor(query),"key":cb.scalar_tensor(key),"value":cb.scalar_tensor(value),
                "before_first_cache_write":True,"model_ready":False,"run_authority":False})
            started=True
            rows=plan_requests(arena,requests,positions,dl.Request)
            b=len(rows);t=self.t
            need(type(arena)is dl.CompactArena and tuple(query.shape)==(b,6,256)and
                 tuple(key.shape)==tuple(value.shape)==(b,256),"actual Qwen TP4 complete post-RoPE Q6/KV1/D256 batch")
            need(query.dtype==key.dtype==value.dtype==arena.dtype and arena.dtype in(t.float16,t.bfloat16)and
                 query.device==key.device==value.device==arena.device and
                 all(x.is_contiguous()and self.format(x)==2 for x in(query,key,value)),
                 "actual A16 ND complete post-RoPE input geometry")
            need(self.arena is None or self.arena is arena,"one actual layer arena, not recreated cache per token")
            fn=getattr(t.npu,"is_current_stream_capturing",None)
            need(callable(fn)and fn()is False,"eager only; no Python-on-FULL-replay assumption")
            if self.diagnostic:
                need(type(pre_refs)is tuple and len(pre_refs)==b and
                     all(type(refs)is dict and set(refs)==PRE_REFS for refs in pre_refs),"four actual seam3Refs per request")
                for refs in pre_refs:
                    for ref in refs.values():bound(ref)
            pool=arena.pool
            input_snapshot=None;sink=None
            if capture_raw:
                sink=RawSink(raw_root,t,cb,sequence)
                t.npu.synchronize()
                input_snapshot={"query":sink.tensor("INPUT-Q",query),"key":sink.tensor("INPUT-K",key),
                                "value":sink.tensor("INPUT-V",value)}
                pub("PACKED-INPUT-RAW",dict(input_snapshot,model_ready=False,run_authority=False))
            input_bases={x.untyped_storage().data_ptr()for x in(query,key,value)}
            need(not input_bases.intersection(pool[n].untyped_storage().data_ptr()for n in FIELDS),
                 "ephemeral actual Q/K/V cannot alias packed destination")
            if self.model is None:
                Model=k.build(t,self.modules["triton"],self.modules["tl"],device_properties=self.properties,
                    get_format=self.format,qualify=self.qualify if self.diagnostic else self.hot_qualify)
                self.model=Model()
            tickets=[]
            for i,(r,position)in enumerate(zip(requests,positions)):
                tickets.append(arena.begin(r,key[i:i+1],value[i:i+1],position))
            views=tuple(arena.view(r)for r in requests)
            if self.metadata is None or self.metadata.batch!=b:
                t.npu.synchronize()
                self.metadata=None # obsolete remaps only, no compact/raw pool release
                self.metadata=m.Metadata.create(t,views,capacity=33792,
                    actual_types=(dl.ReadView,dl.CompactArena,dl.Request),graph=False,
                    qualify=self.qualify if self.diagnostic else self.hot_qualify)
            else:self.metadata.refresh(views)
            self.arena=arena
            self.metadata.assert_tensors(query,self.format)
            pending_refs=[]
            for i,(row,r,ticket) in enumerate(zip(rows,requests,tickets)):
                if self.diagnostic:
                    row.update(controls=(r.length+1,len(r.kp)*128,len(r.vp),r.slot),kp=list(r.kp),vp=list(r.vp))
                if self.diagnostic:pending_refs.append(pub("PACKED-PENDING-%02d"%i,{"schema":"kivi.actual-packed-pending/v1",
                    "rank":self.rank,"identity":identity,"owner":row,"ticket":ticket,
                    "model_ready":False,"run_authority":False}))
            snapshots=None;live_alias=None;query_refs=None
            if capture_raw:
                need(sum(pool[n].numel()*pool[n].element_size()for n in FIELDS)<=MAX_POOL,
                     "whole compact capture budget, not a model RAM lease")
                # Real live descriptors recorded BEFORE independent CPU snapshots.
                live_alias={n:cb.scalar_tensor(pool[n])for n in FIELDS}
                t.npu.synchronize()
                snapshots={n:sink.tensor("POOL-"+n,pool[n])for n in FIELDS}
                # Independent oracle must use Q captured BEFORE candidate execution.
                query_refs=[sink.tensor("Q-%02d"%i,query[i])for i in range(b)]
            output=self.model(query,pool,self.metadata)
            t.npu.synchronize()
            self.metadata.assert_live()
            need(tuple(output.shape)==(b,6,256)and output.dtype==query.dtype and output.device==query.device,
                 "whole actual packed attention result")
            if self.diagnostic:
                need(bool(t.isfinite(output).all().item()),"whole finite actual packed attention result")
                need(self.identity()==identity,"same actual worker after kernel/completion")
            for i,(row,r,ticket)in enumerate(zip(rows,requests,tickets)):
                completion=None
                if self.diagnostic:completion=pub("PACKED-READ-COMPLETE-%02d"%i,{"schema":"kivi.actual-packed-read-complete/v1",
                    "rank":self.rank,"identity":identity,"request_id":r.owner,"slot":r.slot,"epoch":r.epoch,
                    "generation":r.generation,"ticket":ticket,"synchronized":True,
                    "read_length":r.length+1,"original_attention_called":False,
                    "model_ready":False,"run_authority":False})
                if capture_raw:
                    row.update(query_ref=query_refs[i],output_ref=sink.tensor("OUTPUT-%02d"%i,output[i]),
                               identity_refs=dict(pre_refs[i],pending_ticket=pending_refs[i],after_read_completion=completion))
                # Only exact actual read completion can authorize this engineering lifecycle commit.
                arena.owned(r);r.read=True;arena.finish(r,ticket)
                need(r.length==positions[i]+1 and not r.pending,"actual append/seal after read")
            if capture_raw:
                frame={"schema":"kivi.actual-packed-qkav-frame/v1",
                    "kernel_source_sha256":self.refs["kernel"]["sha256"],"bits":arena.bits,
                    "dtype":str(query.dtype).split(".")[-1],
                    "pool_geometry":(pool["key_codes"].shape[0],pool["value_codes"].shape[0],pool["key_residual"].shape[0]),
                    "pool_fields":snapshots,"live_alias_descriptors_before_snapshot":live_alias,
                    "snapshot_is_live_alias":False,"whole_prewrite_input_refs":input_snapshot,"rows":rows,"model_ready":False,"run_authority":False}
                pub("PACKED-FRAME",frame)
            # Future actual Attention wrapper must return this and skip original FA/cache update.
            # Qwen's surrounding gate/o_proj remain the real caller, not reimplemented here.
            return output
        except BaseException as error:
            if not self.diagnostic:self.invalidate()
            primary={"type":type(error).__name__,"message":str(error),"traceback":traceback.format_exc()}
            try:pub("PACKED-FAILURE",{"schema":"kivi.actual-packed-failure/v1","primary":primary,
                "started":started,"pending_state_uncertain":True,"model_ready":False,"run_authority":False})
            except BaseException as secondary:
                print(json.dumps({"primary":primary,"secondary_publication":repr(secondary)}),flush=True)
            # No rollback/recycle under async or partially committed uncertainty.
            raise
