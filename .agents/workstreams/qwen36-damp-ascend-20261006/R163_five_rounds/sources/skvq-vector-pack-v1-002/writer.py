"""Fixed-out SKVQ writer prototype: cold allocation, actual capture-time binding.

Each arithmetic output has original A16 dtype; integer packing remains int32.
Only existing Torch operators are used. 'out=' support and hidden backend scratch
on the actual Ascend image remain pending until the actual matrix succeeds.
"""
import hashlib,os
DONOR_SHA='4fe983904f436496c4d8ff74517f0b330bf8cf8942c09ed01c5f653ff9ed9081'
ENV='SKVQ_TASK_MATH_PROTOTYPE_ENABLE'
def need(ok,why):
    if not ok:raise ValueError(why)
def meta(x):
    return (tuple(x.shape),tuple(x.stride()),str(x.dtype),str(x.device),x.storage_offset(),x.data_ptr(),x.untyped_storage().nbytes())
class WriterResources:
    def __init__(self,torch,pool,layouts,writer_bytes,*,dtype,device,bits=2,capacity=40960,max_batch=16):
        need(os.environ.get(ENV)=='1','fixed writer defaults OFF')
        need(hashlib.sha256(writer_bytes).hexdigest()==DONOR_SHA,'exact original writer authority')
        need(type(bits)is int and bits in(2,4)and capacity==40960 and max_batch==16,'registered actual domain')
        need(dtype in(torch.float16,torch.bfloat16),'original A16 storage')
        self.t=torch;self.pool=pool;self.layouts=layouts;self.dtype=dtype;self.device=device;self.bits=bits;self.capacity=capacity
        self.storage=[];self.capture_bindings={};self.views={};self.constants={};self.groups={};self.pool_flat={}
        def empty(shape,dt=dtype):
            x=torch.empty(shape,dtype=dt,device=device);self.storage.append(x);return x
        def const(values,dt):
            x=torch.tensor(values,dtype=dt,device=device);self.storage.append(x);return x
        self.empty=empty
        # Source-qualified fix: constants and 0D views exist before GLOBAL capture.
        factors=const([1<<(bits*(8//bits-1-j))for j in range(8//bits)],torch.int32)
        self.pack_factors=tuple(factors[j]for j in range(8//bits))
        self.pack_factor_bank=factors.view(1,1,8//bits)
        # All16 batch views share these buffers; actual graph execution is serial.
        self.base={}
        for name in('length','start','stop','slot','safe_slot','safe_length','oldstart','oldstop','newlength','newstart','newstop','target','epoch','count','tmpi'):
            self.base[name]=empty((16,),torch.int64)
        for name in('cmp','valid','seal'):
            self.base[name]=empty((16,),torch.bool)
        for name in('good','unique','bad','errorok'):
            self.base[name]=empty((1,),torch.bool)
        self.base['errorcode']=empty((1,),torch.int32)
        self.base['duplicate']=empty((16,16),torch.bool)
        for name in('token','prior','edge_index'):
            self.base[name]=empty((16,133),torch.int64)
        for name in('mask','active','fresh_mask'):
            self.base[name]=empty((16,133),torch.bool)
        for name in('oldedge','gathered','newedge'):
            self.base[name]=empty((16,133,256))
        for name in('seed','smoothed','permuted'):
            self.base[name]=empty((16,256))
        self.base['post']=empty((16,4),torch.int32)
        # Invalid device controls must not reach the unchanged reader as an OOB
        # address. This poisoned output is never eligible: sticky error survives
        # and the existing output fence must reject the complete step.
        self.base['quarantine']=const([[1,1,1,0]for _ in range(16)],torch.int32)
        self.edge=const(list(range(133)),torch.int64).view(1,133)
        self.eye=const([[i==j for j in range(16)]for i in range(16)],torch.bool)
        for axis in('K','V'):
            l=layouts[axis];l.validate();p=pool[axis]
            width=sum((b-a+8//bits-1)//(8//bits)for a,b in zip(l.starts,l.starts[1:]))
            need(tuple(p['payload'].shape)==(16,capacity,width),'actual axis pool geometry')
            for name,shape,dt in(('payload',(16,capacity,width),torch.uint8),('scales',(16,capacity,4),dtype),
              ('zero_points',(16,capacity,4),dtype),('edges',(16,133,256),dtype)):
                x=p[name]
                need(tuple(x.shape)==shape and x.dtype==dt and x.device==device and x.is_contiguous()and x.storage_offset()==0,'actual fixed writer pool dtype/device/root storage')
            self.pool_flat[axis]={n:p[n].view(-1,p[n].shape[-1])for n in('payload','scales','zero_points')}
            self.constants[axis]={'perm':const(l.permutation,torch.int64),'smooth':const(l.smooth,dtype),'clip':const(l.clip,dtype)}
            axis_base={'payload':empty((16,width),torch.uint8),'scales':empty((16,4)),'zeros':empty((16,4)),
              'old_payload':empty((16,width),torch.uint8),'chosen_payload':empty((16,width),torch.uint8),
              'old_scales':empty((16,4)),'chosen_scales':empty((16,4)),'old_zeros':empty((16,4)),'chosen_zeros':empty((16,4))}
            self.base[axis]=axis_base;self.groups[axis]=[];offset=0;n=8//bits
            for a,z in zip(l.starts,l.starts[1:]):
                count=z-a;w=(count+n-1)//n
                g={'a':a,'z':z,'width':w,'offset':offset,'low':empty((16,)),'high':empty((16,)),
                  'step':empty((16,)),'norm':empty((16,count)),'ints':empty((16,w*n),torch.int32),
                  'packed':empty((16,w),torch.int32),'weighted':empty((16,w,n),torch.int32)}
                self.groups[axis].append(g);offset+=w
        # Construct all metadata-only views BEFORE capture.
        for b in range(1,17):
            s={k:v[:b]if k not in('good','unique','bad','errorok','errorcode')else v for k,v in self.base.items()if k not in('K','V')}
            s['duplicate']=self.base['duplicate'][:b,:b];s['eye']=self.eye[:b,:b]
            s['seed3']=s['seed'].view(b,1,256)
            s['groups']={};s['axis']={}
            for axis in('K','V'):
                s['axis'][axis]={k:v[:b]for k,v in self.base[axis].items()};s['groups'][axis]=[]
                for g in self.groups[axis]:
                    v={k:(x[:b]if hasattr(x,'shape')else x)for k,x in g.items()}
                    v['input']=s['permuted'][:,g['a']:g['z']]
                    v['lowcol']=v['low'][:,None];v['stepcol']=v['step'][:,None]
                    v['ints_live']=v['ints'][:,:g['z']-g['a']];v['ints3']=v['ints'].view(b,g['width'],n)
                    s['groups'][axis].append(v)
            self.views[b]=s
        # Remove the only allocation helper from live resources.
        del self.empty
    def ledger(self):
        seen={}
        for x in self.storage:
            p=x.untyped_storage();seen[p.data_ptr()]=p.nbytes()
        return dict(explicit_scratch_and_constants_bytes=sum(seen.values()),unique_storages=len(seen),
          allocations=[dict(storage_data_ptr=p,storage_nbytes=n)for p,n in sorted(seen.items())],
          hidden_operator_workspace_verified=False,actual_graph_peak_verified=False)
    def bind(self,key,value,controls,row_epochs,slot_epochs,error,*,context):
        # ONLY host metadata/Python views: do not call a Torch operator here.
        b=key.shape[0];need(type(b)is int and 1<=b<=16,'actual tail without padding')
        need(tuple(key.shape)==tuple(value.shape)==(b,1,256),'actual capture post-RoPE KV geometry')
        need(key.dtype==value.dtype==self.dtype and key.device==value.device==self.device,'actual capture KV dtype/device')
        for x,shape,dt in((controls,(b,4),self.t.int32),(row_epochs,(b,),self.t.int64),(slot_epochs,(16,),self.t.int64),(error,(1,),self.t.int32)):
            need(tuple(x.shape)==shape and x.dtype==dt and x.device==self.device and x.is_contiguous(),'exact stable controls/epochs/error')
        capturing=context.capturing;mode=context.cudagraph_runtime_mode.name;d=context.batch_descriptor
        need(type(capturing)is bool and ((capturing and mode=='FULL')or(not capturing and mode=='NONE')),'actual source-bound capture or explicit warmup context')
        need(d.num_tokens==d.num_reqs==b and d.uniform is True,'actual exact-B uniform decode descriptor')
        signature=(meta(key),meta(value),meta(controls),meta(row_epochs),meta(slot_epochs),meta(error))
        if capturing:
            need(b not in self.capture_bindings,'one actual capture binding per B; never reuse a warmup plan')
            self.capture_bindings[b]=signature
        return BoundWriter(self,key,value,controls,row_epochs,slot_epochs,error,b,capturing,signature)
    def bind_eager(self,key,value,controls,row_epochs,slot_epochs,error,*,context,actual_rows,native_query_tokens):
        # Mixed NONE has no uniform graph descriptor. Indices are actual native
        # query rows, not fake capture lanes; caller owns any counted gather.
        need(context.capturing is False and context.cudagraph_runtime_mode.name=='NONE','mixed eager only; never graph replay')
        b=key.shape[0]
        need(type(native_query_tokens)is int and 1<=native_query_tokens<=40960,'actual native query extent')
        need(type(actual_rows)in(list,tuple)and len(actual_rows)==b and all(type(i)is int and 0<=i<native_query_tokens for i in actual_rows)and len(set(actual_rows))==b,'exact unique native decode rows')
        need(type(b)is int and 1<=b<=16 and tuple(key.shape)==tuple(value.shape)==(b,1,256),'actual mixed decode KV rows')
        need(key.dtype==value.dtype==self.dtype and key.device==value.device==self.device,'actual mixed A16 KV')
        for x,shape,dt in((controls,(b,4),self.t.int32),(row_epochs,(b,),self.t.int64),(slot_epochs,(16,),self.t.int64),(error,(1,),self.t.int32)):
            need(tuple(x.shape)==shape and x.dtype==dt and x.device==self.device and x.is_contiguous(),'actual mixed controls/epochs/error')
        signature=(meta(key),meta(value),meta(controls),meta(row_epochs),meta(slot_epochs),meta(error))
        return BoundWriter(self,key,value,controls,row_epochs,slot_epochs,error,b,False,signature)
    def prefill_slot(self,slot,key,value,*,context,assert_live):
        # Full prefill remains outside capture. Small fixed tiles are deliberately
        # correctness-first: T=38912 takes2432 tiles per axis, cost is NOT qualified.
        need(context.capturing is False and context.cudagraph_runtime_mode.name=='NONE','prefill only outside capture')
        assert_live();length=key.shape[0]
        need(type(slot)is int and 0<=slot<16 and type(length)is int and 1<=length<=38912,'owned slot and actual prefill leaves2048 budget')
        need(tuple(key.shape)==tuple(value.shape)==(length,1,256),'actual unpadded prefill KV')
        need(key.dtype==value.dtype==self.dtype and key.device==value.device==self.device,'actual prefill A16/device')
        start=min(5,length);stop=max(start,length-128)
        for axis,real in(('K',key),('V',value)):
            p=self.pool[axis]
            for begin in range(start,stop,16):
                end=min(begin+16,stop);b=end-begin;assert_live()
                plan=BoundWriter(self,None,None,None,None,None,None,b,False,None)
                plan.s['seed'].copy_(real[begin:end,0,:]);plan.quantize(axis);stage=plan.s['axis'][axis]
                for name,part in(('payload','payload'),('scales','scales'),('zero_points','zeros')):
                    p[name][slot,begin:end].copy_(stage[part])
            p['edges'][slot].zero_();p['edges'][slot,:start].copy_(real[:start,0,:])
            p['edges'][slot,start:start+length-stop].copy_(real[stop:,0,:])
        assert_live()
        return [length,start,stop,slot]
class BoundWriter:
    def __init__(self,r,key,value,ct,re,se,error,b,capturing,signature):
        self.r=r;self.key=key;self.value=value;self.ct=ct;self.re=re;self.se=se;self.error=error;self.b=b
        self.capturing=capturing;self.signature=signature;self.s=r.views[b]
    def quantize(self,axis):
        t=self.r.t;s=self.s;c=self.r.constants[axis];out=s['axis'][axis];maximum=(1<<self.r.bits)-1;n=8//self.r.bits
        t.mul(s['seed'],c['smooth'],out=s['smoothed'])
        t.index_select(s['smoothed'],1,c['perm'],out=s['permuted'])
        for gi,g in enumerate(s['groups'][axis]):
            t.amin(g['input'],dim=1,out=g['low']);t.amax(g['input'],dim=1,out=g['high'])
            t.mul(g['low'],c['clip'],out=g['low']);t.mul(g['high'],c['clip'],out=g['high'])
            t.sub(g['high'],g['low'],out=g['step']);t.div(g['step'],maximum,out=g['step']);t.clamp_min(g['step'],1e-5,out=g['step'])
            t.sub(g['input'],g['lowcol'],out=g['norm']);t.div(g['norm'],g['stepcol'],out=g['norm'])
            t.clamp(g['norm'],0,maximum,out=g['norm']);t.round(g['norm'],out=g['norm'])
            g['ints'].zero_();g['ints_live'].copy_(g['norm'])
            t.mul(g['ints3'],self.r.pack_factor_bank,out=g['weighted'])
            t.sum(g['weighted'],dim=2,dtype=t.int32,out=g['packed'])
            out['payload'][:,g['offset']:g['offset']+g['width']].copy_(g['packed'])
            out['scales'][:,gi].copy_(g['step']);out['zeros'][:,gi].copy_(g['low'])
    def launch(self):
        # Every Tensor-producing operator is explicit out= or an in-place copy.
        t=self.r.t;s=self.s;ct=self.ct;cap=self.r.capacity
        for i,n in enumerate(('length','start','stop','slot')):s[n].copy_(ct[:,i])
        t.clamp(s['slot'],0,15,out=s['safe_slot']);t.clamp(s['length'],1,cap-1,out=s['safe_length'])
        t.clamp(s['safe_length'],max=5,out=s['oldstart']);t.sub(s['safe_length'],128,out=s['oldstop']);t.maximum(s['oldstart'],s['oldstop'],out=s['oldstop'])
        t.add(s['safe_length'],1,out=s['newlength']);t.clamp(s['newlength'],max=5,out=s['newstart'])
        t.sub(s['newlength'],128,out=s['newstop']);t.maximum(s['newstart'],s['newstop'],out=s['newstop'])
        t.index_select(self.se,0,s['safe_slot'],out=s['epoch']);s['valid'].fill_(True)
        for op,a,z in((t.ge,s['length'],1),(t.lt,s['length'],cap),(t.ge,s['slot'],0),(t.lt,s['slot'],16),
          (t.eq,s['start'],s['oldstart']),(t.eq,s['stop'],s['oldstop']),(t.gt,self.re,0),(t.eq,self.re,s['epoch'])):
            op(a,z,out=s['cmp']);t.logical_and(s['valid'],s['cmp'],out=s['valid'])
        t.ne(s['slot'][:,None],s['slot'][None,:],out=s['duplicate']);t.logical_or(s['duplicate'],s['eye'],out=s['duplicate'])
        # duplicate view can be noncontiguous for B<16: reduce in two dimensions.
        t.all(s['duplicate'],dim=1,out=s['cmp']);t.all(s['cmp'],dim=0,keepdim=True,out=s['unique'])
        t.all(s['valid'],dim=0,keepdim=True,out=s['good']);t.logical_and(s['good'],s['unique'],out=s['good'])
        t.eq(self.error,0,out=s['errorok']);t.logical_and(s['good'],s['errorok'],out=s['good'])
        t.logical_not(s['good'],out=s['bad']);s['errorcode'].copy_(s['bad']);self.error.bitwise_or_(s['errorcode'])
        t.gt(s['newstop'],s['oldstop'],out=s['seal']);t.eq(s['newstart'],s['oldstart'],out=s['cmp'])
        t.logical_and(s['seal'],s['cmp'],out=s['seal']);t.logical_and(s['seal'],s['good'],out=s['seal'])
        e=self.r.edge;t.lt(e,s['newstart'][:,None],out=s['mask']);t.sub(e,s['newstart'][:,None],out=s['token']);t.add(s['token'],s['newstop'][:,None],out=s['token'])
        t.where(s['mask'],e,s['token'],out=s['token']);t.lt(s['token'],s['oldstart'][:,None],out=s['mask'])
        t.sub(s['token'],s['oldstop'][:,None],out=s['prior']);t.add(s['prior'],s['oldstart'][:,None],out=s['prior'])
        t.where(s['mask'],s['token'],s['prior'],out=s['prior']);t.clamp(s['prior'],0,132,out=s['prior'])
        t.add(s['newstart'],s['newlength'],out=s['count']);t.sub(s['count'],s['newstop'],out=s['count'])
        t.lt(e,s['count'][:,None],out=s['active']);t.logical_and(s['active'],s['good'],out=s['active'])
        t.eq(s['token'],s['safe_length'][:,None],out=s['fresh_mask'])
        t.mul(s['safe_slot'],cap,out=s['target']);t.add(s['target'],s['oldstop'],out=s['target'])
        for axis,fresh in(('K',self.key),('V',self.value)):
            p=self.r.pool[axis];o=s['axis'][axis]
            t.index_select(p['edges'],0,s['safe_slot'],out=s['oldedge'])
            t.gather(s['oldedge'],1,s['oldstart'][:,None,None].expand(-1,1,256),out=s['seed3'])
            self.quantize(axis)
            for name,new,old,chosen in(('payload','payload','old_payload','chosen_payload'),('scales','scales','old_scales','chosen_scales'),('zero_points','zeros','old_zeros','chosen_zeros')):
                flat=self.r.pool_flat[axis][name];t.index_select(flat,0,s['target'],out=o[old]);t.where(s['seal'][:,None],o[new],o[old],out=o[chosen]);flat.index_copy_(0,s['target'],o[chosen])
            t.gather(s['oldedge'],1,s['prior'][:,:,None].expand(-1,-1,256),out=s['gathered'])
            t.where(s['fresh_mask'][:,:,None],fresh,s['gathered'],out=s['newedge'])
            t.where(s['active'][:,:,None],s['newedge'],s['oldedge'],out=s['newedge']);p['edges'].index_copy_(0,s['safe_slot'],s['newedge'])
        for i,n in enumerate(('newlength','newstart','newstop','safe_slot')):s['post'][:,i].copy_(s[n])
        t.where(s['good'],s['post'],s['quarantine'],out=ct)
        return ct,self.error
