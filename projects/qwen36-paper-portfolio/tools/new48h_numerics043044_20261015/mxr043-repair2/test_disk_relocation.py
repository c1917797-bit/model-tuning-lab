"""Execute source-derived disk predicates and actual donor adaptation, no devices."""
import ast,importlib.util,json,types,unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
D=Path("C:/Users/Huawei/AppData/Local/Temp/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py")
if not D.is_file():D=Path('/cache/cch/qwen36-paper-preparation-20261007/lowbit/mxr-r118-proc-snapshot-repair-20261013-008/host_ticket.py')
def need(v,m):
 if not v:raise ValueError(m)
class Tests(unittest.TestCase):
 def test_actual_adapt_output_and_inverse(self):
  s=importlib.util.spec_from_file_location("diskhost",P/"host_ticket.py");h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
  identity=dict(owner="mxr-working-domain-model043-repair2",run_id="mxr-working-domain-model043-repair2",container_prefix="mxr-working-domain-model043-repair2-")
  raw=json.dumps(dict(runtime_identity=identity)).encode()
  with patch.object(Path,"read_bytes",return_value=raw):text,pairs=h.adapt(D.read_text() if False else ORIGINAL,{}, {})
  tree=ast.parse(text);assign=next(n for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(x,ast.Name)and x.id=="OUT"for x in n.targets))
  ns=dict(Path=Path);exec(compile(ast.Module(body=[assign],type_ignores=[]),"actual-adapt","exec"),ns)
  self.assertEqual(str(ns["OUT"]).replace("\\","/"),"/opt/host/vnf/austinov/run-mxr-working-domain-model043-repair2-main-NEW48H_001")
  self.assertEqual(ns["OUT"],h.OUT)
  self.assertIn('_EXTERNAL.docker_gate(self, S, free, initial)',text)
  self.assertIn('not OUT.exists() and OUT.parent.is_dir() and not OUT.is_symlink()',text)
 def test_actual_two_filesystem_predicates(self):
  safety=ast.parse((P/"actual_loader/safety_host.py").read_bytes())
  controller=next(n for n in safety.body if isinstance(n,ast.ClassDef)and n.name=="Controller")
  method=next(n for n in controller.body if isinstance(n,ast.FunctionDef)and n.name=="resources")
  guard=next(n for n in method.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and any(isinstance(a,ast.Constant)and isinstance(a.value,str)and "whole packet32GiB"in a.value for a in n.value.args))
  donor=ast.parse(ORIGINAL);owned=next(n for n in ast.walk(donor)if isinstance(n,ast.ClassDef)and n.name=="Owned")
  rm=next(n for n in owned.body if isinstance(n,ast.FunctionDef)and n.name=="resources")
  docker=next(n for n in rm.body if isinstance(n,ast.Expr)and isinstance(n.value,ast.Call)and any(isinstance(a,ast.Constant)and a.value=="actual Docker root storage reserve"for a in n.value.args))
  def run(node,free):
   ns=dict(c=types.SimpleNamespace(require=need),need=need,free=free*2**30,RESERVE=8.5*2**30,WORKSPACE=32*2**30,used=4*2**30,initial=True,S=types.SimpleNamespace(RESERVE=8.5*2**30,WORKSPACE=32*2**30))
   exec(compile(ast.Module(body=[node],type_ignores=[]),"actual-resource-guard","exec"),ns)
  run(guard,232);run(docker,41)
  for node,free in((guard,40),(docker,16),(docker,40)):
   with self.assertRaises(ValueError):run(node,free)
ORIGINAL=D.read_bytes().decode()
if __name__=="__main__":unittest.main()
