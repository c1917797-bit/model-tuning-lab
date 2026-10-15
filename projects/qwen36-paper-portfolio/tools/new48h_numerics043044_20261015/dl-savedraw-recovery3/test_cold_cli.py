"""Real isolated interpreter front doors, not in-process sys.path fixtures."""
import subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
class ColdCLI(unittest.TestCase):
 def run_cli(self,*args):return subprocess.run([sys.executable,'-I','-B',*args],capture_output=True,text=True,timeout=20)
 def test_real_defaultOFF_runner_and_binder_import(self):
  for name,tail in(('run_recovery.py',['--phase','bind','--template-ref','{}']),('bind_recovery.py',['--template-ref','{}']),('host.py',[])):
   r=self.run_cli(str(P/name),*tail);self.assertEqual(r.returncode,0,r.stderr);self.assertIn('disabled',r.stdout);self.assertNotIn('ModuleNotFoundError',r.stderr)
 def test_actual_child_host_sourceaudit_frontdoor_has_no_local_import_dependency(self):
  r=self.run_cli(str(P/'host.py'),'--source-audit-only')
  self.assertNotEqual(r.returncode,0);self.assertNotIn('ModuleNotFoundError',r.stderr)
  if sys.platform=='win32':self.assertIn('actual Linux owner required',r.stderr)
  else:self.assertEqual(r.returncode,2);self.assertIn('--owner-ref',r.stderr)
 def test_standalone_provenance_import_with_actual_isolated_path(self):
  r=self.run_cli(str(P/'provenance.py'));self.assertEqual(r.returncode,0,r.stderr)
if __name__=='__main__':unittest.main()
