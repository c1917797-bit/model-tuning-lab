"""Source/protocol tests only. No fixture or source test is NPU/model authority."""
import ast,copy,json,sys,unittest
from pathlib import Path
import component_handoff as h,source_contract as c,service_contract as service
class SourceInterfaces(unittest.TestCase):
 def current(self):return c.obj(h.PROPOSED)
 def test_actual_current_manifest_AND_math_pins(self):
  x=h.proposed_source_interfaces();self.assertEqual((x["source_count"],x["own_count"],x["cases"],x["steps"]),(42,31,128,20480))
  self.assertFalse(x["ready"]);self.assertNotIn("torch",sys.modules)
 def test_actual_nine_argument_reader_without_importing_candidate(self):
  raw=(c.KERNEL/"consume_numeric.py").read_text();self.assertEqual(h.signature(raw),h.CONSUME_ARGS)
 def test_foreign_or_extra_signature_rejected(self):
  raw=(c.KERNEL/"consume_numeric.py").read_text()
  for modified in (raw.replace("host_result_sha):","host_result_sha,extra):"),raw.replace("def consume(root,","def consume(foreign_root,")):
   with self.assertRaises(ValueError):h.signature(modified)
 def test_old_native_manifest_does_not_get_union_acceptance(self):
  ref=copy.deepcopy(h.CURRENT);ref["sha256"]="a3103963216cc1e63ebdefef500bdbd5569e1984230f399d42327f765d9c5b6a"
  with self.assertRaises(ValueError):h.manifest(self.current(),ref)
 def test_wrong_count_rejected(self):
  m=self.current();m["source_count"]=29
  with self.assertRaises(ValueError):h.manifest(m,h.CURRENT)
 def test_retired_consumer_schema_or_source_pin_rejected(self):
  m=self.current();m["files"]["consume_numeric.py"]="0"*64
  with self.assertRaises(ValueError):h.manifest(m,h.CURRENT)
 def test_threshold_or_capture_trial_change_rejected(self):
  for key,value in (("original_relative_rms",.006),("original_cosine",.99),("graph_trials",2)):
   m=self.current();m[key]=value
   with self.assertRaises(ValueError):h.manifest(m,h.CURRENT)
 def test_old_stage_equality_requirement_not_quietly_relaxed(self):
  m=self.current();m["registered_author_successor"]["stage_equality"]="one ULP"
  with self.assertRaises(ValueError):h.manifest(m,h.CURRENT)
 def test_all_new_root_owner_paths_agree(self):
  root=Path(__file__).parent
  self.assertEqual(service.INTEGRATED,root)
  self.assertEqual(c.KERNEL_SHA,h.CURRENT["sha256"])
  self.assertIn('OWNER="sparq-author-ann-fp32-stock-full-v3"',(root/"host_run.py").read_text())
  self.assertIn('"model-tuning-lab.owner":"sparq-author-ann-fp32-stock-full-v3"',(root/"consume_model.py").read_text())
  self.assertIn(h.CURRENT["sha256"],(root/"long_workspace.py").read_text())
  self.assertNotIn("a3103963216cc1e63",(root/"long_workspace.py").read_text())
 def test_real_whole_original_failed_fixture_rejected_before_model(self):
  from original_terminal import original_terminal
  raw=json.loads((c.KERNEL/"original_operation_get_ma0e7f_not_found.json").read_text())
  with self.assertRaises(ValueError):original_terminal(raw,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_component_refs_and_nineargument_dispatch_actual_SOURCE(self):
  s=(Path(__file__).parent/"source_contract.py").read_text()
  self.assertIn('h.source_interfaces()',s)
  self.assertIn('("receipt","receipt.py"),("numeric_gate","numeric_gate.py"),("preflight","preflight.py"),("host","host.py")',s)
  self.assertIn('checked=consumer.consume(output/"gate"',s)
  self.assertIn('canonical(checked)==canonical(x)',s)
  s=(Path(__file__).parent/"service_contract.py").read_text();self.assertIn("return readonly_component_mounts(ref)",s)
 def test_facade_ON_cannot_change_original_MAIN_command(self):
  source=(Path(__file__).parent/"entry.py").read_text()
  self.assertNotIn("os.execve(",source)
  self.assertIn("MAIN runtime entry is exact host_run.py",source)
  source=(Path(__file__).parent/"host_run.py").read_text()
  self.assertIn('expected_host_argv=["/usr/bin/python3","-B",str(c.BASE/"host_run.py")',source)
if __name__=="__main__":unittest.main()
