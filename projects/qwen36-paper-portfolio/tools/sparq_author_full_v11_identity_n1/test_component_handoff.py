"""Source/protocol tests only. No fixture or source test is NPU/model authority."""
import ast,copy,json,sys,unittest
from unittest import mock
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
 def test_component_refs_and_fourargument_dispatch_actual_SOURCE(self):
  s=(Path(__file__).parent/"source_contract.py").read_text()
  self.assertIn('h.source_interfaces()',s)
  self.assertIn('h.shard_source_interfaces()',s)
  self.assertIn('("shard_contract","shard_contract.py"),("shard_rows","shard_rows.py"),("shard_proof","shard_proof.py"),("shard_host","shard_host.py")',s)
  self.assertIn('checked=reader.consume_successor(COMPONENT_READER_SOURCE)',s)
  self.assertIn('x.get("consumer_source")==COMPONENT_READER_SOURCE',s)
  self.assertIn('x.get("old_consumer_outcome")=="FAILED-not-promoted"',s)
  self.assertIn('canonical(checked)==canonical(x)',s)
  s=(Path(__file__).parent/"service_contract.py").read_text();self.assertIn("return readonly_component_mounts(ref)",s)
 def test_facade_ON_cannot_change_original_MAIN_command(self):
  source=(Path(__file__).parent/"entry.py").read_text()
  self.assertNotIn("os.execve(",source)
  self.assertIn("MAIN runtime entry is exact host_run.py",source)
  source=(Path(__file__).parent/"host_run.py").read_text()
  self.assertIn('expected_host_argv=["/usr/bin/python3","-B",str(c.BASE/"host_run.py")',source)
