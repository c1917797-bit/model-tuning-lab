import copy,hashlib,importlib.util,json,math,tempfile,unittest
from pathlib import Path
import torch
import raw_codec,precast,sidecar_audit
import direct_round as D
class Raw(unittest.TestCase):
 def test_dtypes_scalar_empty_and_subnormal_bytes(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);store=raw_codec.Store(torch,root,4000000);value={str(dt):torch.tensor([0.,-0.,2**-140],dtype=dt)for dt in(torch.bfloat16,torch.float32,torch.float64)};value.update(scalar=torch.tensor(3.),empty=torch.empty((0,3)),integer=torch.arange(3,dtype=torch.int32));r=store.write(root/'one.pt',value);original=raw_codec.install(torch)
   try:v=torch.load(r['path'],weights_only=False)
   finally:torch.load=original
   for k in value:self.assertEqual(value[k].dtype,v[k].dtype);self.assertEqual(value[k].shape,v[k].shape);self.assertTrue(torch.equal(value[k].reshape(-1).view(torch.uint8),v[k].reshape(-1).view(torch.uint8)))
 def test_roundtrip_dedup_and_negative_zero(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);store=raw_codec.Store(torch,root,4000000);a=torch.tensor([[0.,-0.,float('nan')],[1.,2.,3.]])
   r=store.write(root/'one.pt',dict(a=a,b=a.clone(),pair=(torch.arange(3,dtype=torch.int32),)));n=len(list(store.blobs.iterdir()));store.write(root/'two.pt',dict(a=a.clone()));self.assertEqual(n,len(list(store.blobs.iterdir())))
   original=raw_codec.install(torch)
   try:v=torch.load(r['path'],weights_only=False)
   finally:torch.load=original
   self.assertTrue(precast.bits(torch,a,v['a']));self.assertIsInstance(v['pair'],tuple)
 def test_corrupt_and_ref_drift_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);store=raw_codec.Store(torch,root,4000000);r=store.write(root/'one.pt',torch.ones((2,4)));blob=next(store.blobs.iterdir());blob.write_bytes(b'bad')
   original=raw_codec.install(torch)
   try:
    with self.assertRaises(ValueError):torch.load(r['path'],weights_only=False)
   finally:torch.load=original
 def test_cap_is_actual_unique_bytes(self):
  with tempfile.TemporaryDirectory()as d:
   store=raw_codec.Store(torch,Path(d),100)
   with self.assertRaises(ValueError):store.write(Path(d)/'x.pt',torch.ones(100))
