import copy,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import calibration_pipeline118 as K,common116 as C
def fixture(t,root):
 sr={'software_fixture_not_authority':True};abi={'software_fixture_not_actual_ABI':True};refs=[];pre=[]
 for b in(1,16):
  for act in(False,True):
   state=(t.arange((2*b+3)*3*2560).reshape(2*b+3,3,2560)%7).to(t.bfloat16)/64;ids=t.tensor([2*j+1 for j in range(b)],dtype=t.int32)
   w=t.full((2560,4),.125,dtype=t.bfloat16);bias=None
   for step in range(3):
    i=len(refs);x=t.full((b,2560),(.125+step*.0625),dtype=t.bfloat16);before=state.clone();hist=t.cat((before[ids.long()].double(),x.double().unsqueeze(1)),1);truth=(hist*w.double().T).sum(1)
    if act:truth=truth/(1+(-truth).exp())
    state[ids.long()]=hist[:,1:].bfloat16();seq=t.arange(b+1,dtype=t.int32);inv=[x,w,bias,seq,ids]
    row=dict(source=sr,actual_device_abi_ref=abi,index=i,batch=b,step=step,activation=act,inputs=x,weight=w,bias=bias,indices=ids,before=before,after=state.clone(),output=truth.bfloat16(),returned=truth.bfloat16(),returned_alias_output=True,invariant_before=[None if v is None else v.clone()for v in inv],invariant_after=[None if v is None else v.clone()for v in inv]);prior={k:row[k]for k in('source','actual_device_abi_ref','index','batch','step','activation','inputs','weight','bias','indices','before')};prior['output']=None
    a=root/('frame-%02d.pt'%i);z=root/('before-%02d.pt'%i);t.save(row,a);t.save(prior,z);refs.append(C.ref(a));pre.append(C.ref(z))
 capture=dict(schema='bole.actual-native-conv-capture/v118c',source=sr,actual_device_abi_ref=abi,operator_executed=True,records=refs,before_records=pre);C.write(root/'CAPTURE.json',capture)
 return sr,dict(observed_device_abi_ref=abi),dict(schema='bole.tree-stage/v118c',source=sr,primary=None,NPU=True,result=C.ref(root/'CAPTURE.json')),capture
class Tests(unittest.TestCase):
 def test_real_full12_consumer_independent_double(self):
  import torch as t;t.set_num_threads(1)
  with tempfile.TemporaryDirectory()as d:
   sr,m,outer,cap=fixture(t,Path(d));v=K.consume(t,C,m,sr,outer);self.assertTrue(v['pass_gate']);self.assertEqual(len(v['rows']),12);self.assertFalse(v['qualified']);self.assertFalse(v['model_ready'])
 def test_wrong_mutability_shape_slots_state_and_missing(self):
  import torch as t;t.set_num_threads(1)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);sr,m,outer,cap=fixture(t,root);p=C.checked(cap['records'][-1]);original=t.load(p,weights_only=True)
   for mutate in(lambda r:r['invariant_after'][0].fill_(9),lambda r:r.update(returned=t.zeros_like(r['returned'])),lambda r:r.update(output=r['output'].double()),lambda r:r.update(indices=t.zeros_like(r['indices']))):
    bad=copy.deepcopy(original);mutate(bad);t.save(bad,p);cap['records'][-1]=C.ref(p);C.write(root/('BAD%d.json'%len(list(root.iterdir()))),cap);outer['result']=C.ref(sorted(root.glob('BAD*.json'))[-1])
    with self.assertRaises(ValueError):K.consume(t,C,m,sr,outer)
   bad=copy.deepcopy(original);bad['after'][0,0,0]=1;t.save(bad,p);cap['records'][-1]=C.ref(p);C.write(root/'STATE.json',cap);outer['result']=C.ref(root/'STATE.json');self.assertFalse(K.consume(t,C,m,sr,outer)['pass_gate'])
 def test_actual_I_default_off_and_source_pin_readset(self):
  for n in('run116.py','owner116.py','cpu116.py','guest116.py','consume116.py','ticket116.py','bind116.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,(n,r.stderr));self.assertFalse(json.loads(r.stdout)['NPU'])
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(m['observed_device_abi_ref']['sha256'],'c68ec52dff3bda1162c891b26ac9d6fd8673aacff5c74c72f575ffcd3805dbf6');self.assertIn(m['observed_device_abi_ref'],m['calibration_readset'])
if __name__=='__main__':unittest.main()
