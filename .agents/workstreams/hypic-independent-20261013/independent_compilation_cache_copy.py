"""Stage an audited compiled-cache COPY; never mutate seed evidence."""
import hashlib,json,shutil
from pathlib import Path
from independent_compilation_cache import prepare_cache as original_prepare_cache,inventory
HERE=Path(__file__).resolve().parent
EXTRAS={"cache_reuse_copy_tp4_diagnostic.py","independent_compilation_cache_copy.py"}
def prepare_cache(contract,raw):
 if contract.get("compiled_cache",{}).get("mode")!="reuse":raise ValueError("copy controller accepts reuse only")
 spec=contract.get("compiled_cache_seed_contract")
 if not isinstance(spec,dict) or set(spec)!={"path","sha256"}:raise ValueError("bound seed contract required")
 name=Path(spec["path"])
 if name.name!=str(name) or name.suffix!=".json":raise ValueError("local seed contract basename required")
 path=HERE/name
 if path.is_symlink() or hashlib.sha256(path.read_bytes()).hexdigest()!=spec["sha256"]:raise ValueError("seed contract drift")
 seed=json.loads(path.read_text())
 old=seed["cache_diagnostic"]["source_sha256"];new=contract["cache_diagnostic"]["source_sha256"]
 if set(new)-set(old)!=EXTRAS or any(new.get(f)!=h for f,h in old.items()):raise ValueError("reuse may only add reviewed copy infrastructure")
 for f,h in old.items():
  q=HERE/f
  if not q.resolve().is_relative_to(HERE) or hashlib.sha256(q.read_bytes()).hexdigest()!=h:raise ValueError("seed source drift")
 if contract["compiled_cache"]["path"]!=str(Path(seed["raw_root"])/"compiled-cache"):raise ValueError("wrong seed cache path")
 seed["compiled_cache"]=dict(contract["compiled_cache"])
 source=original_prepare_cache(seed,raw)
 target=Path(raw)/"compiled-cache"
 if target.exists() or target.is_symlink():raise ValueError("fresh staged cache required")
 before=inventory(source)
 shutil.copytree(source,target,symlinks=False)
 after=inventory(target)
 if before!=after:raise ValueError("compiled-cache copy differs")
 return target
