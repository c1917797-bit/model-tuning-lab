"""Real-file publication regressions. No tensor math, framework/device or model PASS.
Actual PackedBatch objects and their bound publication callbacks, actual Collector
and original scalar JournalPublisher, actual raw index/finish, real atomic files.
Only Windows directory fsync is spied; byte writes, hardlinks, stat/SHA and reads
are real. Payloads/identities are explicitly synthetic non-numerical fixtures.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
ARCHIVE=os.environ.get("KIVI_PUBLICATION_ARCHIVE_FIXTURE")
PINS={"adapter.py":"984a5c8b470026d94c456833b9706da14baac4a977120cd818086226617297b1",
 "consume.py":"cd5b012684607465b2a5c489303a30bb55970c93786c455d675037d6723bb851"}
def load(name,path):
 s=importlib.util.spec_from_file_location("_publication_"+name,path);m=importlib.util.module_from_spec(s)
 sys.modules[s.name]=m;s.loader.exec_module(m);return m
def dependency(name):
 if ARCHIVE:path=Path(ARCHIVE)/("ingress-consume.py"if name=="consume.py"else name)
 else:
  mf=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  hits=[r for r in mf["dependencies"]if Path(r["path"]).name==name and r["sha256"]==PINS[name]]
  if len(hits)!=1:raise ValueError("one actual publication dependency")
  path=Path(hits[0]["path"])
 if hashlib.sha256(path.read_bytes()).hexdigest()!=PINS[name]:raise ValueError("actual dependency bytes")
 return load(name.replace(".","_"),path)
class ActualPublication(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.c=load("contract",HERE/"model_contract.py");self.p=load("producer",HERE/"producer.py")
  self.r=load("raw_journal",HERE/"raw_journal.py");self.j=dependency("consume.py");self.a=dependency("adapter.py")
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  if os.name=="nt":
   sentinel=-90173
   def op(p,flags):return sentinel if Path(p).is_dir()else os.open(p,flags)
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
    open=op,fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
    close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
   self.stack.enter_context(patch.object(self.c,"os",view))
  self.ident=dict(pid=111,start_ticks=222,cgroup="publication-fixture")
  self.identity=lambda:dict(self.ident)
  self.event=self.c.write(self.root/"event.json",dict(layers={
   "model.layers.%d.self_attn.attn"%i:dict(kind="FA"if i%4==3 else"GDN")for i in range(64)}))
  self.fa=sorted(k for k,v in self.c.obj(self.event)["layers"].items()if v["kind"]=="FA")
  self.owner=self.c.write(self.root/"owner.json",dict(fixture=True))
  # Actual Collector.publish calls actual existing contract's exclusive publication.
  self.collector=self.a.Collector(types.SimpleNamespace(publish=self.c.write),None,
   dict(diagnostic_root=str(self.root)),self.owner,"0"*64,0,self.ident)
  self.publish=self.collector.publish
  self.raw=self.r.FirstDecodeJournal(self.j,self.publish,self.identity,0,self.owner,self.event)
  self.batches={n:self.p.PackedBatch(None,{},source_refs={},device_properties={},get_format=None,
   qualify=lambda:None,actual_identity=self.identity,rank=0,publish=self.publish)for n in self.fa}
  self.counter=0
 def bind(self):self.raw.bind_packed(self.batches,self.p.PackedBatch,self.publish)
 def frame(self,name):
  self.counter+=1
  owner=self.c.write(self.root/("slot-%d.json"%self.counter),dict(schema="kivi.actual-qwen-slot-owner/v1",
   rank=0,identity=self.ident,request_id="fixture-r0",slot=0,epoch=1,computed=32768,layer=name,
   original_prefill_ref=self.owner))
  # Original producer.py198/237 emits these tuples. It is not mutated by the sink.
  return dict(schema="kivi.actual-packed-qkav-frame/v1",snapshot_is_live_alias=False,
   pool_geometry=(264,33792,16),rows=[dict(request_id="fixture-r0",slot=0,epoch=1,computed=32768,
    controls=(32769,32768,32640,0),identity_refs=dict(slot_owner=owner))],fixture_not_numeric=True)
 def emit(self,name):
  value=self.frame(name);ref=self.batches[name].publish("fixture-frame-%d"%self.counter,value)
  return ref,value
 def final(self):
  return self.c.write(self.root/"final.json",dict(schema="kivi.actual-packed-qwen-installer-final/v1",
   rank=0,identity=self.ident,owner_ref=self.owner,event_ref=self.event,fixture_not_numeric=True))
 def test_actual16_producer_collector_journal_finish_real_bytes(self):
  self.bind();refs={n:self.emit(n)[0]for n in self.fa};out=self.raw.finish(self.final())
  bundle=self.c.obj(out);self.assertEqual(bundle["frame_refs"],refs)
  scalar=self.c.obj(bundle["journal_ref"]);self.assertEqual(scalar["journal_chunks"],[])
  self.assertEqual(bundle["first_decode_length"],32769);self.assertFalse(bundle["model_ready"])
  for ref in refs.values():self.assertEqual(self.c.ref(ref["path"]),ref)
 def test_original_tuple_roundtrip_without_inplace_rewrite(self):
  self.bind();ref,value=self.emit(self.fa[0]);actual=self.c.obj(ref)
  self.assertIs(type(value["pool_geometry"]),tuple);self.assertIs(type(value["rows"][0]["controls"]),tuple)
  self.assertIs(type(actual["pool_geometry"]),list);self.assertIs(type(actual["rows"][0]["controls"]),list)
  self.assertEqual(self.raw.frames[self.fa[0]],ref)
 def test_original_scalar_path_still_publishes_and_chunks_once(self):
  self.bind()
  row=dict(schema="kivi.actual-packed-qwen-update/v1",rank=0,identity=self.ident,fixture_not_numeric=True)
  ref=self.raw("fixture-scalar",row)
  for n in self.fa:self.emit(n)
  result=self.c.obj(self.raw.finish(self.final()));scalar=self.c.obj(result["journal_ref"])
  self.assertEqual(self.c.obj(scalar["journal_chunks"][0])["events"],[ref])
 def test_missing_one_layer_cannot_finish(self):
  self.bind()
  for n in self.fa[:-1]:self.emit(n)
  with self.assertRaisesRegex(ValueError,"all16"):self.raw.finish(self.final())
 def test_duplicate_layer_rejects_after_preserving_original_publication(self):
  self.bind();self.emit(self.fa[0])
  with self.assertRaisesRegex(ValueError,"one original"):self.emit(self.fa[0])
  self.assertEqual(len(list(self.root.glob("*fixture-frame*.json"))),2)
 def test_wrong_first_decode_position_rejected(self):
  self.bind();value=self.frame(self.fa[0]);value["rows"][0]["computed"]=32767
  with self.assertRaisesRegex(ValueError,"true first decode"):self.batches[self.fa[0]].publish("bad-position",value)
  self.assertEqual(len(self.raw.frames),0)
 def test_foreign_owner_rank_rejected(self):
  self.bind();value=self.frame(self.fa[0])
  value["rows"][0]["request_id"]="other"
  with self.assertRaisesRegex(ValueError,"same owner"):self.batches[self.fa[0]].publish("bad-owner",value)
 def test_changed_actual_wire_cannot_enter_index(self):
  self.bind();original=self.raw.publish
  def changed(label,value):
   wire=copy.deepcopy(value);wire["fixture_not_numeric"]="changed";return original(label,wire)
  self.raw.publish=changed
  with self.assertRaisesRegex(ValueError,"complete published JSON"):self.emit(self.fa[0])
  self.assertEqual(self.raw.frames,{})
 def test_bad_actual_Ref_SHA_rejected(self):
  self.bind();original=self.raw.publish
  def bad(label,value):return dict(original(label,value),sha256="f"*64)
  self.raw.publish=bad
  with self.assertRaisesRegex(ValueError,"bytes/SHA"):self.emit(self.fa[0])
 def test_identity_change_rejects_before_actual_packed_write(self):
  self.bind();self.ident=dict(self.ident,pid=999);before=set(self.root.iterdir())
  with self.assertRaisesRegex(ValueError,"same live owner"):self.batches[self.fa[0]].publish("foreign",dict(schema="fixture"))
  self.assertEqual(set(self.root.iterdir()),before)
 def test_bind_partial_shared_used_or_rebound_producer_rejects(self):
  missing=dict(self.batches);missing.pop(self.fa[0])
  with self.assertRaises(ValueError):self.raw.bind_packed(missing,self.p.PackedBatch,self.publish)
  shared=dict(self.batches);shared[self.fa[1]]=shared[self.fa[0]]
  with self.assertRaises(ValueError):self.raw.bind_packed(shared,self.p.PackedBatch,self.publish)
  self.batches[self.fa[0]].model=object()
  with self.assertRaises(ValueError):self.bind()
  self.batches[self.fa[0]].model=None;self.bind()
  with self.assertRaises(ValueError):self.bind()
 def test_actual_worker_binding_precedes_real_installer_call(self):
  tree=ast.parse((HERE/"worker.py").read_bytes())
  calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  binding=next(n for n in calls if n.func.attr=="bind_packed")
  installer=next(n for n in calls if n.func.attr=="install"and isinstance(n.func.value,ast.Name)and n.func.value.id=="installer")
  self.assertLess(binding.lineno,installer.lineno)
  self.assertEqual(hashlib.sha256((HERE/"producer.py").read_bytes()).hexdigest(),
   "f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5")
  worker=load("worker",HERE/"worker.py")
  self.assertEqual(hashlib.sha256((HERE/"raw_journal.py").read_bytes()).hexdigest(),worker.RAW_JOURNAL_SHA)
 def test_nonframe_actual_packed_publication_once_not_scalar_event(self):
  self.bind();value=dict(schema="kivi.actual-packed-pending/v1",controls=(1,2,3,4))
  ref=self.batches[self.fa[0]].publish("pending",value)
  self.assertEqual(self.c.obj(ref)["controls"],[1,2,3,4])
  self.assertEqual(self.raw.frames,{});self.assertEqual(self.raw.original.pending,[])
 def test_original_unbound_producer_bypass_reproduces_failure(self):
  ref,_=self.emit(self.fa[0]);self.assertEqual(self.c.ref(ref["path"]),ref)
  self.assertEqual(self.raw.frames,{})
  with self.assertRaisesRegex(ValueError,"all16"):self.raw.finish(self.final())
 def test_naive_scalar_reroute_retains_tuple_roundtrip_failure(self):
  frame=self.frame(self.fa[0])
  with self.assertRaisesRegex(ValueError,"publication bytes"):self.raw.original("naive-frame",frame)
  self.assertTrue(any(self.root.glob("*naive-frame.json")))
 def test_default_imports_no_framework_or_tensor_execution(self):
  self.assertFalse(any(n=="torch"or n.startswith("torch.")or n in("torch_npu","triton","numpy")for n in sys.modules))
if __name__=="__main__":unittest.main(verbosity=2)
