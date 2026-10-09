"""Source-owned regressions. Pure actual assignment method; NOT NPU/model proof."""
import ast,copy,hashlib,os,sys,types,unittest
from pathlib import Path
import identity_bridge as h,source_contract as c
INPUT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/native009-public-aclgraph-input-source-v1-001/input_processor.py")
HELPER=Path("/cache/cch/qwen36-paper-preparation-20261007/recurrent/vllm023-completion-identity-oracle-v1-user72h-20261009/source_contract.py")
def actual_assignment(disabled):
 extracted=c.module(HELPER,"88a6dcf25d0e720fa5da305edc970be9a2b07310f5ef3d8ab16d4e8843e29a1c","_sparq_identity_test_actual_extract")
 # Actual pure byte-bound method only; these collaborators are software inputs,
 # not runtime modules/DeviceOperator/HAL/architecture replacements.
 return extracted.extracted_function(INPUT,"InputProcessor","assign_request_id",
  dict(envs=types.SimpleNamespace(VLLM_DISABLE_REQUEST_ID_RANDOMIZATION=disabled),
   logger=types.SimpleNamespace(warning_once=lambda *a:None),random_uuid=lambda:"0123456789abcdef"))
class IdentityN1(unittest.TestCase):
 def source(self,name):return Path(__file__).with_name(name).read_text()
 def event(self,disabled=True,external=None):
  request=types.SimpleNamespace(request_id="cmpl-proof-0",external_req_id=external)
  before=request.request_id;actual_assignment(disabled)(request)
  return dict(schema="vllm023.actual-assignment/v1",source_sha256=h.ASSIGN_SHA,
   before_request_id=before,before_external_req_id=external,
   after_request_id=request.request_id,after_external_req_id=request.external_req_id,
   disable_request_id_randomization=disabled)
 def test_actual_source_bytes_not_assumed(self):self.assertEqual(hashlib.sha256(INPUT.read_bytes()).hexdigest(),h.ASSIGN_SHA)
 def test_actual_off_body_and_oracle(self):
  self.assertEqual(h.oracle().validate_assignment("cmpl-proof",h.PROFILE,self.event()),("cmpl-proof-0","cmpl-proof-0"))
 def test_actual_on_body_records_not_predicts_suffix(self):
  self.assertEqual(h.oracle().validate_assignment("cmpl-proof",h.PROFILE,self.event(False))[1],"cmpl-proof-0-01234567")
 def test_actual_repeated_assignment_rejects(self):
  with self.assertRaises(ValueError):self.event(True,"already-assigned")
 def test_wrong_passed_id_rejects(self):
  e=self.event();e["before_request_id"]="foreign"
  with self.assertRaises(ValueError):h.oracle().validate_assignment("cmpl-proof",h.PROFILE,e)
 def test_changed_assignment_source_rejects(self):
  e=self.event();e["source_sha256"]="0"*64
  with self.assertRaises(ValueError):h.oracle().validate_assignment("cmpl-proof",h.PROFILE,e)
 def test_missing_actual_common_flag_rejects(self):
  with self.assertRaises(ValueError):h.validate_worker_flag({})
 def test_worker_disagrees_with_common_off_rejects(self):
  with self.assertRaises(ValueError):h.validate_worker_flag(dict(disable_request_id_randomization=False,environment_value="1",processor_source_sha256=h.ASSIGN_SHA))
 def test_actual_capture_calls_original_and_records_after(self):
  capture=c.module(h.IDROOT/"capture.py",h.CAPTURE_SHA,"_sparq_identity_test_capture")
  cls=type("PureProcessor",(),{"assign_request_id":staticmethod(actual_assignment(True))});events=[]
  capture.install_assignment(cls,lambda kind,event:events.append((kind,event)))
  request=types.SimpleNamespace(request_id="cmpl-proof-0",external_req_id=None);cls.assign_request_id(request)
  self.assertEqual(len(events),1);self.assertEqual(events[0][0],"assignment")
  self.assertEqual(events[0][1]["after_request_id"],request.request_id)
  self.assertEqual(events[0][1]["identity"]["pid"],os.getpid())
 def test_capture_write_failure_is_not_silently_passed(self):
  capture=c.module(h.IDROOT/"capture.py",h.CAPTURE_SHA,"_sparq_identity_test_capture_failure")
  cls=type("PureProcessor",(),{"assign_request_id":staticmethod(actual_assignment(True))})
  def failed(kind,value):raise RuntimeError("exclusive journal failed")
  capture.install_assignment(cls,failed)
  with self.assertRaisesRegex(RuntimeError,"exclusive journal"):cls.assign_request_id(types.SimpleNamespace(request_id="cmpl-proof-0",external_req_id=None))
 def test_double_capture_rejects(self):
  capture=c.module(h.IDROOT/"capture.py",h.CAPTURE_SHA,"_sparq_identity_test_capture_double")
  cls=type("PureProcessor",(),{"assign_request_id":staticmethod(actual_assignment(True))})
  capture.install_assignment(cls,lambda *a:None)
  with self.assertRaises(ValueError):capture.install_assignment(cls,lambda *a:None)
 def test_cpu_probe_no_hardware_dependency_import(self):
  tree=ast.parse(self.source("full_cpu_preflight.py"))
  names=[a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names]+[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
  self.assertFalse(any(x.startswith(("torch","vllm")) for x in names))
  self.assertIn('for path,want in c.RUNTIME_PINS.items()',self.source("full_cpu_preflight.py"))
 def test_n1_retains_real_receiver_import_not_stub(self):
  text=self.source("identity_bridge.py")
  self.assertIn("import vllm_ascend.worker.model_runner_v1 as runner",text)
  self.assertIn("c.runtime_sources(attention,runner,acl)",text)
  self.assertIn('getattr(owner,name)',text);self.assertNotIn("get_arch =",text)
 def test_n1_before_model_exec_and_arm_binding(self):
  text=self.source("full_entry.py")
  self.assertLess(text.index("n1=n1_dependency_gate"),text.index("os.execve"))
  self.assertIn("device_dependency=n1",text)
  for name in ("consume_model.py","consume_service.py"):self.assertIn("identity_bridge.consume_n1",self.source(name))
 def test_old_cpu_import_receipt_not_accepted(self):
  with self.assertRaises(ValueError):h.static_probe(dict(status="source-import-checked"),{}, {})
 def test_new_static_receipt_keeps_all_source_pins(self):
  p=dict(status="source-static-checked",source={},files={},runtime_framework_imported=False,device_query_called_by_probe=False,
   runner_import_pending_admitted_N1=True,actual_device_nodes=[],actual_device_fds=[],installed_runtime_sources=c.RUNTIME_PINS)
  self.assertTrue(h.static_probe(p,{},{}))
  p["installed_runtime_sources"]={}
  with self.assertRaises(ValueError):h.static_probe(p,{}, {})
 def test_model_trigger_requires_real_callback(self):
  import model_workload as m
  with self.assertRaises(ValueError):m.engine_id("cmpl-proof")
  with self.assertRaises((KeyError,ValueError)):m.engine_id(dict(actual_engine_request_id="inferred"))
  state=dict(actual_engine_request_id="post-native-assigned",assignment_ref={"path":"actual"},assignment_frontend_ref={"path":"actual"})
  self.assertEqual(m.engine_id(state),"post-native-assigned")
 def test_wire_uses_assignment_not_server_suffix_for_worker(self):
  text=self.source("wire.py")
  self.assertNotIn('engine_id=state.server_id+"-0"',text)
  self.assertIn("engine=verify_row",text)
  self.assertIn("install_frontend()",self.source("sitecustomize.py"))
if __name__=="__main__":unittest.main()
