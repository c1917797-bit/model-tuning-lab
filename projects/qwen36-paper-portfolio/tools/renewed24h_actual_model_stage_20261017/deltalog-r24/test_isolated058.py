"""Actual isolated guest and consumer prefix reaches immutable Ref checking."""
import subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class Isolated(unittest.TestCase):
 def test_real_isolated_execute_frontdoors_without_backend(self):
  for name in('entry.py','client.py','consume.py'):
   p=subprocess.run([sys.executable,'-I','-B',str(P/name),'--execute','--source-ref','{}'],capture_output=True,text=True,timeout=15)
   self.assertNotEqual(p.returncode,0);self.assertIn("KeyError: 'path'",p.stderr)
   self.assertNotIn('ModuleNotFoundError',p.stderr);self.assertNotIn('UnboundLocalError',p.stderr)
if __name__=='__main__':unittest.main()
