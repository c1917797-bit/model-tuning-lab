"""Actual file publication integration; synthetic nonnumerical inputs, no model PASS.
Runs actual PackedBatch publication callbacks -> Observer -> unchanged scalar
JournalPublisher -> actual Collector/original atomic writer -> independent
capture/position consumers. Does not execute tensor append_read/FA oracles.
Only Windows directory fsync uses an IO shim; data, hardlink, stat/SHA/read are real.
"""
import ast,copy,hashlib,importlib.util,json,os,sys,tempfile,types,unittest
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
CORE=os.environ.get("KIVI_MIXED_PUBLICATION_CORE_FIXTURE")
ARCHIVE=os.environ.get("KIVI_PUBLICATION_ARCHIVE_FIXTURE")
PRODUCER=os.environ.get("KIVI_PUBLICATION_PRODUCER_FIXTURE")
PINS={"adapter.py":"984a5c8b470026d94c456833b9706da14baac4a977120cd818086226617297b1",
 "consume.py":"cd5b012684607465b2a5c489303a30bb55970c93786c455d675037d6723bb851",
 "producer.py":"f7e392325cf3f83cd45d12c9269b6b4fa65914ff139b9f4cd60a68c4cef4aac5",
 "capture_schedule.py":"9b6ad7d3eaad36a7c9efd7ea06b14dd58f048e6b20746f13da805b5f03e6a470",
 "consume_stage.py":"d3f6a9089287521fdb01a4114f814391cfbfc4f25500a103dad0599502aa7da4",
 "stage_observer.py":"89529921e404060e302b7c227fdf2a58dfffec83b444871e66fed464adc58d74"}
def load(name,path):
 spec=importlib.util.spec_from_file_location("_mixed_wire_"+name,path)
 m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m);return m
def archive(name):
 if name=="producer.py" and PRODUCER:path=Path(PRODUCER)
 elif name in ("adapter.py","consume.py") and ARCHIVE:
  path=Path(ARCHIVE)/("ingress-consume.py" if name=="consume.py" else name)
 elif CORE and name in ("capture_schedule.py","consume_stage.py","stage_observer.py"):path=Path(CORE)/name
 else:
  m=json.loads((HERE/"SOURCE_MANIFEST.json").read_bytes())
  hits=[r for r in m["files"]+m["dependencies"] if Path(r["path"]).name==name and r["sha256"]==PINS[name]]
  if not hits:raise ValueError("source-qualified original publication dependency")
  path=Path(hits[0]["path"])
 if hashlib.sha256(path.read_bytes()).hexdigest()!=PINS[name]:raise ValueError("original exact complete bytes")
 return load("original_"+name.replace(".","_"),path)
