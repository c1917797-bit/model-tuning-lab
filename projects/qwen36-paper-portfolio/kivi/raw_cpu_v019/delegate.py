"""Explicit source-qualified017 whole delegate. No copied numeric body."""
import hashlib,importlib.util,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE_CORE_SHA="f695b5caadb3bb2ed58acb97449254509a5a98273c679e1c7b79ffcb0dfd8ddc"
def initialize(base_root):
 global _base
 p=Path(base_root)/"consume_whole.py";b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=BASE_CORE_SHA:raise ValueError("frozen017 whole core identity")
 # The actual base source is compiled unchanged. __file__ names this explicit
 # source adapter so original literal raw CLI/MF binding points to this new leaf.
 ns=dict(__name__=__name__,__file__=str(HERE/"delegate.py"))
 exec(compile(b,str(p),"exec"),ns)
 globals().update({k:v for k,v in ns.items()if not k.startswith("__")})
 _base=Path(base_root)
def cpu_context(ctx,raw_owned,meta):
 import cpu_raw_resources as j
 cid=raw_owned["cid"];old_cleanup=ctx.cleanup;old_observation=ctx.observation
 ctx._joint_base_whole=_base
 ctx._joint_peer_plan=obj(meta["joint_peer_plan"])
 ctx._joint_reviewed_profile=obj(ref(HERE/"SOURCE_MANIFEST.json"))["reviewed_peer_profile"]
 need(raw_owned["arm"]=="cpu-preflight"and meta["cpu_only_raw_resource_source"]==ref(HERE/"cpu_raw_resources.py"),
  "new raw helper actual source")
 def cleanup(r,owned,host_pid):
  if owned["cid"]!=cid:return old_cleanup(r,owned,host_pid)
  return j.consume_cleanup(ctx,r,owned,host_pid)
 def observation(r,owned,host_pid,whole_root,initial=False):
  if owned["cid"]!=cid:return old_observation(r,owned,host_pid,whole_root,initial)
  return j.consume_observation(ctx,r,owned,host_pid,whole_root,initial)
 ctx.cleanup=cleanup;ctx.observation=observation
 return ctx
