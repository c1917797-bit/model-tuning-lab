"""Original-file admission seam regression only; no device/model/PASS authority."""
import ast,copy,hashlib,importlib.util,json,re,tempfile,types,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=None
def load(name):
 spec=importlib.util.spec_from_file_location("_capture_admission_"+name,HERE/(name+".py"))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
def require(value,message):
 if not value:raise ValueError(message)
class TerminalFiles(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(prefix="mixed007-terminal-")
  self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.core=load("release_core");self.reader=load("consume_whole_cpu")
  self.source=self.write("source",dict(fixture_not_authority=True))
  self.inner=["/usr/bin/python3","-I","-B",str(self.root/"host_run.py"),"--execute",
   "--source",self.source["path"],"--source-sha256",self.source["sha256"],"--phase","capture"]
 def write(self,name,value):
  path=self.root/(name+".json");path.write_bytes((json.dumps(value,sort_keys=True)+"\n").encode())
  return self.core.ref(path)
 def documents(self,change=None,outer=None):
  result=dict(source=self.source,status="fixture_not_authority",elapsed_seconds=1,actual_host_argv=self.inner)
  rr=self.write("result",result);argv=outer or self.inner
  rec=dict(id="exec-0123456789abcdef",state="completed",exitCode=0,cancelled=False,timedOut=False,error=None,
   command=argv[0],args=argv[1:],cwd=None,durationMs=1000,stdout=json.dumps(dict(result=rr,status=result["status"]))+"\n",stderr="")
  if change:change(rec,result)
  # Preserve caller mutation of the result, including changed source/argv.
  Path(rr["path"]).write_bytes((json.dumps(result,sort_keys=True)+"\n").encode())
  rr=self.core.ref(rr["path"])
  if not(change and rec.get("duplicate_marker")):
   rec["stdout"]=json.dumps(dict(result=rr,status=result["status"]))+"\n"
  tr=self.write("terminal",dict(operationId=rec["id"],operation=dict(targetPeerId="peer",
   routeDecision="peer_direct",result=dict(record=rec))))
  return rr,tr,rec
 def consume(self,parts):
  rr,tr,rec=parts
  return self.reader.terminal(self.core,rr,tr,"peer",rec["id"],rec["command"],rec["args"],5400)
 def test_01_exact_absolute_null_cwd_actual_files(self):
  parts=self.documents();self.assertEqual(self.consume(parts)[0],self.core.obj(parts[0]))
 def test_02_original_reader_null_failure_preserved(self):
  _,_,rec=self.documents()
  with self.assertRaises(ValueError):self.core.exact_command(rec,rec["command"],rec["args"],5400)
 def test_03_exact_taskset_outer_no_shell(self):
  parts=self.documents(outer=["/usr/bin/taskset","-c","2,3"]+self.inner)
  self.assertEqual(self.consume(parts)[1]["command"],"/usr/bin/taskset")
 def test_04_relative_or_foreign_script_rejected(self):
  for script in("host_run.py",str(self.root/"other.py")):
   with self.subTest(script=script):
    self.inner[3]=script
    with self.assertRaises(ValueError):self.consume(self.documents())
 def test_05_changed_source_directory_rejected(self):
  with self.assertRaises(ValueError):
   self.consume(self.documents(lambda rec,row:row.update(source=dict(self.source,path=str(self.root/"other"/"SOURCE_MANIFEST.json")))))
 def test_06_foreign_nonnull_cwd_rejected(self):
  with self.assertRaises(ValueError):self.consume(self.documents(lambda rec,row:rec.update(cwd="/foreign")))
 def test_07_shell_or_bad_cpuset_rejected(self):
  for prefix in(["/bin/sh","-c"],["/usr/bin/taskset","-c","2;3"]):
   with self.subTest(prefix=prefix):
    with self.assertRaises(ValueError):self.consume(self.documents(outer=prefix+self.inner))
 def test_08_failed_or_truncated_original_rejected(self):
  for bad in(dict(exitCode=1),dict(stdoutTruncated=True),dict(timedOut=True)):
   with self.subTest(bad=bad):
    with self.assertRaises(ValueError):self.consume(self.documents(lambda rec,row:rec.update(bad)))
 def test_09_budget_nan_boolean_overrun_rejected(self):
  for value in(float("nan"),True,5400001):
   with self.subTest(value=value):
    with self.assertRaises(ValueError):self.consume(self.documents(lambda rec,row:rec.update(durationMs=value)))
 def test_10_terminal_ref_byte_mutation_rejected(self):
  parts=self.documents()
  with Path(parts[1]["path"]).open("ab")as output:output.write(b" ")
  with self.assertRaises(ValueError):self.consume(parts)
class CanonicalMounts(unittest.TestCase):
 def pure(self,path):
  names={"create_argv","device_map","environment","labels"}
  nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name in names]
  ns=dict(c=types.SimpleNamespace(GIB=1024**3,ROOT=Path("/source"),IMAGE="sha256:fixture",require=require),
   DOCKER="/usr/bin/docker",MEM=64*1024**3,PHYSICAL=(4,5,6,7),OWNER="fixture")
  exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),"exec"),ns);return ns
 def owner(self):
  return dict(arm="candidate",name="fixture",guest_cpus=[1,2,3,4],source=dict(sha256="a"*64),host_sha256="b"*64,
   mounts={"/z-output":["/z-output",True],"/a-source":["/a-source",False],"/m-input":["/m-input",False]})
 def test_11_actual_create_survives_canonical_JSON_roundtrip(self):
  ns=self.pure(HERE/"safety_host.py");e=self.owner()
  self.assertEqual(ns["create_argv"](e),ns["create_argv"](json.loads(json.dumps(e,sort_keys=True))))
 def test_12_only_mount_order_changes_from_original_function(self):
  self.assertIsNotNone(BASE)
  new=self.pure(HERE/"safety_host.py")
  old_fn=next(n for n in ast.parse((BASE/"safety_host.py").read_bytes()).body if isinstance(n,ast.FunctionDef)and n.name=="create_argv")
  old=dict(new);exec(compile(ast.Module(body=[old_fn],type_ignores=[]),"original-create-body","exec"),old)
  e=self.owner();e["mounts"]=dict(sorted(e["mounts"].items()))
  self.assertEqual(new["create_argv"](e),old["create_argv"](e))
  e=self.owner();self.assertNotEqual(new["create_argv"](e),old["create_argv"](e))
 def test_13_source_or_RW_drift_changes_strict_replayed_argv(self):
  ns=self.pure(HERE/"safety_host.py");e=self.owner();original=ns["create_argv"](e)
  for value in(["/other",False],["/a-source",True]):
   changed=copy.deepcopy(e);changed["mounts"]["/a-source"]=value
   self.assertNotEqual(original,ns["create_argv"](changed))
