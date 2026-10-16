"""Cross-package recovered reader invocation; software fixtures never actual PASS."""
import ast,copy,hashlib,importlib.util,json,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(path,name):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def receiver():
 m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes());r=m['recovery_receiver_template_ref'];q=Path(r['path'])
 if os.name=='nt':q=P.parent/'deltalog-recovered-model-receiver-new24h-128-repair1/SOURCE_TEMPLATE.json'
 b=q.read_bytes();assert len(b)==r['bytes']and hashlib.sha256(b).hexdigest()==r['sha256'];source=json.loads(b)
 rr=source['files']['receiver128.py'];f=Path(rr['path'])
 if os.name=='nt':f=q.parent/'receiver128.py'
 assert hashlib.sha256(f.read_bytes()).hexdigest()==rr['sha256'];return load(f,'_101R6_actual128_receiver'),q.parent
class Controls(unittest.TestCase):
 def test_real_shared_shim_missing_plan_rejects_no_backend(self):
  import subprocess
  code="import sys;sys.path.insert(0,"+repr(str(P/'plugin'))+");from qwen36_deltalog_service import split_qualification as Q\nclass C:\n @staticmethod\n def need(v,s):\n  if not v:raise ValueError(s)\ntry:Q.admit(C,{'admission_mode':Q.MODE})\nexcept ValueError:pass\nelse:raise AssertionError('missing actual recovery admitted')\nassert 'torch' not in sys.modules and 'torch_npu' not in sys.modules\n"
  r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
 def fixture(self):
  R,rp=receiver();T=load(rp/'reader_transform128.py','_101R6_actual_transform')
  F=load(P/'test_domain_admission.py','_101R6_historical_fixture');m,o=F.fixture();old=o['owner']
  old.update(primary="independent consumer ValueError('actual GE child failed; preserved logs/raw')",diagnostic_capture_complete=False,independent_consumer=None)
  o['old']['primary']="ValueError('independent raw numerical/bitwise gate')"
  rs={'label':'distinct recovery software fixture'}
  stage=dict(schema='deltalog.anchor-consumer-CPU-recovery/v127',source=rs,producer_source=m['bridge024_source_ref'],actual_original_producer=old['result'],preserved_original_strict={'label':'old'},domain={'label':'domain'},pass_gate=True,diagnostic_capture_complete=True,domain_checks_pass=True,old_failure_unchanged=True,NPU=False,NPU_reexecuted=False,model_ready=False,model_admitted=False,performance_ready=False)
  proof=dict(consumer_source=rs,recovery_owner={'label':'distinct-recovery-owner'},stage_ref={'label':'distinct-stage'},receiver_source={'label':'exact128'})
  raw=(P/'dependencies/original_split_reader101.py').read_bytes();text=T.transform(raw);self.assertEqual(T.inverse(text),raw)
  ns={'__name__':'_101R6_actual_recovered_predicates','__file__':str(P/'dependencies/original_split_reader101.py')};exec(compile(text,'<actual128-original101-whole-inverse>','exec'),ns)
  class Reader:
   need=staticmethod(F.O.need)
   @staticmethod
   def obj(r):return o[r['label']]
   @staticmethod
   def obj_file(r):return None
  ns.update(C=Reader,META=F.META,RECOVERY=lambda c,x:(old,o['producer'],stage,proof));return ns,m,o,stage
 def test_actual_transform_all_numeric_tail_positive_no_old_success_alias(self):
  ns,m,o,stage=self.fixture();r=ns['consume'](m);self.assertTrue(r['diagnostic_smoke_admitted']);self.assertFalse(r['model_ready']);self.assertIsNotNone(o['owner']['primary']);self.assertIsNone(o['owner']['independent_consumer']);self.assertFalse(o['old']['pass_gate'])
 def test_actual_recovered_tail_bad_state_sidecar_history_and_cardinality(self):
  for kind in('state','sidecar','history','missing','wrongrecovery'):
   ns,m,o,stage=self.fixture()
   if kind=='state':o['domain']['rows'][0]['prefill']['flush_CPU64_relative_l2']=7.93e-7
   elif kind=='sidecar':o['domain']['sidecar_results'][0]['audit']['passed']=False
   elif kind=='history':o['domain']['rows'][0]['cross_history']['candidate_vs_native']=float('nan')
   elif kind=='missing':o['domain']['rows'].pop()
   else:stage['schema']='deltalog.eager-component-operational-consumption/v088'
   with self.assertRaises(ValueError):ns['consume'](m)
if __name__=='__main__':unittest.main()
