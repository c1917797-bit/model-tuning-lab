import copy,hashlib,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import native_footprint101r12 as F,consume_native101r12 as C
NS=types.SimpleNamespace
def fixture():
 import torch,numpy as np
 names=[[('fa'if g==0 else'gdn%d'%g)+'.%d'%i for i in range(16)]for g in range(4)];groups=[];tables=[];static={};meta={};physical=([1,2],[3],[4],[5]);blocks=[list(range(12,36)),[3],[4],[5]]
 for gid in range(4):
  is_mamba=gid>0;groups.append(NS(layer_names=names[gid],kv_cache_spec=NS(block_size=1536)))
  cpu=np.array([blocks[gid]],dtype=np.int32);gpu=torch.tensor(cpu);slots=torch.arange(1536,3584,dtype=torch.int32)
  # FA physical1+2 => kernel12..35, first2048 token slots1536..3583.
  table=NS(pcp_world_size=1,dcp_world_size=1,num_blocks_per_row=np.array([len(blocks[gid])]),blocks_per_phys_block=1 if is_mamba else 12,physical_block_size=1536,logical_block_size=1536 if is_mamba else 128,use_hybrid_blocks=not is_mamba,is_mamba_group=is_mamba,kernel_sizes=None if is_mamba else [128],get_numpy_array=lambda cpu=cpu:cpu,get_device_tensor=lambda n,gpu=gpu:gpu[:n],slot_mapping=NS(gpu=slots))
  tables.append(table)
  for name in names[gid]:
   cache=[torch.empty((32,2,2)),torch.empty((32,2,2))]if is_mamba else[torch.empty((48,128,1,2)),torch.empty((48,128,1,2))]
   static[name]=NS(kv_cache=cache)
   if is_mamba:
    slot=torch.tensor(blocks[gid],dtype=torch.int32);q=torch.tensor([0,2048],dtype=torch.int32);meta[name]=NS(non_spec_state_indices_tensor=slot,num_prefills=1,num_decodes=0,prefill_state_indices=slot,non_spec_prefill_metadata=NS(causal_conv1d=NS(cache_indices=slot,query_start_loc=q)))
   else:meta[name]=NS(block_tables=gpu,slot_mapping=slots,actual_seq_lengths_q=[2048],seq_lens=torch.tensor([2048],dtype=torch.int32))
 r=NS(pcp_size=1,input_batch=NS(req_ids=['actual-software-only'],block_table=NS(block_tables=tables)),requests={'actual-software-only':NS(block_ids=physical)},cache_config=NS(mamba_cache_mode='none',enable_prefix_caching=False,num_gpu_blocks_override=None),kv_cache_config=NS(num_blocks=32,kv_cache_groups=groups,kv_cache_tensors=[NS(size=1,shared_by=[name])for group in names for name in group]),compilation_config=NS(static_forward_context=static))
 return r,NS(num_scheduled_tokens={'actual-software-only':2048},total_num_scheduled_tokens=2048),NS(attn_metadata=meta)