class SourceEdges(unittest.TestCase):
 def test_17_reused_software_branch_calls_only_CPU_create(self):
  tree=ast.parse((HERE/"software_host.py").read_bytes())
  fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=="software_only")
  creates=[n for n in ast.walk(fn)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and n.func.attr=="create"]
  self.assertEqual(len(creates),1);self.assertEqual(ast.literal_eval(creates[0].args[-1]),"cpu-preflight")
  literals=[n.value for n in ast.walk(fn)if isinstance(n,ast.Constant)]
  self.assertNotIn("candidate",literals);self.assertNotIn("n1",literals)
  self.assertIn(240,literals);self.assertIn(150,literals)
 def test_18_software_controller_and_consumer_reused_complete_bodies(self):
  expected={"software_only":"47f15100f17c39347ef93b8a6870b9b91e5e50ba9d5a58a5f34f8565aedb6575",
   "consume_software_stage":"72124d0e8b40be2ff796fcb013cebe381251eb2124c0e83c7fe95088cd664321"}
  functions={n.name:n for n in ast.parse((HERE/"software_host.py").read_bytes()).body if isinstance(n,ast.FunctionDef)}
  for name,digest in expected.items():
   self.assertEqual(hashlib.sha256(ast.dump(functions[name],include_attributes=False).encode()).hexdigest(),digest)
 def test_14_old_raw_source_rejected_before_any_read(self):
  p=load("firstdecode_precondition")
  m=dict(firstdecode_producer_ref=p.PRODUCER,firstdecode_whole_source=p.WHOLE,
   firstdecode_raw_source=dict(p.RAW,sha256="0"*64),runtime_roles={})
  def forbidden(*args):raise AssertionError("must fail before source/evidence read")
  with self.assertRaisesRegex(ValueError,"exact currently reviewed"):
   p._replay(types.SimpleNamespace(require=require,obj=forbidden),m,{})
 def test_15_consumer_gate_pins_exact_complete_top_consumer(self):
  tree=ast.parse((HERE/"paired"/"mixed_gate.py").read_bytes()) if (HERE/"paired"/"mixed_gate.py").exists() else None
  digest=hashlib.sha256((HERE/"consume_whole_cpu.py").read_bytes()).hexdigest()
  self.assertEqual(digest,"3535642efbf50039f35cf65c5a61b36350e141b9c0ab0f9c7261a25aab3be243")
  if tree is not None:self.assertIn(digest,[n.value for n in ast.walk(tree)if isinstance(n,ast.Constant)])
 def test_16_actual_raw_delegate_not_old_direct_consume(self):
  tree=ast.parse((HERE/"firstdecode_precondition.py").read_bytes())
  calls=[n.func.attr for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)]
  self.assertTrue({"initialize","cpu_context","consume"}<=set(calls))
  source=(HERE/"firstdecode_precondition.py").read_text()
  self.assertIn('raw_wall_seconds==5400',source)
  self.assertIn('FA_frames"]==64',source)
  self.assertIn('actual_first_decode_length"]==32769',source)
if __name__=="__main__":unittest.main(verbosity=2)
