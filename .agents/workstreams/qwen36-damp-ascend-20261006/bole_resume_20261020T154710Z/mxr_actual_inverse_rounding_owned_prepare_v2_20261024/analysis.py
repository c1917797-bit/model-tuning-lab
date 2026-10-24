"""Actual same-A FP64 cast ABI diagnostic; no GDN/state recomputation."""
import hashlib,json,os,sys,types
from pathlib import Path
DIRECT={"path":"/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-two-residual-model-new24h-v1-098-repair5/direct_round.py","bytes":3378,"sha256":"60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d"}
SCHEMA='mxr.actual-sameA-FP64-BF16-cast-diagnostic/v1'
FALSE=('qualification','performance','task_accuracy','prefill_state_causation_proven','canonical_changed','thresholds_changed','new_NPU_execution')
def need(v,s):
    if not v:raise ValueError(s)
def checked(r):
    p=Path(r['path']);a=p.stat();h=hashlib.sha256()
    need(set(r)=={'path','bytes','sha256'}and p.is_absolute()and p.is_file()and not any(q.is_symlink()for q in(p,*p.parents)),'exact ordinary Ref3')
    with p.open('rb')as f:
        for b in iter(lambda:f.read(2**20),b''):h.update(b)
    z=p.stat();need((a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns)==(z.st_dev,z.st_ino,z.st_size,z.st_mtime_ns)and z.st_size==r['bytes']and h.hexdigest()==r['sha256'],'stable complete pinned bytes');return p
def load(r,name):
    m=types.ModuleType(name);m.__file__=r['path'];exec(compile(checked(r).read_bytes(),r['path'],'exec'),m.__dict__);return m
