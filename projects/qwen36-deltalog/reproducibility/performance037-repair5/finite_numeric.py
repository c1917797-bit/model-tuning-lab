"""Independent saved035 geometry/reference checks; no candidate recurrence."""
import math
FIELDS=('base','k_log','u_log','lambda_log','decay','length')
DIRECT_SHA='60f64d53aae1e126f1a4de244a3cb224facc881e277386bf120d6a5b2988278d'
CONTRACT=dict(schema='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035',output_limit=.00303,state_limit=7.92e-7,direct_round_sha256=DIRECT_SHA,per_request_worst=True,uncast_metrics_diagnostic_only=True,scope='same035-full160-saved-decode-and-FP32-materialization-production-health')
def need(v,m):
 if not v:raise ValueError(m)
def same(torch,a,b):return a.dtype==b.dtype and a.shape==b.shape and torch.equal(a.contiguous().view(torch.uint8),b.contiguous().view(torch.uint8))
def capture(torch,raw,batch):
 need(batch in(1,16)and len(raw['captures']['decode'])==1,'same existing B1/B16 one decode capture')
 c=raw['captures']['decode'][0];i=c['inputs'];ids=i['ssm_state_indices'];seq=i['actual_seq_lengths']
 need(ids.dtype==torch.int32 and ids.shape==(batch,)and ids.tolist()==raw['ids'][:-1].tolist()and len(set(ids.tolist()))==batch,'same actual ordered slots, no duplicated/misbound row')
 need(seq.dtype==torch.int32 and seq.shape==(batch+1,)and seq.tolist()==[0]+[1]*batch,'native individual sequence ABI, not arange')
 need(type(i['scale'])in(int,float)and math.isclose(i['scale'],128**-.5,rel_tol=0,abs_tol=1e-12),'fixed source scale')
 specs=(('query',torch.bfloat16,(batch,4,128)),('key',torch.bfloat16,(batch,4,128)),('value',torch.bfloat16,(batch,12,128)),('g',torch.float32,(batch,12)),('beta',torch.bfloat16,(batch,12)))
 need(all(i[n].dtype==dt and i[n].shape==shape and i[n].device.type=='cpu'and bool(torch.isfinite(i[n]).all())for n,dt,shape in specs),'same source Hq4/Hv12/D128 dtype/finite input')
 need(c['output'].dtype==torch.bfloat16 and c['output'].shape==(batch,12,128),'saved actual BF16 readout shape')
 need(all(type(x)is int and 0<=x<c['before']['base'].shape[0]for x in ids.tolist()),'actual slot bounds')
 return c,i,ids.tolist()
def reference(torch,R,D,before,after,inputs,actual,slots):
 need(actual.dtype==torch.bfloat16 and actual.shape==(len(slots),12,128),'replay actual BF16 exact shape')
 rows=[]
 for j,slot in enumerate(slots):
  initial=R.restore(torch,before,slot);need(bool(torch.isfinite(initial).all()),'active initial state finite, dead log not scanned')
  expected,truth=R.advance(torch,initial,inputs,j,scale=128**-.5)
  output_error,diag=D.peer_error(torch,actual[j],truth)
  current=R.restore(torch,after,slot);state_error=float((current-expected).norm()/max(float(expected.norm()),1e-30))
  need(all(math.isfinite(v)and v>=0 for v in(state_error,output_error))and state_error<=7.92e-7 and output_error<=.00303,'same independent035 state/direct-RNE request gate')
  rows.append(dict(slot=slot,row=j,state_error=state_error,output_error=output_error,uncast_CPU64_output_error=diag['uncast_peak'],BF16_RNE_floor=diag['rounding_floor_peak'],request_pass=True))
 return rows
