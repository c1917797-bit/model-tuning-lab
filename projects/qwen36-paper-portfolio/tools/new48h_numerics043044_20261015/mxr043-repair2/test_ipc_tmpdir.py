import importlib.util,os,sys,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def leaf(name):
 s=importlib.util.spec_from_file_location("_ipcR2"+name,P/(name+".py"));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class IPC(unittest.TestCase):
 def test_source_bound_TMPDIR_alias_only(self):
  M=leaf("external_output_policy")
  e=dict(external_output_policy=True,external_output_root="/opt/host/vnf/austinov/test",mounts={"/adakv-results":("/opt/host/vnf/austinov/test/candidate",True)})
  env=M.environment(e);self.assertEqual(env["TMPDIR"],"/adakv-results")
  for key,value in M.CACHE_NAMES.items():
   if key!="TMPDIR":self.assertEqual(env[key],"/adakv-results/.runtime/"+value)
  e["mounts"]["/adakv-results"]=("/cache/foreign",True)
  with self.assertRaises(ValueError):M.environment(e)
 @unittest.skipUnless(sys.platform=="linux","real AF_UNIX scan/consume must execute in same-image Devices[] CPU; Windows not qualification")
 def test_actual_Linux_socket_contract(self):
  # Linux MAIN runs the explicit original-owned alias, not arbitrary /tmp.
  v=leaf("ipc_controls").run("/adakv-results");self.assertTrue(v["actual_Linux_AF_UNIX"])
if __name__=="__main__":unittest.main()
