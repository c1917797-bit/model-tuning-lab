"""Explicit deviceless CPU initial observation. No NPU admission grant."""
import ast,copy,hashlib,os,types
from pathlib import Path
SAFETY=(22338,'20bda52a1c3fbc75db47104cbd4759faf91da1f39032d4730160983f7b9c0c30')
CONTRACT=dict(schema='bole.source-owned-cpu-precreate-intent/v1',role='cpu-preflight',
 planned_devices=[],actual_devices_before_create=None,initial_only=True,
 NPU_admission_unchanged=True,protected0_3_unchanged=True)
def need(v,s):
 if not v:raise ValueError(s)
def source_observe(raw):
 need((len(raw),hashlib.sha256(raw).hexdigest())==SAFETY,'exact original025 observe source')
 s=raw.decode();cl=next(n for n in ast.parse(s).body if isinstance(n,ast.ClassDef)and n.name=='Controller')
 fn=next(n for n in cl.body if isinstance(n,ast.FunctionDef)and n.name=='observe')
 old=ast.get_source_segment(s,fn)
 start=old.index('  for card in PHYSICAL:')
 end=old.index('  holders=fd_holders();')
 block=old[start:end]
 replacement="""  record['cpu_precreate_observation']=dict(schema='bole.actual-deviceless-precreate-observation/v1',planned_devices=[],actual_devices=None,NPU_idle_proven=False,ownership_qualified=False)
  for card in PHYSICAL:
   record['actual_hbm'].append(actual_hbm(text,card))
   rows=[(n,ch,pid) for n,ch,pid in self.h.legacy().process_rows(text) if n==card]
   record['actual_compute'].extend(dict(physical=n,chip=ch,pid=pid,smi=sr,raw_observation=original,ownership_qualified=False,source='actual-SMI-only')for n,ch,pid in rows)
"""
 new=old.replace(block,replacement,1)
 gate='  c.require(all(self.cid is not None and self.cid in p["cgroup"] for p in holders),"actual foreign4..7 FD/UDA conflict")'
 fixed='  c.require(all(p["pid"]!=os.getpid() and (self.cid is None or self.cid not in p["cgroup"]) for p in holders),"deviceless CPU/host must have no actual4..7 device FD")'
 need(new.count(gate)==1,'one exact original target FD exclusion')
 new=new.replace(gate,fixed,1)
 inverse=new.replace(replacement,block,1).replace(fixed,gate,1)
 need(inverse==old,'entire original observe source inverse')
 return new,dict(before=old,after=new)
def inverse_observe(made,delta):
 need(made==delta['after'],'exact private CPU observe');return delta['before']
class Intent:
 def __init__(self,policy,ctl,sr):
  self.policy=policy;self.ctl=ctl;self.source=copy.deepcopy(sr);self.name=ctl.name;self.out=ctl.out
  self.start=ctl.created_monotonic;self.deadline=ctl.deadline
class Policy:
 def __init__(self,S,C,m):
  self.S,self.C,self.m=S,C,m
  self.source=C.ref(Path(C.__file__).resolve().parent/'SOURCE_BOUND.json')
  self.original=S.Controller.observe
  raw=Path(S.__file__).read_bytes();made,delta=source_observe(raw)
  need(inverse_observe(made,delta)==delta['before'],'full original observe inverse')
  ns=dict(S.__dict__)
  exec(compile(ast.parse(made),S.__file__+'#explicit-deviceless-CPU-initial','exec'),ns)
  self.cpu_observe=ns['observe']
 def arm(self,ctl,sr,role):
  need(role=='cpu-preflight'and sr==self.source,'exact source-owned explicit CPUpreflight role/source')
  need(ctl.cid is None and ctl.expected is None and not hasattr(ctl,'_cpu_precreate_intent'),'fresh precreate controller before expected')
  need(ctl.deadline==ctl.created_monotonic+self.S.PHASE and ctl.remaining(cap=1)>0,'same original entry/deadline, no CPU clock renewal')
  ctl._cpu_precreate_intent=Intent(self,ctl,sr)
 def intent(self,ctl):
  x=getattr(ctl,'_cpu_precreate_intent',None)
  need(type(x)is Intent and x.policy is self and x.ctl is ctl and x.source==self.source and
   x.name==ctl.name and x.out==ctl.out and x.start==ctl.created_monotonic and x.deadline==ctl.deadline,'unforgeable source/role/controller/lifetime intent')
  return x
 def observe(self,ctl,label,initial=False,cleanup=False):
  if not hasattr(ctl,'_cpu_precreate_intent'):return self.original(ctl,label,initial=initial,cleanup=cleanup)
  self.intent(ctl)
  need(initial is True and cleanup is False and label=='cpu-preflight-admission'and ctl.cid is None and ctl.expected is None,'CPU initial-only before expected, never model observe')
  need(ctl.remaining(cap=1)>0,'original remaining clock still live')
  return self.cpu_observe(ctl,label,initial=initial,cleanup=cleanup)
 def check_create(self,ctl,sr,role,argv):
  if not hasattr(ctl,'_cpu_precreate_intent'):
   need(role!='cpu-preflight','CPU creator requires explicit precreate intent');return
  self.intent(ctl)
  need(sr==self.source and role=='cpu-preflight'and ctl.cid is None and
   ctl.expected['arm']==role and ctl.expected['source']==sr and ctl.expected['cid'] is None,'same CPU source/role reaches exact original creator')
  need(argv==self.S.create_argv(ctl.expected)and '--device'not in argv and
   not any(a.startswith(('--device=','--gpus','--privileged'))for a in argv),'actual original CPU argv has no devices, never an intent-only assertion')
  # Actual Devices[] is established later by unchanged original validate_inspect.
  del ctl._cpu_precreate_intent
def install(S,C,m):
 need(m.get('cpu_precreate_intent')==CONTRACT and C.ref(__file__)==m['files']['cpu_precreate_policy.py'],'exact source-owned CPU initial policy')
 policy=Policy(S,C,m)
 need(not hasattr(S,'_CPU_PRECREATE_POLICY'),'one private source-owned policy installation')
 S._CPU_PRECREATE_POLICY=policy
 def observe(ctl,label,initial=False,cleanup=False):return policy.observe(ctl,label,initial,cleanup)
 S.Controller.observe=observe
 return policy
def arm(S,ctl,sr,role):return S._CPU_PRECREATE_POLICY.arm(ctl,sr,role)
def check_create(S,ctl,sr,role,argv):return S._CPU_PRECREATE_POLICY.check_create(ctl,sr,role,argv)
