import importlib.util,subprocess,sys,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
def load():
 s=importlib.util.spec_from_file_location('_sidecar_inverse',P/'verify_inverse.py');M=importlib.util.module_from_spec(s);s.loader.exec_module(M);return M
class Controls(unittest.TestCase):
 def test_inverse8_actual(self):self.assertEqual(len(load().verify(P)),8)
 def test_hidden_arithmetic_rejected(self):
  original=Path.read_text
  def corrupt(p,*args,**kw):
   t=original(p,*args,**kw)
   if p.name=='qwen36_gdn_deltalog_decode_readout_sidecar_v015.h':t=t.replace('DataCopy(precastGm_[offset], attnUb_, rows);','Adds(attnUb_, attnUb_, 1.0f, rows);\n        DataCopy(precastGm_[offset], attnUb_, rows);')
   return t
  with patch.object(Path,'read_text',corrupt):
   with self.assertRaises(ValueError):load().verify(P)
 def test_original_arithmetic_rejected(self):
  original=Path.read_text
  def corrupt(p,*args,**kw):
   t=original(p,*args,**kw)
   return t.replace('Add(attnUb_, attnUb_, vUb_, rows);','Sub(attnUb_, attnUb_, vUb_, rows);')if p.name.endswith('sidecar_v015.h')else t
  with patch.object(Path,'read_text',corrupt):
   with self.assertRaises(ValueError):load().verify(P)
 def test_real_default_off(self):
  for f in('compare_step.py','consume_step.py','kernel/build_pair.py','build_owner/host.py','build_owner/guest.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/f)],capture_output=True,text=True);self.assertEqual(r.returncode,0,(f,r.stderr))
if __name__=='__main__':unittest.main()
