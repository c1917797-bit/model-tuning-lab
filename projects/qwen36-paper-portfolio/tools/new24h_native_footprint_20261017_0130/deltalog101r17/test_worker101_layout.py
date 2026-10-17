"""Real isolated Python entry/package layout, not same-image/NPU evidence."""
import json,os,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Layout(unittest.TestCase):
 def test_actual_disjoint_deployment_cold_entries(self):
  with tempfile.TemporaryDirectory()as td:
   root=Path(td)/'actual-v1-101';root.mkdir();m=json.loads((P/'SOURCE_TEMPLATE.json').read_bytes())
   for name in m['files']:
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(P/name,target)
   shutil.copyfile(P/'SOURCE_TEMPLATE.json',root/'SOURCE_TEMPLATE.json')
   env=dict(os.environ);env.pop('QWEN36_DELTALOG_SERVICE023_ENABLE',None)
   for n in('entry.py','host_ticket.py','bind_source.py','probe.py','client.py'):
    r=subprocess.run([sys.executable,'-I','-B',str(root/n)],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
   code='import sys;sys.path.insert(0,'+repr(str(root/'plugin'))+');import qwen36_deltalog_service.runtime as R;R.register();assert R._OP is None;assert not any(x in sys.modules for x in ("torch","torch_npu","vllm","vllm_ascend"))'
   r=subprocess.run([sys.executable,'-I','-B','-c',code],env=env,capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
 def test_real_ON_missing_source_rejects_before_backend(self):
  code='import sys,os;sys.path.insert(0,'+repr(str(P/'plugin'))+');os.environ.update(QWEN36_DELTALOG_SERVICE023_ENABLE="1",QWEN36_DELTALOG_SERVICE023_MODE="diagnostic-bridge-only",QWEN36_DELTALOG_SERVICE023_SOURCE_REF="{}");from qwen36_deltalog_service import runtime as R\ntry:R.register()\nexcept (KeyError,RuntimeError,ValueError):pass\nelse:raise AssertionError("missing actual source admitted")\nassert not any(x in sys.modules for x in ("torch","torch_npu","vllm","vllm_ascend"))'
  r=subprocess.run([sys.executable,'-I','-B','-c',code],capture_output=True,text=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()
