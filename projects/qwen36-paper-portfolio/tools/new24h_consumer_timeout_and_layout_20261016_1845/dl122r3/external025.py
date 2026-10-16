"""Source-bound025 external RW leaf, unchanged32GiB payload/8.5GiB reserve."""
import ast,hashlib,json,os,shutil,types
from pathlib import Path
OUT=None # installed from the exact source-bound invocation, never old075 OUT
LOG=dict(Type='json-file',Config={'max-size':'16m','max-file':'2'})
SAFETY=(22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30')
def need(v,m):
 if not v:raise ValueError(m)
def environment(e):
 leaf=Path(e['mounts']['/adakv-results'][0]);need(leaf.parent==OUT and leaf.name in('cpu-preflight','dense','candidate','cpu-consumer'),'exact new064 opt stage')
 need(all(not rw or Path(src)==leaf for src,rw in e['mounts'].values()),'only ONE source-owned RW payload leaf')
 return dict(HOME='/adakv-results/.runtime/home',TMPDIR='/adakv-results',XDG_CACHE_HOME='/adakv-results/.runtime/xdg',TORCH_HOME='/adakv-results/.runtime/torch',TORCH_EXTENSIONS_DIR='/adakv-results/.runtime/extensions',TRITON_CACHE_DIR='/adakv-results/.runtime/triton',HF_HOME='/adakv-results/.runtime/hf',HF_HUB_CACHE='/adakv-results/.runtime/hf/hub',VLLM_CACHE_ROOT='/adakv-results/.runtime/vllm',TORCHINDUCTOR_CACHE_DIR='/adakv-results/.runtime/inductor')
def prepare(leaf):
 leaf=Path(leaf);need(leaf.parent==OUT and leaf.name in('cpu-preflight','dense','candidate','cpu-consumer')and leaf.is_dir()and not leaf.is_symlink(),'pre-created sole exact stage')
 need(not (leaf/'.runtime').exists(),'fresh runtime cache tree')
 for n in ('home','xdg','torch','extensions','triton','hf/hub','vllm','inductor'):(leaf/'.runtime'/n).mkdir(parents=True,exist_ok=True)
def derive(body):
 need((len(body),hashlib.sha256(body).hexdigest())==SAFETY,'original025 exact whole safety source')
 text=body.decode();pairs=[
 ('"--pids-limit","2048","--ipc"','"--read-only","--log-driver","json-file","--log-opt","max-size=16m","--log-opt","max-file=2","--pids-limit","2048","--ipc"'),
 ('for k,v in environment(cpu).items():args+=["--env",k+"="+v]','for k,v in dict(environment(cpu),**_EXTERNAL.environment(e)).items():args+=["--env",k+"="+v]'),
 ('for k,v in environment(cpu).items()),"no duplicated/drifted guest environment")','for k,v in dict(environment(cpu),**_EXTERNAL.environment(e)).items()),"no duplicated/drifted guest environment")'),
 ('h=x["HostConfig"];cfg=x["Config"];','h=x["HostConfig"];cfg=x["Config"];c.require(h.get("ReadonlyRootfs")is True and h.get("LogConfig")==_EXTERNAL.LOG and not h.get("Tmpfs"),"exact readonly/log capped/no tmpfs");')]
 out=text
 for a,b in pairs:need(out.count(a)==1,'exact025 readonly/environment delta');out=out.replace(a,b)
 inv=out
 for a,b in reversed(pairs):need(inv.count(b)==1,'unique025 inverse');inv=inv.replace(b,a)
 need(inv==text,'whole025 inverse, no resource/numeric guard changed')
 return out,pairs
def install(c,S,H,output_root):
 global OUT
 OUT=Path(output_root)
 need(OUT.parent==Path('/opt/host/vnf/austinov')and OUT.name in('run-dl-production122R3-validation-MAIN-NEW24H_001','run-dl-production122R3-smokepair-MAIN-NEW24H_001','run-dl-production122R3-screenpair-MAIN-NEW24H_001'),'exact122 new output leaf')
 need(os.environ.get('DL122_EXTERNAL_OUTPUT_ENABLE')=='1','explicit source-bound external-output opt-in')
 need(S.WORKSPACE==32*2**30 and S.RESERVE==8*2**30 and S.HOST_MEM==512*2**20,'original32GiB payload and postcap48 RAMreserve')
 text,pairs=derive(Path(S.__file__).read_bytes());tree=ast.parse(text);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in('create_argv','validate_inspect')]
 need(len(nodes)==2,'exact two existing safety functions')
 scope=dict(S.__dict__,_EXTERNAL=types.SimpleNamespace(environment=environment,LOG=LOG));exec(compile(ast.Module(body=nodes,type_ignores=[]),S.__file__+'#064-readonly-only','exec'),scope)
 S._EXTERNAL=scope['_EXTERNAL']
 for name in ('create_argv','validate_inspect'):S.__dict__[name]=types.FunctionType(scope[name].__code__,S.__dict__,name)
 oldfresh=H.fresh_leaf
 def fresh(path):
  p=c.ordinary(path);need(p.parent==OUT and p.name in('cpu-preflight','dense','candidate','cpu-consumer')and p.parent.is_dir()and not p.exists(),'exact fresh064 opt stage; no broad opt escape');p.mkdir(mode=0o700);return p
 H.fresh_leaf=fresh
 original=S.Controller.resources
 def resources(self,initial=False):
  value=original(self,initial) # Original32GiB whole output hardcap and8.5GiB disk floor remain.
  need(self.out.parent==OUT,'original025 disk measurement uses this sole opt output root')
  # cap48 changes the shared RAM RESERVE global to8GiB. Disk reserve remains
  # the original0258.5GiB, independently of that RAM-only provider adjustment.
  need(value['disk_free_bytes']>=int(8.5*2**30)+(32*2**30 if initial else 0),'original disk8.5GiB reserve +32GiB payload, never RAM-global8GiB')
  info=json.loads(c.obj(value['engine'])['stdout']);root=Path(info['DockerRootDir'])
  need(root.is_absolute()and root.is_dir()and not root.is_symlink(),'actual ordinary Docker RootDir from original engine response')
  free=shutil.disk_usage(root).free;same=root.stat().st_dev==OUT.stat().st_dev
  need(free>=int(8.5*2**30),'Docker retains independent original8.5GiB diskreserve')
  return dict(value,external_output_ledger=dict(opt_payload_bytes=32*2**30,reserve_bytes=int(8.5*2**30),opt_initial_bytes=int(40.5*2**30),same_filesystem=same,DockerRootDir=str(root),Docker_free_bytes=free,reserve_count=1 if same else 2,readonly_rootfs=True,log=LOG))
 S.Controller.resources=resources
 return dict(original025_guard_preserved=True,source_deltas=len(pairs),NPU=False)
