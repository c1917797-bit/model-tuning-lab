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
   cgroup=memory_fixture(100+r),max_model_len=40960,
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

# Synthetic serializer fixtures below are NOT runtime/model authority. The
# archived0692 test uses its original SHA-bound controller report, no NPU calls.
MEMORY_REPORT={"path":"/cache/cch/qwen36-paper-preparation-20261007/sparse/MAIN-sparq004-cgroup-view-no-device-user72h-20261009-001/REPORT.json","sha256":"d1725f159fa58fe9aa82d2d4cd2523ba62729b73db4b2ea6f8bb6ba2a58abc9f"}
def memory_fixture(pid=100,limit=stream.GUEST,version=1,root=None,cid="a"*64):
 import stat
 from pathlib import PurePosixPath
 group="/docker/"+cid;root=group if root is None else root
 point="/sys/fs/cgroup/memory" if version==1 else "/sys/fs/cgroup"
 line="7:memory:"+group+"\n" if version==1 else "0::"+group+"\n"
 mount="811 804 0:37 "+root+" "+point+" ro,nosuid,nodev,noexec,relatime - "+("cgroup cgroup rw,memory" if version==1 else "cgroup2 cgroup rw")
 layout=stream.memory_layout(line,mount)
 values=(str(limit)+"\n","1073741824\n","1073745920\n")
 files={str(PurePosixPath(layout["path"])/n):v for n,v in zip(stream.MEMORY_KEYS[version],values)}
 # /proc/stat fields3..22. Only software collaborator bytes, not a saved PID.
 tail=["S"]+["1"]*18+["12345"]+["0"]*4
 text=str(pid)+" (software fixture) "+" ".join(tail)+"\n"
 ids={p:dict(device=37,inode=200+i,mode=stat.S_IFREG|0o444) for i,p in enumerate(files)}
 return dict(schema=stream.MEMORY,**layout,process=dict(pid=pid,start_ticks=12345),stat_before=text,stat_after=text,
  proc_cgroup=line,proc_cgroup_after=line,mountinfo_raw=mount,mountinfo_after=mount,
  control_raw=files,expected_limit_bytes=limit,memory_max=limit,memory_current=1073741824,memory_peak=1073745920,
  leaf_identity=dict(device=37,inode=100,mode=stat.S_IFDIR|0o555),
  leaf_identity_after=dict(device=37,inode=100,mode=stat.S_IFDIR|0o555),
  file_identities=copy.deepcopy(ids),file_identities_after=copy.deepcopy(ids),limit_raw_after=values[0])
