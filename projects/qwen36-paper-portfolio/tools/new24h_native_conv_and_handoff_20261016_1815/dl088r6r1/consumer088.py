"""No candidate math: independent CPU64 decode/flush plus native source joins."""
import math
from capture088 import FIELDS,CHUNK_SHA
def need(v,s):
 if not v:raise ValueError(s)
def same(t,a,b):return a.dtype==b.dtype and a.shape==b.shape and t.equal(a.contiguous().view(t.uint8),b.contiguous().view(t.uint8))
def relative(t,a,b):
 need(a.shape==b.shape and bool(t.isfinite(a).all()and t.isfinite(b).all()),'finite same-geometry state')
 e=float((a.double()-b.double()).norm());n=float(b.double().norm());return e/n if n else(0. if e==0 else math.inf)
def check(t,R,raw):
 cap=raw['captures']['prefill'];flush=raw['captures']['prefill_flush088'];need(len(cap)==len(flush)==1,'exact actual native/flush receipts missing')
 c=cap[0];z=c['same_initial088'];f=flush[0];p=raw['prefill_slot'];need(z['schema']=='deltalog.actual-same-materialized-native-controls/v088'and len(z['controls'])==2,'two independent actual native calls required')
 need(z['original_chunk_source']['module_file']['sha256']==CHUNK_SHA,'actual native module source')
 need(z['requested_scale']in(None,128**-.5)and z['effective_scale']==128**-.5,'fixed actual readout scale')
 need(f['actual_ids'].flatten().tolist()==[p]and f['reason']=='prefill_initial_state_only','true prefill slot/reset mapping')
 expect=R.restore(t,f['before'],0);err=relative(t,f['after']['base'][0],expect);need(err<=R.STATE_LIMIT,'original independent flush state gate')
 need(all(bool((f['after'][n]==0).all())for n in('length','decay')),'flush metadata reset')
 for name,value in c['inputs'].items():
  if t.is_tensor(value):need(name in z['given_inputs']and same(t,value,z['given_inputs'][name]),'original actual native input missing/changed '+name)
 need(z['given_inputs']['cu_seqlens'].tolist()==[0,64],'original native order')
 expected_initial=f['after']['base'].transpose(-1,-2).contiguous()
 if not raw['prefill_has_initial_state']:expected_initial=t.zeros_like(expected_initial)
 need(same(t,z['given_inputs']['initial_state'],expected_initial),'wrong base/log/head/reset or detached given initial')
 need(same(t,c['output'],z['actual']['output'])and same(t,c['final_state'],z['actual']['state']),'actual shared native result')
 need(bool(t.isfinite(c['output']).all()and t.isfinite(c['final_state']).all()),'finite native visible outputs')
 for row in z['controls']:
  need(row['call']['actual_original_call_returned']is True,'actual independent native call missing')
  for n,v in z['given_inputs'].items():need(n in row['before']and same(t,v,row['before'][n])and same(t,v,row['after'][n]),'native given-input independent join '+n)
  need(same(t,row['output'],c['output'])and same(t,row['state'],c['final_state']),'true sameinput native control bitwise')
 need(same(t,raw['state']['base'][p].transpose(-1,-2).contiguous(),c['final_state'][0]),'actual native final writeback')
 for n in FIELDS[1:]:need(bool((raw['state'][n][p]==0).all()),'aux after native prefill reset')
 return dict(schema='deltalog.sameinitial-component-operational/v088',flush_CPU64_relative_l2=err,flush_state_limit=R.STATE_LIMIT,actual_native_sameinput_bitwise=True,shared_native_is_not_mathematical_truth=True,cross_history_metrics_required=True,qualified=False)
