"""CPU fixtures exercise actual frozen binding, not a JSON permit."""
import unittest
from types import SimpleNamespace as NS
import torch
import test_cache_registry as F
import cache_registry as R
from model_entry import Owner
import layer_slots131r10 as S
import diagnostic_export as X

class Tests(unittest.TestCase):
 def fixture(self):
  w,m,k=F.Tests().fixture();r=w.model_runner;old=r.input_batch.block_table[0]
  groups=[];tables=[];alloc=[]
  for gid,slot in enumerate((2,11,20)):
   table=F.Block();table.table=torch.tensor([[slot,slot+1]]);table.num_blocks_per_row=[2]
   tables.append(table);alloc.append([slot,slot+1]);groups.append(NS(layer_names=[]))
  fa=r.kv_cache_config.kv_cache_groups[1];ft=r.input_batch.block_table[1]
  r.kv_cache_config.kv_cache_groups=groups+[fa];r.input_batch.block_table=tables+[ft]
  k['request'].block_ids=alloc+[[2,0]]
  for layer in m.layers:
   if layer.layer_type!='linear_attention':continue
   obj=layer.linear_attn;gid=layer.layer_idx%3;slot=(2,11,20)[gid];groups[gid].layer_names.append(obj.prefix)
   conv=torch.zeros(22,11,2560,dtype=torch.bfloat16);state=torch.zeros(22,12,128,128)
   obj.kv_cache=[conv,state];meta=k['metadata'][obj.prefix]
   meta.prefill_state_indices=meta.non_spec_state_indices_tensor=torch.tensor([slot]);meta.non_spec_prefill_metadata.causal_conv1d.cache_indices=torch.tensor([slot])
   obj._bole_pure_prefill_observation.update(slot=slot,arena_identity=F.tensor_id(conv),raw_last3=conv[slot,:3].clone(),extra_before=conv[slot,3:].clone())
  return w,m,k
 def test_three_groups_actual_slots_not_logical_zero(self):
  w,m,k=self.fixture();rows,window=R.register(torch,F.C,w,m,**k);o=Owner('r',1,0,131,0)
  self.assertEqual(window['slot'],0)
  self.assertEqual({S.physical(b,o)for b in rows if b['kind']=='gdn'},{2,11,20})
 def test_mutated_live_request_table_metadata_or_arena_rejected(self):
  for fault in('request','table','metadata','arena','group'):
   w,m,k=self.fixture();rows,_=R.register(torch,F.C,w,m,**k);b=rows[0];o=Owner('r',1,0,131,0);v=b['slot_binding']
   if fault=='request':w.model_runner.requests['r']=object()
   elif fault=='table':v.table.table[0,0]+=1
   elif fault=='metadata':v.metadata.prefill_state_indices=torch.tensor([0])
   elif fault=='arena':v.layer.kv_cache[1]=v.layer.kv_cache[1].clone()
   else:b['group']+=1
   with self.assertRaises(ValueError):S.physical(b,o)
 def test_opaque_binding_omitted_but_identity_preserved(self):
  identity=dict(group=2,physical_slot=20,logical_owner_slot=0)
  row=dict(layer=0,kind='state',arena=torch.zeros(1),arena_identity=(1,),before=torch.zeros(1),after=torch.ones(1),slot_binding=object(),slot_binding_identity=identity)
  p=dict(schema='bole.actual-model-selected-path-staging/v1',published=False,writes=[row])
  result=X.export_staged(torch,p,cap_bytes=1024)['payload']['writes'][0]
  self.assertNotIn('slot_binding',result);self.assertNotIn('arena',result);self.assertEqual(result['slot_binding_identity'],identity)

if __name__=='__main__':unittest.main()
