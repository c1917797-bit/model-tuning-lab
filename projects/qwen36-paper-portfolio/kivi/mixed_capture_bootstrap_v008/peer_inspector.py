"""Source-qualified pure exact peer inspect; no commands, no global policy edit."""
import ast,re
from pathlib import Path
from types import SimpleNamespace
def validate_peer_inspect(x,owned,lease,read):
 m=read(lease["source_ref"])
 if m["schema"]!="kivi.actual-mixed-capture-bootstrap-sources/v2":raise ValueError("explicit mixed peer source")
 own={Path(r["path"]).name:r for r in m["files"]}
 import hashlib
 row=own["safety_host.py"];wire=Path(row["path"]).read_bytes()
 if len(wire)!=row["bytes"]or hashlib.sha256(wire).hexdigest()!=row["sha256"]:raise ValueError("peer source drift")
 tree=ast.parse(wire);wanted=("device_map","environment","labels","validate_inspect")
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in wanted]
 literal={}
 for node in tree.body:
  if isinstance(node,ast.Assign):
   for target in node.targets:
    if isinstance(target,ast.Name)and target.id in("OWNER","PHYSICAL"):literal[target.id]=ast.literal_eval(node.value)
 if len(nodes)!=4 or literal["PHYSICAL"]!=(4,5,6,7):raise ValueError("actual peer inspect source shape")
 def need(v,msg):
  if not v:raise ValueError(msg)
 c=SimpleNamespace(require=need,GIB=1024**3,IMAGE="sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1",
  ROOT=Path("/opt/host/vnf/austinov/model-tuning-lab"))
 ns=dict(c=c,re=re,Path=Path,MEM=64*1024**3,**literal)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),row["path"],"exec"),ns)
 ns["validate_inspect"](x,owned)
