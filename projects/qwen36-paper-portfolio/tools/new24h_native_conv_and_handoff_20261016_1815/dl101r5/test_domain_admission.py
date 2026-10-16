"""Software-only actual088 receipt-schema mutations; never real evidence."""
import ast,copy,importlib.util,types,unittest
from pathlib import Path
from unittest.mock import patch
import owner_overlay as O
P=Path(__file__).resolve().parent
def load(p,n):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
D=load(P/'plugin/qwen36_deltalog_service/split_qualification.py','_101_receipt');D.C=O
META=load(P/'plugin/qwen36_deltalog_service/build_meta051.py','_101_unchanged_build');D.META=META
def fixture():
 # Reuse old actual build/Meta receipt ABI fixture, not its obsolete domain verdict.
 tree=ast.parse((P/'dependencies/old_test_domain_admission.py').read_bytes());fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=='fixture');ns={'D':META};exec(compile(ast.Module(body=[fn],type_ignores=[]),'<old051-Meta-fixture>','exec'),ns);m,o=ns['fixture']()
 s=o['source'];s['component_operational088']=dict(seed=2610168801,mode='eager',qualification=False)
 r=o['pair'];r.update(schema='deltalog.eager-component-operational-consumption/v088',producer=r['actual_result'],observation_complete=True,pass_gate=False,model_ready=False,performance_ready=False,validation_contract=D.CONTRACT)
 d=o['domain'];d.update(schema='deltalog.eager-component-operational-report/v088',steps=160,validation_contract=D.CONTRACT,primary=None,eager_component_operational_pass=True,graph_tested=False,full_requested_scope_pass=False,qualified=False,old069_FAIL_unchanged=True,native_is_not_mathematical_truth=True,cumulative_error_not_ignored=True)
 d['sidecar_results']=[dict(raw=x['raw'],audit=dict(passed=True,production_debug_bitwise=True,actual_input_immutable=True,actual_guard_pointer_pass=True))for x in d.pop('actual_sidecar_rows')]
 for x in d['rows']:
  if x['record']['kind']=='mixed':
   x.update(component_operational_pass=True,decode=dict(passed=True),prefill=dict(actual_native_sameinput_bitwise=True,qualified=False,flush_CPU64_relative_l2=1e-8),old_cross_history_metrics=x['metrics'],cross_history=dict(candidate_vs_independent_cumulative_CPU64=.002,native_vs_independent_cumulative_CPU64=.002,candidate_vs_native=1e-6))
  else:x['unchanged_primitive']=dict(state_error=1e-8,descriptors_exact=True,untouched_bitwise=True)
 return m,o
class Controls(unittest.TestCase):
 def run_fixture(self,m,o):
  with patch.object(O,'obj',side_effect=lambda r:o[r['label']]),patch.object(O,'obj_file',return_value=None):return D.consume(m)
 def test_complete_bounded_fixture(self):
  m,o=fixture();r=self.run_fixture(m,o);self.assertTrue(r['diagnostic_smoke_admitted']);self.assertFalse(r['model_ready']);self.assertFalse(o['old']['pass_gate'])
 def test_missing_future_predecessor(self):
  with self.assertRaises(ValueError):D.admit(O,dict(prepared_only=True))
 def test_16_or_failed_owner(self):
  for key,val in(('steps',16),('primary','failed'),('stopped_retained',False)):
   m,o=fixture();o['owner'][key]=val
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_wrong_source_join(self):
  m,o=fixture();o['owner']['target_source']={'label':'foreign'}
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old_v043_report_rejected(self):
  m,o=fixture();o['pair']['schema']='deltalog.diagnostic-consumption/v043'
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_meta_build_and_actual_plan(self):
  for key in('schema','meta','plan'):
   m,o=fixture()
   if key=='schema':o['build']['schema']='oldbuild'
   elif key=='meta':o['CPU']['actual_precast_meta']['rows'][0]['arguments']=14
   else:o['plan']['cpu_preflight']={'label':'foreign'}
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_source_files_or_seed_drift(self):
  for key in('seed','files'):
   m,o=fixture()
   if key=='seed':o['source']['component_operational088']['seed']=0
   else:o['template']['files']={}
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_missing_raw_or_reordered(self):
  for key in('records','sidecars'):
   m,o=fixture()
   if key=='records':o['domain']['rows'].pop()
   else:o['domain']['sidecar_results'].reverse()
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_bad_numeric_sidecar(self):
  m,o=fixture();o['domain']['sidecar_results'][0]['audit']['passed']=False
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_bad_sameinitial_or_flush(self):
  for key,val in(('actual_native_sameinput_bitwise',False),('flush_CPU64_relative_l2',8e-7)):
   m,o=fixture();o['domain']['rows'][0]['prefill'][key]=val
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_cumulative_error_preserved_not_erased(self):
  m,o=fixture();o['domain']['rows'][0]['cross_history']['candidate_vs_native']=float('nan')
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_old_fail_cannot_relabel(self):
  m,o=fixture();o['old']['pass_gate']=True
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_graph_or_whole_scope_promotion_rejected(self):
  for key in('graph_tested','full_requested_scope_pass','qualified'):
   m,o=fixture();o['domain'][key]=True
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_missing_anchor(self):
  m,o=fixture();o['domain']['anchors']={'1':{}}
  with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_inactive_bytes_and_copy_failure(self):
  for key in('bytes','copy'):
   m,o=fixture()
   if key=='bytes':o['domain']['rows'][0]['old_cross_history_metrics']['untouched_bitwise']=False
   else:next(x for x in o['domain']['rows']if x['record']['kind']=='copy')['unchanged_primitive']['state_error']=8e-7
   with self.assertRaises(ValueError):self.run_fixture(m,o)
 def test_complete_tails_required(self):
  m,o=fixture();o['producer']['boundary_controls'].pop()
  with self.assertRaises(ValueError):self.run_fixture(m,o)
if __name__=='__main__':unittest.main()