class MemoryNamespaceLeaf(unittest.TestCase):
 def test_actual_archived0692_v1_mountroot_equals_group_and_files_at_mountpoint(self):
  from pathlib import Path
  import evidence as e
  actual=e.obj(MEMORY_REPORT);self.assertEqual(actual["schema"],"sparq.actual-no-device-cgroup-view/v1")
  raw="\n".join(m["raw"] for m in actual["mounts"])
  layout=stream.memory_layout(actual["proc_cgroup"],raw);row=actual["candidates"][0]
  self.assertEqual(layout["path"],"/sys/fs/cgroup/memory")
  self.assertEqual(layout["mount_root"],layout["cgroup"])
  self.assertEqual(layout["path"],row["path"])
  self.assertEqual([int(row["files"][n]["value"]) for n in stream.MEMORY_KEYS[1]],[8589934592,5656576,6516736])
  self.assertFalse(layout["full_host_ancestors_observed"])
 def test_v1_full_mount_maps_group_but_truncated_mount_never_double_appends(self):
  for root in (None,"/","/docker"):
   value=memory_fixture(root=root);self.assertIs(stream.consume_memory(value),value)
   self.assertEqual(value["path"],value["mount_point"] if root is None else value["mount_point"]+("/docker/" if root=="/" else "/")+"a"*64)
 def test_v2_exact_owned_leaf_and_no_unified_root_fallback(self):
  value=memory_fixture(version=2);self.assertIs(stream.consume_memory(value),value)
  self.assertEqual(value["path"],"/sys/fs/cgroup")
  bad=copy.deepcopy(value);bad["proc_cgroup"]=bad["proc_cgroup_after"]="0::/outside\n"
  with self.assertRaises(ValueError):stream.consume_memory(bad)
 def test_only_registered_cpu8_or_default_model64_limits_accepted(self):
  for limit in (8*1024**3,stream.GUEST):self.assertIsInstance(stream.consume_memory(memory_fixture(limit=limit),limit),dict)
  with self.assertRaises(ValueError):stream.consume_memory(memory_fixture(limit=8*1024**3))
  for bad in ("max","-1","9223372036854771712","1x"):
   value=memory_fixture();path=next(iter(value["control_raw"]))
   value["control_raw"][path]=value["limit_raw_after"]=bad
   with self.assertRaises(ValueError):stream.consume_memory(value)
  with self.assertRaises(ValueError):stream.consume_memory(memory_fixture(),32*1024**3)
 def test_missing_ambiguous_controller_mount_and_namespace_escape_rejected(self):
  v=memory_fixture()
  for raw,mt in (("7:cpu:/docker/"+"a"*64,v["mountinfo_raw"]),
   (v["proc_cgroup"],v["mountinfo_raw"]+"\n"+v["mountinfo_raw"]),
   (v["proc_cgroup"]+"8:memory:/docker/"+"a"*64+"\n",v["mountinfo_raw"]),
   ("7:memory:/docker/../"+"a"*64,v["mountinfo_raw"]),
   ("7:memory:/external",v["mountinfo_raw"]),
   (v["proc_cgroup"],v["mountinfo_raw"].replace("/sys/fs/cgroup/memory","/tmp/not-a-controller"))):
   with self.assertRaises(ValueError):stream.memory_layout(raw,mt)
 def test_changed_pid_start_cgroup_mountinfo_limit_and_inode_failclosed(self):
  for change in (
   lambda v:v.update(stat_after=v["stat_after"].replace("12345","12346")),
   lambda v:v.update(proc_cgroup_after="7:memory:/different"),
   lambda v:v.update(mountinfo_after=v["mountinfo_raw"]+"\nchanged"),
   lambda v:v.update(limit_raw_after="1"),
   lambda v:v["leaf_identity_after"].update(inode=999),
   lambda v:next(iter(v["file_identities_after"].values())).update(inode=999)):
   v=memory_fixture();change(v)
   with self.assertRaises(ValueError):stream.consume_memory(v)
 def test_foreign_cid_wrong_namespace_pid_or_claimed_numbers_rejected(self):
  for change,kwargs in ((lambda v:None,dict(container_id="b"*64)),
   (lambda v:None,dict(namespace_pid=101)),(lambda v:v.update(memory_current=1),{}),
   (lambda v:v.update(version=True),{}),(lambda v:v["leaf_identity"].update(mode=0o120777),{})):
   v=memory_fixture();change(v)
   with self.assertRaises(ValueError):stream.consume_memory(v,**kwargs)
  self.assertTrue(stream.consume_memory(memory_fixture(),container_id="a"*64,namespace_pid=100))
  # Execute the REAL preweight consumer over immutable unit files; these are
  # software identities, never a fabricated worker or model authority.
  import tempfile,identity_bridge as ib,evidence as e
  from pathlib import Path
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);ident=root/"identity.json";ident.write_text(json.dumps(dict(container_id="a"*64)))
   ir=e.bound(ident,e.sha(ident));p=dict(pid=100,start_ticks=12345,cgroup=memory_fixture()["proc_cgroup"])
   record=dict(schema="sparq.actual-preweight-memory/v1",source={},files={},identity=ir,process=p,
    memory=memory_fixture(),stage="existing-plugin-bootstrap-before-runner-and-weight-allocation",
    model_allocation_not_started=True,worker_rank_not_assumed=True,ready=False)
   path=root/"startup.json";path.write_text(json.dumps(record));ref=e.bound(path,e.sha(path))
   self.assertEqual(ib.consume_startup_memory(ref,{},{},ir,p),record)
   for process in (dict(p,pid=101),dict(p,start_ticks=12346),dict(p,cgroup="/foreign")):
    with self.assertRaises(ValueError):ib.consume_startup_memory(ref,{},{},ir,process)
 def reader(self,fixture):
  from unittest.mock import patch
  import os
  v=copy.deepcopy(fixture);pid=os.getpid()
  v["process"]["pid"]=pid
  for key in ("stat_before","stat_after"):v[key]=str(pid)+v[key][v[key].index(" ("):]
  raw={"/proc/self/stat":v["stat_before"],"/proc/self/cgroup":v["proc_cgroup"],"/proc/self/mountinfo":v["mountinfo_raw"],**v["control_raw"]}
  def inode(path,directory=False):return copy.deepcopy(v["leaf_identity"] if directory else v["file_identities"][path])
  return v,raw,inode,patch
 def test_real_reader_callable_uses_cpu8_and_default64_no_module_hardware(self):
  for limit in (8*1024**3,stream.GUEST):
   v,raw,inode,patch=self.reader(memory_fixture(limit=limit))
   with patch.object(stream,"_read_memory_text",lambda p:raw[p]),patch.object(stream,"_read_memory_identity",inode):
    got=stream.memory(limit) if limit!=stream.GUEST else stream.memory()
   self.assertEqual(got,v);self.assertEqual(got["memory_max"],limit)
  import tempfile,evidence as e
  from pathlib import Path
  with tempfile.TemporaryDirectory() as folder:
   full=memory_fixture();path=Path(folder)/"preweight.json"
   path.write_text(json.dumps(dict(schema="sparq.actual-preweight-memory/v1",memory=full,source={},model_allocation_not_started=True)))
   ref=e.bound(path,e.sha(path));fresh=copy.deepcopy(full)
   usage=list(fresh["control_raw"])[1];fresh["control_raw"][usage]="1073741825\n";fresh["memory_current"]+=1
   sample=stream.memory_sample(fresh,ref)
   self.assertNotIn("mountinfo_raw",sample);self.assertNotIn("proc_cgroup",sample)
   self.assertEqual(stream.consume_memory(sample)["memory_current"],1073741825)
   sample["mountinfo_raw_sha256"]="0"*64
   with self.assertRaises(ValueError):stream.consume_memory(sample)
 def test_live_permission_missing_controls_not_zero_or_host_fallback(self):
  for error in (PermissionError(13,"denied"),FileNotFoundError(2,"absent"),ProcessLookupError(3,"gone")):
   v,raw,inode,patch=self.reader(memory_fixture())
   def fail(path):
    if path.endswith("memory.usage_in_bytes"):raise error
    return raw[path]
   with patch.object(stream,"_read_memory_text",fail),patch.object(stream,"_read_memory_identity",inode):
    with self.assertRaises(type(error)) as ctx:stream.memory()
   self.assertIs(ctx.exception,error)
 def test_real_reader_second_identity_and_limit_reads_detect_changes(self):
  for target in ("/proc/self/stat","/proc/self/cgroup","/proc/self/mountinfo","memory.limit_in_bytes"):
   v,raw,inode,patch=self.reader(memory_fixture());counts={}
   def read(path):
    counts[path]=counts.get(path,0)+1
    value=raw[path]
    if counts[path]>1 and (path==target or path.endswith(target)):
     return value.replace("12345","12346") if target.endswith("stat") else value+"0"
    return value
   with patch.object(stream,"_read_memory_text",read),patch.object(stream,"_read_memory_identity",inode):
    with self.assertRaises(ValueError):stream.memory()
 def test_four_rank_budget_rejects_distinct_leaves_and_duplicate_worker_pid(self):
  for malformed in (None,[],1,"not-memory"):
   with self.assertRaisesRegex(ValueError,"must be a dictionary"):stream.consume_memory(malformed)
  records=FourRankRealBudget().records();source=records[0]["source"]
  for mutate in (lambda v:v[1].update(cgroup=memory_fixture(101,cid="b"*64)),
   lambda v:v[1].update(cgroup=memory_fixture(100))):
   bad=copy.deepcopy(records);mutate(bad)
   with self.assertRaises(ValueError):stream.plan(bad,1024**3,1,source,40960)
  import tempfile,evidence as e
  from pathlib import Path
  # This is the actual source Ref; only process/control bytes are unit fixtures.
  actual_source=e.bound(Path(__file__).with_name("SOURCE_MANIFEST.json"),e.sha(Path(__file__).with_name("SOURCE_MANIFEST.json")))
  with tempfile.TemporaryDirectory() as folder:
   root=Path(folder);compact=FourRankRealBudget().records()
   for row in compact:
    row["source"]=actual_source;raw=row["cgroup"]
    proof=dict(schema="sparq.actual-preweight-memory/v1",memory=raw,source=actual_source,model_allocation_not_started=True)
    path=root/("rank%d.json"%row["rank"]);path.write_text(json.dumps(proof))
    row["cgroup"]=stream.memory_sample(raw,e.bound(path,e.sha(path)))
   self.assertEqual(stream.plan(compact,1024**3,1,actual_source,40960)["all_initialized_states"],384)
   bad=copy.deepcopy(compact);proof=e.obj(bad[1]["cgroup"]["namespace_proof"])
   proof["source"]=dict(actual_source,sha256="0"*64)
   path=root/"wrong-source.json";path.write_text(json.dumps(proof))
   bad[1]["cgroup"]["namespace_proof"]=e.bound(path,e.sha(path))
   with self.assertRaisesRegex(ValueError,"same actual source"):stream.plan(bad,1024**3,1,actual_source,40960)
   bad=copy.deepcopy(compact);bad[2]["cgroup"]["mountinfo_after_sha256"]="0"*64
   with self.assertRaisesRegex(ValueError,"same namespace raw bytes"):stream.plan(bad,1024**3,1,actual_source,40960)
 def test_actual_cpu_n1_and_observer_entry_paths_call_reader_before_hardware(self):
  import ast
  from pathlib import Path
  def body(name):return Path(__file__).with_name(name).read_text()
  cpu=ast.parse(body("full_cpu_preflight.py"));n1=ast.parse(body("identity_bridge.py"));obs=ast.parse(body("gdn_model_observer.py"))
  call=lambda n:isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="memory"
  cpu_calls=[n for n in ast.walk(cpu) if call(n)];self.assertEqual(len(cpu_calls),1)
  self.assertEqual(ast.literal_eval(cpu_calls[0].args[0]),8*1024**3) if isinstance(cpu_calls[0].args[0],ast.Constant) else self.assertEqual(ast.dump(cpu_calls[0].args[0]),ast.dump(ast.parse("8*1024**3",mode="eval").body))
  fn=next(n for n in n1.body if isinstance(n,ast.FunctionDef) and n.name=="n1_dependency_gate")
  mc=[n for n in ast.walk(fn) if call(n)];self.assertEqual(len(mc),1);self.assertEqual(mc[0].args,[])
  imports=[n for n in ast.walk(fn) if isinstance(n,ast.Import) and any(a.name.startswith(("torch","vllm")) for a in n.names)]
  self.assertLess(mc[0].lineno,min(n.lineno for n in imports))
  of=next(n for n in obs.body if isinstance(n,ast.FunctionDef) and n.name=="memory")
  self.assertEqual(len([n for n in ast.walk(of) if call(n)]),1)
  self.assertIn('consume_memory(x["owned_memory_cgroup"]',body("identity_bridge.py"))
  bridge=ast.parse(body("bridge.py"));install=next(n for n in bridge.body if isinstance(n,ast.FunctionDef) and n.name=="install_from_env")
  startup=[n for n in ast.walk(install) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="startup_memory_gate"]
  self.assertEqual(len(startup),1)
  hardware=[n.lineno for n in ast.walk(install) if isinstance(n,ast.Import) and any(a.name.startswith(("torch","vllm")) for a in n.names)]
  self.assertLess(startup[0].lineno,min(hardware))
  self.assertIn("pre_weight_memory=startup_memory",body("bridge.py"))
  self.assertIn('consume_startup_memory(w["pre_weight_memory"]',body("consume_model.py"))
  self.assertIn('consume_startup_memory(start["pre_weight_memory"]',body("consume_service.py"))
  worker=__import__("evidence").bound("/cache/cch/qwen36-paper-preparation-20261007/sparse/sp4-public-actual-npu-worker-source-v1-001/npu_worker.py","c392da56095b255d47fe5ad7ffdfbedd269fe69851690e89a8d2ed44c073f6c3")
  wt=ast.parse(Path(worker["path"]).read_text());cls=next(n for n in wt.body if isinstance(n,ast.ClassDef) and n.name=="NPUWorker")
  init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="init_device");load=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=="load_model")
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=="NPUModelRunner" for n in ast.walk(init)))
  self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Attribute) and n.func.value.attr=="model_runner" and n.func.attr=="load_model" for n in ast.walk(load)))
  self.assertIn('static_probe(cp,source,files,cpu["container_id"])',body("consume_model.py"))

if __name__=="__main__":unittest.main()
