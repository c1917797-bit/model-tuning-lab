"""Default-OFF source-derived 008 external-output policy; no owner/device actions."""
import ast,hashlib,json,os,textwrap
from pathlib import Path,PurePosixPath
ENABLE="MXR_DL_EXTERNAL_OUTPUT008_ENABLE"
SAFETY_SHA="8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7"
DONOR_SHA="c1a26afb164af8fcf4b88fef24a524c2c890be772f56f136b5edc5006b1ff066"
LOG={"Type":"json-file","Config":{"max-size":"16m","max-file":"2"}}
CACHE_NAMES={"HOME":"home","TMPDIR":"tmp","XDG_CACHE_HOME":"xdg","TORCH_HOME":"torch","TORCH_EXTENSIONS_DIR":"extensions","TRITON_CACHE_DIR":"triton","HF_HOME":"hf","HF_HUB_CACHE":"hf/hub","TRANSFORMERS_CACHE":"hf/transformers","VLLM_CACHE_ROOT":"vllm"}
def need(v,m):
 if not v:raise ValueError(m)
def environment(e):
 need(e.get("external_output_policy")is True,"explicit expected policy")
 mounts=e["mounts"];rw={p for p,w in mounts.values()if w}
 need(len(rw)==1,"all RW aliases point to ONE owned leaf")
 leaf=PurePosixPath(next(iter(rw)));root=PurePosixPath(e["external_output_root"])
 need(str(root).startswith("/opt/host/vnf/austinov/")and '..'not in root.parts and '..'not in leaf.parts and leaf.parent==root and leaf.name in("cpu-preflight","candidate","cpu-consumer"),"exact opt owned leaf")
 need(mounts.get("/adakv-results")== (str(leaf),True),"existing owned guest RW alias")
 need(all(not w or p==str(leaf)for p,w in mounts.values()),"no foreign writable bind")
 return {**{k:"/adakv-results/.runtime/"+v for k,v in CACHE_NAMES.items()},"TMPDIR":"/adakv-results"}
def prepare(e):
 env=environment(e);leaf=Path(e["mounts"]["/adakv-results"][0])
 need(leaf.is_dir()and not leaf.is_symlink(),"already-created owned leaf")
 need(not (leaf/'.runtime').exists()and not (leaf/'.runtime').is_symlink(),'fresh nonalias runtime root')
 for name in set(CACHE_NAMES.values()):
  target=leaf/".runtime"/name
  need(not target.exists()and not target.is_symlink(),"fresh cache directory")
 # Parent paths overlap (hf/hub); create only after all absence checks.
 for name in sorted(set(CACHE_NAMES.values()),key=lambda x:len(Path(x).parts)):
  (leaf/".runtime"/name).mkdir(parents=True,exist_ok=True)
 return env
def derive_safety(body):
 need(len(body)==22569 and hashlib.sha256(body).hexdigest()==SAFETY_SHA,"actual011 source")
 text=body.decode()
 pairs=[
 ('"--pids-limit","2048","--ipc"','"--read-only","--log-driver","json-file","--log-opt","max-size=16m","--log-opt","max-file=2","--pids-limit","2048","--ipc"'),
 ('for k,v in environment(cpu,e["algorithm_arm"]).items():args+=["--env",k+"="+v]','for k,v in dict(environment(cpu,e["algorithm_arm"]),**_EXTERNAL.environment(e)).items():args+=["--env",k+"="+v]'),
 ('for k,v in environment(cpu,e["algorithm_arm"]).items()),"no duplicated/drifted guest environment")','for k,v in dict(environment(cpu,e["algorithm_arm"]),**_EXTERNAL.environment(e)).items()),"no duplicated/drifted guest environment")'),
 ('h=x["HostConfig"];cfg=x["Config"];','h=x["HostConfig"];cfg=x["Config"];c.require(h.get("ReadonlyRootfs") is True and h.get("LogConfig")==_EXTERNAL.LOG and not h.get("Tmpfs"),"exact read-only rootfs/bounded json-file/no new tmpfs");')]
 out=text
 for a,b in pairs:need(out.count(a)==1,"exact source-derived safety delta");out=out.replace(a,b)
 inv=out
 for a,b in reversed(pairs):need(inv.count(b)==1,"unique inverse");inv=inv.replace(b,a)
 need(inv==text,"whole safety inverse")
 return out,pairs
