"""Untimed first actual decode: original13arg production plus compact debug.

The production kernel retains its original full arena/actual slot. Only the
independent debug replay uses compact1 and must match actual selected six-state
and output bytes. Wholeinactive is separately checked from actual full storage.
"""
import contextvars
import functools
import hashlib
import io
import json
import os
from pathlib import Path

import live_adapter as V
from byteaudit import Store

FIELDS=('base','k_log','u_log','lambda_log','decay','length')
INPUTS=('query','key','value','g','beta')
CORE=contextvars.ContextVar('dl_firstdecode_actual_core',default=None)
RAW_CAP=512*1024**2
CONTROL_RESERVE=16*1024**2

def need(v,s):
    if not v:raise V.Refusal(s)

def bits(t,a,b):
    return a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))

def ptr(t):
    return dict(pointer=t.data_ptr(),storage_pointer=t.untyped_storage().data_ptr(),storage_bytes=t.untyped_storage().nbytes(),offset=t.storage_offset(),shape=list(t.shape),stride=list(t.stride()),dtype=str(t.dtype),device=str(t.device))

class Collector:
    def __init__(self,lazy,bridge,root_factory,source_ref,model_source_ref,production_ref,debug_ref,checked):
        self.lazy,self.bridge=lazy,bridge
        self.root_factory=root_factory;self.source=source_ref;self.model_source=model_source_ref
        self.production_ref,self.debug_ref=production_ref,debug_ref;self.checked=checked
        self.root=None;self.store=None;self.phase=None;self.epoch=None
        self.rows=[];self.raw_used=0;self.control_used=0;self.prefill_control=None;self.boundaries={};self.ghosts={};self.active_op=False
        self.production=None;self.debug=None
        self.dispatch=self._dispatch  # stable bound object; don't compare fresh descriptors
    @property
    def t(self):return self.lazy.reader.torch
    def cpu(self,t):return t.detach().cpu().clone()
    def write(self,name,value):
        need(self.root is not None,'actual registered worker root')
        p=self.root/name
        body=(json.dumps(value,sort_keys=True,allow_nan=False)+'\n').encode()
        need(self.control_used+len(body)<=CONTROL_RESERVE,'complete control JSON within reserved16MiB before exclusive write')
        need(self.raw_used+self.control_used+len(body)+(self.store.used if self.store is not None else 0)<=self.worker_cap,'actual total worker allocated7.5GiB before control write')
        with p.open('xb') as f:f.write(body);f.flush();os.fsync(f.fileno())
        self.control_used+=len(body)
        return self.file_ref(p)
    def file_ref(self,p):
        h=hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda:f.read(1048576),b''):h.update(b)
        return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())
    def save(self,name,value):
        p=self.root/name
        # Only one compact record is buffered, never the wholepool baseline.
        # Know the exact serialized size before writing under the hard raw cap.
        buffer=io.BytesIO();self.t.save(value,buffer)
        need(buffer.tell()<=16*1024**2 and self.raw_used+buffer.tell()<=RAW_CAP,'complete compact record/raw cap before exclusive write')
        need(self.raw_used+buffer.tell()+self.control_used+(self.store.used if self.store is not None else 0)<=self.worker_cap,'actual total worker allocated7.5GiB before raw write')
        with p.open('xb') as f:f.write(buffer.getbuffer());f.flush();os.fsync(f.fileno())
        buffer.close()
        r=self.file_ref(p);self.raw_used+=r['bytes'];need(self.raw_used<=RAW_CAP,'complete selected raw512MiB worker cap; retain failure, no truncation')
        return r
    def begin(self,epoch,kind):
        need(self.epoch is None or self.phase=='native-prefill','one exact prefill then firstdecode')
        if self.root is None:
            root,worker_cap=self.root_factory(epoch)
            need(type(worker_cap) is int and worker_cap==15*1024**3//2 and worker_cap<=8*1024**3,'exact allocated7.5GiB within unchanged absolute8GiB worker ceiling')
            root=Path(root);need(root.parent.is_dir() and not root.exists() and not any(x.is_symlink() for x in(root,*root.parents)),'source-owned absent worker leaf')
            root.mkdir(mode=0o700);self.root=root;self.worker_cap=worker_cap
        self.epoch,self.phase=epoch,kind
    def snapshot_before(self,epoch):
        need(epoch is self.epoch and self.phase=='first-decode' and self.store is None,'once at firstdecode boundary only')
        self.store=Store(self.root/'whole-pool-baseline',self.worker_cap-RAW_CAP-CONTROL_RESERVE)
        epoch.prepared_snapshot_calls(self.store)
    def core(self,original):
        @functools.wraps(original)
        def wrapped(T,legacy,gdn,specialized,native,layer,mixed_qkv,b,a,core,emit=None):
            epoch=self.epoch
            need(epoch is not None and V.CURRENT.get() is epoch.frame and T is self.t,'real active all64 admitted epoch before every actual GDN')
            ctx=gdn.get_forward_context();meta=ctx.attn_metadata[layer.prefix]
            epoch.before_core(layer,meta,ctx,self.bridge.manager(epoch.frame.runner))
            c=dict(layer=layer,meta=meta,chunks=[],routed=False,slot=epoch.accepted[(layer.prefix,'base')].gpu_rows[0])
            need(CORE.get() is None,'one real core at a time');token=CORE.set(c)
            try:out=original(T,legacy,gdn,specialized,native,layer,mixed_qkv,b,a,core,emit=emit)
            finally:CORE.reset(token)
            if self.phase=='native-prefill':
                need(not c['routed'] and len(c['chunks'])==1 and meta.num_prefills==1 and meta.num_decodes==0,'real single unchanged native prefill')
                chunk=c['chunks'][0];T.npu.synchronize();base=self.cpu(layer.kv_cache[1][c['slot']:c['slot']+1])
                need(bits(T,base,chunk['state'].transpose(-1,-2).contiguous()),'actual physical prefill SSM writeback equals original native final state')
                need(bits(T,self.cpu(core).reshape(1,2048,12,128),chunk['output']),'actual complete returned prefill core equals original native chunk output')
                aux=legacy._ensure_aux(T,layer)
                need(all(bool((aux[n][c['slot']]==0).all()) for n in FIELDS[1:]),'actual prefill private aux reset complete')
                need(layer.prefix in self.bridge.manager(epoch.frame.runner).generation((epoch.generation.request_id,epoch.request)).reset_complete,'actual clear/chunk/writeback completion barrier')
                self.boundaries[layer.prefix]=self.save('prefill-%02d.pt'%len(self.boundaries),dict(state=base,actual_slot=c['slot'],generation=epoch.generation.ordinal,engine_request_id=epoch.generation.request_id,prefix=layer.prefix,source=self.source,model_source=self.model_source,actual_native_clear_chunk_writeback=True,private_aux_zero=True,core_native_chunk_bitwise=True))
            else:need(c['routed'] and not c['chunks'] and meta.num_decodes==1 and meta.num_prefills==0,'one actual13arg decode after native history')
            return out
        return wrapped
    def chunk(self,original):
        @functools.wraps(original)
        def wrapped(*a,**kw):
            c=CORE.get()
            if c is None:return original(*a,**kw)
            need(self.phase=='native-prefill' and not c['chunks'] and kw.get('output_final_state') is True and kw.get('head_first') is False,'sole original native prefill chunk')
            out=original(*a,**kw)
            need(tuple(out[0].shape)==(1,2048,12,128) and tuple(out[1].shape)==(1,12,128,128),'actual unpadded2K native output/state')
            # This clone is a separate small actual state, not a second wholepool.
            ghost=out[1].transpose(-1,-2).contiguous().clone()
            need(ghost.untyped_storage() is not c['layer'].kv_cache[1].untyped_storage(),'native peer isolated from production arena')
            self.ghosts[c['layer'].prefix]=ghost
            c['chunks'].append(dict(output=self.cpu(out[0]),state=self.cpu(out[1])))
            return out
        return wrapped
    def route(self,original):
        @functools.wraps(original)
        def wrapped(T,layer,**kw):
            c=CORE.get();need(self.phase=='first-decode' and c is not None and c['layer'] is layer and not c['routed'],'one actual route within admitted firstdecode core')
            need(layer.prefix in self.boundaries and layer.prefix in self.ghosts,'independent original native prefill boundary required')
            actual=kw['ssm_state_indices'].detach().cpu().flatten().tolist()
            need(actual==[c['slot']] and T is self.t and kw['state'] is layer.kv_cache[1],'actual committed selected production slot')
            c['routed']=True;c['arguments']=kw;c['sidecar']=None
            ghost=self.ghosts[layer.prefix];native_before=self.cpu(ghost)
            self.active_op=True
            try:out=original(T,layer,**kw)
            finally:self.active_op=False
            need(c['sidecar'] is not None,'actual13arg production and debug invocation happened')
            native_out=T.ops._C_ascend.npu_recurrent_gated_delta_rule(query=kw['query'].contiguous(),key=kw['key'].contiguous(),value=kw['value'].contiguous(),g=kw['g'].contiguous(),beta=kw['beta'].contiguous(),state=ghost,scale=kw['scale'],actual_seq_lengths=kw['actual_seq_lengths'].contiguous(),ssm_state_indices=T.zeros_like(kw['ssm_state_indices']).contiguous())
            T.npu.synchronize();s=c['sidecar']
            raw=dict(actual_NPU=True,actual_ids=actual,scale=kw['scale'],inputs={n:s['before'][i] for i,n in enumerate(INPUTS)},input_after={n:s['after'][i] for i,n in enumerate(INPUTS)},before={n:s['before'][i] for i,n in enumerate(FIELDS,5)},after={n:s['after'][i] for i,n in enumerate(FIELDS,5)},output=self.cpu(out),native_before=native_before,native_after=self.cpu(ghost),native_output=self.cpu(native_out),pointer_before=s['original_input_pointers_before'],pointer_after=s['original_input_pointers_after'],compact_sidecar=s)
            need(bits(T,raw['output'],s['production_output']),'actual returned production output bytes')
            rr=self.save('decode-%02d.pt'%len(self.rows),raw)
            self.rows.append(dict(prefix=layer.prefix,layer_idx=layer.layer_idx,actual_slot=c['slot'],generation=self.epoch.generation.ordinal,engine_request_id=self.epoch.generation.request_id,raw=rr,prefill=self.boundaries[layer.prefix],production_library=self.production_ref,debug_library=self.debug_ref))
            return out
        return wrapped
    def _dispatch(self,*args):
        T=self.t;c=CORE.get()
        need(self.active_op and c is not None and len(args)==13 and self.production is not None,'actual original13arg production only')
        need(tuple(args[0].shape)==(1,4,128) and args[12].detach().cpu().flatten().tolist()==[c['slot']] and args[11].detach().cpu().flatten().tolist()==[0,1],'actual C1 source operands/individual lengths')
        index=args[12].flatten().long()
        clones=[x.clone() if i not in range(5,11) else x.index_select(0,index).clone() for i,x in enumerate(args)]
        clones[12]=T.zeros_like(args[12])
        before=[self.cpu(x) for x in clones];before[12]=self.cpu(args[12])
        debug_before=[self.cpu(x) for x in clones]
        # Original inputs retain actual values/sequence, but debug id=compact0.
        pbefore=[ptr(x) for x in args];dbefore=[ptr(x) for x in clones]
        back=T.full((12*128+256,),13.,dtype=T.float32,device=args[0].device);side=back[128:-128].reshape(1,12,128);side.fill_(float('nan'));guard_before=self.cpu(T.cat((back[:128],back[-128:])))
        out=self.production(*args);debug_out=self.debug(*clones,side);T.npu.synchronize()
        after=[self.cpu(x) if i not in range(5,11) else self.cpu(x.index_select(0,index)) for i,x in enumerate(args)]
        debug_after=[self.cpu(x) for x in clones]
        pair=all(bits(T,before[i],debug_before[i]) and bits(T,after[i],debug_after[i]) for i in range(12)) and bits(T,self.cpu(out),self.cpu(debug_out))
        immutable=all(bits(T,before[i],after[i]) for i in(0,1,2,3,4,11,12))
        pafter=[ptr(x) for x in args];dafter=[ptr(x) for x in clones]
        guard_after=self.cpu(T.cat((back[:128],back[-128:])))
        guard=bool((guard_before==13).all() and (guard_after==13).all())
        record=dict(before=before,after=after,debug_before=debug_before,debug_after=debug_after,production_output=self.cpu(out),debug_output=self.cpu(debug_out),actual_precast_FP32=self.cpu(side),production_debug_bitwise=pair,inputs_unchanged=immutable,sidecar_redzones_pass=guard,sidecar_guards_before=guard_before,sidecar_guards_after=guard_after,pointers_before=pbefore,pointers_after=pafter,debug_pointers_before=dbefore,debug_pointers_after=dafter,original_input_pointers_before={n:pbefore[i] for i,n in enumerate(INPUTS)},original_input_pointers_after={n:pafter[i] for i,n in enumerate(INPUTS)},compact_debug_id=0,actual_production_slot=c['slot'])
        c['sidecar']=record
        need(pair and immutable and guard and pbefore==pafter and dbefore==dafter,'actual fullarena production vs compact debug selected six-state/output transparency')
        return out
    def activate(self,R):
        need(self.production is None and R._OP is not None,'one actual activation after original component admission')
        self.checked(self.production_ref);self.checked(self.debug_ref)
        T=self.t;T.ops.load_library(self.debug_ref['path']);ns='qwen36_deltalog_split_scale_sidecar_v051'
        need(T._C._dispatch_has_kernel_for_dispatch_key(ns+'::decode','PrivateUse1') and any(self.debug_ref['path'] in s for s in Path('/proc/self/maps').read_text().splitlines()),'actual debug14arg DSO mapped/privateuse1')
        self.production=R._OP;self.debug=getattr(T.ops,ns).decode;R._OP=self.dispatch
    def end_prefill(self,epoch,mirror):
        need(epoch is self.epoch and self.phase=='native-prefill','actual first prefill completion')
        required={p for p,row in self.lazy.value.layers.items() if row[0]=='GDN'}
        need(epoch.consumed_GDN==required==set(self.boundaries)==set(self.ghosts) and required<=epoch.generation.reset_complete,'complete48 native boundary/physicalwriteback/reset controls')
        mirror.finish_step(epoch.frame.runner)
        self.prefill_control=self.write('PREFILL-COMPLETE.json',dict(source=self.source,model_source=self.model_source,all48=sorted(required),request=epoch.generation.request_id,generation=epoch.generation.ordinal,prefill_tokens=2048,query_kind='native-prefill',wholeinactive_checked=False,candidate_decode_calls=0,qualified=False))
    def end_decode(self,epoch,summary):
        required={p for p,row in self.lazy.value.layers.items() if row[0]=='GDN'}
        need(epoch is self.epoch and epoch.closed and {r['prefix'] for r in self.rows}==required and len(self.rows)==48,'all48 one actual decode before final publication')
        pools=self.lazy.value.pools;pool_ids={id(p):i for i,p in enumerate(pools)}
        selections=[]
        for (prefix,role),s in epoch.accepted.items():
            v=s.view;selections.append(dict(prefix=prefix,group=v.group,role=role,kind=self.lazy.value.layers[prefix][0],pool=pool_ids[id(v.pool)],geometry=v.geometry.__dict__,cpu_rows=s.cpu_rows,gpu_rows=s.gpu_rows,physical_rows=s.physical_rows,physical_block_tokens=s.physical_block_tokens,kernel_block_tokens=s.kernel_block_tokens,writes=s.writes))
        metadata=dict(pools=[dict(index=i,pointer=p.pointer,nbytes=p.nbytes) for i,p in enumerate(pools)],selections=selections)
        report=dict(schema='deltalog.actual-first-decode-all64/v1',source=self.source,model_source=self.model_source,domain=self.lazy.value.domain.__dict__,namespace_pid=os.getpid(),request=epoch.generation.request_id,generation=epoch.generation.ordinal,prefill_tokens=2048,decode_query_tokens=1,computed_tokens_before_decode=2048,rows=self.rows,footprint=summary,active_metadata=metadata,baseline_manifest=[dict(pool=i,name=epoch.before[id(pool)],baseline=dict(path=str(self.store.records[epoch.before[id(pool)]][0]),bytes=self.store.records[epoch.before[id(pool)]][1],sha256=self.store.records[epoch.before[id(pool)]][3]),comparison=self.file_ref(self.store.root/(epoch.before[id(pool)]+'.comparison.json'))) for i,pool in enumerate(pools)],raw_bytes=self.raw_used,model_numeric_qualified=False,reuse_qualified=False,long160_qualified=False,graph=False,performance_qualified=False,task_qualified=False,expected_stop='DL_FIRST_DECODE_COMPLETE_OBSERVATION_NOT_MODEL_QUALIFICATION')
        report['storage_budget']=dict(absolute_worker_cap_bytes=8*1024**3,allocated_worker_cap_bytes=self.worker_cap,
            raw_cap_bytes=RAW_CAP,control_cap_bytes=CONTROL_RESERVE,snapshot_bytes=self.store.used,
            controls_before_final_bytes=self.control_used,prefill_control=self.prefill_control)
        self.write('FIRST-DECODE-REPORT.json',report)
