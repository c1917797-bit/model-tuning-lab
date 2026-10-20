"""Actual CPU tensor/block/Binding objects; native scheduler state is a fixture."""
import unittest,torch
from types import SimpleNamespace as NS
from model_entry import Owner,tensor_id
from layer_slots131r10 import Binding
from live_owner import LiveOwner
class Tests(unittest.TestCase):
 def fixture(self):
  rid='actual-native-request';request=NS(block_ids=[(2,)])
  cpu=torch.tensor([[2]],dtype=torch.int32)
  table=NS(num_blocks_per_row=[1],get_cpu_tensor=lambda:cpu)
  group=NS(layer_names=['layer0'])
  meta=NS(prefill_state_indices=torch.tensor([2]),non_spec_state_indices_tensor=torch.tensor([2]),
   non_spec_prefill_metadata=NS(causal_conv1d=NS(cache_indices=torch.tensor([[2]]))))
  layer=NS(kv_cache=(torch.zeros(4,11,2),torch.zeros(4,2,2)))
  layer._bole_pure_prefill_observation=dict(metadata=meta,request=request,slot=2)
  batch=NS(req_ids=[rid],req_id_to_index={rid:0},num_computed_tokens_cpu=torch.tensor([131]),
   num_tokens_no_spec=torch.tensor([132]),token_ids_cpu=torch.zeros((1,150),dtype=torch.int32),block_table=[table])
  batch.token_ids_cpu[0,131:134]=torch.tensor([4,5,6])
  runner=NS(requests={rid:request},input_batch=batch,kv_cache_config=NS(kv_cache_groups=[group]))
  binding=Binding('layer0',0,2,runner,rid,request,group,table,(2,),meta,layer,
   tensor_id(layer.kv_cache[0]),tensor_id(layer.kv_cache[1]),131)
  b=dict(index=0,kind='gdn',layer=NS(linear_attn=layer),group=0,physical_slot=2,slot_binding=binding)
  owner=Owner(rid,1,0,131,0);live=LiveOwner(runner,[b],owner);live.record_draft(4,(5,6))
  schedule=NS(num_scheduled_tokens={rid:3},scheduled_spec_decode_tokens={rid:[5,6]})
  return live,b,runner,schedule,cpu
 def publish(self,live,frame):
  p=dict(owner=frame.owner,emitted_tokens=(6,7),next_length=133,next_version=1,
   cache_published=True,scheduler_ack_pending=True,scheduler_committed=False)
  live.publication(p);live.close_frame([frame.owner.request],(6,7));return p
 def test_actual_group_table_arena_rebindings_rejected(self):
  for change in('table','arena','request'):
   live,b,r,s,cpu=self.fixture();f=live.make_frame(s,[3]);self.assertEqual(live.physical(b,f.owner),2)
   if change=='table':cpu[0,0]=1
   elif change=='arena':b['layer'].linear_attn.kv_cache=(torch.zeros(4,11,2),torch.zeros(4,2,2))
   else:r.requests[f.owner.request]=NS()
   with self.assertRaises(ValueError):live.physical(b,f.owner)
 def fa_fixture(self,ratio=1):
  old,b,r,s,cpu=self.fixture();rid=old.initial.request
  physical=(1,3)if ratio==1 else(1,)
  row=physical if ratio==1 else tuple(range(ratio,2*ratio))
  page=torch.tensor([row],dtype=torch.int32)
  table=NS(num_blocks_per_row=[len(row)],get_cpu_tensor=lambda:page,
   blocks_per_phys_block=ratio,logical_block_size=128,physical_block_size=ratio*128,
   block_size=128,use_hybrid_blocks=ratio!=1,pcp_world_size=1,dcp_world_size=1)
  group=NS(layer_names=['fa1']);key=torch.zeros(32,128,1,2);value=torch.zeros_like(key)
  attn=NS(kv_cache=(key,value),impl=NS(key_cache=key,value_cache=value))
  fa=dict(index=1,kind='fa',prefix='fa1',group=1,layer=NS(self_attn=NS(attn=attn)),
   key=key,value=value,table=row)
  r.kv_cache_config.kv_cache_groups.append(group);r.input_batch.block_table.append(table)
  r.requests[rid].block_ids.append(physical)
  live=LiveOwner(r,[b,fa],old.initial);live.record_draft(4,(5,6))
  return live,b,fa,r,s,page
 def test_actual_fa_group_table_request_and_cache_alias_rebindings_rejected(self):
  for change in('group','table','pages','request','kv','impl','binding','geometry'):
   live,b,fa,r,s,page=self.fa_fixture();f=live.make_frame(s,[3]);self.assertTrue(live.validate(f.owner))
   if change=='group':r.kv_cache_config.kv_cache_groups[1]=NS(layer_names=['fa1'])
   elif change=='table':r.input_batch.block_table[1]=NS()
   elif change=='pages':page[0,0]=2
   elif change=='request':r.requests[f.owner.request].block_ids[1]=(2,3)
   elif change=='kv':fa['layer'].self_attn.attn.kv_cache=(torch.zeros_like(fa['key']),fa['value'])
   elif change=='impl':fa['layer'].self_attn.attn.impl.value_cache=torch.zeros_like(fa['value'])
   elif change=='binding':fa['key']=torch.zeros_like(fa['key'])
   else:r.input_batch.block_table[1].physical_block_size=256
   with self.assertRaises(ValueError):live.validate(f.owner)
 def test_actual_twelve_kernel_pages_per_physical_block_expansion(self):
  live,b,fa,r,s,page=self.fa_fixture(ratio=12);f=live.make_frame(s,[3])
  self.assertTrue(live.validate(f.owner));proof=live.fa_proof(fa)
  self.assertEqual(proof['request_physical_blocks'],(1,))
  self.assertEqual(proof['CPU_table'],tuple(range(12,24)))
  self.assertEqual(proof['physical_block_size'],1536)
  r.requests[f.owner.request].block_ids[1]=(2,)
  with self.assertRaises(ValueError):live.current()
 def test_next_native_counter_root_and_accepted_count_acknowledge_once(self):
  live,b,r,s,cpu=self.fixture();f=live.make_frame(s,[3]);p=self.publish(live,f)
  r.input_batch.num_computed_tokens_cpu[0]=133;r.input_batch.num_tokens_no_spec[0]=134
  r.input_batch.token_ids_cpu[0,133:136]=torch.tensor([7,8,9]);live.record_draft(7,(8,9))
  s.scheduled_spec_decode_tokens={f.owner.request:[8,9]}
  next_frame=live.make_frame(s,[3])
  self.assertEqual(next_frame.owner.length,133);self.assertEqual(next_frame.owner.version,1)
  self.assertEqual(len(live.acknowledgements),1);self.assertFalse(p['scheduler_ack_pending'])
 def test_wrong_native_input_or_second_open_frame_rejected(self):
  live,b,r,s,cpu=self.fixture();r.input_batch.token_ids_cpu[0,131]=99
  with self.assertRaises(ValueError):live.make_frame(s,[3])
  live,b,r,s,cpu=self.fixture();live.make_frame(s,[3])
  with self.assertRaises(ValueError):live.make_frame(s,[3])
 def test_unadmitted_scheduler_draft_and_stale_counter_rejected(self):
  live,b,r,s,cpu=self.fixture();s.scheduled_spec_decode_tokens={live.initial.request:[6,5]}
  with self.assertRaises(ValueError):live.make_frame(s,[3])
  live,b,r,s,cpu=self.fixture();f=live.make_frame(s,[3]);r.input_batch.num_computed_tokens_cpu[0]=132
  with self.assertRaises(ValueError):live.current()
 def test_native_removal_is_required_and_final_ack_stays_independent(self):
  live,b,r,s,cpu=self.fixture();f=live.make_frame(s,[3]);self.publish(live,f)
  with self.assertRaises(ValueError):live.retire([f.owner.request])
  del r.requests[f.owner.request];r.input_batch.req_ids=[];r.input_batch.req_id_to_index={}
  proof=live.retire([f.owner.request]);self.assertTrue(proof['final_ack_by_retirement_pending'])
  self.assertFalse(proof['scheduler_committed_independently'])
  with self.assertRaises(ValueError):live.record_draft(7,(8,9))
if __name__=='__main__':unittest.main()
