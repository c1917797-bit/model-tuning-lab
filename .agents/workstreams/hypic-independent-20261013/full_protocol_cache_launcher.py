"""Full original workload; sole treatment is an audited compiled-cache COPY."""
import argparse,hashlib,json
from pathlib import Path
import native_tp4_smoke as base
from independent_full_protocol_cache import bindings,identity,stage_cache,inject_cache
from independent_compilation_cache import inventory
HERE=Path(__file__).resolve().parent
BASE_SHA="c360a9d1da1de4db93184da633e569adeb1b1f85073f3c3a61651b40819a23c0"
def validate(c):
 if c.get("controller_sha256")!=BASE_SHA or hashlib.sha256((HERE/"native_tp4_smoke.py").read_bytes()).hexdigest()!=BASE_SHA:raise ValueError("original controller drift")
 if hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=c["launcher_sha256"]:raise ValueError("cache launcher drift")
 if c.get("formal_performance") is not True or c.get("formal_quality") or c.get("max_output_tokens")!=1024 or c.get("enforce_eager") is not True:raise ValueError("full original performance protocol required")
 if c["physical_npus"]!=[0,1,2,3] or c["tp"]!=4:raise ValueError("physical0-3 singleTP4 required")
 for f,h in bindings(c).items():
  p=HERE/f
  if not p.resolve().is_relative_to(HERE) or hashlib.sha256(p.read_bytes()).hexdigest()!=h:raise ValueError("source drift: "+f)
 from independent_full_protocol_cache import seed_contract
 seed_contract(c)
def run(c):
 validate(c);raw=Path(c["raw_root"]);original=base.command;staged=[]
 def command(argv,**kw):
  if list(argv)[:2]==["docker","run"]:
   if staged:raise RuntimeError("only one owned service allowed")
   path,before=stage_cache(c,raw);staged.append(path)
   base.write(raw,"compiled-cache-before.json",before)
   base.write(raw,"compiled-cache-identity.json",identity(c))
   base.write(raw,"cache-launcher.json",{"launcher_sha256":c["launcher_sha256"],"controller_sha256":BASE_SHA,"seed_contract":c["compiled_cache_seed_contract"]})
   argv=inject_cache(argv,path)
  return original(argv,**kw)
 base.command=command
 try:
  base.run_contract(c)
 finally:
  base.command=original
  if staged:
   base.write(raw,"compiled-cache-inventory.json",inventory(staged[0]))
   result=json.loads((raw/"result.json").read_text()) if (raw/"result.json").exists() else {}
   base.write(raw,"cache-launcher-result.json",{"valid":result.get("valid") is True,"source":"audited copy; original seed never writable-mounted"})
def main():
 p=argparse.ArgumentParser();p.add_argument("--contract",type=Path,required=True);p.add_argument("--run",action="store_true");a=p.parse_args();c=json.loads(a.contract.read_text());validate(c)
 if a.run:run(c)
 else:print(json.dumps({"configuration_valid":True,"device_run":False}))
if __name__=="__main__":main()
