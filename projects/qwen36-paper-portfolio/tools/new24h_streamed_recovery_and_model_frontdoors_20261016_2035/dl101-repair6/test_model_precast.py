"""CPU-only record ABI controls; never NPU or model observations."""
import copy,hashlib,tempfile,unittest
from pathlib import Path
import torch
import tensor_consumer as C

def attach(raw,previous):
 R=C.module();slot=raw['actual_ids'][0]
 before=[];after=[]
 for name in ('base','k_log','u_log','lambda_log','decay','length'):
  b=raw['before'][name];a=raw['after'][name]
  bb=torch.zeros((slot+1,*b.shape[1:]),dtype=b.dtype);aa=bb.clone();bb[slot]=b[0];aa[slot]=a[0];before.append(bb);after.append(aa)
 inp=[raw['inputs'][n].clone()for n in('query','key','value','g','beta')]
 sequence=torch.tensor([0,1],dtype=torch.int32);ids=torch.tensor([slot],dtype=torch.int32)
 b=inp+before+[sequence,ids];a=copy.deepcopy(inp)+after+[sequence.clone(),ids.clone()]
 _,truth=R.advance(torch,previous,raw['inputs'],0,scale=128**-.5)
 ptr=[dict(ptr=x.data_ptr(),shape=list(x.shape),stride=list(x.stride()),offset=x.storage_offset())for x in b]
 raw['sidecar_record']=dict(before=b,debug_before=copy.deepcopy(b),after=a,debug_after=copy.deepcopy(a),production_output=raw['output'].clone(),debug_output=raw['output'].clone(),actual_precast_FP32=truth.unsqueeze(0).float(),pointers_before=ptr,pointers_after=copy.deepcopy(ptr),debug_pointers_before=copy.deepcopy(ptr),debug_pointers_after=copy.deepcopy(ptr),sidecar_guards_before=torch.full((256,),13.),sidecar_guards_after=torch.full((256,),13.))
 return raw

class ActualPrecastControls(unittest.TestCase):
 def fixture(self):
  from test_direct_model_reference import Controls
  return Controls().fixture()
 def test_complete13_argument_record_and_independent_trajectory(self):
  t,R,raw,prev=self.fixture();self.assertTrue(C.decode(t,R,raw,prev,7)[1]['passed'])
 def test_missing_or_corrupt_debug_before_rejected(self):
  for field in('missing','corrupt'):
   t,R,raw,prev=self.fixture()
   if field=='missing':raw['sidecar_record'].pop('debug_before')
   else:raw['sidecar_record']['debug_before'][5][7,0,0,0]=1
   with self.assertRaises((ValueError,KeyError)):C.decode(t,R,raw,prev,7)
 def test_wrong_actual_arena_slot_join_rejected(self):
  t,R,raw,prev=self.fixture();raw['sidecar_record']['before'][12][0]=6;raw['sidecar_record']['debug_before'][12][0]=6
  with self.assertRaises(ValueError):C.decode(t,R,raw,prev,7)
 def test_actual_precast_not_CPU_estimate_or_wrong_shape(self):
  for bad in('shift','shape','dtype','nan'):
   t,R,raw,prev=self.fixture();s=raw['sidecar_record']
   if bad=='shift':s['actual_precast_FP32']+=1
   elif bad=='shape':s['actual_precast_FP32']=s['actual_precast_FP32'][:,:3]
   elif bad=='dtype':s['actual_precast_FP32']=s['actual_precast_FP32'].double()
   else:s['actual_precast_FP32'][0,0,0]=float('nan')
   try:passed=C.decode(t,R,raw,prev,7)[1]['passed']
   except ValueError:passed=False
   self.assertFalse(passed)
 def test_guard_pointer_output_and_full_inactive_state_changes_refuse(self):
  for bad in('guard','pointer','output','inactive','both-inactive','padding-signedzero'):
   t,R,raw,prev=self.fixture();s=raw['sidecar_record']
   if bad=='guard':s['sidecar_guards_after'][0]=0
   elif bad=='pointer':s['pointers_after'][5]['ptr']+=32
   elif bad=='output':s['debug_output'][0,0,0]=1
   elif bad=='inactive':s['debug_after'][5][0,0,0,0]=1
   elif bad=='both-inactive':s['after'][5][0,0,0,0]=1;s['debug_after'][5][0,0,0,0]=1
   else:
    s['after'][9][7,0,1]=-0.;s['debug_after'][9][7,0,1]=-0.;raw['after']['decay'][0,0,1]=-0.
   with self.assertRaises(ValueError):C.decode(t,R,raw,prev,7)
 def test_lossless_codec_preserves_NaN_signedzero_and_budget(self):
  import raw_codec
  with tempfile.TemporaryDirectory()as temp:
   root=Path(temp);store=raw_codec.Store(torch,root,8*1024*1024);v=torch.tensor([float('nan'),-0.,0.]);r=store.write(root/'row.pt',dict(v=v))
   old=raw_codec.install(torch)
   try:out=torch.load(r['path'],weights_only=False)['v'];self.assertTrue(torch.equal(v.view(torch.uint8),out.view(torch.uint8)))
   finally:torch.load=old
   store.cap=store.used
   with self.assertRaises(ValueError):store.write(root/'overflow.pt',dict(v=torch.ones(1000)))
 def test_source_runtime_activate_order_and_unchanged_production(self):
  p=Path(__file__).parent;source=(p/'trace_plugin.py').read_text();self.assertLess(source.index('activate=T.install'),source.index('R.register()'));self.assertLess(source.index('R.register()'),source.index(' activate()'))
  observer=(p/'tensor_observer.py').read_text();self.assertIn('R._OP=dispatch_for(actual_op[0])',observer);self.assertIn('sidecar_ref=capture.take()',observer)
 def test_real_ContextVar_dispatch_restores_native_outside_selection(self):
  import tensor_observer as O
  calls=[];f=O.dispatch_for(lambda x:calls.append(('prod',x))or x)
  self.assertEqual(f(1),1);token=O.OP_CAPTURE.set(lambda x:calls.append(('capture',x))or x+1)
  try:self.assertEqual(f(1),2)
  finally:O.OP_CAPTURE.reset(token)
  self.assertEqual(f(2),2);self.assertEqual(calls,[('prod',1),('capture',1),('prod',2)])
 def test_real_Capture_Store_audit_independent_model_consumer_ABI(self):
  from unittest.mock import patch
  import types,sidecar_capture,raw_codec
  t,R,raw,prev=self.fixture();s=raw['sidecar_record'];args=copy.deepcopy(s['before']);expected_after=copy.deepcopy(s['after']);truth=s['actual_precast_FP32'].clone()
  def production(*a):
   for i in range(5,11):a[i].copy_(expected_after[i])
   return raw['output'].clone()
  def debug(*a):
   z=production(*a[:-1]);a[-1].copy_(truth);return z
  with tempfile.TemporaryDirectory()as temp,patch.object(torch,'npu',types.SimpleNamespace(synchronize=lambda:None),create=True):
   store=raw_codec.Store(t,Path(temp),16*1024*1024);capture=sidecar_capture.Capture(t,production,debug);capture.sink=lambda n,v:store.write(Path(temp)/n,v)
   capture(*args);ref=capture.take();old=raw_codec.install(t)
   try:raw['sidecar_record']=t.load(ref['path'],weights_only=False)
   finally:t.load=old
   self.assertTrue(C.decode(t,R,raw,prev,7)[1]['passed']);self.assertEqual(len(capture.records),1)
