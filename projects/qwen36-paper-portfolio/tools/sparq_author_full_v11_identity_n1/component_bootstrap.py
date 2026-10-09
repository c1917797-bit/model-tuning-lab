"""v12 component namespace bootstrap. Stdlib/read-only; no framework or devices.
Initialize the frozen shard/native owners in their original consumer order.
Never delete/rebind cached modules, patch original sources, or accept saved PASS.
"""
import argparse,importlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
NATIVE_NAMES=("contract","receipt","preflight","host","ann_matrix_consumer","cpu_smoke",
 "literal_author","independent_oracle","precision_oracle","matrix","ann_workspace","consume_numeric","numeric_gate")
def expected(c):
 native=c.obj(dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA))
 own=c.obj(dict(path=str(c.ROOT/"SOURCE_MANIFEST.json"),sha256=c.sha(c.ROOT/"SOURCE_MANIFEST.json")))
 out={}
 for name in NATIVE_NAMES:
  out[name]=[(c.KERNEL/(name+".py"),native["files"][name+".py"])]
 for file,digest in native["files"].items():
  if file.startswith("sparq_token_v4/") and file.endswith(".py"):
   name=file[:-3].replace("/",".")
   if name.endswith(".__init__"):name=name[:-9]
   out[name]=[(c.KERNEL/file,digest)]
 for name,digest in c.SHARD_FILES.items():
  if name.endswith(".py"):out[name[:-3]]=[(c.SHARD_ROOT/name,digest)]
 # Both actual owners carry IDENTICAL original whole-envelope reader bytes.
 digest=native["files"]["original_terminal.py"]
 c.require(own["files"]["original_terminal.py"]==digest,"full/native whole reader bytes differ")
 out["original_terminal"]=[(c.KERNEL/"original_terminal.py",digest),(c.ROOT/"original_terminal.py",digest)]
 return out
def verify_cached(c,wants=None):
 wants=expected(c) if wants is None else wants;seen={}
 for name,choices in wants.items():
  mod=sys.modules.get(name)
  if mod is None:continue
  raw=getattr(mod,"__file__",None)
  c.require(type(raw) is str,"cached module has no exact source: "+name)
  path=Path(raw)
  c.require(path.is_absolute() and path.resolve()==path and not path.is_symlink() and
   any(path==p and c.sha(path)==digest for p,digest in choices),
   "foreign cached component namespace: "+name)
  seen[name]=dict(path=str(path),sha256=c.sha(path))
 return seen
def dependencies(c):
 """Exact sc.native() bootstrap BEFORE shard_rows' flat contract import."""
 c.require(c.ROOT==ROOT,"helper belongs to actual full source owner")
 wants=expected(c);verify_cached(c,wants)
 # Root order is local to source_contract.component's finally-restored scope.
 sys.path.insert(0,str(c.KERNEL));sys.path.insert(0,str(c.SHARD_ROOT))
 shard=importlib.import_module("shard_contract");verify_cached(c,wants)
 c.require(Path(shard.__file__).resolve()==c.SHARD_ROOT/"shard_contract.py","actual shard owner")
 own,_=shard.own_identity(c.SHARD_SOURCE["path"],c.SHARD_SOURCE["sha256"])
 native,source,files=shard.native()
 c.require(own==c.SHARD_SOURCE and source==dict(path=str(c.KERNEL/"SOURCE_MANIFEST.json"),sha256=c.KERNEL_SHA) and
  files==c.obj(source)["files"] and Path(native.__file__).resolve()==c.KERNEL/"receipt.py",
  "actual original shard/native full-source bootstrap")
 for name in ("shard_contract","shard_rows","shard_proof","shard_host"):
  mod=importlib.import_module(name);verify_cached(c,wants)
  c.require(Path(mod.__file__).resolve()==c.SHARD_ROOT/(name+".py") and c.sha(mod.__file__)==c.SHARD_FILES[name+".py"],
   "exact frozen shard dependency: "+name)
 return verify_cached(c,wants)
def summary(c,source,component,checked):
 c.require(checked["cases"]==128 and checked["changing_feedback_steps"]==20480 and checked["shards"]==4 and
  checked["consumer_source"]==c.COMPONENT_READER_SOURCE and checked["derived_consumer_sha256"]==c.COMPONENT_READER_DERIVED_SHA and
  checked["original_producer_source"]==c.SHARD_SOURCE and checked["npu_rerun"] is False,
  "real original whole128 replay, not cached PASS")
 return dict(schema="sparq.component-bootstrap-observation/v1",source=source,component=component,
  consumer_source=c.COMPONENT_READER_SOURCE,original_producer_source=c.SHARD_SOURCE,
  derived_consumer_sha256=c.COMPONENT_READER_DERIVED_SHA,cases=128,changing_feedback_steps=20480,shards=4,
  actual_component_replayed=True,npu_rerun=False,model_executed=False,namespace=verify_cached(c))
def verify_probe(c,probe,source,component):
 p=probe["component_bootstrap"]
 c.require(p["schema"]=="sparq.component-bootstrap-observation/v1" and p["source"]==source and p["component"]==component and
  p["consumer_source"]==c.COMPONENT_READER_SOURCE and p["original_producer_source"]==c.SHARD_SOURCE and
  p["derived_consumer_sha256"]==c.COMPONENT_READER_DERIVED_SHA and p["cases"]==128 and
  p["changing_feedback_steps"]==20480 and p["shards"]==4 and p["actual_component_replayed"] is True and
  p["npu_rerun"] is False and p["model_executed"] is False,"actual same-image component namespace/source replay")
 wants=expected(c)
 for name,r in p["namespace"].items():
  c.require(name in wants and any(r==dict(path=str(path),sha256=digest) for path,digest in wants[name]),
   "recorded component module source: "+name)
 c.require({"contract","receipt","preflight","host","shard_contract","shard_rows","shard_proof","shard_host"}<=set(p["namespace"]),
  "complete actually loaded consumer owners")
 return True
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--component");p.add_argument("--component-sha256")
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(status="disabled",ready=False,npu_executed=False)));return
 before=list(sys.path)
 try:
  sys.path.insert(0,str(ROOT));c=importlib.import_module("source_contract")
  source,_=c.source(str(ROOT/"SOURCE_MANIFEST.json"),a.source_manifest_sha256)
  component=c.bound(a.component,a.component_sha256);checked=c.component(component,replay=True)
  result=summary(c,source,component,checked)
  c.require(not any(n=="torch" or n.startswith(("torch.","torch_npu","vllm")) for n in sys.modules),
   "component replay must not import hardware framework")
  print("SPARQ_COMPONENT_BOOTSTRAP "+json.dumps(result,sort_keys=True),flush=True)
 finally:sys.path[:]=before
if __name__=="__main__":main()
