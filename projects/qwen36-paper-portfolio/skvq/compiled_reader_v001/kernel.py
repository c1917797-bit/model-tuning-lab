"""Explicit SKVQ per-token/variable-channel packed QK -> softmax -> AV.
Only JIT-global qualification and masked unsigned conversion reuse KIVI infrastructure.
No KIVI axes, layout, result, model permission or numerical PASS is inherited.
"""
import os
ENV="QWEN36_SKVQ_COMPILED_READER_ENABLE"
def bind_jit_language(actual):
    if globals().setdefault("tl",actual)is not actual:
        raise ValueError("incompatible actual Triton language global")
def build(torch,triton,tl,*,device_properties,validate_nd,qualify):
    if os.environ.get(ENV)!="1":raise ValueError("compiled SKVQ reader defaults OFF")
    qualify()
    aic=device_properties.get("num_aicore");vec=device_properties.get("num_vectorcore")
    if type(aic)is not int or type(vec)is not int or not(0<aic<=65535 and 0<vec<=65535):
        raise ValueError("real core properties; no guessed fallback")
    if not callable(validate_nd):raise ValueError("source-qualified native enum validator required")
    bind_jit_language(tl)
    @triton.jit
    def qk(Q,KC,KS,KZ,KE,KM,CT,S,B:tl.constexpr,LMAX:tl.constexpr,
           WIDTH:tl.constexpr,BITS:tl.constexpr,CORES:tl.constexpr):
        h=tl.arange(0,16);d=tl.arange(0,256);t=tl.arange(0,32)
        tasks=B*tl.cdiv(LMAX,32)
        for task in range(tl.program_id(0),tasks,CORES):
            row=task//tl.cdiv(LMAX,32);token=task%tl.cdiv(LMAX,32)*32+t
            length=tl.load(CT+row*4);start=tl.load(CT+row*4+1)
            stop=tl.load(CT+row*4+2);slot=tl.load(CT+row*4+3)
            middle=(token>=start)&(token<stop)&(token<length)
            byte=tl.load(KM+d*3);shift=tl.load(KM+d*3+1);group=tl.load(KM+d*3+2)
            word=tl.load(KC+(slot*LMAX+token[:,None])*WIDTH+byte[None,:],
                         mask=middle[:,None],other=0).to(tl.uint32)
            code=(word>>shift[None,:])&((1<<BITS)-1)
            scale=tl.load(KS+(slot*LMAX+token[:,None])*4+group[None,:],mask=middle[:,None],other=0)
            low=tl.load(KZ+(slot*LMAX+token[:,None])*4+group[None,:],mask=middle[:,None],other=0)
            # quant_pytorch.mul().add(): EACH intermediate rounds to original A16.
            mul=(code.to(tl.int32).to(tl.float32)*scale.to(tl.float32)).to(KE.dtype.element_ty,fp_downcast_rounding="rtne")
            decoded=(mul.to(tl.float32)+low.to(tl.float32)).to(KE.dtype.element_ty,fp_downcast_rounding="rtne")
            edge=tl.where(token<start,token,start+token-stop)
            dense=tl.load(KE+(slot*133+edge[:,None])*256+d[None,:],
                          mask=(token<length)[:,None]&(~middle)[:,None],other=0)
            key=tl.where(middle[:,None],decoded,dense)
            query=tl.load(Q+row*1536+h[:,None]*256+d[None,:],mask=(h<6)[:,None],other=0)
            score=tl.dot(query,tl.trans(key)).to(Q.dtype.element_ty,fp_downcast_rounding="rtne")
            score=(score.to(tl.float32)*0.0625).to(Q.dtype.element_ty,fp_downcast_rounding="rtne")
            tl.store(S+row*6*LMAX+h[:,None]*LMAX+token[None,:],score,
                     mask=(h<6)[:,None]&(token<length)[None,:])
    @triton.jit
    def softmax(S,CT,P,B:tl.constexpr,LMAX:tl.constexpr,CORES:tl.constexpr):
        ix=tl.arange(0,1024)
        for task in range(tl.program_id(0),B*6,CORES):
            length=tl.load(CT+(task//6)*4);maximum=tl.full((),-float("inf"),tl.float32)
            for first in range(0,length,1024):
                token=first+ix
                x=tl.load(S+task*LMAX+token,mask=token<length,other=-float("inf")).to(tl.float32)
                maximum=tl.maximum(maximum,tl.max(x,0))
            total=tl.full((),0.,tl.float32)
            for first in range(0,length,1024):
                token=first+ix
                x=tl.load(S+task*LMAX+token,mask=token<length,other=-float("inf")).to(tl.float32)
                total+=tl.sum(tl.exp(x-maximum),0)
            for first in range(0,length,1024):
                token=first+ix
                x=tl.load(S+task*LMAX+token,mask=token<length,other=-float("inf")).to(tl.float32)
                prob=(tl.exp(x-maximum)/total).to(P.dtype.element_ty,fp_downcast_rounding="rtne")
                tl.store(P+task*LMAX+token,prob,mask=token<length)
    @triton.jit
    def av(P,VC,VS,VZ,VE,VM,CT,O,B:tl.constexpr,LMAX:tl.constexpr,
           WIDTH:tl.constexpr,BITS:tl.constexpr,CORES:tl.constexpr):
        h=tl.arange(0,8);t=tl.arange(0,32);d=tl.arange(0,32)
        for task in range(tl.program_id(0),B*8,CORES):
            row=task//8;channel=task%8*32+d
            length=tl.load(CT+row*4);start=tl.load(CT+row*4+1)
            stop=tl.load(CT+row*4+2);slot=tl.load(CT+row*4+3)
            byte=tl.load(VM+channel*3);shift=tl.load(VM+channel*3+1);group=tl.load(VM+channel*3+2)
            accum=tl.zeros((8,32),tl.float32)
            for first in range(0,length,32):
                token=first+t;middle=(token>=start)&(token<stop)&(token<length)
                word=tl.load(VC+(slot*LMAX+token[:,None])*WIDTH+byte[None,:],
                             mask=middle[:,None],other=0).to(tl.uint32)
                code=(word>>shift[None,:])&((1<<BITS)-1)
                scale=tl.load(VS+(slot*LMAX+token[:,None])*4+group[None,:],mask=middle[:,None],other=0)
                low=tl.load(VZ+(slot*LMAX+token[:,None])*4+group[None,:],mask=middle[:,None],other=0)
                mul=(code.to(tl.int32).to(tl.float32)*scale.to(tl.float32)).to(VE.dtype.element_ty,fp_downcast_rounding="rtne")
                decoded=(mul.to(tl.float32)+low.to(tl.float32)).to(VE.dtype.element_ty,fp_downcast_rounding="rtne")
                edge=tl.where(token<start,token,start+token-stop)
                dense=tl.load(VE+(slot*133+edge[:,None])*256+channel[None,:],
                              mask=(token<length)[:,None]&(~middle)[:,None],other=0)
                value=tl.where(middle[:,None],decoded,dense).to(tl.float32)
                prob=tl.load(P+row*6*LMAX+h[:,None]*LMAX+token[None,:],
                             mask=(h<6)[:,None]&(token<length)[None,:],other=0).to(tl.float32)
                accum+=tl.sum(prob[:,:,None]*value[None,:,:],1)
            tl.store(O+row*1536+h[:,None]*256+channel[None,:],
                     accum.to(O.dtype.element_ty,fp_downcast_rounding="rtne"),mask=(h<6)[:,None])
    class Reader:
        def __init__(self):
            self.qk=qk;self.softmax=softmax;self.av=av
        def __call__(self,q,pool,controls,*,bits,capacity,assert_live):
            assert_live()
            if q.ndim!=3 or tuple(q.shape[1:])!=(6,256)or q.shape[0]not in(1,16):
                raise ValueError("declared Q6/KV1/D256 B1/B16 only")
            if q.device.type!="npu"or q.dtype not in(torch.float16,torch.bfloat16)or not q.is_contiguous():
                raise ValueError("actual contiguous A16 NPU query")
            validate_nd(q)
            b=q.shape[0]
            if type(capacity)is not int or not(1<=capacity<=33792)or type(bits)is not int or bits not in(2,4):
                raise ValueError("declared exact capacity/bitwidth")
            if tuple(controls.shape)!=(b,4)or controls.dtype!=torch.int32 or not controls.is_contiguous()or controls.device!=q.device:
                raise ValueError("same-device static controls [length,start,stop,slot]")
            validate_nd(controls);slots=pool["K"]["edges"].shape[0]
            spans=[]
            for axis in("K","V"):
                p=pool[axis];width=p["payload"].shape[-1]
                for name,shape,dtype in(("payload",(slots,capacity,width),torch.uint8),
                    ("scales",(slots,capacity,4),q.dtype),("zero_points",(slots,capacity,4),q.dtype),
                    ("edges",(slots,133,256),q.dtype),("map",(256,3),torch.int32)):
                    x=p[name]
                    if tuple(x.shape)!=shape or x.dtype!=dtype or x.device!=q.device or not x.is_contiguous()or x.storage_offset()!=0:
                        raise ValueError("actual disjoint controlled SKVQ plane "+axis+":"+name)
                    validate_nd(x);spans.append((x.data_ptr(),x.data_ptr()+x.untyped_storage().nbytes()))
                if not((bits==2 and 64<=width<=67)or(bits==4 and 128<=width<=131)):
                    raise ValueError("actual bit-specific variable-group packed byte stride")
            if any(not(a[1]<=z[0]or z[1]<=a[0])for i,a in enumerate(spans)for z in spans[i+1:]):
                raise ValueError("all compact/edge/address allocations disjoint")
            score=torch.empty((b,6,capacity),device=q.device,dtype=q.dtype)
            prob=torch.empty_like(score);out=torch.empty_like(q)
            for x in(score,prob,out):validate_nd(x)
            k=pool["K"];v=pool["V"]
            self.qk[(aic,)](q,k["payload"],k["scales"],k["zero_points"],k["edges"],k["map"],controls,score,
                b,capacity,k["payload"].shape[-1],bits,aic,enable_fp_fusion=False)
            self.softmax[(vec,)](score,controls,prob,b,capacity,vec,enable_fp_fusion=False)
            self.av[(vec,)](prob,v["payload"],v["scales"],v["zero_points"],v["edges"],v["map"],controls,out,
                b,capacity,v["payload"].shape[-1],bits,vec,enable_fp_fusion=False)
            assert_live()
            return out,score,prob
    return Reader