class Predicate(unittest.TestCase):
 def test_real_consumer_entry_actual_capture_contract(self):
  import domain_consumer as C,oracle as R,bridge_io
  torch.manual_seed(2610165101)
  st=dict(base=torch.zeros(6,12,128,128),k_log=torch.zeros(6,4,7,128,dtype=torch.bfloat16),u_log=torch.zeros(6,12,7,128),lambda_log=torch.zeros(6,12,16),decay=torch.zeros(6,12,16),length=torch.zeros(6,12,16,dtype=torch.int32))
  i=dict(query=torch.randn(1,4,128).bfloat16(),key=torch.zeros(1,4,128,dtype=torch.bfloat16),value=torch.randn(1,12,128).bfloat16(),g=torch.zeros(1,12),beta=torch.ones(1,12,dtype=torch.bfloat16),ssm_state_indices=torch.tensor([0],dtype=torch.int32),actual_seq_lengths=torch.tensor([0,1],dtype=torch.int32),scale=128**-.5)
  post,y=R.advance(torch,R.restore(torch,st,0),i,0);state=copy.deepcopy(st);state['base'][0]=post.float();z=D.round_bf16(torch,y.float().double()).unsqueeze(0)
  args=[i[k]for k in('query','key','value','g','beta')]+[st[k]for k in C.FIELDS]+[i['actual_seq_lengths'],i['ssm_state_indices']];after=[i[k]for k in('query','key','value','g','beta')]+[state[k]for k in C.FIELDS]+[i['actual_seq_lengths'],i['ssm_state_indices']]
  side=dict(before=args,debug_before=copy.deepcopy(args),after=after,debug_after=copy.deepcopy(after),production_output=z,debug_output=z.clone(),actual_precast_FP32=y.float().unsqueeze(0),pointers_before=[],pointers_after=[],sidecar_redzones_pass=True,sidecar_guards_before=torch.full((256,),13.),sidecar_guards_after=torch.full((256,),13.))
  with tempfile.TemporaryDirectory()as d:
   p=Path(d)/'side.pt';torch.save(side,p);ref=bridge_io.ref(p)
   raw=dict(state=state,ids=torch.tensor([0,1]),candidate_output=torch.cat([z,torch.zeros(64,12,128,dtype=torch.bfloat16)]),native_output=torch.cat([z,torch.zeros(64,12,128,dtype=torch.bfloat16)]),native_state=state['base'].clone(),captures=dict(decode=[dict(before=st,inputs=i,output=z,actual_sidecar043=ref)]))
   self.assertTrue(all(x['request_pass']for x in C.per_request_metrics(torch,R,raw,D)))
   bad=copy.deepcopy(raw);bad['captures']['decode'][0]['inputs']['scale']*=2
   with self.assertRaises(ValueError):C.per_request_metrics(torch,R,bad,D)
   bad=copy.deepcopy(raw);bad['captures']['decode'][0]['inputs']['ssm_state_indices'][0]=2
   with self.assertRaises(ValueError):C.per_request_metrics(torch,R,bad,D)
   side['actual_precast_FP32']+=1.;torch.save(side,p);raw['captures']['decode'][0]['actual_sidecar043']=bridge_io.ref(p)
   self.assertFalse(C.per_request_metrics(torch,R,raw,D)[0]['request_pass'])
 def test_midpoint_actual_precast_is_primary_not_ideal_point(self):
  truth=torch.full((1,12,128),-.0001263618727894541,dtype=torch.float64);y=truth.float();z=D.round_bf16(torch,y.double())
  self.assertTrue(precast.evaluate(torch,y,z,truth)['passed'])
 def test_large_request_cannot_hide_small_error(self):
  truth=torch.tensor([[1000.],[1.]],dtype=torch.float64);y=truth.float();y[1]=1.01;z=D.round_bf16(torch,y.double());r=precast.evaluate(torch,y,z,truth);self.assertFalse(r['passed']);self.assertTrue(r['whole_batch_diagnostic']['passed'])
 def test_zero_sidecar_wrongcast_scale_head_slot(self):
  truth=torch.arange(1,25,dtype=torch.float64).reshape(2,12,1);y=truth.float();z=D.round_bf16(torch,y.double())
  self.assertTrue(precast.evaluate(torch,y,z,truth)['passed'])
  for wrong in(y*2,y.flip(1),y.flip(0),y+1):self.assertFalse(precast.evaluate(torch,wrong,D.round_bf16(torch,wrong.double()),truth)['passed'])
  self.assertFalse(precast.evaluate(torch,y,z+1,truth)['passed'])
  zero=torch.zeros_like(truth);self.assertFalse(precast.evaluate(torch,torch.ones_like(y),torch.ones_like(z),zero)['passed'])
 def test_signedzero_and_nonfinite(self):
  truth=torch.zeros((1,2),dtype=torch.float64);y=truth.float();y[0,0]=-0.;z=D.round_bf16(torch,y.double());self.assertTrue(precast.evaluate(torch,y,z,truth)['passed']);z[0,0]=0.;self.assertFalse(precast.evaluate(torch,y,z,truth)['passed'])
  y.fill_(math.inf);self.assertFalse(precast.evaluate(torch,y,z,truth)['passed'])
if __name__=='__main__':unittest.main()
