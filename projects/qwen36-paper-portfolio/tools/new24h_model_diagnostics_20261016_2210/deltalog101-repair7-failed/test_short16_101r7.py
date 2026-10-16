"""New short-prior scope, not a truncated old160 certificate or real PASS."""
import copy,hashlib,importlib.util,json,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import owner_overlay as O,test_domain_admission as OLD
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
Q=load(P/'plugin/qwen36_deltalog_service/split_qualification.py','_actual101R7_typed16');Q.C=O;Q.META=OLD.META
def fixture():
 m,o=OLD.fixture();m['short_model_diagnostic_scope']=Q.SHORT_SCOPE
 o['owner']['steps']=o['producer']['steps']=o['domain']['steps']=16
 o['producer']['records']=[r for r in o['producer']['records']if r['kind']!='mixed'or r['step']<16]
 o['domain']['rows']=[x for x in o['domain']['rows']if x['record']['kind']!='mixed'or x['record']['step']<16]
 sides=o['producer']['actual_sidecar_records'];keep=sides[:16]+sides[160:176]+sides[320:];paths={x['path']for x in keep}
 o['producer']['actual_mixed_sidecar_records']=sides[:16]+sides[160:176];o['producer']['actual_sidecar_records']=keep
 o['domain']['sidecar_results']=[x for x in o['domain']['sidecar_results']if x['raw']['path']in paths]
 def remap(v):
  if type(v)is dict:
   if set(v)=={'label'}and v['label']in('source','owner','cpu_owner'):return copy.deepcopy(Q.ACTUAL[v['label']])
   return{k:remap(x)for k,x in v.items()}
  if type(v)is list:return[remap(x)for x in v]
  return v
 return remap(m),remap(o)
def consume(m,o):
 def obj(r):
  for k,v in Q.ACTUAL.items():
   if r==v:return o[k]
  return o[r['label']]
 with patch.object(O,'obj',side_effect=obj),patch.object(O,'obj_file',return_value=None):return Q.consume(m)
class Short16Controls(unittest.TestCase):
 def test_complete_new40_63_fixture_only_diagnostic(self):
  m,o=fixture();r=consume(m,o)
  self.assertEqual(r['schema'],'deltalog.actual16-to-model-diagnostic-admission/v101-repair7');self.assertTrue(r['diagnostic_smoke_admitted'])
  for k in('model_ready','model_numeric_qualified','performance_ready','task_ready','long_history_160_qualified','production_admitted'):self.assertIs(r[k],False)
  self.assertFalse(o['old']['pass_gate'])
 def test_legacy160_and_scope_missing_wrong_source_rejected(self):
  m,o=OLD.fixture()
  with self.assertRaises(ValueError):consume(m,o)
  m,o=fixture();o['owner']['steps']=160
  with self.assertRaises(ValueError):consume(m,o)
  m,o=fixture();o['owner']['target_source']={'label':'foreign'}
  with self.assertRaises(ValueError):consume(m,o)
 def test_missing_reordered_failed_boundary_history_and_release_rejected(self):
  for case in('row','side','boundary','state','history','oldstrict','release','meta'):
   m,o=fixture()
   if case=='row':o['domain']['rows'].pop()
   if case=='side':o['domain']['sidecar_results'].reverse()
   if case=='boundary':o['domain']['sidecar_results'][0]['audit']['passed']=False
   if case=='state':next(x for x in o['domain']['rows']if x['record']['kind']=='mixed')['prefill']['flush_CPU64_relative_l2']=1e-4
   if case=='history':next(x for x in o['domain']['rows']if x['record']['kind']=='mixed')['cross_history']['candidate_vs_independent_cumulative_CPU64']=float('nan')
   if case=='oldstrict':o['old']['primary']='changed oldFAIL'
   if case=='release':o['owner']['stopped_retained']=False
   if case=='meta':o['CPU']['actual_precast_meta']['rows'][0]['arguments']=14
   with self.assertRaises(ValueError,msg=case):consume(m,o)
 def test_whole160_reader_inverse_and_math_protected(self):
  inv=json.loads((P/'INVERSE101R7.json').read_bytes());text=(P/'plugin/qwen36_deltalog_service/split_qualification.py').read_text(encoding='utf8');text=text[:text.index('\nSHORT_SCOPE=')]
  for a,b in reversed(inv['reader_edits']):self.assertEqual(text.count(b),1);text=text.replace(b,a,1)
  self.assertEqual(text.encode(),(P/'dependencies/original_split_reader101.py').read_bytes())
  for n in('tensor_consumer.py','tensor_observer.py','precast.py','sidecar_audit.py','sidecar_capture.py','plugin/qwen36_deltalog_service/runtime.py','plugin/qwen36_deltalog_service/primitives.py'):self.assertIn(n,inv['mathematical_files_unchanged'])
 def test_actual_split_cold_ON_stops_before_backend_without_actual_refs(self):
  code='import sys;sys.path.insert(0,'+repr(str(P))+');import owner_overlay as O\ntry:O.model_gate({"admission_mode":"actual052-split-scale-diagnostic-only","prepared_only":False})\nexcept (ValueError,KeyError):pass\nelse:raise AssertionError("missing actual16 admitted")\nassert not any(n in sys.modules for n in ("torch","torch_npu","vllm","vllm_ascend"))'
  r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_actual_bind_source_propagates_typed_scope_to_worker(self):
  text=(P/'bind_source.py').read_text(encoding='utf8');self.assertIn("for k in('short_model_diagnostic_scope','admission_mode'",text)
  top=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());pm=json.loads((P/'plugin/SOURCE_TEMPLATE.json').read_bytes());self.assertEqual(top['short_model_diagnostic_scope'],pm['short_model_diagnostic_scope'])
  self.assertIn('MODEL101R7',top['output_root']);self.assertNotEqual(top['root'],top['reviewed_domain_template_ref']['path'].rsplit('/',1)[0])
  commands=json.loads((P/'COMMANDS.json').read_bytes());args=commands['binding']['args'];actual=top['actual_short_component_prerequisites']
  for flag,key in(('--bridge-source-ref','source'),('--bridge-owner-ref','owner'),('--component-cpu-owner-ref','cpu_owner')):self.assertEqual(json.loads(args[args.index(flag)+1]),actual[key])
  for r in top['preserved_failed_long_history'].values():self.assertIn(r,top['dependencies'])
  self.assertIn('post-source-fence original cleanup/phase/cutoff exceeded',(P/'run_owned.py').read_text(encoding='utf8'))
if __name__=='__main__':unittest.main()
