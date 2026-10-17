"""Focused metadata controls; no NPU or numerical qualification."""
import ast,types,unittest
import torch
import cache_observation as O
class Tests(unittest.TestCase):
 def fixture(self):
  groups=[];tables=[];layers=[];metadata={};static={}
  for gid in range(2):
   groups.append(types.SimpleNamespace(layer_names=[],kv_cache_spec=types.SimpleNamespace(shapes=((4,3),),dtypes=(torch.float32,),page_size_bytes=128)))
   class Block:
    num_blocks_per_row=[1]
    def get_cpu_tensor(self):return torch.tensor([[self.slot]],dtype=torch.int32)
   b=Block();b.slot=gid+3;tables.append(b)
  for i in range(48):
   p='actual.%d'%i;gid=i%2;groups[gid].layer_names.append(p)
   obj=types.SimpleNamespace(prefix=p,kv_cache=(torch.empty(6,4,3),torch.empty(6,4,8)))
   layers.append(types.SimpleNamespace(layer_type='linear_attention',linear_attn=obj));static[p]=obj
   metadata[p]=types.SimpleNamespace(prefill_state_indices=torch.tensor([gid+3]),num_prefills=1,num_decodes=0)
  request=types.SimpleNamespace(block_ids=([3],[4]));ctx=types.SimpleNamespace(attn_metadata=metadata,no_compile_layers=static)
  runner=types.SimpleNamespace(input_batch=types.SimpleNamespace(req_id_to_index={'actual':0},block_table=tables),requests={'actual':request},kv_cache_config=types.SimpleNamespace(kv_cache_groups=groups,kv_cache_tensors=[types.SimpleNamespace(size=128,shared_by=list(static))]),vllm_config=types.SimpleNamespace(compilation_config=types.SimpleNamespace(static_forward_context=static)))
  return types.SimpleNamespace(model_runner=runner),types.SimpleNamespace(layers=layers),request,metadata,ctx
 def test_heterogeneous_metadata_recorded_without_admission(self):
  w,i,r,m,c=self.fixture();before=[x.linear_attn.kv_cache[1].clone()for x in i.layers]
  v=O.collect(w,i,'actual',r,m,c,0)
  self.assertEqual(len(v['all48']),48);self.assertEqual([g['CPU_row']for g in v['groups']],[[3],[4]])
  self.assertEqual(len(v['cache_tensor_declarations'][0]['shared_by']),48);self.assertFalse(v['guard_bypassed'])
  for a,l in zip(before,i.layers):self.assertTrue(torch.equal(a,l.linear_attn.kv_cache[1]))
 def test_wrong_request_or_context_reject(self):
  w,i,r,m,c=self.fixture()
  with self.assertRaises(ValueError):O.collect(w,i,'actual',types.SimpleNamespace(block_ids=()),m,c,0)
  with self.assertRaises(ValueError):O.collect(w,i,'actual',r,dict(m),c,0)
 def test_no_device_copy_and_registration_source_unchanged(self):
  from pathlib import Path
  p=Path(__file__).parent
  tree=ast.parse((p/'cache_observation.py').read_bytes())
  self.assertFalse(any(isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr in('cpu','to','numpy','copy_')for n in ast.walk(tree)))
  # R10 explicitly changes registration authority/indexing, not the original
  # R4 geometry-only observer. Invert every declared registration edit first.
  import json,hashlib
  plan=json.loads((p/'REGISTRY_EDITS131R10.json').read_bytes());raw=(p/'cache_registry.py').read_bytes()
  self.assertEqual(hashlib.sha256(raw).hexdigest(),plan['after_sha256'])
  for edit in reversed(plan['edits']):
   a,b=edit['new_start'],edit['new_end'];self.assertEqual(raw[a:b].decode(),edit['new']);raw=raw[:a]+edit['old'].encode()+raw[b:]
  self.assertEqual(hashlib.sha256(raw).hexdigest(),plan['before_sha256'])
  self.assertEqual(raw,(p/'evidence/HISTORICAL_CACHE_REGISTRY131R3.py').read_bytes())
