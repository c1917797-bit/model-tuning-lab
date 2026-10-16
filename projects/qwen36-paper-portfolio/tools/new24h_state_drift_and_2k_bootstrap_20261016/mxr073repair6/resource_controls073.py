"""Actual source create/inspect unit controls; never actual Docker admission."""
import ast,copy,hashlib,re,types
from pathlib import Path
P=Path(__file__).resolve().parent
def need(v,m):
 if not v:raise ValueError(m)
def run():
 from resource_budget073 import contract
 import cap48_provider as provider
 b=(P/'actual011/safety_host.py').read_bytes();need(hashlib.sha256(b).hexdigest()=='8c83e08318b530c4d022b91bbacd34b12121b3380e1a14d32262c9a3875f6fa7','actual immutable011 source')
 selected={'create_argv','validate_inspect','environment','labels','device_map'};tree=ast.parse(b);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in selected];need(len(nodes)==5,'all actual original resource functions')
 c=types.SimpleNamespace(GIB=2**30,ROOT=Path('/canonical'),IMAGE='sha256:actual-source-control',require=need)
 S=types.ModuleType('_actual011_pure_resource_controls');S.__file__=str(P/'actual011/safety_host.py');S.__dict__.update(c=c,re=re,DOCKER='/usr/bin/docker',MEM=64*2**30,RESERVE=int(8.5*2**30),HOST_MEM=2**29,WORKSPACE=32*2**30,PHYSICAL=(4,5,6,7),OWNER='source-only073')
 exec(compile(ast.Module(body=nodes,type_ignores=[]),S.__file__,'exec'),vars(S));proof=provider.prepare(S,c)
 need(S.MEM==32*c.GIB and S.RESERVE==8*c.GIB and S.HOST_MEM==.5*c.GIB and proof['model_initial_GiB']==40.5,'single source budget32+host.5+reserve8')
 need(S.create_argv.__globals__ is vars(S)and S.validate_inspect.__globals__ is vars(S),'actual functions share actual mutable MEM global')
 for role in('candidate','cpu-preflight'):
  cpu=role=='cpu-preflight';mem=(8 if cpu else 32)*c.GIB;cores=1 if cpu else 4
  e=dict(cid='a'*64,name='source-only073-'+role,arm=role,algorithm_arm='candidate',source=dict(sha256='b'*64),host_sha256='c'*64,guest_cpus=list(range(cores)),mounts={'/adakv-results':('/owned/'+role,True)})
  argv=S.create_argv(e);need(argv[argv.index('--memory')+1]==argv[argv.index('--memory-swap')+1]==str(mem),'actual original create RAM and no swap exact')
  h=dict(Memory=mem,MemorySwap=mem,NanoCpus=cores*10**9,CpusetCpus=','.join(map(str,e['guest_cpus'])),IpcMode='private',NetworkMode='none',ShmSize=4*c.GIB,PidsLimit=2048,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Privileged=False,Devices=[dict(PathOnHost=p,PathInContainer=n,CgroupPermissions='rwm')for p,n in({}if cpu else S.device_map()).items()])
  cfg=dict(Image=c.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(c.ROOT),Labels=S.labels(e),Env=[k+'='+v for k,v in S.environment(cpu,e['algorithm_arm']).items()])
  x=dict(Id=e['cid'],Image=c.IMAGE,Name='/'+e['name'],HostConfig=h,Config=cfg,Mounts=[dict(Type='bind',Destination=n,Source=p,RW=bool(w))for n,(p,w)in e['mounts'].items()]);S.validate_inspect(x,e)
  for key,value in(('Memory',48*c.GIB),('MemorySwap',mem+1)):
   wrong=copy.deepcopy(x);wrong['HostConfig'][key]=value
   try:S.validate_inspect(wrong,e)
   except ValueError:pass
   else:raise ValueError('mismatched actual inspect cap was accepted')
 import stage_resources
 _,derived,_=stage_resources.derive(b);need('guest_budget=8*c.GIB' in derived and 'else MEM' in derived,'CPU unchanged model follows same MEM')
 need(contract()['new2K_peak_proved']is False and contract()['OOM_is_hard_failure']is True,'trial scope not proof')
 return dict(schema='mxr.source-derived-create-inspect-memory-controls/v073',model32=True,CPU8=True,no_swap=True,shared_globals=True,wrong_cap_rejected=True,reserve8_hosthalf=True,NPU=False,actual_Docker_inspect=False)