def derive_donor(body):
 need(len(body)==25508 and hashlib.sha256(body).hexdigest()==DONOR_SHA,"actual008 source")
 old='need(free >= S.RESERVE + (S.WORKSPACE if initial else 0), "actual Docker root storage reserve")'
 new='_EXTERNAL.docker_gate(self, S, free, initial)'
 text=body.decode();need(text.count(old)==1,"exact008 Docker predicate")
 changed=text.replace(old,new);need(changed.replace(new,old)==text,"whole008 inverse")
 return changed,[(old,new)]
def docker_gate(ctl,S,free,initial):
 need(getattr(S,"_external_output_enabled",False)is True,"installed source-derived policy")
 environment(ctl.expected if ctl.cid else ctl._external_output_expected)
 # Before create: exact requested policy. After create: full original inspect,
 # including new rootfs/log/env assertions, before accepting the storage split.
 if ctl.cid:ctl.inspect()
 need(free>=int(8.5*2**30),"Docker retains original8.5GiB reserve")
 return dict(docker_free_bytes=free,docker_reserve_bytes=int(8.5*2**30),output_workspace_bytes=S.WORKSPACE,output_workspace_external=True,initial=initial)
def enable(S,expected_root):
 need(os.environ.get(ENABLE)=="1","defaultOFF explicit policy")
 need(str(expected_root).startswith("/opt/host/vnf/austinov/"),"registered external root")
 need(S.RESERVE in(8*2**30,int(8.5*2**30))and S.WORKSPACE==12*2**30,"source-bound existing RAM reserve/unchanged disk workspace")
 S._external_output_enabled=True
 return dict(prepared_policy=True,actual_sameimage=False,resource_admitted=False,NPU=False)

def install(S,Owned,c,root,safety_ref):
 """Thin existing Owned wiring; all original safety predicates remain installed."""
 need(PurePosixPath(root).is_absolute()and str(root).startswith("/opt/host/vnf/austinov/"),"registered opt root")
 raw=Path(safety_ref["path"]).read_bytes();need(len(raw), "actual source")
 changed,pairs=derive_safety(raw);tree=ast.parse(changed)
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in("create_argv","validate_inspect")]
 need(len(nodes)==2,"two exact safety functions")
 import types
 scope=dict(S.__dict__);scope["_EXTERNAL"]=types.SimpleNamespace(environment=environment,LOG=LOG)
 exec(compile(ast.Module(body=nodes,type_ignores=[]),safety_ref["path"]+"#external-output-readonly","exec"),scope)
 # These functions must share actual S globals (capture env/labels preserved).
 for name in("create_argv","validate_inspect"):
  import types
  S.__dict__["_EXTERNAL"]=scope["_EXTERNAL"]
  S.__dict__[name]=types.FunctionType(scope[name].__code__,S.__dict__,name)
 requested_create=S.create_argv;ctors={};oldinit=Owned.__init__
 def tracked(self,leaf):
  oldinit(self,leaf)
  desc=dict(external_output_policy=True,external_output_root=str(root),mounts={"/adakv-results":(str(leaf),True)})
  environment(desc)
  need(self.name not in ctors,"unique actual owned stage")
  self._external_output_expected=desc;ctors[self.name]=self
 def create(e):
  need(os.environ.get(ENABLE)=="1"and S._external_output_enabled is True,"explicit readonly output policy")
  need(e["name"]in ctors,"actual tracked owner")
  ctl=ctors[e["name"]];desc=ctl._external_output_expected
  e.update(external_output_policy=True,external_output_root=str(root))
  need(environment(e)==environment(desc)and e["mounts"]["/adakv-results"]==desc["mounts"]["/adakv-results"],"requested/actual exact owned leaf")
  prepare(e)
  return requested_create(e)
 Owned.__init__=tracked;S.create_argv=create
 S._external_output_enabled=os.environ.get(ENABLE)=="1"
 if S._external_output_enabled:enable(S,root)
 return dict(schema="shared008.external-output-readonly-install/v1",source=safety_ref,derived_function_deltas=len(pairs),output_root=str(root),Docker_reserve_bytes=int(8.5*2**30),output_workspace_bytes=S.WORKSPACE,actual_sameimage=False,resource_admitted=False)
