"""Independent original138 CPU64 ledger and strict saved one-frame memory evidence."""
import argparse,json,math,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
def pointer_binding(meta,t):
 size=t.element_size();extent=1+sum((n-1)*s for n,s in zip(meta['shape'],meta['stride']))
 return meta['data_ptr']>0 and meta['storage_ptr']>0 and meta['storage_offset']>=0 and meta['data_ptr']%32==0 and meta['storage_ptr']+meta['storage_offset']*size==meta['data_ptr']and meta['shape']==list(t.shape)and meta['stride']==list(t.stride())and meta['dtype']==str(t.dtype)and meta['device']=='npu:0'and all(s>=0 for s in meta['stride'])and (meta['storage_offset']+extent)*size<=meta['storage_nbytes']
def byte_transition_invariants(torch,R,before,after,ids):
 from precast import bits
 inv=R.invariant(torch,before,after,ids)
 inv['untouched_bitwise']=all(bits(torch,before[k][s],after[k][s])for k in before for s in range(before['base'].shape[0])if s not in ids)
 inv['append_base_unchanged']=all(bits(torch,before['base'][s],after['base'][s])for s in ids if int(before['length'][s,0,0])<7)
 return inv
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','result-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,rr=json.loads(a.source_ref),json.loads(a.result_ref);m=C.source(sr);stage=C.obj(rr)
 C.need(not list(Path('/dev').glob('davinci*'))and stage['source']==sr and stage['NPU']is True and stage['observation_complete'],'Devices[] exact actual stage')
 v=C.obj(stage['actual_result']);C.need(v['scope']=='single-original137-guard-v020'and v['source']==sr and v['NPU']is True and v['rows']==[],'exact single actual call pair, not325')
 import torch
 torch.set_num_threads(1);from precast import regression_truth,evaluate,bits
 R=C.load(m['files']['oracle.py'],'guard020_reference');S=C.load(m['files']['scenarios.py'],'guard020_scenarios')
 def tensor(r):return torch.load(C.checked(r),map_location='cpu',weights_only=True)
 def state(r):return {k:tensor(t)for k,t in r.items()}
 ir,original,truth,ledger=regression_truth(torch,C,m,R,S);rg=v['regression'];x=tensor(rg['raw']);C.need(x['original_raw']==ir and original['event']['step']==137,'frozen original137')
 before,db,after,da=map(state,(x['before'],x['debug_before'],x['after'],x['debug_after']));oldbefore=state(original['before']);oldafter=state(original['after'])
 checks=dict(before_exact_original=all(bits(torch,before[k],oldbefore[k])and bits(torch,db[k],oldbefore[k])for k in oldbefore),after_exact_original=all(bits(torch,after[k],oldafter[k])for k in oldafter),prod_debug_state_bytes=all(bits(torch,after[k],da[k])for k in after),prod_debug_output_bytes=bits(torch,x['candidate_output'],x['debug_output']),output_exact_original=bits(torch,x['candidate_output'],original['candidate_output']),inputs_exact=all(bits(torch,x['inputs_after'][k],t)for k,t in original['inputs'].items()),sequence_exact=bits(torch,x['sequence_after'],original['sequence']))
 ids=original['event']['ids'];checks['inactive_bytes']=all(bits(torch,before[k][s],after[k][s])for k in before for s in range(before['base'].shape[0])if s not in ids)
 checks['metadata_padding_bytes']=bits(torch,before['lambda_log'][:,:,7:],after['lambda_log'][:,:,7:])and all(bits(torch,before[k][:,:,1:],after[k][:,:,1:])for k in('decay','length'));checks['slot_guards']=all(bool((after[k][-2:]==13).all())for k in after)
 red=x['sidecar_backing'];y=x['actual_precast_FP32'];checks['side_redzones']=red.dtype==torch.float32 and red.numel()==y.numel()+256 and bool((red[:128]==13).all()and(red[-128:]==13).all())and bits(torch,red[128:-128].view_as(y),y)
 ptr=pointer_binding
 pre,post=x['pointers_before'],x['pointers_after'];checks['all_pointers_stable']=pre==post
 C.need(set(pre)=={'states','inputs','sequence','sidecar','side_back'}and set(pre['states'])=={'prod','debug'},'complete pointer inventory')
 checks['pointer_tensor_binding']=all(ptr(pre['states'][arm][k],t)for arm,st in(('prod',before),('debug',db))for k,t in st.items())and all(ptr(pre['inputs'][k],t)for k,t in original['inputs'].items())and ptr(pre['sequence'],original['sequence'])and ptr(pre['side_back'],red)
 sm=pre['sidecar'];checks['side_view_binding']=sm['shape']==list(y.shape)and sm['stride']==list(y.stride())and sm['dtype']=='torch.float32'and sm['device']=='npu:0'and sm['storage_ptr']==pre['side_back']['storage_ptr']and sm['storage_offset']==128 and sm['data_ptr']==sm['storage_ptr']+512
 q=evaluate(torch,y,x['candidate_output'],truth);ratios=[]
 for s,request in zip(ids,original['event']['requests']):
  t=R.restore(torch,after,s);C.need(bool(torch.isfinite(t).all()and torch.isfinite(ledger[request]).all()),'finite logical live state/CPU64 truth')
  ratio=float((t-ledger[request]).norm()/ledger[request].norm().clamp_min(1e-30));C.need(math.isfinite(ratio),'finite relative state');ratios.append(ratio)
 rel=max(ratios);inv=byte_transition_invariants(torch,R,before,after,ids)
 passed=q['passed']and rel<=R.STATE_LIMIT and all(inv.values())and all(checks.values())
 C.need(passed==rg['passed']and abs(rel-rg['state_relative_l2'])<1e-12,'independent consumer/producer verdict agrees')
 C.write(a.output,dict(schema='deltalog.independent-lifecycle-consumption/v007',scope='single-original137-guard-v020',source=sr,actual_result=rr,raw_producer=stage['actual_result'],raw=rg['raw'],records=[dict(original_raw=ir,checks=checks,precast=q,state_relative_l2=rel,passed=passed)],expected_records=1,observation_complete=True,pass_gate=passed and v['primary']is None,coverage=dict(NPU_calls=2,frames=1,previous324_not_rerun=True,full_lifecycle_qualified=False),NPU=False,model_ready=False,graph_qualified=False,actual_runtime_copy_qualified=False))
 return 0
if __name__=='__main__':raise SystemExit(main())
