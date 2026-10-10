"""Real source and filesystem seam tests. No numerical/model/device authority.
Scheduler methods are source-projected, NOT installed pydantic/native execution.
"""
import ast,hashlib,importlib.util,json,os,sys,tempfile,time,types,unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SCHEDULER_ARCHIVE=None
SCHEDULER_SHA="36bdfcf50a8f30d9f1c0dbdd3630a0075234f5c9e1a77943a934c45329f25c86"
def load(name):
 p=HERE/(name+".py");s=importlib.util.spec_from_file_location("_mixed_ref3_test_"+name,p)
 m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
class Owner(unittest.TestCase):
 def creator(self,root,selected_kind="ref2",bad=None):
  c=load("model_contract");l=load("loader");whole=load("release_core")
  fn=next(x for x in ast.parse((HERE/"host_run.py").read_bytes()).body if isinstance(x,ast.FunctionDef)and x.name=="owner_precondition")
  env=dict(c=c,Path=Path,time=time);exec(compile(ast.Module(body=[fn],type_ignores=[]),str(HERE/"host_run.py"),"exec"),env)
  stack=ExitStack();self.addCleanup(stack.close)
  if os.name=="nt":
   sentinel=-90217
   view=types.SimpleNamespace(O_RDONLY=os.O_RDONLY,O_DIRECTORY=getattr(os,"O_DIRECTORY",0),
    open=lambda p,f:sentinel if Path(p).is_dir()else os.open(p,f),
    fsync=lambda fd:None if fd==sentinel else os.fsync(fd),
    close=lambda fd:None if fd==sentinel else os.close(fd),link=os.link)
   stack.enter_context(patch.object(c,"os",view))
  safety=types.ModuleType("safety_host")
  # The original pure mapping, not a guessed or broadened hardware map.
  mapfn=next(x for x in ast.parse((HERE/"safety_host.py").read_bytes()).body if isinstance(x,ast.FunctionDef)and x.name=="device_map")
  safety_tree=ast.parse((HERE/"safety_host.py").read_bytes())
  physical=next(n for n in safety_tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=="PHYSICAL"for t in n.targets))
  envs={};exec(compile(ast.Module(body=[physical,mapfn],type_ignores=[]),"actual-pure-device-map","exec"),envs)
  safety.device_map=envs["device_map"];stack.enter_context(patch.dict(sys.modules,{"safety_host":safety}))
  refs=dict(source=c.write(root/"SOURCE.json",dict(schema="software-fixture-not-authority")))
  inspection=c.write(root/"inspect.json",dict(exit_code=0,stdout=json.dumps([dict(Id="a"*64)])))
  selected=dict(inspection if selected_kind=="ref3"else {k:inspection[k]for k in("path","sha256")})
  if bad:selected.update(bad)
  pre=c.write(root/"RESOURCE.json",dict(fixture_only=True))
  cpu=dict(report=c.write(root/"CPU.json",dict(fixture_only=True)))
  n1=c.write(root/"N1.json",dict(fixture_only=True));calls=[]
  def inspect():calls.append(dict(selected));return dict(Id="a"*64),dict(selected)
  ctl=types.SimpleNamespace(out=root,cid="a"*64,inspect=inspect,created_monotonic=10.0,deadline=5410.0,remaining=lambda cap:5300.0)
  return c,l,whole,env["owner_precondition"],ctl,refs,pre,cpu,n1,inspection,calls
 def actual(self,root,**kwargs):
  c,l,w,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(root,**kwargs)
  rr=creator(ctl,refs,pre,cpu,n1);return c,l,w,rr,l.obj(rr),inspection,calls
 def test_actual_creator_to_strict_loader_and_independent_reader(self):
  with tempfile.TemporaryDirectory(prefix="mixed-owner3-")as t:
   c,l,w,rr,value,inspection,calls=self.actual(Path(t))
   self.assertEqual(value["schema"],"kivi.mixed.actual-owned-precondition/v2")
   self.assertEqual(w.obj(rr),value);self.assertEqual(len(calls),2)
   self.assertTrue(all(set(r)=={"path","sha256"}for r in calls))
   self.assertEqual(value["owned_inspect_ref"],inspection)
   for n in("owned_inspect_ref","resource_ref","mapping_ref","clock_ref","canary_ref","cpu_ref"):
    self.assertEqual(set(value[n]),{"path","bytes","sha256"});self.assertEqual(l.obj(value[n]),w.obj(value[n]))
   mapping=l.obj(value["mapping_ref"]);self.assertEqual(mapping["inspect"],inspection);l.obj(mapping["inspect"])
   self.assertEqual(value["portfolio_cutoff"],1791788425);self.assertEqual(value["phase_seconds_including_cleanup"],5400)
   self.assertFalse(value["model_ready"]);self.assertFalse(value["performance_ready"])
 def test_actual_unchanged_loader_rejects_original_Ref2(self):
  with tempfile.TemporaryDirectory(prefix="mixed-ref2-")as t:
   c,l,w,creator,ctl,refs,pre,cpu,n1,inspection,calls=self.creator(Path(t))
   with self.assertRaisesRegex(ValueError,"exact bounded3Ref"):l.obj(ctl.inspect()[1])
   self.assertEqual(c.checked(ctl.inspect()[1]),inspection)
 def test_actual_bad_SHA_cannot_publish_owner(self):
  with tempfile.TemporaryDirectory(prefix="mixed-bad-sha-")as t:
   root=Path(t);c,l,w,f,ctl,refs,pre,cpu,n1,_,_=self.creator(root,bad=dict(sha256="0"*64))
   with self.assertRaisesRegex(ValueError,"actual complete SHA"):f(ctl,refs,pre,cpu,n1)
   self.assertFalse((root/"OWNER_PRECONDITION.json").exists())
 def test_actual_bad_size_bool_or_extra_key_rejected(self):
  for bad in(dict(bytes=True),dict(bytes=1),dict(origin="unknown")):
   with tempfile.TemporaryDirectory(prefix="mixed-bad-ref-")as t:
    root=Path(t);c,l,w,f,ctl,refs,pre,cpu,n1,_,_=self.creator(root,bad=bad)
    with self.assertRaises(ValueError):f(ctl,refs,pre,cpu,n1)
    self.assertFalse((root/"OWNER_PRECONDITION.json").exists())
 def test_missing_original_never_invents_bytes(self):
  with tempfile.TemporaryDirectory(prefix="mixed-no-inspect-")as t:
   root=Path(t);c,l,w,f,ctl,refs,pre,cpu,n1,inspection,_=self.creator(root)
   Path(inspection["path"]).unlink()
   with self.assertRaisesRegex(ValueError,"actual regular file"):f(ctl,refs,pre,cpu,n1)
   self.assertFalse((root/"OWNER_PRECONDITION.json").exists())
 def test_postpublication_mutation_rejected_by_both_readers(self):
  with tempfile.TemporaryDirectory(prefix="mixed-mutated-")as t:
   c,l,w,rr,value,inspection,calls=self.actual(Path(t))
   with Path(inspection["path"]).open("ab")as f:f.write(b" ")
   for reader in(l.obj,w.obj):
    with self.assertRaises(ValueError):reader(value["owned_inspect_ref"])
 def test_original_Ref3_preserved(self):
  with tempfile.TemporaryDirectory(prefix="mixed-existing-")as t:
   c,l,w,rr,value,inspection,calls=self.actual(Path(t),selected_kind="ref3")
   self.assertEqual(value["owned_inspect_ref"],inspection)
   self.assertEqual(l.obj(value["mapping_ref"])["inspect"],inspection)
 def test_two_checked_calls_and_strict_consumers_byte_unchanged(self):
  tree=ast.parse((HERE/"host_run.py").read_bytes())
  fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef)and x.name=="owner_precondition")
  calls=[x for x in ast.walk(fn)if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and x.func.attr=="checked"]
  self.assertEqual(len(calls),2)
  for call in calls:self.assertEqual(ast.dump(call.args[0]),ast.dump(ast.parse("ctl.inspect()[1]",mode="eval").body))
  pins={"model_contract.py":"144d33cc3dfa47084496f058fb81d5649a1251c5e87b6df8897b5fdf77ad8722",
   "prerequisite.py":"a91f82094f3b9270b01af87da983e6ccfe2f8bc391aef9e9b129504309fdfc3e",
   "release_core.py":"a5d27c8945e21c88f5ba82e5b6f1f8c05c7252b68b7ea237b67d7aef7cae31e1"}
  for name,h in pins.items():
   data=(HERE/name).read_bytes()
   self.assertEqual(hashlib.sha256(data).hexdigest(),h)
  # Provider and source roles deliberately change. The actual strict Ref,
  # namespace/source guards and atomic publisher keep their complete006 AST.
  strict={"checked":"856826223abf93b4af14af3be517d6dcc180ba6a7f15bee2f7b606cfc8bc43bd",
   "obj":"e6a843d3e4afc29a030f8571aa70e4956e140d8a22a041bc62b149c0ecd9fdbb",
   "module":"90468cce936b035b71eb51df1714c120210f2f3eed755a29cd504d3391c79347",
   "source":"d1c5a67229637db14dc08d8da09c6b0b556491fa8981c87f1d9d466530b4978e",
   "publish":"4eb9109229c82b45baceb066b29235181b0e1f0a2ed8cfd9c466b13fc4631a4e"}
  for n in ast.parse((HERE/"loader.py").read_bytes()).body:
   if isinstance(n,ast.FunctionDef)and n.name in strict:
    self.assertEqual(hashlib.sha256(ast.dump(n,include_attributes=False).encode()).hexdigest(),strict[n.name])
