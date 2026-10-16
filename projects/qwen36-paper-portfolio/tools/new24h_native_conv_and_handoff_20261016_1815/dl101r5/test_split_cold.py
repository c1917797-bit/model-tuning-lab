"""Real cold entry/source receiver checks, no fake NPU receipts persisted."""
import ast,importlib.util,os,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_actual_cold_model_and_binder_defaultOFF(self):
  for n in('host_ticket.py','bind_source.py','entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=20)
   self.assertEqual(r.returncode,0,r.stderr)
   self.assertTrue('false'in r.stdout or'disabled'in r.stdout)
 def test_actual_new_plugin_OFF_does_not_import_backend(self):
  code="import sys;sys.path.insert(0,"+repr(str(P/'plugin'))+");import qwen36_deltalog_service.runtime as R;R.register();assert not any(x in sys.modules for x in ('torch','torch_npu','vllm','vllm_ascend'));assert R._OP is None"
  env=dict(os.environ);env.pop('QWEN36_DELTALOG_SERVICE023_ENABLE',None)
  r=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
 def test_shared_reader_model_worker_and_namespace_actual_sources(self):
  runtime=(P/'plugin/qwen36_deltalog_service/runtime.py').read_text(encoding='utf8')
  original=(P.parent/'deltalog-service-composite-new48h-20261015-023-repair1/qwen36_deltalog_service/runtime.py').read_text(encoding='utf8')
  prelude=" for precision_group in('matmul','conv'):\n  precision=getattr(torch.npu,precision_group);A.need(type(precision.allow_hf32)is bool,'actual common HF32 property')\n  precision.allow_hf32=False;A.need(precision.allow_hf32 is False,'model smoke shares explicit PF071 HF32 OFF')\n"
  witness="  A.need(torch.npu.matmul.allow_hf32 is False and torch.npu.conv.allow_hf32 is False,'actual unchanged model common HF32 policy')\n  emit('actual_common_precision_policy',matmul_allow_hf32=False,conv_allow_hf32=False,phase='first-real-layer-before-core')\n"
  self.assertEqual(runtime.count(prelude),1);self.assertEqual(runtime.count(witness),1);self.assertEqual(runtime.replace(prelude,'').replace(witness,''),original)
  a=(P/'plugin/qwen36_deltalog_service/admission.py').read_text(encoding='utf8');d=(P/'domain_qualification.py').read_text(encoding='utf8')
  self.assertIn('Q.admit(Reader,m)',a);self.assertIn('api(m).admit(C,m)',d)
  self.assertIn('qwen36_deltalog_split_scale_v051',(P/'plugin/qwen36_deltalog_service/contract.py').read_text(encoding='utf8'))
  self.assertIn("namespace='qwen36_deltalog_split_scale_sidecar_v051'",(P/'tensor_observer.py').read_text(encoding='utf8'))
 def test_pending_source_rejects_before_library_or_backend(self):
  code="import sys;sys.path.insert(0,"+repr(str(P/'plugin'))+");from qwen36_deltalog_service import split_qualification as Q;\nclass C:\n @staticmethod\n def need(v,m):\n  if not v:raise ValueError(m)\n\ntry:Q.admit(C,{'admission_mode':Q.MODE})\nexcept ValueError:pass\nelse:raise AssertionError('missing reviewed pins admitted')\nassert 'torch' not in sys.modules"
  r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
 def test_new_CPU_Meta_source_and_160_owner_contract_implemented(self):
  s=(P/'plugin/qwen36_deltalog_service/split_qualification.py').read_text(encoding='utf8');ast.parse(s)
  for x in("o['source']==o['target_source']==sr",'len(sides)==351',"o['steps']==160",'META.actual_build_meta',"deltalog.eager-component-operational-consumption/v088"):
   self.assertIn(x,s)
  meta=(P/'plugin/qwen36_deltalog_service/build_meta051.py').read_text()
  for x in("cpu_owner['result']","plan['cpu_preflight']","deltalog.split-scale-actual-Meta/v051"):self.assertIn(x,meta)
if __name__=='__main__':unittest.main()
