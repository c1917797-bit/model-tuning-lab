"""Independent artifact audit; presence is not runtime cache-hit proof."""
import base64,json,re
from pathlib import Path,PurePosixPath
from independent_compilation_cache import inventory
def audit_groups(root,*,recorded_inventory=None):
 root=Path(root);actual=inventory(root)
 if recorded_inventory is not None and actual!=recorded_inventory:raise ValueError("compiled artifacts changed")
 rows=[]
 for group in sorted(root.rglob("__grp__*.json")):
  d=json.loads(group.read_text());paths=d.get("child_paths")
  if not isinstance(paths,dict) or not paths:raise ValueError("group child mapping missing")
  children={}
  for name,value in paths.items():
   q=PurePosixPath(value)
   if not isinstance(name,str) or PurePosixPath(name).name!=name or ".." in q.parts:
    raise ValueError("invalid child path")
   try:rel=q.relative_to("/compilation-cache")
   except ValueError:raise ValueError("child outside stable cache mount")
   p=root/str(rel)
   if p.parent!=group.parent or p.name!=name or not p.is_file() or p.is_symlink() or not p.stat().st_size:
    raise ValueError("missing/misbound compiled child")
   children[name]=p
  metadata_name=group.name[len("__grp__"):]
  if metadata_name not in children:raise ValueError("exact group metadata missing")
  metadata=json.loads(children[metadata_name].read_text())
  h=metadata.get("hash","")
  if not re.fullmatch("[0-9a-f]{64}",h):raise ValueError("compiled source key missing")
  key=base64.urlsafe_b64encode(bytes.fromhex(h)).decode().rstrip("=")
  if group.parent.name!=key:raise ValueError("compiled cache key mismatch")
  if metadata.get("target",{}).get("backend")!="npu" or metadata["target"].get("arch")!="Ascend910B4":
   raise ValueError("wrong compiler target")
  name=metadata.get("name")
  if not isinstance(name,str) or not name or metadata_name!=name+".json":raise ValueError("kernel name mismatch")
  if name+".npubin" not in children:raise ValueError("NPU binary missing")
  rows.append({"kernel":name,"key":h,"group":str(group.relative_to(root)),"target":metadata["target"],"binary_bytes":children[name+".npubin"].stat().st_size})
 if not rows:raise ValueError("no complete NPU compile groups")
 return {"compiled_artifacts_valid":True,"groups":rows,"inventory":actual,
  "scope":"complete source-key/target/binary artifact groups only; not runtime hit, source provenance, correctness or service performance"}
