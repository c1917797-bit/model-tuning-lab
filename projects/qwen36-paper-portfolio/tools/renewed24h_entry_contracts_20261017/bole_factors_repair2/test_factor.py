"""CPU source/layout/reference controls only; no simulated NPU/HAL success."""
import ast,hashlib,json,subprocess,sys,unittest
from pathlib import Path
import torch as t
import factor as F,root_pair as R,cpu_root_alias as A
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def saved(self):
  k=t.arange(2*128*256,dtype=t.float32).reshape(2,1,128,256).to(t.bfloat16)
  mask=t.ones(1,1,3,256,dtype=t.bool);mask[:,:,:,:132]=False;mask[0,0,1,132]=False;mask[0,0,2,133]=False
  return dict(query=t.zeros(1,6,3,256,dtype=t.bfloat16),key=k,value=k.clone(),atten_mask=mask,block_table=t.tensor([[0,1]],dtype=t.int32))
 def test_preregistered_single_factor_kwargs_not_unfounded_precision_claim(self):
  base=F.kwargs(True,1,2)
  self.assertEqual({k for k in base if base[k]!=F.kwargs(True,1,0)[k]},{'inner_precise'})
  self.assertEqual({k for k in base if base[k]!=F.kwargs(True,0,2)[k]},{'sparse_mode'})
  with self.assertRaises(ValueError):F.kwargs(True,0,0)
  self.assertNotIn('block_size',F.kwargs(False,1,2))
 def test_dense_KV_transform_bitwise_and_full_padding_ancestor_mask(self):
  saved=self.saved();dense=F.inputs(t,saved,False)
  for pos in range(256):self.assertTrue(t.equal(dense['key'][0,0,pos],saved['key'][pos//128,0,pos%128]))
  self.assertTrue(F.bits(t,dense['query'],saved['query']));self.assertTrue(F.bits(t,dense['atten_mask'],saved['atten_mask']))
  self.assertNotIn('block_table',dense)
  self.assertTrue(bool(dense['atten_mask'][...,134:].all()))
  wrong=self.saved();wrong['block_table'][0,0]=1
  with self.assertRaises(ValueError):F.inputs(t,wrong,False)
 def test_root_pair_first_actual_operand_difference_and_hidden_alias_scope(self):
  roots=[]
  for child in(1,2):
   captures={}
   for i in range(64):
    a=t.ones(1,2);common=dict(output=a.clone())
    if i%4==3:common.update(kind='fa-native-AR',query=a.clone(),key=a.clone(),value=a.clone(),after_key=a.clone(),after_value=a.clone())
    else:common.update(kind='gdn-native-AR',**{k:a.clone()for k in('inputs','a','b','weight','conv_before','state_before','actual_seq','actual_indices','conv_after','state_after')},normalized_inputs=[a.clone()for _ in range(5)])
    captures[i]=common
   ctx=dict(captures=captures,positions=[131],tokens=[5]);roots.append(dict(child=child,steps=[dict(node=0,context=ctx,hidden=t.ones(1,2),logits=t.ones(1,3)),dict(node=child,hidden=t.zeros(1,2))]))
  raw=dict(rank=0,source={},native=roots);same=R.run(t,raw);self.assertIsNone(same['first_actual_saved_operand_difference'])
  roots[1]['steps'][0]['context']['captures'][0]['state_before'][0,0]=2
  changed=R.run(t,raw);self.assertEqual(changed['first_actual_saved_operand_difference'],dict(layer=0,field='state_before'))
  self.assertTrue(changed['saved_CPU_storage_is_not_original_NPU_alias_proof'])
 def test_saved_original_native_BF16_output_anchor_not_CPU_truth_or_cast(self):
  import consume_factor as K
  original=t.ones(3,6,256,dtype=t.bfloat16);capture={'output':original}
  same=K.anchor_comparison(t,capture,original.clone())
  self.assertTrue(same['bitwise_reproduced']);self.assertFalse(same['comparison_cast'])
  other=original.clone();other[0,0,0]=2
  self.assertFalse(K.anchor_comparison(t,capture,other)['bitwise_reproduced'])
  with self.assertRaises(ValueError):K.anchor_comparison(t,{'output':original.float()},original)
  with self.assertRaises(KeyError):K.anchor_comparison(t,{'trial':{'output':original}},original)
 def test_raw_tensor_budget_and_whole_owner_inverse(self):
  # Per call: BEFORE + RAW(before+after+output). Dense arm drops table8B.
  inputs=sum(x.numel()*x.element_size()for x in self.saved().values())
  budget=64*(3*(3*inputs+9216)+(3*(inputs-8)+9216))
  self.assertEqual(budget,211358208);self.assertLess(budget,224*2**20)
  e=json.loads((P/'PROFILE_EDITS.json').read_bytes())
  for name,row in e.items():
   raw=(P/name).read_bytes();r2=json.loads((P/'REPAIR2_EDITS.json').read_bytes())
   if name in r2['changed']:
    self.assertEqual(hashlib.sha256(raw).hexdigest(),r2['changed'][name]['after']['sha256']);raw=r2['changed'][name]['before_body'].encode()
   repair=json.loads((P/'REPAIR1_EDITS.json').read_bytes())
   if name in repair:
    value=raw.decode()
    for delta in reversed(repair[name]['edits']):
     self.assertEqual(value.count(delta['after']),delta['count']);value=value.replace(delta['after'],delta['before'])
    raw=value.encode()
   self.assertEqual(hashlib.sha256(raw).hexdigest(),row['after']['sha256'])
   text=raw.decode()
   for change in reversed(row['edits']):self.assertEqual(text.count(change['after']),change.get('count',1));text=text.replace(change['after'],change['before'])
   self.assertEqual(text.encode(),(P/'evidence'/('DONOR_'+name)).read_bytes())
 def test_cold_actual_typed_cli_frontdoors_default_OFF_and_missing_evidence(self):
  for name in('run116.py','bind116.py','owner116.py','owned_cpu116.py','guest116.py','cpu116.py','consume116.py'):
   z=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=15)
   self.assertEqual(z.returncode,0,(name,z.stderr));self.assertIs(json.loads(z.stdout)['enabled'],False)
  z=subprocess.run([sys.executable,'-I','-B',str(P/'run116.py'),'--execute','--stage','bind','--reviewed-template-ref','{}'],capture_output=True,text=True,timeout=15)
  self.assertNotEqual(z.returncode,0);self.assertNotIn('unrecognized arguments',z.stderr)
 def test_exact_root_report_alias_docker_receipt_protocol_no_generic_replace(self):
  import tempfile,types,common116 as C
  with tempfile.TemporaryDirectory()as td:
   parent=Path(td);(parent/'preflight').mkdir();target=parent/'preflight/ROOT_PAIR_STAGE.json'
   C.write(target,dict(schema='software_mount_contract_not_actual_CID'));real=C.ref(target)
   owner_ref=dict(path=str(parent/'RESULT.json'),bytes=0,sha256='0'*64);owner=dict(cid='a'*64)
   inspection=dict(Id='a'*64,Image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',State=dict(Running=False,Pid=0,ExitCode=0,OOMKilled=False),ExecIDs=None,HostConfig=dict(ReadonlyRootfs=True,Devices=[],DeviceRequests=[]),Mounts=[dict(Source=str(parent),Destination='/adakv-results',RW=True)])
   C.write(parent/'FINAL_INSPECT.json',inspection);ir=C.ref(parent/'FINAL_INSPECT.json');alias=dict(real,path='/adakv-results/preflight/ROOT_PAIR_STAGE.json')
   self.assertEqual(A.resolve(C,alias,cpu_owner_ref=owner_ref,owner=owner,final_inspect_ref=ir),real)
   for bad in(dict(alias,path='/adakv-results/../preflight/ROOT_PAIR_STAGE.json'),dict(alias,sha256='0'*64)):
    with self.assertRaises(ValueError):A.resolve(C,bad,cpu_owner_ref=owner_ref,owner=owner,final_inspect_ref=ir)
   inspection['Mounts'][0]['Source']+='/wrong';C.write(parent/'WRONG_INSPECT.json',inspection);wrong=C.ref(parent/'WRONG_INSPECT.json')
   with self.assertRaises(ValueError):A.resolve(C,alias,cpu_owner_ref=owner_ref,owner=owner,final_inspect_ref=wrong)
 def test_actual_controller_composes_renewed_original_Lane_before_backend(self):
  import controller_probe as K
  original=list(sys.path)
  try:self.assertEqual(K.construct(False).__name__,'GE')
  finally:sys.path[:]=original
if __name__=='__main__':unittest.main()
