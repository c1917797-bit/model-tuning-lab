"""Actual025 function bodies, CPU software only; not actual Docker/OOM proof."""
import ast,copy,json,re,types,unittest
from pathlib import Path
import cap48_provider as CAP
P=Path(__file__).parent
def require(v,m):
 if not v:raise ValueError(m)
def fixture():
 path=P/'evidence/ORIGINAL025_SAFETY.py';tree=ast.parse(path.read_bytes());names=('labels','environment','device_map','create_argv','validate_inspect');nodes=[copy.deepcopy(n)for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
 S=types.ModuleType('_actual025_resource');S.__file__=str(path);c=types.SimpleNamespace(GIB=2**30,IMAGE='sha256:'+'a'*64,ROOT=Path('/source'),require=require)
 S.__dict__.update(c=c,re=re,Path=Path,DOCKER='/usr/bin/docker',MEM=64*2**30,RESERVE=int(8.5*2**30),HOST_MEM=2**29,OWNER='new-test-only',PHYSICAL=(4,5,6,7))
 exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),S.__dict__);proof=CAP.prepare(S,c);return S,c,proof
def expected(S,c,cpu=False):
 e=dict(name='source-owned',arm='cpu-preflight'if cpu else'dense',source=dict(sha256='b'*64),host_sha256='c'*64,guest_cpus=[8]if cpu else[8,9,10,11],mounts={},cid='d'*64)
 mem=8*2**30 if cpu else S.MEM;cores=1 if cpu else 4
 x=dict(Id=e['cid'],Image=c.IMAGE,Name='/'+e['name'],Config=dict(Image=c.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(c.ROOT),Labels=S.labels(e),Env=[k+'='+v for k,v in S.environment(cpu).items()]),HostConfig=dict(Privileged=False,Memory=mem,MemorySwap=mem,NanoCpus=cores*10**9,CpusetCpus=','.join(map(str,e['guest_cpus'])),IpcMode='private',NetworkMode='none',ShmSize=4*c.GIB,PidsLimit=2048,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Devices=[dict(PathOnHost=k,PathInContainer=v,CgroupPermissions='rwm')for k,v in({}if cpu else S.device_map()).items()]),Mounts=[])
 return e,x
class Tests(unittest.TestCase):
 def test_same_source_globals_and_original32_plus_reserve_formula(self):
  S,c,p=fixture();self.assertIs(S.create_argv.__globals__,S.__dict__);self.assertIs(S.validate_inspect.__globals__,S.__dict__);self.assertEqual(S.MEM,32*c.GIB);self.assertEqual(S.RESERVE+S.HOST_MEM+S.MEM,int(40.5*c.GIB));self.assertEqual(S.RESERVE+S.HOST_MEM,int(8.5*c.GIB));self.assertEqual(p['CPU_initial_GiB'],40.5)
 def test_actual_model32_cpu8_create_arguments(self):
  S,c,p=fixture()
  for cpu,mem in((False,32*c.GIB),(True,8*c.GIB)):
   e,x=expected(S,c,cpu);argv=S.create_argv(e);self.assertEqual(argv[argv.index('--memory')+1],str(mem));self.assertEqual(argv[argv.index('--memory-swap')+1],str(mem));self.assertEqual(len([a for a in argv if a=='--device']),0 if cpu else 7)
 def test_actual_inspect_exact32_and_wrong_cap_swap_reject(self):
  S,c,p=fixture()
  for cpu in(False,True):
   e,x=expected(S,c,cpu);S.validate_inspect(x,e)
   for key,value in(('Memory',48*c.GIB),('MemorySwap',-1)):
    bad=copy.deepcopy(x);bad['HostConfig'][key]=value
    with self.assertRaises(ValueError):S.validate_inspect(bad,e)
 def test_original_prepare_preconditions_and_scan_live_globals(self):
  S,c,p=fixture()
  with self.assertRaises(ValueError):CAP.prepare(S,c)
  # The real scanner compiles resources using this live module dictionary,
  # not the external create/inspect temporary compilation dictionary.
  import output_scan131r8 as SC
  parsed=ast.parse((P/'evidence/ORIGINAL025_SAFETY.py').read_bytes());cls=next(n for n in parsed.body if isinstance(n,ast.ClassDef)and n.name=='Controller')
  S.H=types.SimpleNamespace(Controller=object)
  exec(compile(ast.Module(body=[cls],type_ignores=[]),str(S.__file__),'exec'),S.__dict__)
  SC.install(c,S,P/'not-created-source-only-output')
  functions=[cell.cell_contents for cell in S.Controller.resources.__closure__ if isinstance(cell.cell_contents,types.FunctionType)]
  patched=next(fn for fn in functions if fn.__code__.co_filename.endswith('#output-scan131r8'))
  self.assertIs(patched.__globals__,S.__dict__);self.assertEqual(patched.__globals__['MEM'],32*c.GIB)
  plan=json.loads((P/'RESOURCE_EDITS131R14.json').read_bytes());body=(P/'cap48_provider.py').read_text()
  for e in reversed(plan['edits']):
   self.assertEqual(body.count(e['after']),1);body=body.replace(e['after'],e['before'])
  import hashlib
  self.assertEqual(dict(bytes=len(body.encode()),sha256=hashlib.sha256(body.encode()).hexdigest()),plan['before'])
if __name__=='__main__':unittest.main()
