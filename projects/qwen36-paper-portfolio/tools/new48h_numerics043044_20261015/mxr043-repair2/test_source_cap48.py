"""Source-fixture consistency tests, never actual Docker or guest-memory PASS."""
import ast,importlib.util,json,re,types,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;G=1024**3
def need(v,s):
 if not v:raise ValueError(s)
def scope():
 text=(P/'actual_loader/safety_host.py').read_text();tree=ast.parse(text);names={'device_map','labels','environment','create_argv','validate_inspect'}
 c=types.SimpleNamespace(GIB=G,ROOT=Path('/fixture-repo'),IMAGE='image-fixture',require=need)
 ns=dict(c=c,re=re,Path=Path,MEM=48*G,PHYSICAL=(4,5,6,7),OWNER='source-fixture',DOCKER='/usr/bin/docker')
 nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name in names]
 exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-immutable-source-fixture','exec'),ns);return ns,c
def fixture(ns,c,cpu=False):
 e=dict(arm='cpu-preflight'if cpu else'candidate',algorithm_arm='candidate',cid='a'*64,name='fixture',source={'sha256':'b'*64},host_sha256='c'*64,guest_cpus=[1]if cpu else[1,2,3,4],mounts={'/fixture-out':('/fixture-out',True)})
 mem=(8 if cpu else 48)*G;dev={}if cpu else ns['device_map']()
 x=dict(Id=e['cid'],Image=c.IMAGE,Name='/'+e['name'],Config=dict(Image=c.IMAGE,Entrypoint=['/bin/bash'],Cmd=['-c','exec /bin/sleep infinity'],WorkingDir=str(c.ROOT),Labels=ns['labels'](e),Env=[k+'='+v for k,v in ns['environment'](cpu,e['algorithm_arm']).items()]),HostConfig=dict(Privileged=False,Memory=mem,MemorySwap=mem,NanoCpus=(1 if cpu else 4)*10**9,CpusetCpus=','.join(map(str,e['guest_cpus'])),IpcMode='private',NetworkMode='none',ShmSize=4*G,PidsLimit=2048,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Devices=[dict(PathOnHost=k,PathInContainer=v,CgroupPermissions='rwm')for k,v in dev.items()]),Mounts=[dict(Type='bind',Source='/fixture-out',Destination='/fixture-out',RW=True)])
 return e,x
class Tests(unittest.TestCase):
 def test_actual_create48_inspect48(self):
  ns,c=scope();e,x=fixture(ns,c);argv=ns['create_argv'](e);self.assertEqual(argv[argv.index('--memory')+1],str(48*G));self.assertEqual(argv[argv.index('--memory-swap')+1],str(48*G));ns['validate_inspect'](x,e)
 def test_inspect_reject64(self):
  ns,c=scope();e,x=fixture(ns,c);x['HostConfig']['Memory']=64*G
  with self.assertRaises(ValueError):ns['validate_inspect'](x,e)
 def test_CPU8_unchanged(self):
  ns,c=scope();e,x=fixture(ns,c,True);argv=ns['create_argv'](e);self.assertEqual(argv[argv.index('--memory')+1],str(8*G));ns['validate_inspect'](x,e)
 def test_cgroup_identity(self):
  s=importlib.util.spec_from_file_location('_mem009',P/'memory_observer.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);cid='a'*64
  self.assertEqual(m.locate('0::/docker/'+cid,cid)[0],'v2');self.assertEqual(m.locate('5:memory:/docker/'+cid,cid)[0],'v1')
  with self.assertRaises(ValueError):m.locate('0::/docker/'+'b'*64,cid)
if __name__=='__main__':unittest.main()
