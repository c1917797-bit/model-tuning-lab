"""Stdlib only. No device/container/build/Torch invocation."""
import ast,json,sys,unittest
from datetime import datetime,timezone
from pathlib import Path
from unittest.mock import patch
from contract import (IMAGE,LIBRARY_SHA,BUILD_SHA,META_SHA,CGROUP_BYTES,NATIVE_PINS,REPO_PINS,
 protocol,validate_identity,cgroup_limit,receipts)

class Contract(unittest.TestCase):
 def ident(self,batch=1,physical=5):
  return dict(schema="kvbp.split-launch-identity/v1",image_id=IMAGE,physical_devices=[physical],
   logical_to_physical={"0":physical},fresh_idle_verified=True,nonprivileged=True,source_canary_passed=True,
   memory_cgroup_bytes=CGROUP_BYTES,protocol=protocol(batch,physical),library_sha256=LIBRARY_SHA,
   build_receipt_sha256=BUILD_SHA,meta_receipt_sha256=META_SHA,repo_sources=REPO_PINS,native_sources=NATIVE_PINS,
   driver_sources={"fixture":"cpu-only-no-hardware-proof"},evidence={"fixture":"cpu-only"},
   preflight_utc=datetime.now(timezone.utc).isoformat())
 def test_fixed_batches_devices(self):
  for batch,physical in ((1,5),(16,6)):
   p=protocol(batch,physical);self.assertEqual(p["steps_per_case"],160);self.assertEqual(p["graph_trials"],3)
   self.assertEqual(p["slots"],batch+3);self.assertEqual(p["complete_and_per_head_l2_limit"],2e-6)
 def test_wrong_pair_or_width_rejected(self):
  for pair in ((1,6),(16,5),(2,5),(True,5),(1,True),(16,4)):
   with self.subTest(pair=pair),self.assertRaises(ValueError):protocol(*pair)
 def test_b16_dummy_schedule_unchanged(self):
  self.assertEqual(protocol(16,6)["graph_active_schedule"],[0,1,3,7,12,15,16,16])
  self.assertEqual(protocol(1,5)["graph_active_schedule"],[1])
 def test_identity_accepted_only_as_cpu_fixture(self):
  for batch,physical in ((1,5),(16,6)):
   obj=self.ident(batch,physical);validate_identity(obj,batch,physical,obj["driver_sources"])
 def test_wrong_mapping_rejected(self):
  obj=self.ident();obj["logical_to_physical"]={"0":4}
  with self.assertRaises(ValueError):validate_identity(obj,1,5,obj["driver_sources"])
 def test_cgroup_budget_or_canary_rejected(self):
  for k,v in (("memory_cgroup_bytes",16*1024**3),("nonprivileged",False),("source_canary_passed",False)):
   obj=self.ident();obj[k]=v
   with self.subTest(key=k),self.assertRaises(ValueError):validate_identity(obj,1,5,obj["driver_sources"])
 def test_source_mismatch_rejected(self):
  for k in ("driver_sources","repo_sources","native_sources"):
   obj=self.ident();obj[k]={}
   with self.subTest(key=k),self.assertRaises(ValueError):validate_identity(obj,1,5,{"fixture":"cpu-only-no-hardware-proof"})
 def test_receipt_mismatch_rejected(self):
  for k in ("library_sha256","build_receipt_sha256","meta_receipt_sha256"):
   obj=self.ident();obj[k]="0"*64
   with self.subTest(key=k),self.assertRaises(ValueError):validate_identity(obj,1,5,obj["driver_sources"])
 def test_stale_identity_rejected(self):
  obj=self.ident();obj["preflight_utc"]="2000-01-01T00:00:00+00:00"
  with self.assertRaises(ValueError):validate_identity(obj,1,5,obj["driver_sources"])
 def test_cgroup_exact_v2_limit(self):
  with patch.object(Path,"is_file",return_value=True),patch.object(Path,"read_text",return_value=str(CGROUP_BYTES)):
   self.assertEqual(cgroup_limit()["bytes"],CGROUP_BYTES)
 def test_unlimited_or_wrong_cgroup_rejected(self):
  for x in ("max",str(CGROUP_BYTES*2)):
   with patch.object(Path,"is_file",return_value=True),patch.object(Path,"read_text",return_value=x):
    with self.assertRaises(ValueError):cgroup_limit()
 def test_missing_cgroup_rejected(self):
  with patch.object(Path,"is_file",return_value=False):
   with self.assertRaises(ValueError):cgroup_limit()
 def test_existing_receipts_match_frozen_source_only(self):
  project=Path(__file__).resolve().parents[2];ext=Path("/cache/cch/qwen36-kvbuffer-parallel-20261006")
  result=receipts(ext/"build-p1-v1/build-receipt.json",ext/"meta-p1-v1/report.json",
   ext/"build-p1-v1/libqwen36_gdn_kvbuffer_parallel_ops.so",project)
  self.assertIs(result["meta_is_not_npu_proof"],True)
 def test_frozen_run_case_reused_not_rewritten(self):
  source=(Path(__file__).resolve().parent/"run.py").read_text()
  self.assertIn("oracle.run_case(a.batch,mode,trial,report,save,out)",source)
  self.assertNotIn("for step in range",source);self.assertNotIn("OUT_LIMIT =",source)
  self.assertIn('(("eager",1),("graph",3))',source)
 def test_no_top_level_runtime_import(self):
  import run
  for filename in ("run.py","contract.py"):
   tree=ast.parse((Path(__file__).resolve().parent/filename).read_text())
   for node in tree.body:
    if isinstance(node,ast.Import):
     self.assertFalse(any(n.name in ("torch","torch_npu") for n in node.names))
    elif isinstance(node,ast.ImportFrom):self.assertFalse(str(node.module).startswith(("torch","kvbuffer_parallel")))
  self.assertNotIn("torch",sys.modules);self.assertNotIn("torch_npu",sys.modules)
 def test_packet_two_owned_splits_not_tp4_performance(self):
  obj=json.loads((Path(__file__).resolve().parent/"PACKET.json").read_text())
  self.assertEqual([(x["batch"],x["physical_device"]) for x in obj["jobs"]],[(1,5),(16,6)])
  self.assertFalse(obj["executed_by_preparer"])
  for job in obj["jobs"]:
   self.assertEqual(job["container_constraints"]["memory_bytes"],CGROUP_BYTES)
   self.assertFalse(job["container_constraints"]["privileged"])
   self.assertEqual(job["container_constraints"]["physical_devices"],[job["physical_device"]])
 def test_all_python_ast(self):
  for f in Path(__file__).resolve().parent.glob("*.py"):ast.parse(f.read_text(),filename=str(f))
if __name__=="__main__":unittest.main()
