"""HOST-only R45 contract/callback/clock controls; no NPU allocation."""
import copy,hashlib,json,time,unittest
from unittest.mock import patch
from host_audits import r45_diagnostic_policy as p,r45_diagnostic_controller as c,r45_diagnostic_audit as a,r45_launch_capsule as capsule
class HostControls(unittest.TestCase):
 def contract(self):return p.make_contract(clock={"path":str(p.CPU_CLOCK),"sha256":"0"*64})
 def check(self,value):
  with patch.object(p,"clock_proof",return_value={"scope":"HOST-only clock substitution, actual image probe still required"}):
   return p.check(value)
 def test_real_original_source_and_math_binding(self):
  d=self.check(self.contract());self.assertEqual(d["runtime_python"],442);self.assertEqual(d["old_runtime_python_unchanged"],438)
  self.assertEqual(d["source_bindings"],472);self.assertFalse(d["device_admission_performed"])
 def test_ruler_authority_and_algorithm_mutations(self):
  for key,value in(("performance_group","G1"),("tp",2),("physical_npus",[4,5,6,7]),("absolute_stop_utc","2026-10-30T19:15:24Z"),
    ("max_output_tokens",512),("r40_target_warmup_count",1),("enable_prefix_caching",True),("r45_diagnostic_only",False),("r42_profiler",{})):
   v=self.contract();v[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(v)
 def test_closed_host_source_and_runtime_identity(self):
  for key in("r45_host_source_sha256","r45_runtime_added_source_sha256"):
   v=self.contract();v[key][next(iter(v[key]))]="0"*64
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(v)
  v=self.contract();v["host_controller_sha256"]="0"*64
  with self.assertRaises(ValueError):self.check(v)
 def test_new_root_and_manifest_not_legacy_alias(self):
  for key,value in(("raw_root","/tmp/other"),("container_name","other"),("successor_manifest","FORMAL_WARM_R40_G3_MANIFEST_20261026.json"),("r45_role","formal-performance")):
   v=self.contract();v[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(v)
 def test_common_map_cannot_drop_retained_source(self):
  v=self.contract();v["cache_diagnostic"]["source_sha256"].pop("formal_r15_tp4.py")
  v["study_source_map_sha256"]=p.digest_map(v["cache_diagnostic"]["source_sha256"])
  with self.assertRaises(ValueError):self.check(v)
 def test_budget_rejects_before_any_device_action(self):
  v=self.contract()
  from independent_execution_deadline import deadline_epoch
  with patch.object(p.time,"time",return_value=deadline_epoch(p.DEADLINE)-7289):
   with self.assertRaises(TimeoutError):p.require_budget(v)
 def test_controller_recovers_exact_callbacks_on_runtime_error_and_exit(self):
  value=self.contract();before=(c.base.write,c.base.snapshot,c.workload_slot.run_formal_workload)
  for error in(RuntimeError("original"),SystemExit(7)):
   with patch.object(c,"check_contract",return_value={}),patch.object(p,"require_budget",return_value=10000),patch.object(c.base,"run_contract",side_effect=error):
    with self.assertRaises(type(error))as caught:c.run_contract(value)
    self.assertIs(caught.exception,error)
   self.assertEqual(before,(c.base.write,c.base.snapshot,c.workload_slot.run_formal_workload));self.assertFalse(c._LOCK.locked())
 def test_actual_namespace_snapshot_rejects_foreign_clock(self):
  def link(path):return "time:[1]"if path=="/proc/self/ns/time"else"time:[2]"
  with patch.object(c.os,"readlink",side_effect=link):
   with self.assertRaises(ValueError):c.clock_observation({"processes":[(0,123)]})
 def clock_record(self):
  image=p.reference()["image"];clocks={n:{"implementation":"clock_gettime(CLOCK_MONOTONIC)","monotonic":True,"adjustable":False,"resolution":1e-9}for n in("monotonic","perf_counter")}
  return {"helper_sha256":p.sha(capsule.__file__),"code_sha256":hashlib.sha256(capsule.CLOCK_CODE.encode()).hexdigest(),
   "exit":0,"exact_cpu_container_absent":True,"no_devices":True,"image":image,"cid":"a"*64,
   "terminal_state_before_cleanup":{"Running":False,"ExitCode":0},
   "declaration":{"Image":image,"Id":"a"*64,"HostConfig":{"Devices":[],"Privileged":False,"NetworkMode":"none"}},
   "host_clock":clocks,"host_time_namespace":"time:[1]",
   "stdout":json.dumps({"clocks":clocks,"time_namespace":"time:[1]","bracket_monotonic_ns":str(2**60),"perf_counter_ns":str(2**60+1),"bracket_monotonic_end_ns":str(2**60+2),"no_inference_imports":True})}
 def proof(self,raw):
  original=p.sha
  with patch.object(p,"load",return_value=raw),patch.object(p,"sha",side_effect=lambda x:"f"*64 if str(x)==str(p.CPU_CLOCK)else original(x)):
   return p.clock_proof({"path":str(p.CPU_CLOCK),"sha256":"f"*64})
 def test_source_bound_clock_probe_schema(self):
  self.assertEqual(self.proof(self.clock_record())["exit"],0)
 def test_clock_probe_refuses_inherited_devices_or_source_drift(self):
  for change in("device","source","live","clock","namespace"):
   raw=self.clock_record()
   if change=="device":raw["declaration"]["HostConfig"]["Devices"]=[{"PathOnHost":"/dev/davinci0"}]
   if change=="source":raw["helper_sha256"]="0"*64
   if change=="live":raw["terminal_state_before_cleanup"]["Running"]=True
   if change=="clock":raw["host_clock"]["perf_counter"]["implementation"]="CLOCK_REALTIME"
   if change=="namespace":raw["host_time_namespace"]="time:[2]"
   with self.subTest(change=change),self.assertRaises(ValueError):self.proof(raw)
 def samples(self):
  return [{"r45_clock":{"host_time_namespace":"time:[1]","host_clock":{"clock":"source"},"process_time_namespaces":{str(100+i):"time:[1]"for i in range(4)}},
   "owners":[{"owned":True,"pid":100+i,"nspid":[100+i,31+i]}for i in range(4)]}]
 def test_four_actual_worker_clock_bindings(self):
  raw={"host_time_namespace":"time:[1]","host_clock":{"clock":"source"}}
  with patch.object(p,"clock_proof",return_value=raw):
   d=a.audit_clock(self.samples(),dict(enumerate(range(31,35))),{})
   self.assertTrue(d["clock_binding_valid"])
   samples=self.samples();samples[0]["owners"].pop()
   with self.assertRaises(ValueError):a.audit_clock(samples,dict(enumerate(range(31,35))),{})
   samples=self.samples();samples[0]["r45_clock"]["process_time_namespaces"]["100"]="time:[2]"
   with self.assertRaises(ValueError):a.audit_clock(samples,dict(enumerate(range(31,35))),{})
if __name__=="__main__":unittest.main()
