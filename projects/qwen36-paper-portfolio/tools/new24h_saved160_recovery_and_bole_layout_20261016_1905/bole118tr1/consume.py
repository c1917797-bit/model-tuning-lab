"""Independent Devices[] consumer of all eight TND paged raw records."""
import dataclasses
import json
from pathlib import Path
import adapter as A
import reference as R
from run_component import checked,write


def native_boundary(t, raw):
    # Independently reconstruct call operands from original paged CPU inputs.
    cpu=raw['inputs'];length=raw['owner']['length'];pages=(length+3+127)//128
    k=t.zeros((pages,1,128,256),dtype=t.bfloat16);v=t.zeros_like(k)
    for pos in range(length+3):
        if pos<length:
            k[pos//128,0,pos%128]=cpu['kc'][raw['table'][pos//128],pos%128,0]
            v[pos//128,0,pos%128]=cpu['vc'][raw['table'][pos//128],pos%128,0]
        else:
            k[pos//128,0,pos%128]=cpu['k'][pos-length,0]
            v[pos//128,0,pos%128]=cpu['v'][pos-length,0]
    mask=t.ones((1,1,3,pages*128),dtype=t.bool)
    for node in range(3):
        for pos in range(pages*128):
            mask[0,0,node,pos]=not(pos<=length or (node>0 and pos==length+node))
    expected=dict(query=cpu['q'].permute(1,0,2).unsqueeze(0).contiguous(),
                  key=k,value=v,atten_mask=mask,block_table=t.arange(pages,dtype=t.int32).reshape(1,-1))
    A.need(set(raw['native_before'])==set(raw['native_after'])==set(raw['native_layout'])==set(expected),'actual native operand set')
    A.need(raw['native_call']==dict(input_layout='BNSD',block_size=128,actual_seq_lengths=[3],actual_seq_lengths_kv=[length+3],num_key_value_heads=1,num_heads=6,scale=256**-.5,sparse_mode=raw['mode'],pre_tokens=2147483647,next_tokens=2147483647,inner_precise=2),'actual native scalar kwargs')
    for name,x in expected.items():
        A.need(A.bits(t,x,raw['native_before'][name])and A.bits(t,x,raw['native_after'][name]),'actual native operand bytes/immutability '+name)
        # Permute retains the stride of the singleton KV axis even though contiguous.
        stride=[32768,256,256,1] if name in('key','value') else list(x.stride())
        A.need(raw['native_layout'][name]==dict(shape=list(x.shape),stride=stride,dtype=str(x.dtype)),'actual native operand layout '+name)
    return True


def evaluate(t,raw):
    A.need(raw['schema']=='bole.paged-tree-raw/v1'and raw['primary']is None,'actual successful raw required')
    cpu=raw['inputs'];owner=A.Owner(**raw['owner']);table=raw['table']
    case=raw['case'];A.need(type(case)is int and 0<=case<4 and type(raw['mode'])is int and raw['mode']in(0,1),'frozen case/mode')
    A.need(owner==A.Owner('component-request',1,7,(0,127,128,131)[case],0)
           and tuple(table)==(3,1,4)and raw['accepted_child']==(None,1,-1,2)[case],
           'frozen geometry/ownership/path')
    A.validate(t,owner,cpu['q'],cpu['k'],cpu['v'],cpu['kc'],cpu['vc'],table)
    r64=R.sequential(t,cpu['q'],cpu['k'],cpu['v'],cpu['kc'],cpu['vc'],table,owner.length,dtype=t.double)
    r32=R.sequential(t,cpu['q'],cpu['k'],cpu['v'],cpu['kc'],cpu['vc'],table,owner.length,dtype=t.float32)
    result=R.assess(t,raw['output'],r64,r32)
    result['native_operand_bytes_layout_immutable']=native_boundary(t,raw)
    child=raw['accepted_child'];A.need(child is None or type(child)is int and child in(-1,1,2),'selected path')
    path=[]if child is None else [0]+([]if child==-1 else [child])
    ek=cpu['kc'].clone();ev=cpu['vc'].clone()
    # Independent logical-position walk, not adapter.commit or adapter.slots.
    for offset,node in enumerate(path):
        pos=owner.length+offset;page=table[pos//128];within=pos%128
        ek[page,within]=cpu['k'][node];ev[page,within]=cpu['v'][node]
    result['accepted_scatter_and_inactive_bitwise']=A.bits(t,ek,raw['after_k'])and A.bits(t,ev,raw['after_v'])
    expected=dataclasses.asdict(dataclasses.replace(owner,length=owner.length+len(path),version=owner.version+1))
    result['owner_publication_exact']=raw['committed_owner']==expected
    # Independently verify actual scratch prefix and node cells; padding must stay zero.
    sk=t.zeros_like(raw['scratch_k']);sv=t.zeros_like(raw['scratch_v'])
    A.need(sk.shape==sv.shape==((owner.length+3+127)//128,128,1,256)
           and sk.dtype==sv.dtype==t.bfloat16,'exact scratch shape/dtype')
    for pos in range(owner.length):
        sk.view(-1,1,256)[pos]=cpu['kc'][table[pos//128],pos%128]
        sv.view(-1,1,256)[pos]=cpu['vc'][table[pos//128],pos%128]
    sk.view(-1,1,256)[owner.length:owner.length+3]=cpu['k']
    sv.view(-1,1,256)[owner.length:owner.length+3]=cpu['v']
    result['scratch_prefix_nodes_padding_bitwise']=A.bits(t,sk,raw['scratch_k'])and A.bits(t,sv,raw['scratch_v'])
    mask=t.ones((3,owner.length+3),dtype=t.bool);mask[:,:owner.length+1]=False
    mask[1,owner.length+1]=False;mask[2,owner.length+2]=False
    result['actual_mask_exact']=A.bits(t,mask,raw['actual_mask'])
    result['component_pass']=all(result[k]is True for k in
        ('component_pass','accepted_scatter_and_inactive_bitwise','owner_publication_exact',
         'scratch_prefix_nodes_padding_bitwise','actual_mask_exact'))
    return result


def run(t,sr,stage_ref,out):
    checked(sr)
    stage=json.loads(checked(stage_ref).read_bytes())
    A.need(stage['schema']=='bole.paged-tree-stage/v1'and stage['source']==sr and
           stage['NPU']is True and stage['qualified']is False,'actual source-bound diagnostic stage')
    A.need([(r['case'],r['mode'])for r in stage['rows']]==[(c,m)for c in range(4)for m in(0,1)],'exact eight rows')
    rows=[]
    for r in stage['rows']:
        A.need(r['primary']is None,'preserved native call failure; no qualification')
        raw=t.load(checked(r['raw']),map_location='cpu',weights_only=False)
        before=t.load(checked(r['before']),map_location='cpu',weights_only=False)
        A.need(raw['source']==before['source']==sr and raw['case']==r['case']and raw['mode']==r['mode'],'raw source/index')
        A.need(raw['owner']==before['owner']and raw['table']==before['table']and raw['accepted_child']==before['accepted_child'],'before/after metadata')
        for name in ('q','k','v','kc','vc'):
            A.need(A.bits(t,raw['inputs'][name],before['inputs'][name]),'saved before operand bytes')
        value=evaluate(t,raw);rows.append(dict(case=r['case'],mode=r['mode'],raw=r['raw'],metrics=value))
    value=dict(schema='bole.paged-tree-independent/v1',source=sr,actual_stage=stage_ref,rows=rows,
               component_pass=all(r['metrics']['component_pass']for r in rows),qualified=False,model_ready=False)
    
    if out is not None:write(out,value)
    return value
