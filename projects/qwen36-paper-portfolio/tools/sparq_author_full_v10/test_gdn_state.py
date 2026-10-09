"""Complete-slot evidence contract negatives; no actual GDN/model PASS fixture."""
import unittest
import gdn_state as g
class State(unittest.TestCase):
 def test_48_actual_architecture_positions(self):
  self.assertEqual(len(g.GDN),48);self.assertEqual(set(g.GDN)|set(range(3,64,4)),set(range(64)))
 def test_missing_metadata_fails_before_a_state_pass(self):
  with self.assertRaises((ValueError,KeyError)):g.consume(dict(layer=0,prefix="model.layers.0",original_forward_core_unchanged=False),{})
 def test_FA_cannot_be_counted_as_GDN(self):
  with self.assertRaises(ValueError):g.consume(dict(layer=3,prefix="model.layers.3",original_forward_core_unchanged=True,
   original_forward_unchanged=True,deployed_state_sources={}),{})


# Unit bytes are IEEE wire-format fixtures, not native GDN/model evidence.
import copy,struct,sys,json
import gdn_stream as stream
class AllRowLiveBytes(unittest.TestCase):
 def identity(self,dtype="torch.bfloat16",slots=3):
  return dict(shape=[slots,2,2],dtype=dtype)
 def body(self,word=0x3f80):
  return struct.pack("<4H",word,word,word,word)
 def test_complete_actual_serializer_to_independent_summary_consumer(self):
  ident=self.identity();check=stream.Checker(ident,[1])
  for i in range(3):check.row(i,self.body(),self.body(0x4000) if i==1 else self.body())
  raw=json.loads(json.dumps(check.finish()));got=stream.consume_summary(raw,ident,[1])
  self.assertTrue(got["all_after_finite"]);self.assertEqual(got["active_changed_slots"],[1])
  self.assertEqual(got["all_rows"],3);self.assertFalse(got["postmortem_success_bytes_replay_claimed"])
 def test_inactive_one_byte_change_rejected_with_original_hashes(self):
  check=stream.Checker(self.identity(),[1]);after=bytearray(self.body());after[0]^=1
  with self.assertRaises(stream.FirstRowError) as err:check.row(0,self.body(),after)
  self.assertFalse(err.exception.record["written"]);self.assertTrue(err.exception.record["finite"]["finite"])
  self.assertNotEqual(err.exception.record["before_sha256"],err.exception.record["after_sha256"])
 def test_every_active_nan_and_inf_rejected_not_dense_bitwise_gate(self):
  for word in (0x7f80,0xff80,0x7fc1):
   check=stream.Checker(self.identity(slots=1),[0])
   with self.assertRaises(stream.FirstRowError) as err:check.row(0,self.body(),self.body(word))
   self.assertTrue(err.exception.record["written"]);self.assertFalse(err.exception.record["finite"]["finite"])
 def test_inactive_nonfinite_also_rejected(self):
  check=stream.Checker(self.identity(slots=1),[])
  with self.assertRaises(stream.FirstRowError):check.row(0,self.body(0x7f80),self.body(0x7f80))
 def test_float32_full_row_exponent_and_signed_finite(self):
  ident=self.identity("torch.float32",1);finite=struct.pack("<4I",0,0x80000000,0x3f800000,0xff7fffff)
  check=stream.Checker(ident,[]);check.row(0,finite,finite)
  self.assertEqual(check.finish()["finite_elements_checked"],4)
  after=struct.pack("<4I",0,0x80000000,0x3f800000,0x7f800001)
  check=stream.Checker(ident,[0])
  with self.assertRaises(stream.FirstRowError) as err:check.row(0,finite,after)
  self.assertEqual(err.exception.record["finite"]["element"],3)
 def test_multidimensional_uint8_view_is_flattened(self):
  original=memoryview(bytearray(8)).cast("B",shape=(2,4))
  self.assertEqual(len(original),2);self.assertEqual(len(stream.view(original)),8)
 def test_tail_chunk_is_checked_not_sampled(self):
  raw=bytearray(stream.CHUNK+2);raw[-2:]=struct.pack("<H",0x7f80)
  got=stream.finite(raw,"torch.bfloat16")
  self.assertFalse(got["finite"]);self.assertEqual(got["element"],stream.CHUNK//2)
 def test_missing_duplicate_and_out_of_order_row_rejected(self):
  check=stream.Checker(self.identity(),[1])
  with self.assertRaises(ValueError):check.row(1,self.body(),self.body())
  check.row(0,self.body(),self.body())
  with self.assertRaises(ValueError):check.row(0,self.body(),self.body())
  with self.assertRaises(ValueError):check.finish()
 def test_whole_byte_size_and_dtype_negative(self):
  check=stream.Checker(self.identity(slots=1),[])
  with self.assertRaises(ValueError):check.row(0,self.body(),self.body()[:-1])
  with self.assertRaises(ValueError):stream.finite(b"00","torch.float16")
 def test_serializer_coverage_writer_finite_disagreement_rejected(self):
  check=stream.Checker(self.identity(),[1])
  for i in range(3):check.row(i,self.body(),self.body())
  actual=check.finish()
  for field,value in (("rows_checked",2),("finite_elements_checked",11),("all_after_finite",False),
   ("written_slots",[]),("active_changed_slots",[0]),("permanent_success_after_dump",True)):
   bad=copy.deepcopy(actual);bad[field]=value
   with self.assertRaises(ValueError):stream.consume_summary(bad,self.identity(),[1])
class FourRankRealBudget(unittest.TestCase):
 def records(self):
  return [dict(schema=stream.BUDGET,rank=r,epoch=1,source={"path":"/unit/source","sha256":"a"*64},
   cgroup=dict(memory_max=stream.GUEST,memory_current=1024**3),max_model_len=40960,
   states=[dict(layer=i,prefix="model.layers."+str(i),name=n,identity=dict(shape=[2,2,2],dtype="torch.bfloat16"))
    for i in range(64) if i%4!=3 for n in ("conv","recurrent")]) for r in range(4)]
 def test_real_shape_plan_serializer_consumer_and_exact_byte_formula(self):
  records=self.records();proof=stream.plan(records,1024**3,1,records[0]["source"],40960)
  got=stream.consume_budget(json.loads(json.dumps(proof)))
  self.assertEqual(got["all_before_bytes"],4*96*2*8);self.assertEqual(got["all_initialized_states"],384)
  self.assertLess(got["planned_upper_bytes"],stream.GUEST);self.assertFalse(got["blind_limit_allocation"])
 def test_four_rank_joint_not_four_independent_full_limits(self):
  records=self.records();source=records[0]["source"]
  for item in (records[:3],records+[copy.deepcopy(records[0])]):
   with self.assertRaises(ValueError):stream.plan(item,1024**3,1,source,40960)
  with self.assertRaises(ValueError):stream.plan(records,stream.GUEST-1,1,source,40960)
 def test_incomplete_state_shape_dtype_rank_and_stale_epoch_negative(self):
  source=self.records()[0]["source"]
  for mutate in (lambda x:x[0]["states"].pop(),lambda x:x[0].update(rank=False),
   lambda x:x[2].update(epoch=2),lambda x:x[1]["states"][0]["identity"].update(dtype="torch.float16"),
   lambda x:x[3]["cgroup"].update(memory_max=stream.GUEST+1)):
   records=self.records();mutate(records)
   with self.assertRaises(ValueError):stream.plan(records,1024**3,1,source,40960)
 def test_actual_larger_initialized_pool_is_rejected_not_clamped(self):
  records=self.records()
  for r in records:
   for s in r["states"]:s["identity"].update(shape=[64,128,128,128],dtype="torch.float32")
  with self.assertRaises(ValueError):stream.plan(records,1024**3,1,records[0]["source"],40960)
 def test_budget_serializer_cannot_drop_real_before_bytes(self):
  records=self.records();proof=stream.plan(records,1024**3,1,records[0]["source"],40960)
  proof["all_before_bytes"]-=8
  with self.assertRaises(ValueError):stream.consume_budget(proof)


class ActualObserverEndFlow(unittest.TestCase):
 def fixture(self,active_bad=False):
  from types import SimpleNamespace as NS
  import gdn_model_observer as observer
  obj=observer.Observer.__new__(observer.Observer)
  ident=dict(shape=[3,2,2],stride=[4,2,1],dtype="torch.bfloat16",device="npu:0",
   pointer=1024,storage_pointer=1024,storage_offset=0,storage_bytes=24,native_format_value=0)
  good=struct.pack("<4H",0x3f80,0x3f80,0x3f80,0x3f80)
  bad=struct.pack("<4H",0x7f80,0x3f80,0x3f80,0x3f80)
  class CPU:
   def __init__(self,raw):self.raw=raw
   def view(self,*args):return self
   def numpy(self):return self.raw
  arrays=[[CPU(good),CPU(bad if active_bad else good),CPU(good)] for _ in range(2)]
  current=NS(kv_cache=arrays)
  event=dict(layer=0,prefix="model.layers.0",rank=0,epoch=1,states=[
   dict(name=n,identity_before=copy.deepcopy(ident)) for n in ("conv","recurrent")])
  obj.pending={"model.layers.0":dict(obj=current,event=event,states=arrays,
   domain={"written_slots":{"conv":[1],"recurrent":[1]}},before=[[CPU(good) for _ in range(3)] for _ in range(2)])}
  obj.t=NS(uint8="uint8",npu=NS(current_stream=lambda:NS(synchronize=lambda:None)))
  obj.npu=NS();obj.np=None;obj.epochs=0;obj.pins={};obj.source={"path":"/unit/source","sha256":"a"*64};obj.checker={"path":"/unit/checker","sha256":"a"*64}
  obj.validate_original=lambda unused:None # Isolate unchanged donor identity; byte checker is REAL.
  obj.space=lambda:None;obj.cpu=lambda t:(t,t.raw)
  retained=[];obj.first=lambda e,s,i,b,a,err:retained.append((i,bytes(b),None if a is None else bytes(a),repr(err)))
  return obj,ident,retained,observer
 def test_real_end_streams_both_states_all_active_and_inactive_rows(self):
  from types import SimpleNamespace as NS
  from unittest.mock import patch
  obj,ident,retained,observer=self.fixture()
  checks=[]
  def pure_consume(event,pins,ref,source):
   for state in event["states"]:
    checks.append(stream.consume_summary(state["live_check"],state["identity_before"],[1]))
   return {"unit_contract_only":True}
  with patch.object(observer,"identity",lambda *args:copy.deepcopy(ident)),patch.object(g,"consume",pure_consume):
   out=obj.end(NS(capturing=False))
  self.assertEqual(len(out),1);self.assertEqual(len(checks),2)
  self.assertEqual([x["all_rows"] for x in checks],[3,3]);self.assertEqual(retained,[])
  self.assertIsNone(obj.pending);self.assertEqual(obj.epochs,1)
 def test_real_end_active_nonfinite_retains_first_original_row_before_raise(self):
  from types import SimpleNamespace as NS
  from unittest.mock import patch
  obj,ident,retained,observer=self.fixture(True)
  with patch.object(observer,"identity",lambda *args:copy.deepcopy(ident)),patch.object(g,"consume",side_effect=AssertionError("consumer reached before finite")):
   with self.assertRaises(stream.FirstRowError):obj.end(NS(capturing=False))
  self.assertEqual(len(retained),1);self.assertEqual(retained[0][0],1)
  self.assertNotEqual(retained[0][1],retained[0][2]);self.assertEqual(obj.epochs,0)
 def test_real_begin_joint_actualshape_admission_precedes_first_cpu_copy(self):
  import ast
  from pathlib import Path
  tree=ast.parse(Path(__file__).with_name("gdn_model_observer.py").read_text())
  fn=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=="begin")
  calls=[n for n in ast.walk(fn) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
  joint=next(n.lineno for n in calls if n.func.attr=="joint")
  cpu=next(n.lineno for n in calls if n.func.attr=="cpu")
  self.assertLess(joint,cpu);self.assertIn("not ctx.capturing",ast.get_source_segment(Path(__file__).with_name("gdn_model_observer.py").read_text(),fn))
if __name__=="__main__":unittest.main()
