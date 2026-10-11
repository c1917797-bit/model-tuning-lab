"""Actual post_input source + source-native provider/geometry + real JSON file chain.
Framework/tensors remain the original explicit-provider inert fixtures.
Not native framework, mathematical output, or NPU permission.
"""
import argparse,copy,hashlib,importlib.util,json,os,sys,time,types,unittest
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ORIGINAL=Path(os.environ.get("KIVI_COST001_ARCHIVE",
 ("C:/Users/Huawei/AppData/Local/Temp/kivi-b1-cost-attribution-20261011-001/bootstrap" if os.name=="nt" else
 "/cache/cch/qwen36-paper-preparation-20261007/lowbit/kivi-b1-cost129-bootstrap-v1-001")) )
if os.name=="nt":os.environ["KIVI_PROVIDER_LOCAL_ARCHIVE"]="1"
sys.path.insert(0,str(ORIGINAL))
def load(path,name):
 if name in sys.modules:raise ValueError("no ambient fixture namespace")
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
 sys.modules[name]=m;spec.loader.exec_module(m);return m
INTEGRATION=Path(os.environ.get("KIVI_SCREEN_PRODUCER_ARCHIVE",str(ORIGINAL)))
I=load(INTEGRATION/"test_provider_integration.py","_cost003_actual_integration")
OLD=load(ORIGINAL/"runtime_owner.py","_cost003_failed_owner")
NEW=load(HERE/"runtime_owner.py","_cost003_actual_owner")
INPUT=load(ORIGINAL/"input_recipe.py","_cost003_actual_input")
class Protocol(unittest.TestCase):
 def setUp(self):
  self.f=I.ExplicitIntegration("test01_actual_native_provider_real_publication_all16_consumer")
  self.f.setUp();self.addCleanup(self.f.doCleanups)
  self.root=self.f.root;C=I.C;self.C=C
  config=C.write(self.root/"config.json",dict(model_type="qwen3_5",
   text_config=dict(model_type="qwen3_5_text",vocab_size=300000)))
  C.write(self.root/"tokenizer_config.json",dict(fixture=True))
  model=C.write(self.root/"model.json",dict(host_model_root=str(self.root)))
  out=self.root/"input";out.mkdir()
  with patch.object(C,"CONFIG_SHA",config["sha256"]):
   plan,protocol=INPUT.create(C,self.f.source,model,out,"scope-fixture")
  rows=C.obj(plan)["rows"]
  self.bindings=types.SimpleNamespace(owner=dict(container_id="a"*64,rank_bindings={"0":self.f.ident}),
   plan_ref=plan,expected={r["declared_passed_id"]:dict(prompt=C.obj(r["prompt_token_ids_ref"]))for r in rows},
   frontend_binding_ref=plan,rank_bindings_ref=plan)
  self.recipe=dict(container_id="a"*64,actual_input_protocol_ref=protocol,bits=2,run_id="fixture",
   diagnostic_root=str(self.root),native_format_binding={},external_owner_authority_ref=plan,
   compiled_numeric_qualification_ref=plan,algorithm_arm="candidate",
   screen_output_counts=[r["outputs"]for r in C.obj(protocol)["requests"]])
  self.final=C.write(self.root/"native-final.json",dict(fixture=True))
  self.published=[]
 def publish(self,label,value):
  row=self.C.write(self.root/(label+".json"),value);self.published.append((label,row));return row
 def call(self,module=NEW):
  return module.post_input(self.recipe,self.bindings,self.f.event,self.f.event_ref,
   self.final,self.f.zero,I.G,I.spans,self.publish,provider_state=self.f.state)
 def test01_original0623_reproduced_then_new_complete_chain(self):
  with self.assertRaisesRegex(ValueError,"two decode warmups then fixed1024"):self.call(OLD)
  self.assertEqual(self.published,[])
  owner,ref=self.call()
  self.assertEqual(self.C.obj(ref),owner)
  self.assertEqual(len(self.published),2)
  self.assertEqual(len(owner["regions"]),16)
  self.assertEqual(len(owner["declared_passed_request_ids"]),3)
  self.assertEqual(set(owner["prompt_lengths"].values()),{32768})
  cap=self.C.obj(owner["capacity_receipt_ref"])
  self.assertEqual(cap["maximum_output"],1024)
  self.assertTrue(all(v>=33792 for v in cap["geometry"]["actual_native_tokens"].values()))
  allocation=self.C.obj(owner["explicit_allocation_ref"])
  checked=I.G.consume_rank(owner,self.f.event,allocation["compact"],self.f.zero)
  self.assertEqual(checked["fields"],144);self.assertFalse(checked["numerical_checked"])
 def test02_old1024_protocol_rejected_by_new(self):
  self.recipe["screen_output_counts"]=[2,2,1024]
  with self.assertRaisesRegex(ValueError,"cost129"):self.call()
  self.assertEqual(self.published,[])
 def test03_wrong128_or130_protocol_rejected(self):
  for output in(128,130):
   self.recipe["screen_output_counts"]=[2,2,output]
   with self.assertRaisesRegex(ValueError,"cost129"):self.call()
  self.assertEqual(self.published,[])
 def test04_wrong_warmup_rejected(self):
  self.recipe["screen_output_counts"]=[1,2,129]
  with self.assertRaisesRegex(ValueError,"cost129"):self.call()
 def test05_dense_cannot_enter_candidate_owner(self):
  self.recipe["algorithm_arm"]="dense"
  with self.assertRaisesRegex(ValueError,"cost129"):self.call()
 def test06_missing_owner_rejected(self):
  self.bindings.expected.pop(next(iter(self.bindings.expected)))
  with self.assertRaisesRegex(ValueError,"cost129"):self.call()
 def test07_wrong_prompt_preserves_guard(self):
  next(iter(self.bindings.expected.values()))["prompt"].pop()
  with self.assertRaisesRegex(ValueError,"cost129"):self.call()
 def test08_bad_provider_state_rejected(self):
  self.f.state["state"]="planned"
  with self.assertRaisesRegex(ValueError,"completed explicit provider"):self.call()
 def test09_native_allocation_mismatch_rejected(self):
  self.f.state["plan"]["native"]["num_blocks"]+=1
  with self.assertRaisesRegex(ValueError,"planned native geometry"):self.call()
 def test10_real_json_tamper_rejected(self):
  ref=self.bindings.plan_ref;path=Path(ref["path"])
  with path.open("ab")as handle:handle.write(b" ")
  with self.assertRaisesRegex(ValueError,"bytes/SHA"):self.call()
 def test11_actual_geometry_negative_not_bypassed(self):
  self.f.zero["rank"]=1
  with self.assertRaises(ValueError):self.call()
  self.assertEqual(self.published,[])
 def test12_only_exact_protocol_literal_and_text_changed(self):
  old=(ORIGINAL/"runtime_owner.py").read_text(encoding="utf8")
  new=(HERE/"runtime_owner.py").read_text(encoding="utf8")
  needle='and recipe["algorithm_arm"]=="candidate" and recipe["screen_output_counts"]==[2,2,1024],'
  self.assertEqual(old.count(needle),1)
  want=old.replace(needle,needle.replace("1024","129")).replace(
   '"exact three sequential full32768 owners: two decode warmups then fixed1024")',
   '"exact three sequential full32768 owners: two decode warmups then cost129")')
  self.assertEqual(new,want)
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
 start=time.monotonic();suite=unittest.defaultTestLoader.loadTestsFromTestCase(Protocol)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 value=dict(schema="kivi.cost129-protocol-source-regression/v1",tests=result.testsRun,
  failures=len(result.failures),errors=len(result.errors),skipped=len(result.skipped),
  successful=result.wasSuccessful(),seconds=time.monotonic()-start,python=list(sys.version_info[:3]),
  original_failure="0623 original post_input rejects exact current129 input",
  source_refs=[dict(path=str(v.resolve()),bytes=len(v.read_bytes()),sha256=hashlib.sha256(v.read_bytes()).hexdigest())
   for v in (ORIGINAL/"runtime_owner.py",HERE/"runtime_owner.py",Path(__file__))],
  scope="actual source-native provider/geometry and actual input/post_input/publication; inert Tensor APIs",
  native_framework=False,NPU=False,numeric_verified=False,performance_accepted=False)
 with a.output.open("x",encoding="utf8",newline="\n")as f:json.dump(value,f,indent=2);f.write("\n")
 raise SystemExit(0 if result.wasSuccessful()else 1)