class DisjointHandoff(unittest.TestCase):
 """Only software transport/header witnesses. Never actual numerical authority."""
 def test_actual_new50_source_and_original42_math(self):
  x=h.shard_source_interfaces()
  self.assertEqual((x["source_count"],x["own_count"],x["cases"],x["steps"]),(50,7,128,20480))
  self.assertEqual(x["native_source"],h.CURRENT);self.assertFalse(x["ready"])
  self.assertEqual(c.SHARD_SOURCE["sha256"],"2f01233797f130c17f94bf4f0c6a631c9f0875b86ac073f2d4fc551eadd1a5ba")
  self.assertNotIn("torch",sys.modules)
 def test_real_fourarg_consumer_and_incompatible_signatures(self):
  raw=(c.SHARD_ROOT/"shard_consume.py").read_text()
  self.assertEqual(h.shard_signature(raw),("own_ref","result_ref","terminal_ref","peer"))
  for bad in (raw.replace("def consume(own_ref,","def consume(legacy_root,"),
   raw.replace("terminal_ref,peer):","terminal_ref,peer,extra):"),
   raw.replace("terminal_ref,peer):","terminal_ref,peer='any'):" )):
   with self.assertRaises(ValueError):h.shard_signature(bad)
 def test_real0227_failed_whole_cannot_grant_model(self):
  from original_terminal import original_terminal
  ref=dict(path="/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-original-operations-v10b-20261009-001/MAIN_0227_ORIGINAL_TERMINAL_20261009_001.json",
   sha256="8571ecb058f4cd8bcdc1663741846267d3ad7a44abc2f565f960329b08630508")
  raw=c.obj(ref);outer=raw.get("structuredContent",raw)
  record=outer["operation"]["result"]["record"] if "operation" in outer else outer["result"]["record"]
  self.assertEqual(record["exitCode"],1)
  self.assertEqual(record["error"],"exit code")
  with self.assertRaises(ValueError):original_terminal(raw,"lgw_a6109c51076a4a2c9d2674ca5a8704a0")
 def test_partial_rejected_by_REAL_component_before_whole_dispatch(self):
  ref=dict(path="/software-fixture-only/partial.json",sha256="a"*64)
  old=c.obj
  row=dict(schema="sparq.author-ann-disjoint4-numeric/v1",status="complete-numerical-component",
   packet_source=c.SHARD_SOURCE,native_source=h.CURRENT,cases=127,changing_feedback_steps=20320,shards=4)
  with mock.patch.object(c,"obj",side_effect=lambda r:row if r==ref else old(r)):
   with self.assertRaises(ValueError):c.component(ref,replay=True)
 def test_new_whole_shape_header_and_disagreement_NOT_numeric_license(self):
  # Copy an actual archived envelope SHAPE; changes exist only in this software
  # fixture. replay=False cannot assert every original case/step has passed.
  raw=json.loads((c.KERNEL/"original_operation_get_ma0e85.json").read_text())
  outer=raw.get("structuredContent",raw);op=outer["operation"];record=op["result"]["record"]
  own=dict(path="/software-fixture-only/header.json",sha256="a"*64)
  rr=dict(path="/software-fixture-only/RESULT.json",sha256="b"*64)
  tr=dict(path="/software-fixture-only/whole.json",sha256="c"*64)
  argv=["/usr/bin/python3","-B",str(c.SHARD_ROOT/"shard_host.py"),"--execute"]
  host=dict(schema="sparq.disjoint4-host-result/v1",status="complete-disjoint-numerics",
   packet_source=c.SHARD_SOURCE,native_source=h.CURRENT,primary_error=None,secondary_errors=[],
   native_sources_before=self.native_files(),native_sources_after=self.native_files(),
   actual_host_argv=argv,expected_host_argv=argv,
   parts=[dict(shard_id=i,physical=4+i,container_id=("%064x"%(i+1))) for i in range(4)])
  record["command"],record["args"]=argv[0],argv[1:]
  record["stdout"]="MAIN_SPARQ_DISJOINT_HOST "+json.dumps(dict(result=rr,status=host["status"],packet_source=c.SHARD_SOURCE))+"\n"
  for block in raw.get("content",[]):
   if block.get("type")=="text":block["text"]=json.dumps(outer)
  x=dict(schema="sparq.author-ann-disjoint4-numeric/v1",status="complete-numerical-component",
   packet_source=c.SHARD_SOURCE,native_source=h.CURRENT,cases=128,changing_feedback_steps=20480,shards=4,
   partial_cases_used=0,numerical_component_checked=True,MAIN_original_operation_authority_verified=True,
   ready=False,model_executed=False,matched1024_e2e_verified=False,final2048_task_verified=False,
   execution_clock=dict(c.NATIVE_EXECUTION_CLOCK,owner="sparq-ann-disjoint4-v1"),
   original0227_status="timeout-not-promoted",original_ba508_status="FAILED-not-promoted",
   original_terminal=tr,result=rr,operation_id=outer["operationId"],
   consumer_source=c.COMPONENT_READER_SOURCE,original_consumer_source=dict(path=str(c.SHARD_ROOT/"shard_consume.py"),sha256=c.SHARD_FILES["shard_consume.py"]),
   derived_consumer_sha256=c.COMPONENT_READER_DERIVED_SHA,consumer_redecision_schema="sparq.disjoint4-consumer-redecision/v1",
   old_consumer_outcome="FAILED-not-promoted",original_producer_source=c.SHARD_SOURCE,npu_rerun=False,numeric_reference_recomputed=False,
   cleanup_mount_replays=[dict(shard_id=i,physical=4+i) for i in range(4)])
  old=c.obj
  def read(r):
   if r==own:return x
   if r==rr:return host
   if r==tr:return raw
   return old(r)
  with mock.patch.object(c,"obj",side_effect=read):
   out=c.component(own,replay=False)
   self.assertFalse(out["model_ready"]);self.assertFalse(out["model_executed"])
   self.assertEqual(out["original_operation_id"],outer["operationId"])
   self.assertEqual(out["component_transport"],"one MAIN whole operation/four complete Docker children")
   raw["stdoutTruncated"]=True
   with self.assertRaises(ValueError):c.component(own,replay=False)
 def native_files(self):return c.obj(h.CURRENT)["files"]
 def test_replay_ON_full_four_consumer_and_RO_prerequisite_closure(self):
  tree=ast.parse((c.ROOT/"source_contract.py").read_text())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=="actual_component")
  call=next(n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="component")
  self.assertTrue(next(k.value.value for k in call.keywords if k.arg=="replay"))
  s=(c.ROOT/"component_handoff.py").read_text()
  self.assertIn('prior=host["predecessor"];old=c.obj(prior["result"]);tree(old["output_dir"])',s)
  self.assertNotIn('x["actual_report"]',s)
  self.assertNotIn('x["native_no_device_abi"]',s)
  self.assertIn('paths[str(p)]=(str(p),False)',s)
if __name__=="__main__":unittest.main()
