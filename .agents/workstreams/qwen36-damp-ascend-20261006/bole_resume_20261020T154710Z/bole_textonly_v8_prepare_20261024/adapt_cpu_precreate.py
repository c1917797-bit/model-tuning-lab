"""Pure exact-seam adapter shared by short8/formal; no owner/authority."""
import copy,hashlib
from pathlib import Path
import cpu_precreate_policy as P
def need(v,s):
 if not v:raise ValueError(s)
def once(s,a,b):
 need(s.count(a)==1,'unique source-owned CPU intent seam '+a[:90]);return s.replace(a,b,1)
def adapt(files):
 out=dict(files)
 host=out['host_service.py'].decode()
 old="owned.append(ctl);mark(role,'initial-observation');"
 new="""owned.append(ctl)
  if role=='cpu-preflight':
   import cpu_precreate_policy as CPU_PRECREATE
   C.need(C.ref(CPU_PRECREATE.__file__)==m['files']['cpu_precreate_policy.py'],'actual source-owned precreate intent')
   CPU_PRECREATE.arm(S,ctl,sr,role)
  mark(role,'initial-observation');"""
 out['host_service.py']=once(host,old,new).encode()
 creator=out['owned_create.py'].decode()
 old=" if not re.fullmatch('[A-Za-z0-9_-]{1,100}',ctl.name):"
 new=""" if role=='cpu-preflight':
  import cpu_precreate_policy as CPU_PRECREATE
  if C.ref(CPU_PRECREATE.__file__)!=C.obj(sr)['files']['cpu_precreate_policy.py']:raise ValueError('actual source-owned CPU creator policy')
  CPU_PRECREATE.check_create(S,ctl,sr,role,S.create_argv(ctl.expected))
 if not re.fullmatch('[A-Za-z0-9_-]{1,100}',ctl.name):"""
 out['owned_create.py']=once(creator,old,new).encode()
 loader=out['owned_substrate.py'].decode()
 old=' CPU_RELEASE.install(S,C,current)'
 new=old+"\n raw(current['files']['cpu_precreate_policy.py'])\n import cpu_precreate_policy as CPU_PRECREATE\n CPU_PRECREATE.install(S,C,current)"
 out['owned_substrate.py']=once(loader,old,new).encode()
 out['cpu_precreate_policy.py']=Path(P.__file__).read_bytes()
 for n,b in out.items():
  if n.endswith('.py'):compile(b,n,'exec')
 delta={n:dict(before=files.get(n),after=b)for n,b in out.items()if files.get(n)!=b}
 need(set(delta)=={'host_service.py','owned_create.py','owned_substrate.py','cpu_precreate_policy.py'},'exact four-file CPU-only delta')
 return out,delta
def inverse(files,delta):
 out=dict(files)
 for n,row in delta.items():
  need(out[n]==row['after'],'complete CPU-only inverse byte')
  if row['before']is None:out.pop(n)
  else:out[n]=row['before']
 return out
def manifest(m):
 out=copy.deepcopy(m);out['cpu_precreate_intent']=copy.deepcopy(P.CONTRACT);return out
