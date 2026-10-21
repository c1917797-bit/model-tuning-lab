"""Execute exact live-owner/ack methods with controlled native CPU metadata."""
import ast
from dataclasses import dataclass
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import sourceio as C
import g3_fia_contract as D

@dataclass(frozen=True)
class Owner:
 request:str
 generation:int
 slot:int
 length:int
 version:int


def load():
 source=ast.parse((P/'transaction.py').read_bytes());ack=next(n for n in source.body if isinstance(n,ast.FunctionDef)and n.name=='acknowledge')
 env=dict(need=C.need);exec(compile(ast.Module(body=[ack],type_ignores=[]),'exact-original-transaction-ack','exec'),env)
 nodes=[n for n in ast.parse((P/'live_owner.py').read_bytes()).body if isinstance(n,ast.ClassDef)]
 env.update(dataclass=dataclass,Owner=Owner,tensor_id=id,transaction=NS(acknowledge=env['acknowledge']),DOMAIN=D)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'exact-G3-live-owner','exec'),env)
 return env['LiveOwner']

class IDs:
 def __init__(self):self.items={}
 def __getitem__(self,key):
  _,index=key
  if isinstance(index,slice):return NS(tolist=lambda:[self.items[j]for j in range(index.start,index.stop)])
  return self.items[index]

class LifecycleTests(unittest.TestCase):
 def fixture(self):
  req=NS(output_token_ids=[7]);batch=NS(req_ids=['real'],req_id_to_index={'real':0},num_computed_tokens_cpu=[131],num_tokens_no_spec=[132],token_ids_cpu=IDs())
  runner=NS(requests={'real':req},input_batch=batch);live=load()(runner,[],Owner('real',1,0,131,0),max_steps=1023,output_budget=1024)
  return live,runner,req,batch
 def frame(self,live,req,batch,child2=False):
  root=req.output_token_ids[-1];children=(10000+len(req.output_token_ids)*2,10001+len(req.output_token_ids)*2)
  live.record_draft(root,children);length=batch.num_computed_tokens_cpu[0];tokens=(root,*children);count=3 if child2 else 1
  for j,token in enumerate(tokens[:count]):batch.token_ids_cpu.items[length+j]=token
  return live.make_frame(NS(num_scheduled_tokens={'real':count},scheduled_spec_decode_tokens={'real':list(children)}if child2 else{}),[count])
 def publish(self,live,frame,emitted):
  value=dict(owner=frame.owner,emitted_tokens=tuple(emitted),next_length=frame.owner.length+len(emitted),
   next_version=frame.owner.version+1,cache_published=True,scheduler_ack_pending=True)
  live.publication(value);live.close_frame(['real'],emitted);return value
 def advance(self,live,req,batch,child2=False):
  frame=self.frame(live,req,batch,child2);emitted=[frame.tokens[2],20+len(req.output_token_ids)]if child2 else[20+len(req.output_token_ids)]
  self.publish(live,frame,emitted);req.output_token_ids.extend(emitted)
  batch.num_computed_tokens_cpu[0]+=len(emitted);batch.num_tokens_no_spec[0]+=len(emitted)
  return frame
 def test_actual1023_ingresses_have1022_acks_then_retire_with_final_pending_transaction(self):
  live,runner,req,batch=self.fixture()
  for _ in range(1023):self.advance(live,req,batch)
  self.assertEqual(live.steps,1023);self.assertEqual(len(live.acknowledgements),1022);self.assertEqual(len(req.output_token_ids),1024)
  pending=live.pending
  with self.assertRaises(ValueError):live.retire({'real'})
  runner.requests={};batch.req_ids=[];proof=live.retire({'real'})
  self.assertTrue(proof['final_ack_by_retirement_pending']);self.assertIs(live.pending,pending)
  self.assertTrue(pending['scheduler_ack_pending']);self.assertEqual(proof['last_publication']['next_length'],1154)
 def test_child2_path_keeps_actual_admitted_metadata_to_last_root_only_budget(self):
  live,runner,req,batch=self.fixture()
  for _ in range(511):
   f=self.advance(live,req,batch,True);self.assertEqual(f.scheduled_nodes,3)
   self.assertEqual(f.real_input_ids,f.tokens)
  self.assertEqual(len(req.output_token_ids),1023)
  f=self.advance(live,req,batch);self.assertEqual(f.scheduled_nodes,1)
  self.assertEqual(live.steps,512);self.assertEqual(len(live.acknowledgements),511)
  runner.requests={};batch.req_ids=[];self.assertTrue(live.retire({'real'})['final_ack_by_retirement_pending'])
  source=(P/'service_runner.py').read_text()
  self.assertIn('eligibility.native_compaction_order(f.scheduled_nodes, decision.terminal)',source)
  self.assertIn('num_rejected_tokens_gpu',source)
  self.assertNotIn('token_ids_cpu[0, f.owner.length:',source)
 def test_late_wrong_counter_bonus_or_strong_request_cannot_clear_pending(self):
  for wrong in('counter','bonus','request'):
   live,runner,req,batch=self.fixture()
   for _ in range(700):self.advance(live,req,batch)
   pending=live.pending;acks=len(live.acknowledgements)
   if wrong=='counter':batch.num_computed_tokens_cpu[0]+=1
   elif wrong=='bonus':req.output_token_ids[-1]+=1
   else:runner.requests['real']=NS(output_token_ids=list(req.output_token_ids))
   with self.subTest(wrong=wrong),self.assertRaises(ValueError):self.frame(live,req,batch)
   self.assertIs(live.pending,pending);self.assertTrue(pending['scheduler_ack_pending']);self.assertEqual(len(live.acknowledgements),acks)
 def test_early_normal_EOS_is_outside_fixed1024_and_does_not_fabricate_a_next_ack(self):
  live,runner,req,batch=self.fixture();f=self.frame(live,req,batch);self.publish(live,f,[248046]);req.output_token_ids.append(248046)
  runner.requests={};batch.req_ids=[]
  with self.assertRaisesRegex(ValueError,'exact output'):live.retire({'real'})
  self.assertIsNotNone(live.pending);self.assertEqual(live.acknowledgements,[])

if __name__=='__main__':unittest.main()