class ActualSchedulerSource(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(SCHEDULER_ARCHIVE,"explicit original SchedulerConfig source required")
  b=Path(SCHEDULER_ARCHIVE).read_bytes()
  if hashlib.sha256(b).hexdigest()!=SCHEDULER_SHA and b.endswith(b"\n"):b=b[:-1]
  self.assertEqual(hashlib.sha256(b).hexdigest(),SCHEDULER_SHA)
  self.cls=next(x for x in ast.parse(b).body if isinstance(x,ast.ClassDef)and x.name=="SchedulerConfig")
  self.m=load("native_config_adapter")
  self.args=types.SimpleNamespace(**self.m.POLICY,max_num_partial_prefills=1,max_long_partial_prefills=1,
   long_prefill_token_threshold=0,scheduler_reserve_full_isl=True)
 def construct(self,**values):
  known={n.target.id for n in self.cls.body if isinstance(n,ast.AnnAssign)}
  required={n.target.id for n in self.cls.body if isinstance(n,ast.AnnAssign)and n.value is None
   and isinstance(n.annotation,ast.Subscript)and isinstance(n.annotation.value,ast.Name)and n.annotation.value.id=="InitVar"}
  self.assertEqual(required,{"max_model_len","is_encoder_decoder"})
  self.assertTrue(required<=set(values));self.assertTrue(set(values)<=known)
  obj=types.SimpleNamespace(**values,max_num_scheduled_tokens=None)
  functions=[n for n in self.cls.body if isinstance(n,ast.FunctionDef)and n.name in("__post_init__","verify_max_model_len")]
  env=dict(Self=object,logger=types.SimpleNamespace(info=lambda *a:None,info_once=lambda *a:None,warning=lambda *a:None))
  exec(compile(ast.Module(body=functions,type_ignores=[]),"actual-installed-SchedulerConfig-methods","exec"),env)
  obj.verify_max_model_len=types.MethodType(env["verify_max_model_len"],obj)
  env["__post_init__"](obj,values["max_model_len"],values["is_encoder_decoder"]);return obj
 def test_mixed_kwargs_bind_both_actual_required_InitVars(self):
  observed=[]
  def ctor(**kw):observed.append(kw);return self.construct(**kw)
  value=self.m.scheduler_necessary(self.args,ctor)
  self.assertIs(observed[0]["is_encoder_decoder"],False);self.assertEqual(observed[0]["max_model_len"],33792)
  self.assertEqual(value["max_num_batched_tokens"],40960);self.assertEqual(value["max_num_seqs"],16)
 def test_actual_encoder_branch_cannot_masquerade_as_mixed_policy(self):
  def ctor(**kw):kw["is_encoder_decoder"]=True;return self.construct(**kw)
  with self.assertRaisesRegex(ValueError,"B16/40960"):self.m.scheduler_necessary(self.args,ctor)
 def test_actual_native_validation_rejects_partial_count_drift(self):
  self.args.max_long_partial_prefills=2
  with self.assertRaisesRegex(ValueError,"must be less than or equal"):self.m.scheduler_necessary(self.args,self.construct)
if __name__=="__main__":
 if len(sys.argv)!=2:raise SystemExit("exact SchedulerConfig archive path required")
 SCHEDULER_ARCHIVE=Path(sys.argv[1]);sys.argv=sys.argv[:1];unittest.main(verbosity=2)
