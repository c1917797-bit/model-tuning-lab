"""Exact source and entrypoint discovery, no torch/vLLM/HAL imports."""
import hashlib,importlib,importlib.metadata,importlib.util,json,sys
from pathlib import Path
EXPECTED={'mxr_common_precision044':'mxr_common_precision044:register','mxr_block_refinement044':'mxr_block_refinement044:register'}
def need(v,m):
 if not v:raise ValueError(m)
def checked(r):
 p=Path(r['path']);b=p.read_bytes();need(p.is_absolute()and p.is_file()and not p.is_symlink()and(len(b),hashlib.sha256(b).hexdigest())==(r['bytes'],r['sha256']),'exact actual044 source bytes');return p
def component(sr):
 p=checked(sr);m=json.loads(p.read_bytes());root=Path(m['root'])
 need(p==root/'SOURCE_MANIFEST.json'and m['schema']=='mxr.observerless-source/v1'and m['default_enabled']is False,'same immutable actual044 source root')
 for name,r in m['files'].items():need(r['path']==str(root/name),'source leaf at sole044 root');checked(r)
 r=m['files']['common_precision.py'];s=importlib.util.spec_from_file_location('_048_actual_common',checked(r));v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
 return root,v
def static_discovery(root):
 root=Path(root).resolve();need(root.is_dir()and not root.is_symlink(),'actual component directory')
 # Explicit path enumeration excludes ambient unrelated distributions.
 entries={}
 for dist in importlib.metadata.distributions(path=[str(root)]):
  for ep in dist.entry_points:
   if ep.group=='vllm.general_plugins'and ep.name in EXPECTED:
    need(ep.name not in entries and ep.value==EXPECTED[ep.name],'unique exact044 general entrypoint');entries[ep.name]=ep
 need(set(entries)==set(EXPECTED),'both actual044 distribution entrypoints present')
 sys.path.insert(0,str(root))
 for name,ep in entries.items():
  mod=importlib.import_module(ep.module);need(Path(mod.__file__).resolve()==root/name/'__init__.py'and callable(getattr(mod,ep.attr)),'static package import at exact044 root')
 need(not any(n in('torch','vllm')or n.startswith(('torch.','torch_npu','vllm.'))for n in sys.modules),'static discovery imported no backend/framework/HAL')
 return dict(schema='mxr.actual044-static-entrypoint-discovery/v048',root=str(root),entrypoints={k:ep.value for k,ep in entries.items()},static_import=True,NPU=False,register_called=False)
