"""Private v16 stdlib reference regressions. No candidate math; no device.
005 real plans/all192 metadata are immutable fixtures. FA fixture is explicitly
hypothetical because005 rejected before actual FA writer snapshots existed.
"""
import ast,copy,hashlib,json,struct,tempfile,unittest
from pathlib import Path
import evidence as c,gdn_stream as g,gdn_state as state
ROOT=Path(__file__).resolve().parent
FIXTURE_ROOT=Path("/cache/cch/qwen36-paper-preparation-20261007/sparse/sparq-full-gdn-physicalpool-reference-v16-user72h-20261010-001")
SOURCE=dict(path="/opt/host/vnf/austinov/model-tuning-lab/projects/qwen36-paper-portfolio/tools/sparq_author_full_v11_identity_n1/SOURCE_MANIFEST.json",
 sha256="7e0a03d5b201fa0646d0cb2e1268bf4d2932a7cc4b4f6de077f92b223585d142")
FIXTURES=[]
_FA_TEMP=None
def fixture_fa_ref(value):
 # A REAL ordinary temp file for an explicitly synthetic FA fixture.
 # Runtime plans also hold metadata Refs, not repeated32K embedded lists.
 # This does NOT claim005 captured FA bytes or a real request writer.
 global _FA_TEMP
 if _FA_TEMP is None:_FA_TEMP=tempfile.TemporaryDirectory(prefix="v16-fa-ref-fixture-")
 data=json.dumps(value,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
 sha=hashlib.sha256(data).hexdigest();path=Path(_FA_TEMP.name)/(sha+".json")
 if path.exists():c.require(path.read_bytes()==data,"same immutable software FA fixture bytes")
 else:
  with path.open("xb") as f:c.require(f.write(data)==len(data),"whole immutable software FA metadata fixture")
 return dict(path=str(path),bytes=len(data),sha256=sha)
def raw(ref):
 if ref.get("software_fixture") is True:return ref["value"]
 c.require(set(ref) in ({"path","sha256"},{"path","bytes","sha256"}),"actual original two/three-field Ref")
 c.bound(ref["path"],ref["sha256"]);actual_bytes=Path(ref["path"]).stat().st_size
 if "bytes" in ref:c.require(type(ref["bytes"]) is int and ref["bytes"]==actual_bytes,"original005 actual byte count")
 return c.obj(ref)
def build(rank):
 f=FIXTURES[rank];plan=raw(f["plan"]);states=[]
 assert len(plan["states"])==96 and plan["source"]==SOURCE
 for row in plan["states"]:
  x=dict(row,rank=rank,epoch=1,metadata=f["metadata"][str(row["layer"])])
  states.append(x)
 # Same source-derived possible K/V layout; NOT an actual005 FA snapshot.
 # Shared one Python slot list prevents test fixture metadata amplification.
 mapping=list(range(32768));fa=[]
 for layer in range(3,64,4):
  base=next(s["identity"] for s in states if s["layer"]==layer-3 and s["name"]=="conv")
  offset=next(s["identity"]["storage_offset"]*4 for s in states if s["layer"]==layer-3 and s["name"]=="recurrent")
  n=(base["storage_bytes"]-offset)//(2*128*256*2)
  caches=[]
  for k in range(2):
   start=offset+k*n*128*256*2
   caches.append(dict(base,shape=[n,128,1,256],stride=[32768,256,256,1],storage_offset=start//2,
    pointer=base["storage_pointer"]+start))
  value=dict(schema="sparq.actual-native-FA-writer-metadata/v1",rank=rank,epoch=1,layer=layer,
   prefix="software-fixture.layers.%d.self_attn"%layer,num_actual_tokens=32768,slot_mapping=mapping,
   cache_write_scope="original-reshape-and-cache-real-token-slice",is_encoder_decoder=False,
   cache_sharing_target=None,CP=False,quantized=False,allocator_source_pins=g.ALLOCATOR_PINS,
   actual_implementation={"class":"vllm_ascend.attention.attention_v1.AscendAttentionBackendImpl","impl_id":layer+1,
    "attn_type":"decoder","decoder_value":"decoder","enable_c8_quant":False,"enable_hamming_sparse":False,
    "is_kv_producer":False,"kv_sharing_target_layer_name":None})
  fa.append(dict(rank=rank,epoch=1,layer=layer,prefix=value["prefix"],cache=caches,
   metadata=fixture_fa_ref(value)))
 return plan,states,fa
def tiny(ops=None):
 return dict(all_physical_bytes=32,protected_extents=[[0,4],[12,32]],protected_bytes=24,
  before_owner="a"*64,operations=ops or [],members=[dict(layer=0)],exact_views=[])
def segment(start=4,stop=12):
 return dict(start=start,stop=stop,dtype="torch.float32",view="v",layer=0)
class PhysicalBytes(unittest.TestCase):
 def test_partial_row_exact_allowed_bytes(self):
  p=tiny();b=bytearray(32);a=bytearray(b);a[4:12]=struct.pack("<ff",1,2)
  x=g.PhysicalChecker(p,[segment()]);x.chunk(0,b,a);s=x.finish()
  self.assertEqual(s["physical_bytes_checked"],32);self.assertEqual(s["protected_bytes_checked"],24)
  self.assertTrue(s["old_per_layer_inactive_gate_not_claimed"])
 def test_unwritten_byte_in_same_row_rejected(self):
  b=bytes(32);a=bytearray(b);a[13]=1
  with self.assertRaisesRegex(ValueError,"unwritten byte"):g.PhysicalChecker(tiny(),[segment()]).chunk(0,b,a)
 def test_padding_byte_rejected(self):
  a=bytearray(32);a[-1]=1
  with self.assertRaisesRegex(ValueError,"unwritten byte"):g.PhysicalChecker(tiny(),[]).chunk(0,bytes(32),a)
 def test_allowed_GDN_NaN_rejected(self):
  a=bytearray(32);a[4:8]=struct.pack("<I",0x7fc00001)
  with self.assertRaisesRegex(ValueError,"nonfinite"):g.PhysicalChecker(tiny(),[segment()]).chunk(0,bytes(32),a)
 def test_FA_only_bytes_not_reinterpreted(self):
  a=bytearray(32);a[4:8]=struct.pack("<I",0x7fc00001)
  x=g.PhysicalChecker(tiny(),[segment(8,12)]);x.chunk(0,bytes(32),a);self.assertEqual(x.finish()["typed_bytes_checked"],4)
 def test_multiple_chunks_cover_type(self):
  x=g.PhysicalChecker(tiny(),[segment()]);b=bytes(32)
  for a,z in ((0,8),(8,20),(20,32)):x.chunk(a,b[a:z],b[a:z])
  self.assertEqual(x.finish()["typed_bytes_checked"],8)
 def test_chunk_reorder_rejected(self):
  with self.assertRaisesRegex(ValueError,"exactly once"):g.PhysicalChecker(tiny(),[]).chunk(1,b"0",b"0")
 def test_missing_tail_rejected(self):
  x=g.PhysicalChecker(tiny(),[]);x.chunk(0,bytes(16),bytes(16))
  with self.assertRaisesRegex(ValueError,"complete pool"):x.finish()
 def test_summary_tamper_rejected(self):
  p=tiny();x=g.PhysicalChecker(p,[segment()]);x.chunk(0,bytes(32),bytes(32));s=x.finish()
  g.consume_physical_summary(s,p,[segment()]);s["typed_bytes_checked"]-=1
  with self.assertRaises(ValueError):g.consume_physical_summary(s,p,[segment()])
class Actual005(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  FIXTURES[:]=[json.loads((FIXTURE_ROOT/("fixtures-r%d.json"%r)).read_text()) for r in range(4)]
  cls.actual=[build(r) for r in range(4)]
 def test_all4_all48_actual_metadata(self):
  for rank,(plan,states,fa) in enumerate(self.actual):
   self.assertEqual(len(states),96)
   for s in states:
    m=raw(s["metadata"]);self.assertEqual(m["rank"],rank);self.assertEqual(m["epoch"],1)
    d=__import__("gdn_metadata").plan(m,s["identity"]["shape"][0],s["identity"]["shape"][0])
    self.assertEqual(d["written_slots"][s["name"]],[23+s["layer"]%4])
 def test_005_exact_physical_bytes_once(self):
  amount=0
  for plan,states,fa in self.actual:
   pools=g.physical_owners(states,fa,raw);self.assertEqual(len(pools),16)
   self.assertEqual(sum(len(p["members"]) for p in pools),96)
   self.assertEqual(sum(len(p["exact_views"]) for p in pools),32)
   amount+=sum(p["all_physical_bytes"] for p in pools)
  self.assertEqual(amount,42894753792)
 def test_complete_alias_three_distinct_writers(self):
  pools=g.physical_owners(self.actual[0][1],self.actual[0][2],raw)
  p=pools[0];self.assertEqual({m["layer"] for m in p["members"]},{0,1,2})
  self.assertEqual({tuple(op["slots"]) for op in p["operations"] if op["kind"]=="GDN"},{(23,),(24,),(25,)})
 def test_same_pointer_different_shape_rejected(self):
  rows=copy.deepcopy(self.actual[0][1]);rows[2]["identity"]["shape"][0]-=1
  with self.assertRaisesRegex(ValueError,"partial overlap"):g.physical_owners(rows,self.actual[0][2],raw)
 def test_pointer_offset_mismatch_rejected(self):
  x=copy.deepcopy(self.actual[0][1][0]["identity"]);x["pointer"]+=2
  with self.assertRaisesRegex(ValueError,"pointer"):g.physical_identity(x)
 def test_crossrank_alias_rejected(self):
  rows=copy.deepcopy(self.actual[0][1]);rows[0]["identity"]["device"]="npu:1"
  with self.assertRaisesRegex(ValueError,"cross-rank"):g.physical_owners(rows,self.actual[0][2],raw)
 def test_missing_FA_rejected(self):
  with self.assertRaisesRegex(ValueError,"all16"):g.physical_owners(self.actual[0][1],self.actual[0][2][:-1],raw)
 def test_FA_source_drift_rejected(self):
  fa=copy.deepcopy(self.actual[0][2]);value=raw(fa[0]["metadata"]);value["allocator_source_pins"]={}
  fa[0]["metadata"]=fixture_fa_ref(value)
  with self.assertRaisesRegex(ValueError,"source"):g.physical_owners(self.actual[0][1],fa,raw)
 def test_FA_real_token_outside_cache_rejected(self):
  row=copy.deepcopy(self.actual[0][2][0]);value=raw(row["metadata"])
  value["slot_mapping"]=[10**9];value["num_actual_tokens"]=1;row["metadata"]=fixture_fa_ref(value)
  with self.assertRaisesRegex(ValueError,"slot mapping"):g.fa_write_extents(row["cache"][0],raw(row["metadata"]))
 def test_FA_NZ_unsupported_rejected(self):
  x=copy.deepcopy(self.actual[0][2][0]["cache"][0]);x["native_format_value"]=29
  with self.assertRaisesRegex(ValueError,"unsupported layout"):g.physical_identity(x)
 def test_new_budget_full_before_and_original_reserve(self):
  namespace=self.actual[0][0]["cgroup"]["namespace_proof"]
  self.assertEqual(set(namespace),{"path","sha256"});self.assertIn("memory",raw(namespace))
  with self.assertRaisesRegex(ValueError,"byte count"):raw(dict(namespace,bytes=1))
  records=[];baselines=[]
  for r,(p,s,f) in enumerate(self.actual):
   records.append(dict(p,schema=g.PHYSICAL_BUDGET,states=s,fa=f))
   baselines.append(dict(software_fixture=True,value=p["cgroup"]))
  proof=g.physical_budget(records,baselines,1,SOURCE,raw_loader=raw)
  self.assertEqual(proof["all_physical_before_bytes"],42894753792)
  self.assertEqual(proof["physical_copy_count"],64);self.assertEqual(proof["all_logical_state_count"],384)
  self.assertEqual(proof["reserve_bytes"],2*1024**3);self.assertEqual(proof["guest_limit_bytes"],64*1024**3)
  self.assertGreater(proof["metadata_heap_bytes_per_worker"],0)
  self.assertEqual(proof["all4_metadata_transient_reserved_bytes"],4*(8*proof["metadata_heap_bytes_per_worker"]+4*proof["metadata_wire_bytes_per_worker"]))
  self.assertTrue(proof["budget_fits"]);g.consume_physical_budget(proof,raw)
  # Actual consumers reparse published JSON in independent Python processes.
  # Object-id/key-interning/list-capacity benefits may not change this ledger.
  reloaded=json.loads(json.dumps(proof,sort_keys=True,separators=(",",":")))
  self.assertEqual(g.consume_physical_budget(reloaded,raw),proof)
 def test_over_budget_detail_returned_before_reject(self):
  records=[];baselines=[]
  for r,(p,s,f) in enumerate(self.actual):
   records.append(dict(p,schema=g.PHYSICAL_BUDGET,states=s,fa=f))
   m=copy.deepcopy(p["cgroup"])
   # Preserve original raw controller numbers coherently for the fixture.
   for path in m["control_raw"]:
    if path.endswith("usage_in_bytes"):m["control_raw"][path]=str(40*1024**3)+"\n"
   m["memory_current"]=m["memory_peak"]=40*1024**3
   baselines.append(dict(software_fixture=True,value=m))
  proof=g.physical_budget(records,baselines,1,SOURCE,raw_loader=raw)
  self.assertFalse(proof["budget_fits"]);self.assertEqual(proof["baseline_refs"],baselines)
  with self.assertRaisesRegex(ValueError,"same64GiB"):g.consume_physical_budget(proof,raw)
class TypesAndSeams(unittest.TestCase):
 def pool(self,ops):
  ident=dict(shape=[2,2],stride=[2,1],dtype="torch.float32",device="npu:0",
   pointer=1000,storage_pointer=1000,storage_offset=0,storage_bytes=32,
   native_format_value=2,native_format_type="torch_npu.npu._format.Format")
  vk=g.exact_view_key(ident)
  return dict(tiny(ops),exact_views=[dict(identity=ident)],members=[dict(layer=0),dict(layer=1)]),vk
 def test_last_FA_writer_removes_only_exact_bytes(self):
  p,v=self.pool([]);p["operations"]=[dict(kind="GDN",layer=0,dtype="torch.float32",view=v,extents=[[0,16]]),
   dict(kind="FA",layer=3,extents=[[4,8]])]
  rows=g.type_segments(p,[]);self.assertEqual([(r["start"],r["stop"]) for r in rows],[(0,4),(8,16)])
 def test_next_GDN_writer_reclaims_exact_type(self):
  p,v=self.pool([]);prior=[dict(start=0,stop=16,dtype="torch.float32",view=v,layer=0)]
  p["operations"]=[dict(kind="FA",layer=3,extents=[[4,8]]),dict(kind="GDN",layer=4,dtype="torch.bfloat16",view=v,extents=[[4,8]])]
  rows=g.type_segments(p,prior);self.assertEqual([r["dtype"] for r in rows],["torch.float32","torch.bfloat16","torch.float32"])
 def test_unknown_retained_cached_ID_not_type_authority(self):
  p,v=self.pool([]);self.assertEqual(g.type_segments(p,[]),[])
  # No self.requests/blockIDs are used by last-writer typing.
  source=(ROOT/"gdn_stream.py").read_text().split("def type_segments",1)[1]
  self.assertNotIn("native_requests",source)
 def test_prior_typed_segment_overlap_rejected(self):
  p,v=self.pool([]);prior=[dict(start=0,stop=8,dtype="torch.float32",view=v,layer=0)]*2
  with self.assertRaisesRegex(ValueError,"nonoverlapping"):g.type_segments(p,prior)
 def test_unknown_prior_view_rejected(self):
  p,v=self.pool([])
  with self.assertRaisesRegex(ValueError,"prior typed history"):g.type_segments(p,[dict(start=0,stop=8,dtype="torch.float32",view="foreign",layer=0)])
 def test_original_cpu_copy_only_once_owner(self):
  body=ast.parse((ROOT/"gdn_model_observer.py").read_text())
  begin=next(n for n in ast.walk(body) if isinstance(n,ast.FunctionDef) and n.name=="begin")
  loops=[n for n in ast.walk(begin) if isinstance(n,ast.For) and isinstance(n.iter,ast.Name) and n.iter.id=="pools"]
  self.assertEqual(len(loops),1)
  calls=[n for n in ast.walk(loops[0]) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="cpu"]
  self.assertEqual(len(calls),1) # Source contract, actual device copy remains UNRUN.
 def test_budget_published_before_budget_guard(self):
  text=(ROOT/"gdn_model_observer.py").read_text().split(" def joint",1)[1].split(" def first_pool",1)[0]
  self.assertLess(text.index("if rank==0:c.write(final,proof)"),text.index('c.require(actual["budget_fits"]'))
 def test_no_source_torch_import(self):
  for name in ("gdn_stream.py","gdn_state.py","gdn_model_observer.py"):
   tree=ast.parse((ROOT/name).read_text())
   self.assertFalse(any(isinstance(n,ast.Import) and any(a.name in ("torch","torch_npu") for a in n.names) for n in ast.walk(tree)))

 def test_FA_cut_FP32_element_rejected_at_type_geometry(self):
  p,v=self.pool([]);prior=[dict(start=0,stop=4,dtype="torch.float32",view=v,layer=0)]
  p["operations"]=[dict(kind="FA",layer=3,extents=[[2,4]])]
  with self.assertRaisesRegex(ValueError,"cuts a retained typed element"):g.type_segments(p,prior)
 def test_actual_encoder_implementation_branch_rejected(self):
  plan,states,fa=build(0);row=copy.deepcopy(fa[0]);value=raw(row["metadata"])
  value["actual_implementation"]["attn_type"]="encoder_decoder"
  with self.assertRaisesRegex(ValueError,"implementation fields"):g.fa_write_extents(row["cache"][0],value)
 def test_actual_quant_implementation_branch_rejected(self):
  plan,states,fa=build(0);row=copy.deepcopy(fa[0]);value=raw(row["metadata"])
  value["actual_implementation"]["enable_c8_quant"]=True
  with self.assertRaisesRegex(ValueError,"implementation fields"):g.fa_write_extents(row["cache"][0],value)

class ConsumerContexts(unittest.TestCase):
 """Lifecycle-only fixtures isolate numerical-budget validation explicitly.
 The full physical/budget path is separately tested against actual005 inputs.
 """
 @classmethod
 def setUpClass(cls):
  cls.actual=[raw(json.loads((FIXTURE_ROOT/("fixtures-r%d.json"%r)).read_text())["plan"]) for r in range(4)]
 def harness(self,epoch=1,previous=None,record_rank=0,root="/cache/cch/software-context-a"):
  from unittest.mock import patch
  source=SOURCE;checker=dict(path="/cache/cch/software-checker.py",sha256="b"*64)
  p=tiny();p["identity"]=dict(device="npu:0",storage_pointer=1000,storage_bytes=32,
   native_format_value=2,native_format_type="test.explicit-software")
  prior=previous or dict(schema="sparq.actual-pool-last-writer-types/v1",rank=0,epoch=0,
   source=source,pools=[],allocator_retirement_not_claimed=True)
  refs={};seed=dict(path=root+("/previous.json" if epoch==1 else "/ledger-%d.json"%(epoch-1)),sha256=str(epoch)*64 if epoch==1 else "d"*64);refs[seed["path"]]=prior
  proof=dict(epoch=epoch,source=source,records=[dict(rank=0,cgroup=self.actual[record_rank]["cgroup"],numpy={})],
   pools=[dict(rank=0,pools=[p])])
  budget=dict(path=root+"/budget-%d.json"%epoch,sha256="c"*64);refs[budget["path"]]=proof
  ledger=g.typed_ledger([p],prior,0,epoch,source);ledger.update(previous=seed,joint_budget=budget)
  lr=dict(path=root+"/ledger-%d.json"%epoch,sha256="d"*64);refs[lr["path"]]=ledger
  check=g.PhysicalChecker(p,[]);check.chunk(0,bytes(32),bytes(32))
  sr=dict(path=root+"/summary-%d.json"%epoch,sha256="e"*64);refs[sr["path"]]=check.finish()
  ref=dict(path=root+"/physical-%d.json"%epoch,sha256=str(epoch)*64)
  refs[ref["path"]]=dict(schema=g.PHYSICAL_PROTOCOL,source=source,rank=0,epoch=epoch,
   independent_checker=checker,all64_actual_writer_metadata=True,postmortem_success_bytes_replay_claimed=False,
   joint_budget=budget,ledger=lr,pool_summaries=[sr],original_full_before_copy_count=1)
  def obj(r):
   if r["path"] in refs:return refs[r["path"]]
   return json.loads(Path(c.bound(r["path"],r["sha256"])["path"]).read_text())
  return ref,checker,source,patch.object(c,"obj",side_effect=obj),patch.object(g,"consume_physical_budget",side_effect=lambda x:x)
 def call(self,context,epoch=1,previous=None,record_rank=0,root="/cache/cch/software-context-a"):
  ref,ch,src,obj,budget=self.harness(epoch,previous,record_rank,root)
  with obj,budget:return state.consume_physical_epoch(ref,ch,src,context)
 def test_same_epoch48_aliases_reuse_local_context(self):
  context=state.PhysicalContext();first=self.call(context)
  self.assertIs(self.call(context),first)
 def test_same_owner_whole_replay_independent_context(self):
  first=self.call(state.PhysicalContext());again=self.call(state.PhysicalContext())
  self.assertEqual(first["ledger"],again["ledger"]);self.assertIsNot(first,again)
 def test_same_owner_sequential_epoch_accepted(self):
  context=state.PhysicalContext();first=self.call(context);second=self.call(context,2,first["ledger"])
  self.assertEqual(second["epoch"],2)
 def test_owner_start_change_rejected_within_epoch_history(self):
  context=state.PhysicalContext();first=self.call(context)
  # Captured rank1 has a different actual PID/start on the same actual leaf.
  with self.assertRaisesRegex(ValueError,"same actual PID/start"):
   self.call(context,2,first["ledger"],record_rank=1)
 def test_skipped_epoch_rejected(self):
  context=state.PhysicalContext();first=self.call(context)
  forged=dict(first["ledger"],epoch=2)
  with self.assertRaisesRegex(ValueError,"sequential"):
   self.call(context,3,forged)
 def test_changed_trace_root_does_not_inherit_prior_history(self):
  context=state.PhysicalContext();first=self.call(context)
  with self.assertRaisesRegex(ValueError,"sequential"):
   self.call(context,2,first["ledger"],root="/cache/cch/software-context-b")
 def test_explicit_context_required_not_process_global(self):
  with self.assertRaisesRegex(ValueError,"isolated"):
   self.call(None)

class ExactExtentGeometry(unittest.TestCase):
 """Independent old row/slot expressions on small exhaustive geometries."""
 def view(self,dtype="torch.float32",rows=3,inner=2,padding=0,offset=1):
  width=4 if dtype=="torch.float32" else 2
  size=(offset+(rows-1)*(inner+padding)+inner+5)*width
  return dict(shape=[rows,inner],stride=[inner+padding,1],dtype=dtype,device="npu:0",
   pointer=1000+offset*width,storage_pointer=1000,storage_offset=offset,storage_bytes=size,
   native_format_value=2,native_format_type="torch_npu.npu._format.Format")
 def original_rows(self,x):
  width=2 if x["dtype"]=="torch.bfloat16" else 4;row=width
  for n in x["shape"][1:]:row*=n
  return g.normalize_extents([[(x["storage_offset"]+i*x["stride"][0])*width,
   (x["storage_offset"]+i*x["stride"][0])*width+row] for i in range(x["shape"][0])],x["storage_bytes"])
 def fa(self,slots):
  x=dict(self.view("torch.bfloat16"),shape=[2,128,1,256],stride=[32768,256,256,1],
   storage_bytes=2*(1+2*32768+5))
  raw=dict(schema="sparq.actual-native-FA-writer-metadata/v1",cache_write_scope="original-reshape-and-cache-real-token-slice",
   allocator_source_pins=g.ALLOCATOR_PINS,is_encoder_decoder=False,cache_sharing_target=None,CP=False,quantized=False,
   num_actual_tokens=len(slots),slot_mapping=slots,actual_implementation=dict(
    **{"class":"vllm_ascend.attention.attention_v1.AscendAttentionBackendImpl"},impl_id=1,attn_type="decoder",
    decoder_value="decoder",enable_c8_quant=False,enable_hamming_sparse=False,is_kv_producer=False,
    kv_sharing_target_layer_name=None))
  return x,raw
 def test_all_small_contiguous_rows_equal_original_expression(self):
  from unittest.mock import patch
  original=g.physical_identity
  for dtype in ("torch.bfloat16","torch.float32"):
   for rows in range(1,8):
    for inner in range(1,5):
     x=self.view(dtype,rows,inner)
     with patch.object(g,"physical_identity",wraps=original) as check:
      self.assertEqual(g.full_view_extents(x),self.original_rows(x));self.assertEqual(check.call_count,1)
 def test_all_small_padded_rows_preserve_every_gap(self):
  for rows in range(2,8):
   for pad in range(1,5):
    x=self.view(rows=rows,padding=pad)
    self.assertEqual(g.full_view_extents(x),self.original_rows(x))
    self.assertEqual(len(g.full_view_extents(x)),rows)
    self.assertEqual(sum(b-a for a,b in g.full_view_extents(x)),rows*8)
 def test_FA_unordered_partial_pages_equal_original_slot_expression(self):
  x,raw=self.fa([129,-1,0,127,128,7,-1])
  old=[]
  for slot in raw["slot_mapping"]:
   if slot<0:continue
   block,offset=divmod(slot,128);start=(x["storage_offset"]+block*x["stride"][0]+offset*x["stride"][1])*2
   old.append([start,start+512])
  self.assertEqual(g.fa_write_extents(x,raw),g.normalize_extents(old,x["storage_bytes"]))
  self.assertEqual(sum(b-a for a,b in g.fa_write_extents(x,raw)),5*512)
 def test_FA_repeated_positive_slot_rejected_minus_one_still_padding(self):
  x,raw=self.fa([3,-1,3])
  with self.assertRaisesRegex(ValueError,"collision"):g.fa_write_extents(x,raw)
 def test_FA_out_of_range_and_noninteger_hard_negative(self):
  for slots in ([256],[-2],[True],[0.0]):
   x,raw=self.fa(slots)
   with self.assertRaisesRegex(ValueError,"slot mapping"):g.fa_write_extents(x,raw)
 def test_unsupported_dtype_hard_negative(self):
  x=self.view();x["dtype"]="torch.float64"
  with self.assertRaisesRegex(ValueError,"typed shape"):g.full_view_extents(x)
 def test_cross_JSON_heap_bound_has_no_shared_object_credit(self):
  values=[1,2,3];shared={"a":values,"b":values};reloaded=json.loads(json.dumps(shared))
  self.assertEqual(g._metadata_heap_upper(shared),g._metadata_heap_upper(reloaded))
  self.assertGreater(g._metadata_heap_upper(shared),0)
 def test_nonJSON_or_cyclic_heap_metadata_rejected(self):
  x=[];x.append(x)
  with self.assertRaisesRegex(ValueError,"cyclic"):g._metadata_heap_upper(x)
  with self.assertRaisesRegex(ValueError,"JSON-built"):g._metadata_heap_upper({1,2})

class ActualCPUProducerProtocol(unittest.TestCase):
 def produced(self):
  # Execute the exact real producer assignment, not a hand-written protocol.
  # NumPy here is an explicit source-format fixture; no framework import.
  from types import SimpleNamespace
  tree=ast.parse((ROOT/"full_cpu_preflight.py").read_text())
  writes=[]
  for n in ast.walk(tree):
   if isinstance(n,ast.Assign) and len(n.targets)==1:
    target=n.targets[0]
    if (isinstance(target,ast.Subscript) and isinstance(target.value,ast.Name) and
        target.value.id=="observed" and isinstance(target.slice,ast.Constant) and
        target.slice.value=="GDN_stream_checker"):
     writes.append(n)
  self.assertEqual(len(writes),1,"one exact CPU report producer assignment")
  files={"gdn_stream.py":c.sha(Path(g.__file__).resolve())}
  ns=dict(observed={},gdn_stream=g,c=c,Path=Path,files=files,
   numpy=SimpleNamespace(__version__="software-source-format-fixture",
    __file__=str((ROOT/"full_cpu_preflight.py").resolve())))
  exec(compile(ast.Module(body=writes,type_ignores=[]),"actual-full-CPU-report-assignment","exec"),ns)
  return ns["observed"],files
 def test_actual_CPU_producer_physical_v3_accepted(self):
  observed,files=self.produced()
  self.assertEqual(observed["GDN_stream_checker"]["protocol"],g.PHYSICAL_PROTOCOL)
  got=g.validate_probe(observed,files)
  self.assertFalse(got["state_arithmetic_executed"])
  self.assertTrue(got["actual_initialized_shape_and_joint_budget_pending"])
 def test_actual_CPU_producer_legacy_v2_rejected(self):
  observed,files=self.produced()
  self.assertNotEqual(g.PROTOCOL,g.PHYSICAL_PROTOCOL)
  observed["GDN_stream_checker"]["protocol"]=g.PROTOCOL
  with self.assertRaisesRegex(ValueError,"actual same-image CPU new-checker"):
   g.validate_probe(observed,files)
