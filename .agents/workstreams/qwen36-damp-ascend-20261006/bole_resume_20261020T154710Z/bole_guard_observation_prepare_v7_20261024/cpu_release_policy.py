"""Private source-bound CPU-preflight release domain. No NPU admission grant."""
import ast,hashlib,os,textwrap,types
from pathlib import Path
SAFETY=(22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30')
CONTRACT=dict(schema='bole.deviceless-cpu-preflight-release/v1',arm='cpu-preflight',
 actual_devices=[],protected=[0,1,2,3],NPU_admission_unchanged=True,
 own_source_identity_unchanged=True,own_init_exec_oom_cli_checks_unchanged=True)
OLD='   for card in PHYSICAL:self.h.idle_one(raw["stdout"],card)'
NEW='''   if _CPU_RELEASE.cpu(self,x):
    v["cpu_release_boundary"]=_CPU_RELEASE.release(self,raw["stdout"],sr)
   else:
    for card in PHYSICAL:self.h.idle_one(raw["stdout"],card)'''
def need(v,s):
 if not v:raise ValueError(s)
def adapt(raw):
 need((len(raw),hashlib.sha256(raw).hexdigest())==SAFETY,'exact original025 safety source')
 s=raw.decode();need(s.count(OLD)==1,'one cleanup target idle seam')
 made=s.replace(OLD,NEW,1);need(made.replace(NEW,OLD,1)==s,'entire original safety inverse')
 return made.encode(),dict(before=s,after=made)
def inverse(raw,delta):
 need(raw.decode()==delta['after'],'whole cleanup inverse domain');return delta['before'].encode()
def cpu(ctl,x):
 if ctl.expected['arm']!='cpu-preflight':return False
 need(x['HostConfig'].get('Devices')==[],'CPUpreflight release requires actual inspected Devices[]')
 need(not x['State']['Running']and x['State']['Pid']==0 and not x.get('ExecIDs')
      and not x['State'].get('OOMKilled'),'original stopped own init/Exec/OOM')
 return True
def residuals(cid,root=Path('/proc')):
 need(type(cid)is str and len(cid)==64 and all(c in '0123456789abcdef'for c in cid),'actual exact owned CID')
 ids=[];count=0
 for p in root.iterdir():
  if not p.name.isdigit():continue
  count+=1;need(count<=20000,'bounded readable host process inventory')
  try:cg=(p/'cgroup').read_text()
  except(FileNotFoundError,ProcessLookupError):continue
  if cid in cg:ids.append(int(p.name))
 return ids
def release(ctl,text,smi_ref):
 # Protected boundary, exact own inspect, source, foreground CLI, Exec and OOM
 # checks already ran in original cleanup. No external NPU workload is stopped.
 rows=ctl.h.legacy().process_rows(text)
 need(all(type(row)in(tuple,list)and len(row)==3 for row in rows),'actual original process rows')
 need(all(row[2]!=os.getpid()for row in rows),'own host PID unexpectedly using NPU')
 owned=residuals(ctl.cid);need(not owned,'owned CPU CID still has processes')
 return dict(schema=CONTRACT['schema'],cid=ctl.cid,arm=ctl.expected['arm'],
  release_smi=smi_ref,own_residual_pids=owned,
  external_compute=[dict(physical=n,chip=chip,pid=pid)for n,chip,pid in rows],
  external_idle_required=False,NPU_idle_proven=False,NPU_admission_unchanged=True,
  protected_original_check_preserved=True,source_owner_checks_preserved=True)
def install(S,C,m):
 need(m.get('deviceless_cpu_release')==CONTRACT,'source-bound CPU release policy contract')
 need(C.ref(__file__)==m['files']['cpu_release_policy.py'],'actual source-owned CPU release helper')
 raw=Path(S.__file__).read_bytes();made,delta=adapt(raw);need(inverse(made,delta)==raw,'exact safety inverse')
 old=S.Controller.cleanup
 need(old.__globals__ is S.__dict__ and old.__code__.co_filename==S.__file__,'unmodified actual025 cleanup dispatch')
 tree=ast.parse(made);cls=[n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller'];need(len(cls)==1,'actual Controller')
 fn=[n for n in cls[0].body if isinstance(n,ast.FunctionDef)and n.name=='cleanup'];need(len(fn)==1,'actual cleanup')
 scope=dict(S.__dict__,_CPU_RELEASE=__import__(__name__));exec(compile(ast.Module(body=fn,type_ignores=[]),S.__file__+'#CPU-release-domain','exec'),scope)
 S._CPU_RELEASE=scope['_CPU_RELEASE'];S.Controller.cleanup=types.FunctionType(scope['cleanup'].__code__,S.__dict__,'cleanup')
 return dict(contract=CONTRACT,original_safety_sha256=SAFETY[1],private_scope_only=True,NPU_admission=False)