class Publication(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.c=load("contract",HERE/"model_contract.py");self.l=load("loader",HERE/"loader.py")
  self.o=load("observer",HERE/"stage_observer.py");self.s=archive("capture_schedule.py")
  self.p=archive("producer.py");self.j=archive("consume.py");self.a=archive("adapter.py")
  self.v=archive("consume_stage.py");self.capture=load("capture",HERE/"capture_receipt.py")
  self.stack=ExitStack();self.addCleanup(self.stack.close)
  if os.name=="nt":
   sentinel=-93370
   def op(p,flags):return sentinel if Path(p).is_dir()else os.open(p,flags)
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),open=op,
    fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
    close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
   self.stack.enter_context(patch.object(self.c,"os",view))
  self.plan=self.write("PLAN",dict(fixture_not_numeric=True))
  self.ids={k:k for k in self.s.CAPS}
  self.identities={str(i):dict(pid=100+i,start_ticks=200+i,cgroup="wire-fixture")for i in range(4)}
  self.ob,self.batch,self.journal,self.collector=self.observer(0)
  self.counter=0
 def write(self,label,value):return self.c.write(self.root/(label+".json"),value)
 def observer(self,rank,original=False,sequence=None):
  ident=self.identities[str(rank)];identity=lambda:dict(ident)
  owner=self.write("OWNER-%d"%rank,dict(fixture_not_numeric=True))
  event=self.write("EVENT-%d"%rank,dict(fixture_not_numeric=True))
  col=self.a.Collector(types.SimpleNamespace(publish=self.c.write),None,
   dict(diagnostic_root=str(self.root)),owner,"0"*64,rank,ident)
  journal=self.j.JournalPublisher(col.publish,identity,rank,owner,event)
  schedule=self.s.Schedule(rank=rank,target_layer="FA0",declared=self.ids,plan_ref=self.plan)
  mod=archive("stage_observer.py") if original else self.o
  observer=mod.Observer(schedule,torch=None,producer=self.p,callback=None,root=str(self.root),
   identity=identity,publish=journal,sequence=sequence)
  batch=self.p.PackedBatch(None,{},source_refs={},device_properties={},get_format=None,
   qualify=lambda:None,actual_identity=identity,rank=rank,publish=observer.publish)
  return observer,batch,journal,col
 def payload(self):
  return dict(schema="kivi.actual-packed-pending/v1",owner=dict(controls=(32769,32768,32640,0)),
   rank=0,identity=self.identities["0"],fixture_not_numeric=True)
 def frame(self,positions,epoch=1):
  ids=list(positions);counts=[positions[r][1]for r in ids];computed=[positions[r][0]for r in ids]
  starts=[0]
  for n in counts:starts.append(starts[-1]+n)
  return dict(schema="kivi.actual-packed-qwen-frame/v1",req_ids=ids,computed_tokens=computed,
   scheduled_counts=counts,query_start_loc=starts,total_tokens=starts[-1],
   positions=[i for r in ids for i in range(* (positions[r][0],positions[r][0]+positions[r][1]))],
   epoch=epoch,rank=0,identity=self.identities["0"],kind="mixed",fixture_not_numeric=True)
 def test_01_actual_producer_pending_roundtrip_preserves_original_object(self):
  value=self.payload();expected=json.loads(json.dumps(value));ref=self.batch.publish("pending",value)
  self.assertEqual(self.l.obj(ref),expected);self.assertIs(type(value["owner"]["controls"]),tuple)
  self.assertEqual(self.journal.pending,[])
 def test_02_original_journal_tuple_failure_preserved(self):
  value=self.payload()
  with self.assertRaisesRegex(ValueError,"publication bytes"):self.journal("old-pending",value)
  self.assertTrue(any(self.root.glob("*old-pending.json")))
 def test_03_actual_frame_indexes_and_independent_position_reader(self):
  rows={"holder0":(32770,1),"holder1":(32768,1),"holder2":(0,32768)}
  frame=self.frame(rows);fr=self.ob.publish("frame",frame)
  self.fill(self.ob.schedule,"holder0",32770,0,1);self.fill(self.ob.schedule,"holder1",32768,1,1)
  self.ob.start("FA0",frame,fr,{"holder0":dict(slot=0,epoch=1),"holder1":dict(slot=1,epoch=1)})
  value=dict(schema="kivi.actual-packed-qkav-frame/v1",pool_geometry=(264,33792,16),
   rows=[dict(controls=(32771,32768,32640,0))],fixture_not_numeric=True)
  ref=self.batch.publish("packed",value)
  self.assertEqual(self.ob.indices[0]["packed_frame_ref"],ref)
  actual=self.l.obj(ref);self.assertEqual(actual["pool_geometry"],[264,33792,16])
  self.v.predicate("mixed-intake",self.v.position_rows(self.l.obj(fr)),self.ids)
  self.assertIs(type(value["pool_geometry"]),tuple)
 def test_04_old_observer_raw_failure_does_not_register_frame(self):
  old=archive("stage_observer.py")
  o=old.Observer(self.ob.schedule,torch=None,producer=self.p,callback=None,root=str(self.root),
   identity=lambda:self.identities["0"],publish=self.journal)
  with self.assertRaisesRegex(ValueError,"publication bytes"):
   o.publish("old-frame",dict(schema="kivi.actual-packed-qkav-frame/v1",pool_geometry=(264,33792,16)))
  self.assertEqual(o.indices,[])
 def test_05_all16_actual_output_returns_publish_readable_progress(self):
  self.ob.sequence=types.SimpleNamespace(layers=["FA%d"%i for i in range(16)])
  fr=self.write("decode-frame",self.frame({"holder0":(32768,1)}))
  self.ob.progress_frame=dict(ref=fr,frame=self.l.obj(fr))
  for i in range(16):
   self.ob.publish("out-%d"%i,dict(schema="kivi.actual-packed-qwen-output/v1",frame_ref=fr,
    layer="FA%d"%i,rank=0,identity=self.identities["0"]))
  client=load("client",HERE/"client_stage.py")
  path=client.paths(self.root,self.identities,0,"HOLDER0-DECODE-READY")[0]
  row=self.l.obj(self.l.ref(path));self.assertEqual(row["positions"],{"holder0":[32768,1]})
  self.assertEqual(len(row["all16_actual_FA_output_returns"]),16);self.assertFalse(row["model_ready"])
 def test_06_missing_duplicate_or_wrong_frame_still_rejects(self):
  self.ob.sequence=types.SimpleNamespace(layers=["FA%d"%i for i in range(16)])
  fr=self.write("decode-frame",self.frame({"holder0":(32768,1)}))
  self.ob.progress_frame=dict(ref=fr,frame=self.l.obj(fr))
  row=dict(schema="kivi.actual-packed-qwen-output/v1",frame_ref=fr,layer="FA0",rank=0,identity=self.identities["0"])
  self.ob.publish("out",row);self.assertNotIn("HOLDER0-DECODE-READY",self.ob.ready)
  with self.assertRaises(ValueError):self.ob.publish("dup",row)
  with self.assertRaises(ValueError):self.ob.publish("bad-frame",dict(row,frame_ref=self.plan,layer="FA1"))
 def test_07_direct_progress_canonical_not_inplace(self):
  body=dict(positions={"holder0":(32768,1)})
  r=self.ob.progress("fixture-progress",body);self.assertEqual(self.l.obj(r)["positions"]["holder0"],[32768,1])
  self.assertIs(type(body["positions"]["holder0"]),tuple)
 def test_08_canonical_serialized_wire_is_byte_equivalent(self):
  row=dict(schema="fixture",nested=((1,2),{"x":(3,None,True)}))
  r=self.ob.publish("wire",row)
  self.assertEqual(Path(r["path"]).read_bytes(),(json.dumps(row,sort_keys=True,separators=(",",":"))+"\n").encode())
  self.assertEqual(self.l.obj(r),json.loads(json.dumps(row)));self.assertIs(type(row["nested"]),tuple)
 def test_09_original_bad_Ref_SHA_still_rejected(self):
  original=self.journal.publish
  self.journal.publish=lambda name,row:dict(original(name,row),sha256="f"*64)
  with self.assertRaisesRegex(ValueError,"bytes/SHA"):self.batch.publish("bad-ref",self.payload())
  self.assertEqual(self.ob.indices,[])
 def test_10_original_publisher_changed_bytes_still_rejected(self):
  original=self.journal.publish
  self.journal.publish=lambda name,row:original(name,dict(row,fixture_not_numeric="changed"))
  with self.assertRaisesRegex(ValueError,"publication bytes"):self.batch.publish("changed",self.payload())
  self.assertEqual(self.ob.indices,[])
 def test_11_identity_change_rejects_before_write(self):
  self.ob.identity=lambda:dict(self.identities["0"],pid=999);before=set(self.root.iterdir())
  with self.assertRaisesRegex(ValueError,"same actual worker"):self.batch.publish("foreign",self.payload())
  self.assertEqual(before,set(self.root.iterdir()))
 def test_12_nonfinite_JSON_rejects_before_write(self):
  before=set(self.root.iterdir())
  with self.assertRaises(ValueError):self.batch.publish("nan",dict(schema="fixture",x=float("nan")))
  self.assertEqual(before,set(self.root.iterdir()))
 def test_13_original_scalar_membership_and_chunk_unchanged(self):
  raw=self.batch.publish("raw",self.payload())
  scalar=self.ob.publish("scalar",dict(schema="kivi.actual-packed-qwen-update/v1",rank=0,identity=self.identities["0"]))
  self.journal.flush();chunk=self.l.obj(self.journal.chunks[0])
  self.assertEqual(chunk["events"],[scalar]);self.assertNotIn(raw,chunk["events"])
 def fill(self,s,rid,position,slot,epoch):
  # Metadata-only fixtures; repeated explicit Ref is not a real numerical ledger.
  for i in range(len(s.history.get(rid,[])),position-32768+1):
   s.append("FA0",rid,32768+i,slot,epoch,self.plan)
 def capture_stage(self,rank,ob,batch):
  s=ob.schedule
  for rid in self.ids.values():s.original_prefill(rid,self.plan)
  positions=[{"holder0":(32770,1),"holder1":(32768,1),"holder2":(0,32768)},
   {"holder0":(32895,1),"holder1":(32893,1)},
   {"holder0":(32896,1),"holder1":(32894,1)},
   {"replacement":(32768,1),"holder1":(33030,1)},{"holder1":(33790,1)}]
  def retire(rid,slot,epoch):
   label=next(k for k,v in self.ids.items()if v==rid);length=32768+self.s.CAPS[label]-1
   self.fill(s,rid,length-1,slot,epoch);ob.retire(rid,slot,epoch,length)
   ob.publish("update-"+rid,dict(schema="kivi.actual-packed-qwen-update/v1",
    rank=rank,identity=self.identities[str(rank)]))
   ob.publish("retire-"+rid,dict(schema="kivi.actual-packed-qwen-retire/v1",
    rank=rank,identity=self.identities[str(rank)],request_id=rid))
  for idx,(name,rows)in enumerate(zip(self.s.POINTS,positions)):
   if name=="reuse-first-decode":
    retire("holder0",0,1);retire("holder2",2,1);s.reuse_prefill_ref=self.plan
   states={rid:dict(slot=(0 if rid in("holder0","replacement")else 1),epoch=2 if rid=="replacement"else 1)
    for rid in rows}
   for rid,(p,n)in rows.items():
    if p>=32768:self.fill(s,rid,p,states[rid]["slot"],states[rid]["epoch"])
   frame=self.frame(rows,idx+1);frame.update(rank=rank,identity=self.identities[str(rank)])
   fr=ob.publish("schedule-%d"%idx,frame);ob.start("FA0",frame,fr,states)
   self.v.predicate(name,self.v.position_rows(self.l.obj(fr)),self.ids)
   packed=dict(schema="kivi.actual-packed-qkav-frame/v1",pool_geometry=(264,33792,16),
    rows=[dict(controls=(p+1,32768,32640,states[rid]["slot"]))for rid,(p,n)in rows.items()if p>=32768],
    fixture_not_numeric=True)
   batch.publish("packed-%d"%idx,packed)
   point=ob.context["published_point"]
   # Actual tensor scatter is deliberately not exercised by a publication test.
   pr=ob.publish_wire("point-%d"%idx,dict(point,schema="kivi.actual-mixed-numeric-point/v1",
    observer_source_sha256=self.capture.OBSERVER_SHA,fixture_not_numeric=True))
   s.points[name]["complete_point_ref"]=pr
  retire("replacement",0,2);retire("holder1",1,1)
  return ob.stage_ref
 def full_capture(self):
  refs=[self.capture_stage(0,self.ob,self.batch)]
  for rank in range(1,4):
   ob,batch,_,_=self.observer(rank);refs.append(self.capture_stage(rank,ob,batch))
  report=self.write("CLIENT",dict(schema="kivi.actual-mixed-stage-client/v1",
   status="RAW_STAGE_PENDING_INDEPENDENT_CONSUMPTION",stage=0,capture_plan_ref=self.plan,primary=None,
   rank_stage_refs=refs,responses={k:dict(ok=True,completion_tokens=v)for k,v in self.s.CAPS.items()}))
  sealed=self.capture.seal(report,plan_ref=self.plan,identities=self.identities,document=self.l.obj,
   publish=lambda label,row:self.write(label,row))
  return sealed,refs
 def test_14_all4_fivepoint_raw_indices_actual_capture_consumer(self):
  ref,refs=self.full_capture()
  out=self.capture.validate(ref,stage=0,plan_ref=self.plan,identities=self.identities,document=self.l.obj)
  self.assertEqual(out["rank_stage_refs"],refs)
  for k in("numeric_consumed","raw_payload_read","model_ready","run_authority"):self.assertIs(out[k],False)
 def test_15_capture_consumer_retains_wrong_source_coverage_and_verdict_rejection(self):
  ref,refs=self.full_capture();value=self.l.obj(ref)
  for key in("numeric_consumed","model_ready","run_authority"):
   bad=self.write("BAD-"+key,dict(value,**{key:True}))
   with self.assertRaises(ValueError):self.capture.validate(bad,stage=0,plan_ref=self.plan,
    identities=self.identities,document=self.l.obj)
  rank=self.l.obj(refs[0]);rank["observer_source_sha256"]="0"*64
  bad=self.write("BAD-SOURCE",rank)
  with self.assertRaises(ValueError):self.capture.indices([bad]+refs[1:],stage=0,
   plan_ref=self.plan,identities=self.identities,document=self.l.obj)
  rank=self.l.obj(refs[0]);del rank["points"]["long-tail"];bad=self.write("BAD-COVERAGE",rank)
  with self.assertRaises(ValueError):self.capture.indices([bad]+refs[1:],stage=0,
   plan_ref=self.plan,identities=self.identities,document=self.l.obj)
  with self.assertRaises(ValueError):self.l.obj(dict(ref,sha256="0"*64))
 def test_16_all_runtime_pins_and_only_publish_algorithm_delta(self):
  asm=load("asm",HERE/"assemble.py");installer=load("installer",HERE/"installer.py")
  worker=load("worker",HERE/"worker.py");client=load("client",HERE/"client_stage.py")
  for role,name in asm.SUCCESSOR_NAMES.items():
   self.assertEqual(hashlib.sha256((HERE/name).read_bytes()).hexdigest(),asm.SUCCESSOR_PINS[role])
  sha=asm.SUCCESSOR_PINS["stage_observer"]
  self.assertEqual(installer.OBSERVER_SHA,sha);self.assertEqual(client.OBSERVER_SHA,sha)
  self.assertEqual(self.capture.OBSERVER_SHA,sha)
  self.assertEqual(worker.CAPTURE_RECEIPT_SHA,asm.SUCCESSOR_PINS["capture_receipt"])
  self.assertEqual(self.capture.CLIENT_SHA,asm.SUCCESSOR_PINS["client_stage"])
  self.assertEqual(self.l.INSTALLER_SHA,asm.SUCCESSOR_PINS["installer"])
  self.assertEqual(installer.CRITICAL_SHA["kernel"],"ecdae41fa1a3487beb872b01522bbb586f3546100f9fd22b9dd4159ca9c0ac2a")
  old=archive("stage_observer.py")
  old_tree=ast.parse(Path(old.__file__).read_bytes());new_tree=ast.parse((HERE/"stage_observer.py").read_bytes())
  old_cls=next(n for n in old_tree.body if isinstance(n,ast.ClassDef));new_cls=next(n for n in new_tree.body if isinstance(n,ast.ClassDef))
  def restore(n):
   n=copy.deepcopy(n)
   for x in ast.walk(n):
    if isinstance(x,ast.Attribute)and x.attr=="publish_wire":x.attr="original_publish"
   return ast.dump(n,include_attributes=False)
  self.assertEqual([restore(n)for n in old_cls.body],[restore(n)for n in new_cls.body if getattr(n,"name",None)!="publish_wire"])
  self.assertFalse(any(n.split(".")[0]in("torch","torch_npu","triton","numpy")for n in sys.modules))
if __name__=="__main__":unittest.main(verbosity=2)
