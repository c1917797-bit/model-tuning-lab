"""CPU-only synthetic/source regressions; never imports Torch/host controller."""
import ast,copy,hashlib,importlib.util,json,sys,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=Path(sys.argv[1]) if len(sys.argv)>1 else None
SCANNER=Path(sys.argv[2]) if len(sys.argv)>2 else None
def load(name):
 p=HERE/(name+".py");s=importlib.util.spec_from_file_location("_test_"+name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def methods(path):
 tree=ast.parse(path.read_bytes());cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=="Controller")
 return {n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
def need(v,m):
 if not v:raise ValueError(m)
class Handoff(unittest.TestCase):
 def setUp(self):
  self.log=[];self.result=None;self.inspect_queue=[]
  c=types.SimpleNamespace(require=need,write=self.write)
  ns=dict(c=c,DOCKER="/usr/bin/docker")
  fn=copy.deepcopy(methods(HERE/"safety_host.py")["cleanup_cpu_only"])
  exec(compile(ast.Module(body=[fn],type_ignores=[]),"fixture","exec"),ns)
  self.fn=ns["cleanup_cpu_only"]
 def write(self,path,value):self.result=value;return {"path":str(path),"bytes":1,"sha256":"a"*64}
 def owner(self,*,arm="cpu-preflight",devices=None,oom=False,running=False,execs=None):
  test=self
  class Owner:
   cid="a"*64;expected={"arm":arm};primary=None;out=Path("/cache/cch/owned/cpu-numeric")
   secondary=[];server=None;client=None
   def inspect(self,cleanup=False):
    test.log.append(("inspect",self.cid))
    return dict(HostConfig={"Devices":[] if devices is None else devices},
     State={"Running":running,"Pid":1 if running else 0,"OOMKilled":oom},ExecIDs=execs),{"ref":"actual"}
   def call(self,label,argv,**kwargs):
    test.log.append((label,argv));return {},{"ref":"stop"}
   def remaining(self,**kwargs):return 10
  return Owner()
 def test_legal_new_npu_job_irrelevant(self):
  owner=self.owner();owner.foreign_NPU_CID="b"*64
  self.fn(owner)
  self.assertTrue(self.result["stopped"]);self.assertFalse(self.result["npu_release_claim"])
  self.assertEqual([r[0]for r in self.log],["inspect","stop-retain","inspect"])
 def test_stops_only_exact_cpu(self):
  self.fn(self.owner())
  self.assertEqual(self.log[1][1],["/usr/bin/docker","stop","--time","15","a"*64])
 def test_candidate_forbidden(self):
  self.fn(self.owner(arm="candidate"));self.assertTrue(self.result["errors"]);self.assertEqual(self.log,[])
 def test_devices_forbidden(self):
  self.fn(self.owner(devices=[{"PathOnHost":"/dev/davinci4"}]));self.assertTrue(self.result["errors"])
  self.assertNotIn("stop-retain",[v[0]for v in self.log])
 def test_oom_retains_failure(self):
  self.fn(self.owner(oom=True));self.assertTrue(self.result["errors"]);self.assertFalse(self.result["stopped"])
 def test_live_after_stop_rejected(self):
  self.fn(self.owner(running=True));self.assertTrue(self.result["errors"])
 def test_execs_rejected(self):
  self.fn(self.owner(execs=["foreign"]));self.assertTrue(self.result["errors"])
 def test_no_delete(self):
  self.fn(self.owner());self.assertFalse(self.result["deleted"]);self.assertTrue(self.result["retained"])
class Peer(unittest.TestCase):
 def setUp(self):
  self.m=load("peer_lease")
  self.host=dict(effective_cpus=list(range(12)),effective_capacity=12,quota_ancestors=[dict(key="root",capacity=12)])
  self.daemon=copy.deepcopy(self.host)
  self.peer=dict(host=dict(effective_cpus=[0],effective_capacity=1,quota_ancestors=[dict(key="root",capacity=12)]),
   guest=dict(effective_cpus=[1],effective_capacity=1,quota_ancestors=[dict(key="root",capacity=12)]),owned_cid="b"*64)
 def test_distinct9(self):
  x=self.m.choose_allocation(self.host,self.daemon,self.peer)
  self.assertEqual(x["host_cpu"],2);self.assertEqual(x["guest_cpus"],[3,4,5,6])
  self.assertEqual(x["reserve_cpus"],[7,8]);self.assertEqual(x["joint_CPU_budget"],9)
 def test_shared8_rejected(self):
  self.host["quota_ancestors"][0]["capacity"]=8
  with self.assertRaises(ValueError):self.m.choose_allocation(self.host,self.daemon,self.peer)
 def test_peer_overlap_host_rejected(self):
  self.host["effective_cpus"]=[0,1]
  with self.assertRaises(ValueError):self.m.choose_allocation(self.host,self.daemon,self.peer)
 def test_too_few_cpuset_rejected(self):
  self.daemon["effective_cpus"]=list(range(8))
  with self.assertRaises(ValueError):self.m.choose_allocation(self.host,self.daemon,self.peer)
class Source(unittest.TestCase):
 def test_candidate_cleanup_original_body(self):
  a=methods(BASE/"safety_host.py")["cleanup"];b=copy.deepcopy(methods(HERE/"safety_host.py")["cleanup"])
  self.assertIsInstance(b.body[0],ast.If);b.body=b.body[1:]
  self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
 def test_candidate_observe_original_body(self):
  a=methods(BASE/"safety_host.py")["observe"];b=copy.deepcopy(methods(HERE/"safety_host.py")["observe"])
  b.body=b.body[1:];self.assertEqual(ast.dump(a,include_attributes=False),ast.dump(b,include_attributes=False))
 def test_candidate_mapping_inspect_unchanged(self):
  names=("device_map","labels","validate_inspect","actual_hbm")
  def f(path):
   return {n.name:ast.dump(n,include_attributes=False)for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name in names}
  self.assertEqual(f(BASE/"safety_host.py"),f(HERE/"safety_host.py"))
  # Only mount iteration becomes canonical; actual argv equivalence and
  # JSON-roundtrip replay are separately executed in test_capture_admission.
 def test_scanner_delta_exact(self):
  old=SCANNER.read_bytes()
  if hashlib.sha256(old).hexdigest()!="44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad":old=old[:-1]
  self.assertEqual(hashlib.sha256(old).hexdigest(),"44e5ccfdad173e6b9eebc025260e489893d672c316c6aac3f8bf68a5e03c16ad")
  changed=old.decode().replace("32*1024**3","160*1024**3").replace("32GiB","160GiB").replace("adakv.actual-output-budget-observation/v1","kivi.mixed-output-budget-observation/v2")
  self.assertEqual(changed,(HERE/"output_budget.py").read_text())
 def test_complete16_not_cpu_wait(self):
  text=(HERE/"client.py").read_text();self.assertIn("for stage in range(16):",text)
  self.assertNotIn("fast_oracle",text);self.assertNotIn("offline_consume",text)
 def test_cpu_release_before_create(self):
  text=(HERE/"cpu_phase.py").read_text()
  self.assertLess(text.index("stopped=ctx.cleanup"),text.index("ctl.create("))
  self.assertLess(text.index("core.raw_after_release"),text.index('child(ctl,"independent-all16"'))
 def test_CPU_new_inspect_order(self):
  text=(HERE/"cpu_phase.py").read_text()
  self.assertLess(text.index("ctl.create("),text.index("actual,inspect_ref=ctl.inspect()"))
 def test_no_hidden_background(self):
  for p in HERE.glob("*.py"):
   if p.name.startswith("test_"):continue
   text=p.read_text()
   self.assertNotIn("nohup",text);self.assertNotIn("docker rm",text)
 def test_engine_not_parser_only(self):
  self.assertIn("actual_engine_config=config",(HERE/"guest_probe.py").read_text())
  self.assertIn('check.actual(api,args,"n1"',(HERE/"server_entry.py").read_text())
 def test_source_vocab_before_create(self):
  text=(HERE/"host_run.py").read_text()
  self.assertLess(text.index("inputs=input_recipe("),text.index("ctl.create("))
 def test_no_hidden_resident_dense_and_explicit_compact_budget(self):
  text=(HERE/"runtime_owner.py").read_text()
  self.assertIn("new_device_allocation_bytes=0",text);self.assertIn("tokens>=33792",text)
  self.assertNotIn("tokens>=16*33792",text)
  self.assertIn('provider_state',text)
  provider=(HERE/"explicit_provider.py").read_text()
  self.assertIn("total_budget_bytes",provider)
  self.assertIn("native_raw_check",provider)
 def test_joint_retained_output_charged(self):
  text=(HERE/"model_contract.py").read_text()
  self.assertIn("used+retained<=160*GIB",text)
  self.assertIn("prior not in now.parents and now not in prior.parents",text)
 def test_loader_isolated_from_predecessor(self):
  text=(HERE/"model_contract.py").read_text()
  self.assertIn('"_kivi_mixed_source_loader"',text)
  self.assertNotIn('"_kivi_firstdecode_source_loader"',text)
 def test_inputs_and_output_budget_not_shape_fixture(self):
  text=(HERE/"client.py").read_text()
  self.assertLess(text.index("from_layouts("),text.index("for stage in range(16):"))
  self.assertIn('capacity["event_ref"]',text);self.assertNotIn("4224",text)
 def test_same_frozen_mixed_source_pins(self):
  asm=load("assemble");self.assertEqual(asm.CORE_PINS["installer"],"150b149762ce1b2cf43f29b13595ee66c7012382f180de9dce8463cb5a5b0ef9")
  self.assertEqual(asm.CORE_PINS["worker"],"bfd9cd5ef70be0bf6df07079aff25f6465aff24ee9359f20e434fff62552b943")
 def test_external_config_not_invented_pass(self):
  bridge=load("config_bridge")
  a=types.SimpleNamespace(**bridge.POLICY);m={"runtime_roles":{"native_config_adapter":{"path":"missing"}},"files":[],"dependencies":[]}
  with self.assertRaises(ValueError):bridge.actual(None,a,"cpu",None,m,types.SimpleNamespace(need=need))
class Budget(unittest.TestCase):
 def test_absolute_cutoff(self):
  b=load("budget")
  with self.assertRaises(ValueError):b.preregister(b.CUTOFF-48599)
  self.assertEqual(b.preregister(b.CUTOFF-48600)["total_reserved_seconds"],48600)
 def test_CPU_bound_does_not_extend(self):
  b=load("budget")
  self.assertEqual(b.require_fit(b.CUTOFF-43200,"cpu-numeric"),b.CUTOFF)
  with self.assertRaises(ValueError):b.require_fit(b.CUTOFF-43199,"cpu-numeric")
 def test_unmeasured_explicit(self):
  self.assertFalse(load("budget").preregister(1)["CPU_budget_is_measured_upper_bound"])
 def test_compile_all(self):
  for p in HERE.glob("*.py"):compile(p.read_bytes(),str(p),"exec")
if __name__=="__main__":
 sys.argv=sys.argv[:1];unittest.main(verbosity=2)
