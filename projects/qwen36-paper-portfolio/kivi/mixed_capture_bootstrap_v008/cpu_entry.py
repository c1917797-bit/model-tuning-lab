"""Actual separate CPU8 cgroup check before/after unchanged mixed002 consumer."""
import argparse,importlib.util,json,runpy,sys
from pathlib import Path
def main():
 p=argparse.ArgumentParser();p.add_argument("--execute",action="store_true")
 p.add_argument("--source-manifest-sha256");p.add_argument("--recipe");p.add_argument("--recipe-sha256");p.add_argument("--output-dir")
 a=p.parse_args()
 if not a.execute:print(json.dumps(dict(enabled=False,NPU=False)));return
 spec=importlib.util.spec_from_file_location("_mixed_cpu_source_loader",Path(__file__).parent/"loader.py")
 l=importlib.util.module_from_spec(spec);sys.modules[spec.name]=l;spec.loader.exec_module(l)
 m,source=l.source(a.source_manifest_sha256);memory=l.memory_module(m)
 # Original writer helper imports these exact scalar dependencies; no HAL path.
 l.geometry_modules(m)
 before=memory.memory(expected_limit=8*1024**3)
 l.need("torch"not in sys.modules and "torch_npu"not in sys.modules,"actual no-Torch independent CPU")
 recipe=l.obj(dict(path=a.recipe,bytes=Path(a.recipe).stat().st_size,sha256=a.recipe_sha256))
 l.need(recipe["producer_ref"]==source,"exact qualified offline recipe")
 owned=l.obj(recipe["cpu_owned_ref"])
 memory.consume_memory(before,expected_limit=8*1024**3,container_id=owned["cid"])
 out=Path(a.output_dir)
 l.publish(out/"MEMORY-BEFORE.json",dict(source=source,actual_memory=before,Devices_declaration_requires_inspect=True))
 row=m["runtime_roles"]["offline_consume"];core=m["runtime_roles"]["release_core"]
 original=sys.argv
 try:
  sys.argv=[row["path"],"--recipe",a.recipe,"--recipe-sha256",a.recipe_sha256,
   "--release-core",core["path"],"--release-core-bytes",str(core["bytes"]),"--output-dir",str(out)]
  runpy.run_path(row["path"],run_name="__main__")
 finally:
  sys.argv=original
  after=memory.memory(expected_limit=8*1024**3)
  memory.consume_memory(after,expected_limit=8*1024**3,container_id=owned["cid"],namespace_pid=before["process"]["pid"])
  l.publish(out/"MEMORY-AFTER.json",dict(source=source,actual_memory=after,Devices_declaration_requires_inspect=True))
if __name__=="__main__":main()
