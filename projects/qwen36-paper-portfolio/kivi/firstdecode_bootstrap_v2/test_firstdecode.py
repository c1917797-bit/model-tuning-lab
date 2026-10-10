"""Focused stdlib source/real finish-wrapper regressions, not model authority."""
import ast,hashlib,importlib.util,json,os,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def module(name):
 key="_test_kivi_firstdecode_"+name
 spec=importlib.util.spec_from_file_location(key,HERE/(name+".py"))
 value=importlib.util.module_from_spec(spec);sys.modules[key]=value;spec.loader.exec_module(value);return value
FINISH=module("finish_after_native");PRE=module("prerequisite");SERVER=module("server_entry")
def fixture(drained=True):
 calls=[];closed=[];published=[]
 runner=types.SimpleNamespace(requests={},input_batch=types.SimpleNamespace(num_reqs=0,req_ids=[]))
 def native(scheduler):
  calls.append(scheduler)
  if not drained:runner.requests={"real-id":object()}
  return lambda:"original-deferred-answer"
 runner._update_states=native
 close=lambda:closed.append("close")or{"actual_final":"fixture-only"}
 digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
 final=FINISH.install(runner,close,["real-id"],digest,published.append)
 return runner,final,calls,closed,published,native
class FirstDecode(unittest.TestCase):
 def test_complete_own_source_compiles_no_token_concatenation(self):
  for p in sorted(HERE.glob("*.py")):
   wire=p.read_bytes();compile(wire,str(p),"exec");ast.parse(wire)
   self.assertNotIn(b"__name__"+b"for",wire)
 def test_default_off_export_does_not_import_torch(self):
  before=set(sys.modules);old=os.environ.pop("QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC",None)
  try:
   value=module("kivi_firstdecode_bootstrap")
   with self.assertRaisesRegex(ValueError,"explicit firstdecode opt-in"):getattr(value,"FirstDecodeWorker")
   self.assertFalse(any(x=="torch"or x.startswith("torch.")for x in set(sys.modules)-before))
  finally:
   if old is not None:os.environ["QWEN36_KIVI_FIRSTDECODE_DIAGNOSTIC"]=old
 def test_actual_finish_zero_tick_preserves_original_deferred_and_restore(self):
  r,final,calls,closed,published,native=fixture()
  output=r._update_states(types.SimpleNamespace(finished_req_ids=["real-id"],total_num_scheduled_tokens=0))
  self.assertEqual(output(),"original-deferred-answer");self.assertEqual(len(calls),1)
  self.assertIs(r._update_states,native);self.assertEqual(len(closed),1);self.assertEqual(final(),published[0])
 def test_no_http_done_or_empty_schedule_can_make_final(self):
  r,final,calls,closed,published,native=fixture()
  r._update_states(types.SimpleNamespace(finished_req_ids=[]))
  with self.assertRaisesRegex(ValueError,"has not occurred"):final()
  self.assertEqual(len(calls),1);self.assertEqual(closed,[]);self.assertEqual(published,[])
 def test_foreign_finished_rejected_before_original_call(self):
  r,final,calls,closed,published,native=fixture()
  with self.assertRaisesRegex(ValueError,"unrelated retirement"):r._update_states(types.SimpleNamespace(finished_req_ids=["foreign-id"]))
  self.assertEqual(calls,[]);self.assertEqual(closed,[])
 def test_actual_finished_but_native_not_drained_rejected(self):
  r,final,calls,closed,published,native=fixture(False)
  with self.assertRaisesRegex(ValueError,"native request/batch drain"):r._update_states(types.SimpleNamespace(finished_req_ids=["real-id"]))
  self.assertEqual(len(calls),1);self.assertEqual(closed,[]);self.assertEqual(published,[])
 def test_wrong_original_source_guard_is_not_bypassed(self):
  runner=types.SimpleNamespace(_update_states=lambda x:None)
  with self.assertRaisesRegex(ValueError,"exact installed update owner"):
   FINISH.install(runner,lambda:None,["real-id"],"0"*64,lambda x:None)
 def test_actual_packed3_whole_ref_is_not_model_permission(self):
  if not(HERE/"SOURCE_MANIFEST.json").is_file():self.fail("actual source manifest is required for declared software CLI")
  l=module("loader");m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  value=PRE.consumed(m["packed3_qualification_ref"],l.obj)
  self.assertEqual((value["frames"],value["output_rows"],value["kernel_calls"]),(20,24,60))
  self.assertIs(value["model_ready"],False)
 def test_prior_packed3_result_wrong_sha_rejected_without_read(self):
  calls=[]
  with self.assertRaisesRegex(ValueError,"actual MAIN-consumed"):
   PRE.consumed(dict(path="/not-an-authority",bytes=2195,sha256="0"*64),lambda x:calls.append(x))
  self.assertEqual(calls,[])
 def test_actual_native_cli_boolean_actions_not_false_string(self):
  args=SERVER.native_argv(8250,10*1024**3)
  for flag in("--no-async-scheduling","--no-enable-chunked-prefill","--no-enable-prefix-caching","--enforce-eager"):
   self.assertEqual(args.count(flag),1)
  self.assertNotIn("false",args);self.assertEqual(args[args.index("--max-num-seqs")+1],"1")
  self.assertEqual(args[args.index("--max-num-batched-tokens")+1],"32768")
  self.assertEqual(args[args.index("--worker-cls")+1],"kivi_firstdecode_bootstrap.FirstDecodeWorker")
 def test_cli_bounds_remain_hard(self):
  for port,cache in((True,1),(8250,True),(8250,11*1024**3),(80,10*1024**3)):
   with self.assertRaises(ValueError):SERVER.native_argv(port,cache)
 def test_cpu_native_worker_import_is_only_in_real_n1_branch(self):
  tree=ast.parse((HERE/"guest_probe.py").read_bytes());parents={}
  for p in ast.walk(tree):
   for ch in ast.iter_child_nodes(p):parents[ch]=p
  found=[]
  for node in ast.walk(tree):
   if isinstance(node,ast.Call)and isinstance(node.func,ast.Attribute)and node.func.attr=="import_module"and node.args and isinstance(node.args[0],ast.Constant)and node.args[0].value=="vllm_ascend.worker.worker":
    cur=node;ancestor=None
    while cur in parents:
     cur=parents[cur]
     if isinstance(cur,ast.If):ancestor=cur;break
    found.append(ancestor)
  self.assertEqual(len(found),1);self.assertEqual(ast.dump(found[0].test),ast.dump(ast.parse('mode == "n1"',mode="eval").body))
if __name__=="__main__":unittest.main(verbosity=2)