def digest(torch,t):
    t=t.detach().cpu().contiguous()
    need(bool(torch.isfinite(t).all()),'finite full actual tensor')
    raw=t.view(torch.uint8).numpy().tobytes()
    return dict(shape=list(t.shape),dtype=str(t.dtype),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def aggregate(bits_a,bits_b,shape):
    need(shape==(1,2048,12,64)and len(bits_a)==len(bits_b)==2048*12*64,'full packed comparison ABI')
    byhead=[0]*12;bytile=[[0]*12 for _ in range(32)];examples=[]
    for i,(a,b)in enumerate(zip(bits_a,bits_b)):
        if a!=b:
            token,tail=divmod(i,12*64);head,col=divmod(tail,64)
            byhead[head]+=1;bytile[token//64][head]+=1
            if len(examples)<32:examples.append(dict(index=[0,token,head,col],library_bits=a,integer_RNE_bits=b))
    n=sum(byhead)
    return dict(mismatches=n,per_head=byhead,per_chunk_head=[dict(chunk=c,head=h,mismatches=bytile[c][h])for c in range(32)for h in range(12)],examples=examples,
        classification='ACTUAL_SAME_A_CAST_DIFFERENCE'if n else'NO_CAST_DIFFERENCE_ON_RETAINED_ACTUAL_A',
        next_action='PRE_REGISTER_REFERENCE_BOUNDARY_COMPARISON_NOT_QUALIFICATION'if n else'NO_SAME_A_CAST_CAUSE_EVIDENCE')
def verify_report(r,plan):
    need(r['schema']==SCHEMA and r['input_plan']==plan and r['direct_reference']==DIRECT and r['diagnostic_complete']is True,'exact report/source/plan')
    need(all(r[k]is False for k in FALSE),'diagnostic does not grant qualification or causation')
    need(r['full_integer_RNE_B_anchor']is True and r['same_inverse_object_for_two_casts']is True,'real saved full-B anchor before comparison')
    need(r['anchor_raw']==plan['fixed_inputs']['arms'][2]and r['case']==plan['fixed_inputs']['case'],'actual retained case/arm')
    need(len(r['residuals'])==32 and [x['start']for x in r['residuals']]==list(range(0,2048,64))and all(x['max_residual']<=1e-10 and x['rows']==64 for x in r['residuals']),'unchanged complete original32 inverse residual checks')
    need(len(r['per_head'])==12 and len(r['per_chunk_head'])==384 and [(x['chunk'],x['head'])for x in r['per_chunk_head']]==[(c,h)for c in range(32)for h in range(12)],'all32x12 groups')
    need(all(type(n)is int and 0<=n<=2048*64 for n in r['per_head'])and all(type(x['mismatches'])is int and 0<=x['mismatches']<=4096 for x in r['per_chunk_head']),'strict complete count types')
    need(r['mismatches']==sum(r['per_head'])==sum(x['mismatches']for x in r['per_chunk_head'])and all(r['per_head'][h]==sum(x['mismatches']for x in r['per_chunk_head']if x['head']==h)for h in range(12)),'independent full count joins')
    n=r['mismatches'];need(type(n)is int and len(r['examples'])==min(n,32),'bounded examples, complete counts')
    need(r['classification']==('ACTUAL_SAME_A_CAST_DIFFERENCE'if n else'NO_CAST_DIFFERENCE_ON_RETAINED_ACTUAL_A')and r['next_action']==('PRE_REGISTER_REFERENCE_BOUNDARY_COMPARISON_NOT_QUALIFICATION'if n else'NO_SAME_A_CAST_CAUSE_EVIDENCE'),'strict non-waiver decision')
    for key,dtype,size in [('A','torch.float32',6291456),('inverse','torch.float64',12582912),('saved_B','torch.bfloat16',3145728),('integer_RNE_B','torch.bfloat16',3145728),('library_B','torch.bfloat16',3145728)]:
        d=r['full_tensors'][key];need(set(d)=={'shape','dtype','bytes','sha256'}and d['shape']==[1,2048,12,64]and d['dtype']==dtype and d['bytes']==size and len(d['sha256'])==64 and all(c in '0123456789abcdef'for c in d['sha256']),'full typed tensor digest')
    need(r['full_tensors']['saved_B']==r['full_tensors']['integer_RNE_B'],'bitwise full-B hash anchor')
    need((r['full_tensors']['library_B']==r['full_tensors']['integer_RNE_B'])==(n==0),'all-byte digest/count concordance')
    return r
def analyze(torch,plan):
    C=load(plan['continuous_source'],'_actual_cast_fixed_source');need(C.FIXED==plan['fixed_inputs'],'unchanged fixed real input')
    donor=C.load(C.FIXED['donor'],'_actual_cast_original_frame',{'need','fp','equal','validate_frame'})
    codec=C.load(C.FIXED['codec'],'_actual_cast_original_codec')
    checked(C.FIXED['case']['raw_sidecar']);saved=codec.read(torch,checked(C.FIXED['case']['raw']))
    x=donor.validate_frame(torch,saved);need(x['cu_seqlens'].tolist()==[0,2048],'full native2K source input')
    r=C.FIXED['arms'][2];actual=torch.load(checked(r),map_location='cpu',weights_only=True)
    wanted={k:donor.fp(torch,x[k])for k in('q','k','v','g','beta','initial_state','cu_seqlens')}
    need(actual['arm']=='cpu64_cast'and actual['inputs_after']==wanted and donor.equal(torch,actual['A'],saved['solve']['A']),'retained actual A/normalized input identity')
    A=actual['A'];B=actual['B'];need(A.dtype==torch.float32 and B.dtype==torch.bfloat16 and tuple(A.shape)==tuple(B.shape)==(1,2048,12,64)and A.device.type==B.device.type=='cpu','actual A/B CPU ABI')
    O=load(C.FIXED['metrics'],'_unchanged_actual_A_FP64') # exact full independent module retains required math namespace
    inverse,residuals=O.fp64_reference(torch,A,x['cu_seqlens'].tolist())
    D=load(DIRECT,'_unchanged_integer_RNE')
    direct=D.round_bf16(torch,inverse)
    need(digest(torch,direct)==digest(torch,B),'FIRST full integer-RNE B bitwise saved anchor; reject before library comparison')
    library=inverse.to(torch.bfloat16) # exact same FP64 object; only second cast
    import struct
    raw=lambda t:t.contiguous().view(torch.uint8).numpy().tobytes()
    a=struct.unpack('<%dH'%library.numel(),raw(library));b=struct.unpack('<%dH'%direct.numel(),raw(direct))
    result=dict(schema=SCHEMA,input_plan=plan,case=plan['fixed_inputs']['case'],anchor_raw=r,direct_reference=DIRECT,
        diagnostic_complete=True,full_integer_RNE_B_anchor=True,same_inverse_object_for_two_casts=True,residuals=residuals,
        full_tensors={k:digest(torch,v)for k,v in [('A',A),('inverse',inverse),('saved_B',B),('integer_RNE_B',direct),('library_B',library)]},
        **{k:False for k in FALSE},**aggregate(a,b,tuple(A.shape)))
    verify_report(result,plan);return result