class NativeTests(unittest.TestCase):
 def test_actual_cpu_views_offset_and_stride(self):
  import torch
  x=torch.empty((8,4,4));a=F.geometry(x[1:3]);self.assertEqual(a['data_ptr'],x.data_ptr()+64);self.assertEqual(a['end']-a['start'],128)
  with self.assertRaises(ValueError):F.geometry(x.transpose(0,1))
  with self.assertRaises(ValueError):F.selected(a,2,'state','r')
 def test_all64_producer_consumer(self):
  r,s,c=fixture();v=F.collect(r,s,c);v['native_source_proof']=dict(runner=dict(sha256=F.RUNNER_SHA),block_table=dict(sha256=F.BLOCK_SHA));result=C.evaluate(v)
  self.assertTrue(result['all64_metadata_join']);self.assertFalse(result['physical_layout_valid']);self.assertFalse(result['qualified'])
  self.assertEqual(len(v['layers']),64);self.assertEqual(v['groups'][0]['GPU_table'],list(range(12,36)))
  for role in ('K-current-write','V-current-write'):self.assertTrue(any(x['role']==role for x in v['layers'][0]['current_write_intervals']))
 def test_gpu_commit_wrong_slot_head_group_negative(self):
  r,s,c=fixture();r.input_batch.block_table.block_tables[0].get_device_tensor(1)[0,0]=99
  with self.assertRaises(ValueError):F.collect(r,s,c)
  r,s,c=fixture();c.attn_metadata['gdn1.0'].non_spec_state_indices_tensor[0]=4
  with self.assertRaises(ValueError):F.collect(r,s,c)
  r,s,c=fixture();v=F.collect(r,s,c);v['native_source_proof']=dict(runner=dict(sha256=F.RUNNER_SHA),block_table=dict(sha256=F.BLOCK_SHA));v['layers'][0]['views'][0]['stride'][-1]=2
  with self.assertRaises(ValueError):C.evaluate(v)
 def test_stop_before_native_and_partial_failure_saved(self):
  calls=[]
  class Runner:
   def __init__(self):self.input_batch=NS(req_ids=['request'])
   def execute_model(self,scheduler):calls.append('native-prepare');return self._model_forward()
   def _model_forward(self):calls.append('FORBIDDEN-decoder')
  with tempfile.TemporaryDirectory()as td,patch.dict(os.environ,dict(QWEN36_DELTALOG_SERVICE023_AUDIT=td,MST_MXR_NATIVE_WORKER_RUN_ID='software-only')):
   F.install(Runner,lambda:NS(),dict(path='software',bytes=0,sha256='0'*64),lambda:0,{},None)
   with patch.object(F,'collect',side_effect=ValueError('actual unsupported ABI')):
    with self.assertRaises(F.DiagnosticStop):Runner().execute_model(NS())
   self.assertEqual(calls,['native-prepare']);v=json.loads(next(Path(td).glob('NATIVE-POSTPREPARE-*.json')).read_bytes());self.assertEqual(v['errors'][0]['error'],'actual unsupported ABI');self.assertFalse(v['all64_complete'])
   with self.assertRaises(FileExistsError):F.publish(v,{})
 def test_default_off_fresh_I_no_backend(self):
  env=dict(os.environ);env.pop('DL101R12_NATIVE_OBSERVATION_ENABLE',None)
  code='import sys;sys.path.insert(0,'+repr(str(P))+');import native_observer_plugin101r12 as N;N.register();assert not any(k in sys.modules for k in ("torch","torch_npu","vllm","vllm_ascend"))'
  z=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True);self.assertEqual(z.returncode,0,z.stderr)
 def test_actual_native_source_seam_and_no_DL_installer(self):
  proof=json.loads((P/'NATIVE_SOURCE_EVIDENCE101R12.json').read_bytes());import base64
  runner=base64.b64decode(proof['runner']['base64']);self.assertEqual(hashlib.sha256(runner).hexdigest(),F.RUNNER_SHA)
  text=runner.decode();pos=text.index('hidden_states = self._model_forward(',text.index('def execute_model('));self.assertLess(text.index('self._build_attention_metadata(',text.index('def execute_model(')),pos);self.assertLess(text.index('set_ascend_forward_context(',text.index('def execute_model(')),pos)
  plugin=(P/'native_observer_plugin101r12.py').read_text();self.assertNotIn('R.register(',plugin);self.assertNotIn('integration',plugin);self.assertNotIn('tensor_observer',plugin)
  client=(P/'client.py').read_text();self.assertIn("for name,n in(('native-postprepare',2048),):",client);self.assertEqual(client.count('response=C.request_once('),1);self.assertIn("E.need(False,'R12 single request unexpectedly returned10 output tokens",client)
if __name__=='__main__':unittest.main()
