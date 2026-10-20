"""Utilization-only common resource ABI controls, no device fit claim."""
import ast,json,os,sys,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import contract090 as C,server090 as S
from repair14_ledger import previous_text
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def manifest(self):return json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
 def test_real_builder_source_parser_engine_budget_join_and_stacked_knobs_reject(self):
  m=self.manifest();argv=C.server_command();expected=dict(gpu_memory_utilization=.8,kv_cache_memory_bytes=None,num_gpu_blocks_override=None)
  self.assertEqual(C.cache_memory_config(argv,m,args=SimpleNamespace(**expected),engine=SimpleNamespace(**expected)),expected)
  for flag in('--kv-cache-memory-bytes','--num-gpu-blocks-override','--gpu-memory-utilization'):
   with self.assertRaises(ValueError):C.cache_memory_config(argv+[flag,'1'],m)
  for key,value in(('gpu_memory_utilization',.9),('kv_cache_memory_bytes',1),('num_gpu_blocks_override',32)):
   with self.assertRaises(ValueError):C.cache_memory_config(argv,m,args=SimpleNamespace(**dict(expected,**{key:value})))
  self.assertEqual(json.loads(argv[argv.index('--speculative-config')+1]),dict(method='mtp',num_speculative_tokens=8))
 def test_actual_CPU_preflight_budget_join_expression_and_receipt_dataflow(self):
  m=self.manifest();argv=C.server_command();budget=m['cache_memory_config']
  tree=ast.parse((P/'preflight114.py').read_bytes());run=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='run')
  actual=next(n for n in run.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=='cache_memory'for x in n.targets))
  scope=dict(C=C,argv=argv,m=m,args=SimpleNamespace(**budget),engine=SimpleNamespace(**budget));exec(compile(ast.fix_missing_locations(ast.Module(body=[actual],type_ignores=[])),str(P/'preflight114.py'),'exec'),scope);self.assertEqual(scope['cache_memory'],budget)
  scope['engine'].gpu_memory_utilization=.9
  with self.assertRaises(ValueError):exec(compile(ast.fix_missing_locations(ast.Module(body=[actual],type_ignores=[])),str(P/'preflight114.py'),'exec'),scope)
  self.assertIn('actual_cache_memory_config=cache_memory',(P/'preflight114.py').read_text())
 def test_actual_enabled_server_main_to_runpy_saves_same_command_and_source_budget(self):
  import identity_journal
  class NativeBoundary(Exception):pass
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);m=dict(self.manifest(),model_receipt_root=str(root));sr=C.write(root/'SOFTWARE_SOURCE.json',m);argv=C.server_command();installed=[]
   def boundary(module,run_name):
    self.assertEqual(installed,[sr]);self.assertEqual(sys.argv,[argv[2],*argv[3:]]);self.assertEqual(module,argv[2]);self.assertEqual(run_name,'__main__')
    value=C.obj(C.ref(root/'SERVER_COMMAND.json'));self.assertEqual(value['source'],sr);self.assertEqual(value['argv'],argv);self.assertEqual(value['actual_cache_memory_config'],m['cache_memory_config']);self.assertEqual(value['num_speculative_tokens'],8);self.assertEqual(os.environ['BOLE_THREE_NODE_MODEL_ENABLE'],'1');raise NativeBoundary()
   # Only software admission/frontend boundary are substituted; actual main,
   # builder, writes and environment execute. No actual parent/HAL is forged.
   with patch.object(C,'source',side_effect=lambda r:C.obj(r)),patch.object(identity_journal,'install_frontend',side_effect=lambda r:installed.append(r)),patch.object(S.runpy,'run_module',side_effect=boundary),patch.object(sys,'argv',['server090.py','--execute','--source-ref',json.dumps(sr),'--receipt-root',str(root)]),patch.dict(os.environ,{'ASCEND_RT_VISIBLE_DEVICES':'0,1,2,3'},clear=True):
    with self.assertRaises(NativeBoundary):S.main()
 def test_complete_runtime_inverse_original_math_and_HBM_guard_unchanged(self):
  import hashlib
  edits=json.loads((P/'EDITS131R16.json').read_bytes());identity=json.loads((P/'IDENTITY_EDITS131R17.json').read_bytes());current=json.loads((P/'IDENTITY_EDITS131R18.json').read_bytes())
  for n,row in edits.items():
   text=previous_text(P/n)
   outer=json.loads((P/'ROOT_WITNESS_EDITS.json').read_bytes())
   if n in outer:
    d=outer[n];self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),d['after']['sha256'])
    for e in reversed(d['edits']):
     self.assertEqual(text.count(e['after']),1);text=text.replace(e['after'],e['before'])
    self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),d['before']['sha256'])
   if n in current:
    layer=current[n];self.assertEqual(dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest()),layer['after'])
    for delta in reversed(layer['edits']):
     self.assertEqual(text.count(delta['after']),1);text=text.replace(delta['after'],delta['before'])
    self.assertEqual(dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest()),layer['before'])
   if n in identity:
    layer=identity[n];self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),layer['after']['sha256'])
    for delta in reversed(layer['edits']):
     self.assertEqual(text.count(delta['after']),1);text=text.replace(delta['after'],delta['before'])
    self.assertEqual(dict(bytes=len(text.encode()),sha256=hashlib.sha256(text.encode()).hexdigest()),layer['before'])
   self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['after']['sha256'])
   for edit in reversed(row['edits']):
    self.assertEqual(text.count(edit['after']),1);text=text.replace(edit['after'],edit['before'])
   self.assertEqual(len(text.encode()),row['before']['bytes']);self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),row['before']['sha256'])
  m=self.manifest();old=json.loads((P/'evidence/HISTORICAL_SOURCE_TEMPLATE131R15.json').read_bytes())
  for n in('model_entry.py','consume_model.py','independent_model.py','core112.py','oracle112.py','adapter.py','treeconv118.py','native_seams.py','model_calibration131r12.py','cap48_provider.py','external025.py','evidence/ORIGINAL025_SAFETY.py'):
   if n in old['files']:
    outer=json.loads((P/'ROOT_WITNESS_EDITS.json').read_bytes())
    prior=previous_text(P/n).encode()
    actual=outer[n]['before']if n in outer else dict(bytes=len(prior),sha256=hashlib.sha256(prior).hexdigest())
    self.assertEqual(actual,{k:old['files'][n][k]for k in('bytes','sha256')})
  self.assertEqual(m['resources'],old['resources']);self.assertEqual(m['profile'],old['profile']);self.assertEqual(m['native_speculative_config'],old['native_speculative_config'])
if __name__=='__main__':unittest.main()
