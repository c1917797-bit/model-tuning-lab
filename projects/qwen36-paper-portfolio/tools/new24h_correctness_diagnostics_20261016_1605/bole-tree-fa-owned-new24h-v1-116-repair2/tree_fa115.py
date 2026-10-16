"""Tree FA inputs and path oracle. No NPU or model imports at module import."""
import math

PARENTS=(-1,0,0,1,1,2,2)


def paths(parents):
    result=[]
    for i,p in enumerate(parents):
        if type(p)is not int or not -1<=p<i:raise ValueError('parent-before-child')
        result.append(([]if p==-1 else result[p])+[i])
    return result


def forbid_mask(t,prefixes,parents,padded_kv):
    path=paths(parents);n=len(parents)
    mask=t.ones((len(prefixes),1,n,padded_kv),dtype=t.bool)
    for b,length in enumerate(prefixes):
        if type(length)is not int or not 0<=length or length+n>padded_kv:raise ValueError('complete actual KV length')
        mask[b,0,:,:length]=False
        for i,ancestors in enumerate(path):
            for j in ancestors:mask[b,0,i,length+j]=False
    return mask.contiguous()


def recipe(t,batch,prefixes,witness=False):
    n=len(PARENTS);d=256;kv=((max(prefixes)+n+31)//32)*32
    g=t.Generator(device='cpu').manual_seed(2610161151+batch+sum(prefixes))
    q=(t.randn((batch,6,n,d),generator=g)*.3).bfloat16()
    k=(t.randn((batch,1,kv,d),generator=g)*.3).bfloat16()
    v=(t.randn((batch,1,kv,d),generator=g)*.3).bfloat16()
    if witness:
        q.zero_();k.zero_();v.zero_()
        for b,length in enumerate(prefixes):
            for j in range(n):v[b,0,length+j,j]=1
    return dict(query=q,key=k,value=v,mask=forbid_mask(t,prefixes,PARENTS,kv),prefixes=list(prefixes),parents=list(PARENTS),scale=d**-.5,actual_seq_lengths=[n]*batch,actual_seq_lengths_kv=[x+n for x in prefixes])


def path_reference(t,raw):
    """Each node gathers only actual prefix+ancestor KV, no packed-mask reuse."""
    q,k,v=(raw[n].double()for n in('query','key','value'))
    batch,hq,n,d=q.shape;hkv=k.shape[1]
    if hq%hkv or d!=k.shape[-1]or v.shape!=k.shape:raise ValueError('exact GQA/QKV shape')
    result=t.empty((batch,hq,n,d),dtype=t.double);path=paths(raw['parents'])
    for b,length in enumerate(raw['prefixes']):
        for head in range(hq):
            kh=head//(hq//hkv)
            for node,ancestors in enumerate(path):
                selected=list(range(length))+[length+j for j in ancestors]
                keys=k[b,kh,selected];values=v[b,kh,selected]
                scores=t.mv(keys,q[b,head,node])*raw['scale']
                probs=(scores-scores.max()).exp();probs=probs/probs.sum()
                result[b,head,node]=t.mv(values.transpose(0,1),probs)
    return result


def call_fia(torch_npu,raw,*,sparse_mode):
    if sparse_mode not in(0,1):raise ValueError('only preregistered complete-mask modes0/1')
    return torch_npu.npu_fused_infer_attention_score(
        query=raw['query'],key=raw['key'],value=raw['value'],
        atten_mask=raw['mask'],actual_seq_lengths=raw['actual_seq_lengths'],
        actual_seq_lengths_kv=raw['actual_seq_lengths_kv'],
        num_heads=6,num_key_value_heads=1,input_layout='BNSD',
        scale=raw['scale'],sparse_mode=sparse_mode,pre_tokens=2147483647,
        next_tokens=2147483647,inner_precise=2)


def score(t,actual,reference):
    if actual.shape!=reference.shape or actual.dtype!=t.bfloat16:raise ValueError('exact BF16 observed output ABI')
    if not bool(t.isfinite(actual).all())or not bool(t.isfinite(reference).all()):raise ValueError('finite oracle/output')
    delta=actual.double()-reference
    return dict(peak_abs=float(delta.abs().max()),relative_l2=float(t.linalg.vector_norm(delta)/t.linalg.vector_norm(reference).clamp_min(1e-30)),preregistered_allclose=bool(t.all(delta.abs()<=.001+.01*reference.abs())))
