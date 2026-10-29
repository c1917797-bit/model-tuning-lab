import copy,unittest
from host_audits import r45_compilation_evidence as e
class EvidenceControls(unittest.TestCase):
 def rows(self,*,offset=0):
  common={"pid":31,"manifest_sha256":"a"*64}
  install=dict(common,event="r45_compilation_observer_installed",profile=e.PROFILE,max_calls=512,default_disabled=True,upstream_sources=e.PINS)
  def begin(i,parent,kind,t):
   return dict(common,event="r45_compilation_begin",call_id=i,parent_call_id=parent,kind=kind,rank=0,thread_id="9007199254740993",metadata={"kernel_name":"k","async_compile_active":False},wrapper_entry_ns=str(offset+t))
  def end(b,a,z):
   return dict(b,event="r45_compilation_end",original_started_ns=str(offset+a),original_ended_ns=str(offset+z),original_duration_ns=str(z-a),begin_probe_ns=str(offset+a-int(b["wrapper_entry_ns"])),failed=False,error_type=None,return_type="builtins.NoneType")
  a=begin(1,None,"jit_cache_miss",0);b=begin(2,1,"compiler_api",12)
  health=dict(common,event="r45_compilation_health",profile=e.PROFILE,rank=0,step=2053,calls=2,completed=2,active=0,failed=False,skipped_initialized_loads=0)
  return [install,a,b,end(b,14,30),end(a,5,40),health]
 def audit(self,rows):return e.audit_worker(rows,pid=31,rank=0,manifest="a"*64)
 def test_nested_union_exact_above_double_precision(self):
  d=self.audit(self.rows(offset=2**60));self.assertEqual(d["calls"],2);self.assertEqual(d["native_call_union_ns"],"35")
  self.assertEqual(d["per_kind_union_ns"]["compiler_api"],"16")
  self.assertEqual(d["frames"][0]["native_start_ns"],str(2**60+14))
 def test_missing_and_duplicate_records_rejected(self):
  for i in(0,1,2,3,4):
   rows=self.rows();rows.pop(i)
   with self.subTest(drop=i),self.assertRaises(ValueError):self.audit(rows)
  rows=self.rows();rows.insert(4,copy.deepcopy(rows[3]))
  with self.assertRaises(ValueError):self.audit(rows)
 def test_pid_manifest_rank_drift_rejected(self):
  for key,value in(("pid",32),("manifest_sha256","b"*64),("rank",1)):
   rows=self.rows();rows[2][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.audit(rows)
 def test_parent_thread_and_counter_drift_rejected(self):
  for key,value in(("parent_call_id",None),("thread_id","9007199254740992"),("call_id",3)):
   rows=self.rows();rows[2][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.audit(rows)
 def test_bad_clock_or_duration_rejected(self):
  for key,value in(("original_started_ns","-1"),("original_ended_ns","13"),("original_duration_ns","17"),("begin_probe_ns","3"),("original_ended_ns","NaN")):
   rows=self.rows();rows[3][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.audit(rows)
 def test_child_outside_parent_rejected(self):
  rows=self.rows();rows[3].update(original_ended_ns="50",original_duration_ns="36")
  with self.assertRaises(ValueError):self.audit(rows)
 def test_failed_original_not_valid(self):
  rows=self.rows();rows[3]["failed"]=True;rows[3]["error_type"]="RuntimeError"
  with self.assertRaises(ValueError):self.audit(rows)
 def test_health_missing_or_inconsistent_rejected(self):
  rows=self.rows();rows.pop()
  with self.assertRaises(ValueError):self.audit(rows)
  for key,value in(("calls",3),("completed",1),("failed",True),("rank",False)):
   rows=self.rows();rows[-1][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.audit(rows)
 def test_unassigned_and_async_retained_explicitly(self):
  rows=self.rows()
  for i in(2,3):rows[i]["rank"]=None;rows[i]["metadata"]["async_compile_active"]=True
  d=self.audit(rows);self.assertEqual(d["unassigned_or_unassociated_calls"],1);self.assertEqual(d["async_jit_misses"],1)
 def test_unknown_or_wrong_source_activation_rejected(self):
  for mutate in("event","pin","bound"):
   rows=self.rows()
   if mutate=="event":rows[2]["event"]="r45_compilation_unknown"
   if mutate=="pin":rows[0]["upstream_sources"]={}
   if mutate=="bound":rows[0]["max_calls"]=4096
   with self.subTest(mutate=mutate),self.assertRaises(ValueError):self.audit(rows)
 def test_union_intersection_without_double_count(self):
  self.assertEqual(e.duration([(0,20),(5,10),(20,30)]),30)
  self.assertEqual(e.intersection([(0,20),(25,30)],[(10,28)]),[(10,20),(25,28)])
  for rows in([(-1,2)],[(5,4)],[(0.0,2)]):
   with self.assertRaises(ValueError):e.duration(rows)
 def results(self):
  return [{"ok":True,"metrics":{"request_id":str(i),"started":i*4.,"first_content":i*4.+1.,"ended":i*4.+3.}}for i in range(40)]
 def reports(self,spans):
  return [{"rank":i,"intervals":copy.deepcopy(spans)}for i in range(4)]
 def test_no_shared_clock_never_invents_budget(self):
  d=e.budget(self.reports([(0,10)]),self.results())
  self.assertFalse(d["causal_budget_valid"]);self.assertFalse(d["allow_kernel_rewrite"]);self.assertNotIn("upper_weighted_ns",d)
 def test_global_union_not_rank_or_inclusive_sum(self):
  d=e.budget(self.reports([(0,10**9),(0,2*10**9)]),self.results(),shared_monotonic_clock_proven=True)
  self.assertLessEqual(int(d["upper_weighted_ns"]),1000000002)
  self.assertTrue(d["insufficient_even_with_observation_overhead"]);self.assertFalse(d["allow_kernel_rewrite"])
 def test_large_upper_bound_does_not_prove_cause(self):
  rows=[{"ok":True,"metrics":{"request_id":str(i),"started":0.,"first_content":1.,"ended":100.}}for i in range(40)]
  d=e.budget(self.reports([(0,100*10**9)]),rows,shared_monotonic_clock_proven=True)
  self.assertFalse(d["insufficient_even_with_observation_overhead"]);self.assertFalse(d["allow_kernel_rewrite"])
  self.assertFalse(d["causal_budget_valid"]);self.assertLessEqual(int(d["upper_weighted_ns"]),16*100*10**9+32)
 def test_request_denominator_identity_and_order(self):
  for mutate in("missing","duplicate","order","nan"):
   rows=self.results()
   if mutate=="missing":rows.pop()
   if mutate=="duplicate":rows[1]["metrics"]["request_id"]="0"
   if mutate=="order":rows[0]["metrics"]["ended"]=0
   if mutate=="nan":rows[0]["metrics"]["first_content"]=float("nan")
   with self.subTest(mutate=mutate),self.assertRaises(ValueError):e.request_intervals(rows)
 def test_outward_float_clock_does_not_claim_exact_ns(self):
  lo=e.outward_float_ns(1.1,upper=False);hi=e.outward_float_ns(1.1,upper=True)
  self.assertLessEqual(lo,1100000000);self.assertGreaterEqual(hi,1100000000);self.assertLessEqual(hi-lo,3)
if __name__=="__main__":unittest.main()
