"""Actual create/inspect/resources AST; fixtures never allocate a container."""
import ast,copy,hashlib,json,sys,textwrap,time,types,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import cap48_provider as CAP,stage_resources as R,test_external_output as E
P=Path(__file__).resolve().parent

class Cap32(unittest.TestCase):
 def safety(self):
  old=E.T('test_actual_create_inspect');old.setUp();S=types.ModuleType('_actual_cap32_source_fixture');S.__dict__.update(old.ns)
  body,_=E.M.derive_safety(E.SAFETY.read_bytes());nodes=[n for n in ast.parse(body).body if isinstance(n,ast.FunctionDef)and n.name in('environment','labels','device_map','create_argv','validate_inspect')]
  exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-original-create-inspect','exec'),S.__dict__)
  S.__file__=str((P/'actual_loader/safety_host.py').resolve());S.MEM=64*2**30;S.RESERVE=int(8.5*2**30);S.HOST_MEM=2**29
  # The fixture's exact native algorithm environment is the old test seam.
  S.environment=lambda cpu,arm:{'TMPDIR':'/adakv-results','ASCEND_RT_VISIBLE_DEVICES':''};old.ns=S.__dict__
  return S,old
 def test_actual_create_inspect32_and_CPU8(self):
  S,t=self.safety();proof=CAP.prepare(S,S.c);self.assertEqual(proof['model_initial_GiB'],40.5)
  self.assertEqual(S.MEM,32*2**30);self.assertEqual(S.RESERVE,8*2**30);self.assertEqual(S.HOST_MEM,2**29)
  cpu=S.create_argv(t.e);self.assertEqual(cpu[cpu.index('--memory')+1],str(8*2**30));S.validate_inspect(t.inspect(),t.e)
  e=copy.deepcopy(t.e);e['arm']='candidate';e['guest_cpus']=[0,1,2,3]
  argv=S.create_argv(e);self.assertEqual(argv[argv.index('--memory')+1],str(32*2**30));self.assertEqual(argv[argv.index('--memory-swap')+1],str(32*2**30))
  x=t.inspect();x['Config']['Labels']=S.labels(e);x['HostConfig'].update(Memory=32*2**30,MemorySwap=32*2**30,NanoCpus=4*10**9,CpusetCpus='0,1,2,3',Devices=[dict(PathOnHost=a,PathInContainer=b,CgroupPermissions='rwm')for a,b in S.device_map().items()])
  S.validate_inspect(x,e)
  x['HostConfig']['Memory']=x['HostConfig']['MemorySwap']=48*2**30
  with self.assertRaises(ValueError):S.validate_inspect(x,e)
  with self.assertRaises(ValueError):CAP.prepare(S,S.c)
 def test_resources_capture32_and40point5_boundary(self):
  S,t=self.safety();CAP.prepare(S,S.c);available=[40.5*2**30]
  S.c.sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();S.c.write=lambda *a:{};S.c.output_scan=lambda *a:({},0)
  S.Path=lambda p:types.SimpleNamespace(read_text=lambda:'MemAvailable: %d kB\nMemTotal: 999999999 kB\nHugetlb: 0 kB\nSwapTotal: 0 kB\nSwapFree: 0 kB\n'%int(available[0]/1024))if str(p)=='/proc/meminfo'else Path(p)
  S.shutil=types.SimpleNamespace(disk_usage=lambda *a:types.SimpleNamespace(free=200*2**30));S.time=time;S.json=json;S.os=__import__('os');S.H=types.SimpleNamespace(cpu_view=lambda *a:{},daemon_view=lambda:{});S.cpu_admission=lambda *a:{};S.WORKSPACE=32*2**30
  raw=Path(S.__file__).read_bytes();tree=ast.parse(raw);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef)and n.name=='Controller');node=next(n for n in cls.body if isinstance(n,ast.FunctionDef)and n.name=='resources');original=textwrap.dedent('\n'.join(raw.decode().splitlines()[node.lineno-1:node.end_lineno]));exec(compile(original,'actual-original-resource-function','exec'),S.__dict__);S.Controller=type('Controller',(),{'resources':S.resources})
  class Owned:
   def __init__(self,leaf):self.out=leaf;self.cpu=None
   def create_native(self,model,cpu):return None
   def call(self,*a):return dict(stdout='{"NCPU":7}'),{}
   def rss(self):return{}
  sr=dict(path=S.__file__,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest());proof=R.install(S,Owned,S.c,sr)
  model=Owned(P/'candidate');model.resources=types.MethodType(S.Controller.resources,model)
  v=model.resources(initial=True);self.assertEqual(v['guest_budget_bytes'],32*2**30);self.assertEqual(v['ordinary_floor_bytes'],int(40.5*2**30));self.assertEqual(proof['actual_model_guest_GiB'],32)
  available[0]-=1024
  with self.assertRaises(ValueError):model.resources(initial=True)
  available[0]=16.5*2**30;cpu=Owned(P/'cpu-preflight');cpu.resources=types.MethodType(S.Controller.resources,cpu);self.assertEqual(cpu.resources(initial=True)['guest_budget_bytes'],8*2**30)
 def test_cgroup32_and_early_writer_check_scope(self):
  body=(P/'memory_observer.py').read_text();self.assertIn("else 32)*c.GIB",body);self.assertIn('oom',body);self.assertIn('memory.events',body)
  text=(P/'firstdecode_refs.py').read_text();self.assertLess(text.index('early.no_writers()'),text.index("value=seal.readset("))
  host=(P/'host_ticket.py').read_text();self.assertIn("S.MEM==32*base.GIB",host);self.assertIn("model_initial_GiB=40.5",host)

if __name__=='__main__':unittest.main()
