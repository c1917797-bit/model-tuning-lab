"""CPU FP64/FP32 diagnosis of every retained native-AR FA call."""
import argparse,gc,json,sys
from pathlib import Path
P=Path('/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r20')
sys.path.insert(0,str(P))
import sourceio as C
def bits(t,a,b):
 return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def truth(t,q,k,v,dtype):
 q=q[0,:,0,:].to(dtype);k=k[0,0].to(dtype);v=v[0,0].to(dtype)
 outputs=[]
 for head in range(6):
  logits=k.mv(q[head])*(256**-.5);p=(logits-logits.max()).exp();p/=p.sum()
  outputs.append(v.T.mv(p))
 return t.stack(outputs).reshape(1,6,1,256)
def run(t,sr,ir,out):
 m=C.obj(sr);C.need(m['root']==str(P),'exact immutable r20 producer')
 for reference in m['files'].values():C.checked(reference)
 inputs=C.obj(ir);C.need(inputs['source']==sr and len(inputs['ranks'])==4,'all4 source/rank captures')
 frames=[];rows=[]
 for rank,pair in enumerate(inputs['ranks']):
  receipt=C.obj(pair['receipt']);C.need(receipt['rank']==rank and receipt['source']==sr and receipt['primary']is None and receipt['raw']==pair['raw'],'genuine completed rank capture')
  export=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False);raw=export['payload']
  C.need(raw['source']==sr and raw['rank']==rank and raw['request']['length']==131,'same actual C1/131 request')
  anchors={x['layer']:x for x in raw['initial_FA_pages']}
  for path in raw['native']:
   prior={}
   for step_index,step in enumerate(path['steps']):
    C.need(step['node']==(0 if step_index==0 else path['child']),'actual root/child chronology')
    for layer in range(3,64,4):
     cap=step['context']['captures'][layer];a=anchors[layer];table=list(a['physical_pages'])
     prefix_k=t.stack([a['key'][table.index(table[pos//128]),pos%128,0]for pos in range(131)]).unsqueeze(1)
     prefix_v=t.stack([a['value'][table.index(table[pos//128]),pos%128,0]for pos in range(131)]).unsqueeze(1)
     ak=cap['after_key'];av=cap['after_value']
     C.need(cap['phase']=='NATIVE_FA_COMPLETE'and ak.shape==av.shape==(132+step_index,1,256),'actual completed native AR key length')
     C.need(bits(t,ak[:131],prefix_k)and bits(t,av[:131],prefix_v),'AR prefix equals independently owned actual native prefill pages')
     C.need(bits(t,ak[-1:],cap['key'].reshape(1,1,256))and bits(t,av[-1:],cap['value'].reshape(1,1,256)),'actual last key/value projected for this AR token')
     if step_index:
      C.need(bits(t,ak[:-1],prior[layer][0])and bits(t,av[:-1],prior[layer][1]),'child retains exact preceding root cache')
     else:prior[layer]=(ak.clone(),av.clone())
     q=cap['query'].reshape(1,1,6,256).permute(0,2,1,3).contiguous()
     k=ak.permute(1,0,2).unsqueeze(0).contiguous();v=av.permute(1,0,2).unsqueeze(0).contiguous()
     output=cap['output'];C.need(output.shape==q.shape and output.dtype==t.bfloat16,'actual native output BF16 ABI')
     refs=[truth(t,q,k,v,d)for d in(t.float64,t.float32)]
     metrics=[]
     for ref in refs:
      error=(output.double()-ref.double()).abs()
      metrics.append(dict(pointwise_pass=bool((error<=.001+.01*ref.double().abs()).all()),peak_abs=float(error.max())))
     casts={}
     for name,x in (('query',q),('key',k),('value',v)):
      converted=x.to(t.float16);delta=(converted.double()-x.double()).abs()
      casts[name]=dict(changed=int((delta!=0).sum()),elements=x.numel(),peak_abs=float(delta.max()),
       nonfinite=int((~t.isfinite(converted)).sum()),nonzero_to_zero=int(((x!=0)&(converted==0)).sum()))
     identity=dict(rank=rank,path=path['child'],node=step['node'],layer=layer)
     row=dict(**identity,double=metrics[0],float=metrics[1],fp16_cast=casts)
     rows.append(row);frames.append(dict(**identity,query=q,key=k,value=v,original=output,reference64=refs[0],reference32=refs[1]))
  del raw,export;gc.collect()
 with (out/'FRAMES.pt').open('xb')as f:t.save(frames,f)
 result=dict(schema='bole.native-ar-independent-fa-attribution/v1',source=sr,inputs=ir,
  reader=C.ref(__file__),frame_count=len(rows),rows=rows,
  failed=[{k:r[k]for k in('rank','path','node','layer')}for r in rows if not(r['double']['pointwise_pass']and r['float']['pointwise_pass'])],
  frames=C.ref(out/'FRAMES.pt'),original_pointwise_limits_unchanged=True,
  actual_NPU_executed=False,reference_source='literal per-head FP64/FP32 softmax on exact retained BF16 native-AR inputs',
  whole_model_qualified=False,final_success=False)
 C.need(len(rows)==256,'all4 ranks x2 paths x2 nodes x16 FA')
 C.write(out/'ATTRIBUTION.json',result)
 print(json.dumps(dict(frame_count=len(rows),failed_count=len(result['failed']),failed=result['failed'][:40],frames=result['frames'])))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--inputs-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 C.need(a.execute,'explicit CPU analysis')
 import os
 C.need(os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'owned Devices[] reader')
 import torch
 run(torch,json.loads(a.source_ref),json.loads(a.inputs_ref),a.output)
if __name__=='__main__':main()

