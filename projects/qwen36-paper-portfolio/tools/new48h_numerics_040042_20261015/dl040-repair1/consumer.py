"""Independent reopened saved frame/precast diagnosis; never admission."""
import argparse,json,math,sys
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import io_contract as C
from frame import bits,unpack,FIELDS,CAPTURE_FIELDS,transparency
def metrics(T,a,b):
 a,b=a.double(),b.double();C.need(a.shape==b.shape,'diagnostic same shape');den=max(float(b.abs().max()),1e-30);return dict(peak=float((a-b).abs().max())/den,l2=float((a-b).norm())/max(float(b.norm()),1e-30))
def main():
 if '--execute'not in sys.argv:print('disabled');return 0
 p=argparse.ArgumentParser(allow_abbrev=False);p.add_argument('--execute',action='store_true')
 for k in('source-ref','result-ref','output'):p.add_argument('--'+k,required=True)
 a=p.parse_args();sr,rr=json.loads(a.source_ref),json.loads(a.result_ref);m=C.source(sr);stage=C.obj(rr);C.need(stage['source']==sr and stage['authority']==m['authority_ref']and stage['stage']=='numeric'and stage['steps']==stage['records']==1 and stage['NPU']is True and stage['observation_complete']is True and stage['primary']is None,'actual one-frame producer stage ABI')
 p040=C.obj(stage['actual_result']);C.need(p040['source']==sr and p040['saved_raw']==m['saved_raw_ref']and p040['batch']==16 and p040['steps']==p040['records']==1,'actual complete16 frame, not request10 slice');C.need(not list(Path('/dev').glob('davinci*')),'actual Devices[] independent consumer')
 import torch as T
 T.set_num_threads(1);raw=T.load(C.checked(m['saved_raw_ref']),map_location='cpu',weights_only=False);wire=T.load(C.checked(p040['raw']),map_location='cpu',weights_only=False);cap,i,slots=unpack(T,raw)
 C.need(wire['source']==sr and wire['saved_raw']==m['saved_raw_ref']and all(bits(T,wire['before'][n],cap['before'][n])for n in CAPTURE_FIELDS),'independent original complete seven-field capture-before join')
 guards=[bits(T,a,wire['guard_after'][n][j])for n,v in wire['guard_before'].items()for j,a in enumerate(v)]
 checks=transparency(T,raw,wire['before'],wire['outputs'],wire['after'],wire['inputs'],wire['inputs_after'],guards,wire['pointers_before'],wire['pointers_after']);C.need(checks==wire['transparency']==p040['transparency'],'independently recomputed transparency')
 R=C.load(m['files']['oracle.py'],'_040_scalar_CPU64');D=C.load(m['files']['direct_round.py'],'_040_exact_integer_RNE');pre=wire['actual_precast_FP32'];actual=wire['outputs']['production'];finite=bool(T.isfinite(pre).all());cast_exact=finite and bits(T,D.round_bf16(T,pre.double()),wire['outputs']['debug']);rows=[]
 for row,slot in enumerate(slots):
  before=R.restore(T,cap['before'],slot);expected,truth=R.advance(T,before,i,row,scale=128**-.5);after=R.restore(T,wire['after']['production'],slot);native=raw['native_state'][slot].double();q=i['query'][row].double().repeat_interleave(3,dim=0)*(128**-.5)
  ca_read=T.einsum('hvk,hk->hv',after,q);na_read=T.einsum('hvk,hk->hv',native,q);point,diag=D.peer_error(T,actual[row],truth);nativeout=raw['native_output'][row];state=metrics(T,after,expected)
  target=D.round_bf16(T,truth);delta=(actual[row].float()-target.float()).abs();top=T.topk(delta.flatten(),min(8,int((delta>0).sum()))).indices.tolist();cells=[]
  for index in top:
   h,v=index//128,index%128;got=float(actual[row,h,v]);want=float(target[h,v]);pc=float(pre[row,h,v]);tr=float(truth[h,v]);mid=(got+want)/2
   cells.append(dict(index=[row,h,v],slot=slot,actual=got,target=want,precast_FP32=pc,CPU64=tr,midpoint=mid,precast_minus_midpoint=pc-mid,truth_minus_midpoint=tr-mid,cast_cell_distance=abs(got-want),actual_after_readout_CPU64=float(ca_read[h,v]),native_after_readout_CPU64=float(na_read[h,v])))
  rows.append(dict(request=row,slot=slot,before_length=cap['before']['length'][slot,:,0].tolist(),CPU64_RNE_output_error=point,CPU64_uncast=diag,actual_precast_CPU64=metrics(T,pre[row],truth),actual_precast_after_state_readout=metrics(T,pre[row],ca_read),native_after_state_readout=metrics(T,na_read,truth),native_peer=metrics(T,actual[row],nativeout),state=state,original_RNE_gate_pass=point<=.00303,original_state_gate_pass=state['l2']<=7.92e-7,cells=cells))
 complete=all(checks.values())and finite and cast_exact
 result=dict(schema='deltalog.single-frame-sidecar-independent/v040',source=sr,authority=m['authority_ref'],actual_result=rr,producer=stage['actual_result'],saved_raw=m['saved_raw_ref'],records=1,requests=16,steps=1,observation_complete=True,primary=None,transparency=checks,actual_precast_finite=finite,actual_FP32_to_direct_RNE_exact=cast_exact,rows=rows,pass_gate=complete,diagnostic_complete=complete,qualification=False,lifecycle_gate_pass=False,model_ready=False,NPU=False,old_failed160=m['failed160_owner_ref'],old_thresholds=dict(output=.00303,state=7.92e-7),scope='conditioned actual-before single-frame discrimination, not new numerical admission')
 C.write(a.output,result);return 0
if __name__=='__main__':raise SystemExit(main())
