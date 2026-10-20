"""Execute exact lifecycle/ack method AST with controlled CPU metadata objects."""
import ast
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import g2_channel as CH
P=Path(__file__).resolve().parent


@dataclass(frozen=True)
class Owner:
 request:str
 generation:int
 slot:int
 length:int
 version:int


def load():
 source=ast.parse((P/'transaction.py').read_bytes());ack=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='acknowledge')
 env={'need':CH.need};exec(compile(ast.Module(body=[ack],type_ignores=[]),'exact-transaction-ack','exec'),env)
 source=ast.parse((P/'live_owner.py').read_bytes());nodes=[n for n in source.body if isinstance(n,ast.ClassDef)]
 env.update(dataclass=dataclass,Owner=Owner,tensor_id=lambda x:id(x),transaction=NS(acknowledge=env['acknowledge']))
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-live-owner','exec'),env)
 return env['LiveOwner']


class IDs:
 def __init__(self):self.items={131:7,132:11,133:13}
 def __getitem__(self,key):
  _,index=key
  if isinstance(index,slice):return NS(tolist=lambda:[self.items[j]for j in range(index.start,index.stop)])
  return self.items[index]


class LifecycleTests(unittest.TestCase):
 def fixture(self):
  request=NS(output_token_ids=[7]);batch=NS(req_ids=['real'],req_id_to_index={'real':0},num_computed_tokens_cpu=[131],num_tokens_no_spec=[132],token_ids_cpu=IDs())
  runner=NS(requests={'real':request},input_batch=batch);live=load()(runner,[],Owner('real',1,0,131,0),max_steps=3,output_budget=4)
  return live,runner,request,batch
 def frame(self,live,batch,root):
  live.record_draft(root,(root+1,root+2));length=batch.num_computed_tokens_cpu[0];batch.token_ids_cpu.items[length]=root
  return live.make_frame(NS(num_scheduled_tokens={'real':1},scheduled_spec_decode_tokens={}),[1])
 def publish(self,live,frame,token):
  value=dict(owner=frame.owner,emitted_tokens=(token,),next_length=frame.owner.length+1,next_version=frame.owner.version+1,cache_published=True,scheduler_ack_pending=True)
  live.publication(value);live.close_frame(['real'],[token]);return value
 def test_three_real_steps_have_two_counter_ACKs_and_final_pending_retirement(self):
  live,runner,request,batch=self.fixture()
  for i in range(3):
   frame=self.frame(live,batch,request.output_token_ids[-1]);self.publish(live,frame,11+i)
   request.output_token_ids.append(11+i)
   if i<2:batch.num_computed_tokens_cpu[0]+=1;batch.num_tokens_no_spec[0]+=1
  self.assertEqual(len(live.acknowledgements),2);pending=live.pending
  with self.assertRaises(ValueError):live.retire({'real'})
  runner.requests={};batch.req_ids=[]
  proof=live.retire({'real'})
  self.assertTrue(proof['final_ack_by_retirement_pending']);self.assertIs(live.pending,pending)
  self.assertTrue(live.pending['scheduler_ack_pending']);self.assertEqual(proof['steps'],3)
 def test_wrong_actual_next_counter_root_or_strong_request_cannot_acknowledge(self):
  for field in('counter','bonus','request'):
   with self.subTest(field=field):
    live,runner,request,batch=self.fixture();f=self.frame(live,batch,7);self.publish(live,f,11);request.output_token_ids.append(11)
    batch.num_computed_tokens_cpu[0]=132;batch.num_tokens_no_spec[0]=133;batch.token_ids_cpu.items[132]=11
    if field=='counter':batch.num_computed_tokens_cpu[0]=133
    elif field=='bonus':batch.token_ids_cpu.items[132]=12
    else:runner.requests['real']=NS(output_token_ids=[7,11])
    live.record_draft(11,(12,13))if field!='request'else None
    with self.assertRaises(ValueError):live.make_frame(NS(num_scheduled_tokens={'real':1},scheduled_spec_decode_tokens={}),[1])
    self.assertTrue(live.pending['scheduler_ack_pending']);self.assertEqual(live.acknowledgements,[])
 def test_normal_EOS_early_finish_is_outside_fixed_output_scope(self):
  live,runner,request,batch=self.fixture();f=self.frame(live,batch,7);self.publish(live,f,248046)
  request.output_token_ids.append(248046);runner.requests={};batch.req_ids=[]
  with self.assertRaisesRegex(ValueError,'exact output'):live.retire({'real'})
  self.assertIsNotNone(live.pending)
 def test_admitted_child2_keeps_all_admitted_metadata_and_original_CPU_history(self):
  # The current producer still orders only real proposal GPU IDs/native hidden;
  # the original _bookkeeping_sync CPU history remains in its original method.
  text=(P/'service_runner.py').read_text()
  self.assertIn('eligibility.native_compaction_order(f.scheduled_nodes, decision.terminal)',text)
  parsed=ast.parse((P/'eligibility.py').read_bytes());node=next(n for n in parsed.body if isinstance(n,ast.FunctionDef)and n.name=='native_compaction_order')
  env={'need':CH.need};exec(compile(ast.Module(body=[node],type_ignores=[]),'exact-compaction','exec'),env)
  self.assertEqual(env['native_compaction_order'](3,2),(0,2,1))
  self.assertIn('num_rejected_tokens_gpu',text)
  self.assertNotIn('token_ids_cpu[0, f.owner.length:',text)


if __name__=='__main__':unittest.main()
