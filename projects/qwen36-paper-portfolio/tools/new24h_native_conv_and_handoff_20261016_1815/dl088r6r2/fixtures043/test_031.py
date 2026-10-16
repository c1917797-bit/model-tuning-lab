import ast,copy,hashlib,importlib.util,json,pathlib,re,sys,tempfile,types,unittest
P=pathlib.Path(__file__).resolve().parent
def load(n):
 s=importlib.util.spec_from_file_location(n,P/(n+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Controls(unittest.TestCase):
 def test_original_math_and_diagnostic_inverse(self):
  m=json.loads((P/'BASELINE035.json').read_text())
  for n in('oracle.py','consume.py','consume_increment.py','flush_increment.py','qwen36_deltalog_fresh/primitives.py','qwen36_deltalog_fresh/provider.py','scope_adapter.py'):
   self.assertEqual(hashlib.sha256((P/n).read_bytes()).hexdigest(),m['files'][n]['sha256'])
 def test_host_inverse_and_streamed_three_loops(self):
  s=(P/'host.py').read_text()
  for a,b in reversed(json.loads((P/'HOST_DELTA035R1.json').read_text())['changes']):self.assertEqual(s.count(b),1);s=s.replace(b,a)
  s=s.replace('deltalog-diagnostic-bridge-new48h-MAIN-035','deltalog-diagnostic-bridge-new48h-MAIN-031-repair1').replace('/v035','/v031');d=json.loads((P/'HOST_INVERSE.json').read_text())
  for a,b in reversed(d['changes']):self.assertEqual(s.count(a),1);s=s.replace(a,b)
  self.assertEqual(hashlib.sha256(s.encode()).hexdigest(),d['original_sha256'])
  current=(P/'host.py').read_text();self.assertIn('for f in refs:validate_ref_streamed(f)',current);self.assertIn('[validate_ref_streamed(r)for r in refs]',current);self.assertIn('for r in refs:validate_ref_streamed(r)',current)
  self.assertLess(current.index('patch.install(adapter,topguard)'),current.index('_adapter_protected=adapter.protected_observation'))
 def test_smoke_scope_and_false_qualification(self):
  g=load('preregister');s={'source':1};c=dict(schema='deltalog.diagnostic-consumption/v035',source=s,actual_result={'p':1},validation_contract=dict(schema='deltalog.independent-CPU64-operational-recurrence-direct-integer-BF16-RNE/v035'),diagnostic_capture_complete=True,domain_checks_pass=True,complete_proof=False,original_strict_result_preserved=dict(pass_gate=False,primary='old real failure'))
  o=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=s,stage='numeric',steps=16,stopped_retained=True,primary=None,secondary=[],bridge_primitive_gate_pass=False,model_ready=False,result={'p':1})
  self.assertFalse(g.admit_smoke(o,s,c)['qualification'])
  for key,bad in [('stopped_retained',False),('bridge_primitive_gate_pass',True),('model_ready',True)]:
   v=dict(o);v[key]=bad
   with self.assertRaises(ValueError):g.admit_smoke(v,s,c)
 def test_metric_batch_mask_and_missing(self):
  import torch
  d=load('domain_consumer');R=types.SimpleNamespace(STATE_LIMIT=7.92e-7,OUTPUT_LIMIT=.00303)
  truth=torch.tensor([[1000.],[1.]],dtype=torch.float64);bad=truth.clone();bad[1]+=.01
  globalerror=float((bad-truth).abs().max()/truth.abs().max());smallerror=float((bad[1]-truth[1]).abs().max()/truth[1].abs().max())
  self.assertTrue(d.bounded(dict(state_error=0.,output_error=globalerror),R));self.assertFalse(d.bounded(dict(state_error=0.,output_error=smallerror),R))
  with self.assertRaises(ValueError):d.bounded({},R)
  copy_metrics=dict(state_error=0.,bitwise=True,untouched_bitwise=True,conv_bitwise=True,descriptors_exact=True)
  self.assertTrue(d.copy_bounded(copy_metrics,R));copy_metrics['conv_bitwise']=False;self.assertFalse(d.copy_bounded(copy_metrics,R))
 def test_runtime_after_operands_strict_source(self):
  s=(P/'domain_consumer.py').read_text();self.assertIn("a['input_fingerprints'][name]==op['actual']",s)
  f=(P/'qwen36_deltalog_fresh/capture_evidence.py').read_text();self.assertIn("after['controls']==before['controls']",f)
 def test_source_and_defaultoff_cli(self):
  import subprocess
  for n in('host.py','consume_pair.py','domain_entry.py','entry.py','producer.py','consume.py','bind_composite.py'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True);self.assertEqual(p.returncode,0,(n,p.stderr))
  self.assertIn("json.dumps(m['composite_cpu_owner_ref'])",(P/'run031.py').read_text())
if __name__=='__main__':unittest.main()
