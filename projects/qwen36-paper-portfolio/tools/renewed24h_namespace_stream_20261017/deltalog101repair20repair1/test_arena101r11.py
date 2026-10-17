import hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from unittest.mock import patch
from pathlib import Path
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('_test_actual_arena101R11',P/'plugin/qwen36_deltalog_service/arena_observation101r11.py');O=importlib.util.module_from_spec(spec);spec.loader.exec_module(O)
class ArenaObservation(unittest.TestCase):
 def test_actual_CPU_views_half_open_ranges(self):
  import torch
  x=torch.empty((4,12,128,128));a=O.geometry(x[:2]);b=O.geometry(x[2:]);self.assertEqual(a['storage_ptr'],b['storage_ptr']);self.assertEqual(a['end'],b['start']);self.assertGreater(b['storage_offset'],0)
  whole=O.geometry(x);overlap=lambda a,b:not(a['end']<=b['start']or a['start']>=b['end'])
  self.assertTrue(overlap(whole,whole));self.assertFalse(overlap(O.geometry(x[:1]),O.geometry(x[1:2])));self.assertTrue(overlap(O.geometry(x[:1]),O.geometry(x[:1])))
 def test_collect48_metadata_no_committed_or_numeric_claim(self):
  import numpy as np,torch
  ns=types.SimpleNamespace;x=torch.empty((2,12,128,128));layers=[ns(prefix='layer%d'%i,layer_idx=i,kv_cache=[None,x])for i in range(48)];groups=[ns(layer_names=[v.prefix for v in layers[i*24:(i+1)*24]],kv_cache_spec=ns(shapes=((12,128,128),),dtypes=(torch.float32,),page_size_bytes=786432))for i in range(2)];tables=[ns(is_mamba_group=True,num_blocks_per_row=np.array([1]),get_numpy_array=lambda i=i:np.array([[i]],dtype=np.int32))for i in range(2)];r=ns(compilation_config=ns(static_forward_context={v.prefix:v for v in layers}),kv_cache_config=ns(kv_cache_groups=groups,kv_cache_tensors=[ns(size=x.numel()*4,shared_by=[v.prefix for v in layers])]),input_batch=ns(req_ids=['software'],block_table=ns(block_tables=tables)),requests={'software':ns(block_ids=([0],[1]))});scheduler=ns(num_scheduled_tokens={'software':2048},total_num_scheduled_tokens=2048,scheduled_new_reqs=[ns(req_id='software',block_ids=([0],[1]))],scheduled_cached_reqs=ns(req_ids=[],new_block_ids=[],resumed_req_ids=set()))
  value=O.collect(r,[(v,i//24)for i,v in enumerate(layers)],scheduler);self.assertEqual(len(value['all48']),48);self.assertEqual(len(value['collisions']),1128);self.assertFalse(value['actual_committed_slot_proof']);self.assertFalse(value['guard_bypassed']);self.assertFalse(value['numerical_qualified']);self.assertEqual(value['CPU_tables'][1]['rows'][0]['values'],[1]);json.dumps(value,allow_nan=False)
  with tempfile.TemporaryDirectory()as td:
   def ref(p):
    b=p.read_bytes();return dict(path=str(p.resolve()),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
   source=Path(td)/'SOFTWARE_SOURCE.json';source.write_text(json.dumps(dict(files={'qwen36_deltalog_service/arena_observation101r11.py':ref(Path(O.__file__))})),encoding='utf8');sr=ref(source)
   with patch.dict(os.environ,dict(QWEN36_DELTALOG_SERVICE023_SOURCE_REF=json.dumps(sr),QWEN36_DELTALOG_TRACE025_SOURCE_REF=json.dumps(sr),QWEN36_DELTALOG_SERVICE023_AUDIT=td)):
    O.capture(r,[(v,i//24)for i,v in enumerate(layers)],scheduler)
    with self.assertRaises(FileExistsError):O.capture(r,[(v,i//24)for i,v in enumerate(layers)],scheduler)
   saved=json.loads(next(Path(td).glob('ARENA-REGISTRATION-*.json')).read_bytes());self.assertFalse(saved['numerical_qualified']);self.assertEqual(saved['runtime_source'],sr)
 def test_original_guard_preserved_and_capture_precedes(self):
  m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());r=m['original_arena_guard_ref'];b=(P/'plugin/qwen36_deltalog_service/builder_mirror.py').read_bytes();self.assertIn(b'registered actual layer arenas must not overlap',b);self.assertEqual((len(b),hashlib.sha256(b).hexdigest()),(r['bytes'],r['sha256']));s=(P/'plugin/qwen36_deltalog_service/integration.py').read_text();self.assertLess(s.index('capture(r,rows,'),s.index('receipt=M.register_layers'));self.assertLess(s.index('receipt=M.register_layers'),s.index('return prepare(r,*a,**kw)'))
