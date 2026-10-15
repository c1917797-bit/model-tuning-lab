"""Stage source-bound official compiled-cache copies for full-protocol runs."""
import hashlib,json,shutil
from pathlib import Path
from independent_compilation_cache import inventory
HERE=Path(__file__).resolve().parent
BASE=Path("/cache/cch/hypic-independent-20261013")
EXTRAS={"full_protocol_cache_launcher.py","independent_full_protocol_cache.py"}
def bindings(c):
 return c.get("compiled_cache_source_sha256") or c["cache_diagnostic"]["source_sha256"]
def identity(c):
 return {"image":c["image"],"model_config_sha256":c["model_config_sha256"],
  "source_sha256":bindings(c),"tp":c["tp"],"physical_npus":c["physical_npus"],
  "scope":"official compiled binaries only; no prompt/KV/public-state transfer"}
def seed_contract(c):
 spec=c["compiled_cache_seed_contract"];name=Path(spec["path"])
 if name.name!=str(name) or name.suffix!=".json":raise ValueError("bound local seed contract required")
 p=HERE/name
 if p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=spec["sha256"]:raise ValueError("seed contract drift")
 seed=json.loads(p.read_text());old=bindings(seed);new=bindings(c)
 if set(new)!=set(old)|EXTRAS or any(new.get(f)!=h for f,h in old.items()):raise ValueError("runtime bindings may not change with cache staging")
 for key in ["image","model","model_config_sha256","physical_npus","tp"]:
  if c[key]!=seed[key]:raise ValueError("seed runtime identity differs")
 return seed
def stage_cache(c,raw):
 seed=seed_contract(c);source=Path(seed["raw_root"])/"compiled-cache";raw=Path(raw);target=raw/"compiled-cache"
 for p in [source,raw]:
  if not p.is_absolute() or ".." in p.parts or not p.is_relative_to(BASE):raise ValueError("owned cache path required")
  if any(q.is_symlink() for q in [p,*p.parents]):raise ValueError("symlink cache path rejected")
 if target.exists():raise ValueError("fresh target required")
 result=json.loads((source.parent/"result.json").read_text())
 if not result.get("valid") or not result.get("release",{}).get("removed") or not result["release"].get("port_free"):raise ValueError("seed must be valid and released")
 if seed.get("launcher_sha256"):
  if not json.loads((source.parent/"cache-launcher-result.json").read_text()).get("valid"):raise ValueError("seed launcher did not seal")
 if json.loads((source.parent/"compiled-cache-identity.json").read_text())!=identity(seed):raise ValueError("seed identity receipt differs")
 before=inventory(source)
 if before!=json.loads((source.parent/"compiled-cache-inventory.json").read_text()) or not before["file_count"]:raise ValueError("seed bytes differ")
 shutil.copytree(source,target,symlinks=False)
 if inventory(target)!=before:raise ValueError("staged cache copy differs")
 return target,before
def inject_cache(argv,path):
 argv=list(argv)
 if argv[:2]!=["docker","run"]:raise ValueError("only exact docker run launch may be augmented")
 if any(x.startswith("TRITON_CACHE_DIR=") or "/compilation-cache" in x for x in argv):raise ValueError("cache options already present")
 return argv[:2]+["-v",str(path)+":/compilation-cache:rw","-e","TRITON_CACHE_DIR=/compilation-cache"]+argv[2:]
