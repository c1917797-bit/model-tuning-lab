import unittest,subprocess,os,sys
from pathlib import Path
W=Path(__file__).resolve().parent.parent
class BootstrapControls(unittest.TestCase):
 def run_child(self,graph,compile):
  env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",INDEPENDENT_GRAPH_HYPIC=graph,INDEPENDENT_COMPILATION_BUDGET=compile)
  env["PYTHONPATH"]=str(W/"compilation_budget_r45")+os.pathsep+str(W)
  return subprocess.run([sys.executable,"-B","-c","import sys; print('MAIN_REACHED'); assert not any(x.startswith('triton')for x in sys.modules)"],env=env,capture_output=True,text=True,timeout=15)
 def test_disabled_does_not_import_inference(self):
  r=self.run_child("0","0");self.assertEqual(r.returncode,0,r.stderr);self.assertIn("MAIN_REACHED",r.stdout)
 def test_invalid_switch_fails_before_main(self):
  r=self.run_child("0","x");self.assertNotEqual(r.returncode,0);self.assertNotIn("MAIN_REACHED",r.stdout)
 def test_enabled_without_owned_graph_fails_before_main(self):
  r=self.run_child("0","1");self.assertNotEqual(r.returncode,0);self.assertNotIn("MAIN_REACHED",r.stdout)
if __name__=="__main__":unittest.main()
