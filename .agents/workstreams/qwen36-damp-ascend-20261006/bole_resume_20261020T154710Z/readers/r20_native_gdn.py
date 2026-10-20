"""CPU-only independent native-AR GDN/state/conv chronology diagnosis."""
import argparse,gc,json,sys
from pathlib import Path
P=Path('/opt/host/vnf/austinov/bole-model-fa64-fp16-20261020T154710Z-r20')
sys.path.insert(0,str(P))
import sourceio as C
import oracle112 as O
def bits(t,a,b):
 return a.shape==b.shape and a.dtype==b.dtype and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def metric(t,actual,truth):
 delta=(actual.double()-truth).abs();norm=float(t.linalg.vector_norm(truth))
 relative=float(t.linalg.vector_norm(delta)/max(norm,1e-30));peak=float(delta.max());scale=float(truth.abs().max())
 return dict(peak_abs=peak,relative_l2=relative,passed=bool(t.isfinite(actual).all())and peak<=2e-5+2e-4*scale and relative<=2e-4)
def run(t,sr,ir,out):
 m=C.obj(sr);C.need(m['root']==str(P),'exact actual r20 producer')
 C.need(C.ref(O.__file__)==m['files']['oracle112.py'],'original unchanged independent GDN mathematical reference')
 inputs=C.obj(ir);rows=[];history_errors=[]
 for rank,pair in enumerate(inputs['ranks']):
  receipt=C.obj(pair['receipt']);C.need(receipt['source']==sr and receipt['rank']==rank and receipt['primary']is None,'completed genuine native capture')
  export=t.load(C.checked(pair['raw']),map_location='cpu',weights_only=False);raw=export['payload']
  C.need(raw['source']==sr and raw['rank']==rank,'actual source/rank payload')
  initial={a['layer']:a for a in raw['actual_native_initial_GDN']}
  for path in raw['native']:
   prior={}
   for step_index,step in enumerate(path['steps']):
    for layer in range(64):
     if layer%4==3:continue
     cap=step['context']['captures'][layer];anchor=initial[layer]
     C.need(cap['phase']=='NATIVE_RECURRENT_COMPLETE','actual completed native recurrent operation')
     state_before=cap['state_before'];state_after=cap['state_after'];conv_before=cap['conv_before'];conv_after=cap['conv_after']
     if step_index==0:
      state_history=bits(t,state_before,anchor['initial_native_state'].unsqueeze(0))
      conv_history=bits(t,conv_before,anchor['full_conv_slot'][:,:3])
     else:
      state_history=bits(t,state_before,prior[layer][0]);conv_history=bits(t,conv_before,prior[layer][1])
     prior[layer]=(state_after.clone(),conv_after.clone())
     expected_conv=t.cat((conv_before,cap['inputs'].unsqueeze(0)),dim=1)[:,-3:]
     conv_update=bits(t,conv_after,expected_conv)
     q,k,v,g,beta=cap['normalized_inputs']
     qh=q.permute(0,2,1,3).double().repeat_interleave(3,dim=1)*(128**-.5)
     kh=k.permute(0,2,1,3).double().repeat_interleave(3,dim=1);vh=v.permute(0,2,1,3).double()
     gamma=g.transpose(1,2).double().exp();bh=beta.transpose(1,2).double()
     base=state_before.transpose(-1,-2).double()
     truth,states=O.sequential(t,qh,kh,vh,bh,gamma,base,(-1,))
     actual_state=state_after.transpose(-1,-2)
     C.need(state_after.dtype==t.float32,'original native recurrent state FP32')
     state_metric=metric(t,actual_state,states[0])
     ref_output=truth.permute(0,2,1,3).squeeze(0);actual_output=cap['output']
     C.need(actual_output.dtype==t.bfloat16 and actual_output.shape==ref_output.shape,'original native output BF16')
     error=(actual_output.double()-ref_output).abs()
     output_metric=dict(peak_abs=float(error.max()),pointwise_pass=bool((error<=.001+.01*ref_output.abs()).all()),
      exact_BF16_reference=bits(t,actual_output,ref_output.to(t.bfloat16)))
     identity=dict(rank=rank,path=path['child'],node=step['node'],layer=layer)
     row=dict(**identity,state=state_metric,output=output_metric,state_history=state_history,conv_history=conv_history,conv_update=conv_update)
     rows.append(row)
     if not(state_history and conv_history and conv_update):history_errors.append(identity)
  del raw,export;gc.collect()
 C.need(len(rows)==768,'all4 ranks x4 forwards x48 GDN')
 result=dict(schema='bole.native-ar-independent-gdn-diagnostic/v1',source=sr,inputs=ir,reader=C.ref(__file__),oracle=C.ref(O.__file__),
  frame_count=len(rows),rows=rows,history_errors=history_errors,
  state_failed=[{k:r[k]for k in('rank','path','node','layer')}for r in rows if not r['state']['passed']],
  output_pointwise_failed=[{k:r[k]for k in('rank','path','node','layer')}for r in rows if not r['output']['pointwise_pass']],
  original112_state_limits_unchanged=True,actual_NPU_executed=False,whole_model_qualified=False,final_success=False)
 C.write(out/'ATTRIBUTION.json',result)
 print(json.dumps(dict(frame_count=len(rows),history_errors=len(history_errors),state_failed=len(result['state_failed']),output_pointwise_failed=len(result['output_pointwise_failed']))))
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');ap.add_argument('--source-ref');ap.add_argument('--inputs-ref');ap.add_argument('--output',type=Path);a=ap.parse_args()
 import os
 C.need(a.execute and os.environ.get('ASCEND_RT_VISIBLE_DEVICES')==''and os.environ.get('TORCH_DEVICE_BACKEND_AUTOLOAD')=='0'and not list(Path('/dev').glob('davinci[0-9]*')),'owned Devices[] reader')
 import torch
 run(torch,json.loads(a.source_ref),json.loads(a.inputs_ref),a.output)
if __name__=='__main__':main()

