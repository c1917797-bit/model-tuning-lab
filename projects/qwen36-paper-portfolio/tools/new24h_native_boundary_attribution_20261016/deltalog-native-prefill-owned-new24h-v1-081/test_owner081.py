import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('owner081',P/'owner081.py');O=importlib.util.module_from_spec(s);s.loader.exec_module(O)
DONOR=Path('C:/Users/Huawei/AppData/Local/Temp/deltalog-split-scale-numeric-new24h-20261016-069-repair1')
class Test(unittest.TestCase):
 def test_off(self):
  p=subprocess.run([sys.executable,'-I','-B',str(P/'owner081.py')],capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertFalse(json.loads(p.stdout)['enabled'])
 def test_methods(self):
  methods=O.exact_methods(O.ref(DONOR/'host.py'));self.assertEqual({m.name for m in methods},{'run','cleanup','cpu_observe'})
  tree=ast.parse((DONOR/'host.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');ge=next(n for n in main.body if isinstance(n,ast.ClassDef)and n.name=='GE')
  for m in methods:self.assertEqual(ast.dump(m),ast.dump(next(n for n in ge.body if getattr(n,'name',None)==m.name)))
  class Base:
   def run(self,*a):return 'actual-super-path'
   def cleanup(self):return 'actual-cleanup-path'
  ns=dict(Base=Base,time=__import__('time'),need=O.need)
  node=ast.ClassDef(name='GE',bases=[ast.Name(id='Base',ctx=ast.Load())],keywords=[],body=methods,decorator_list=[])
  exec(compile(ast.fix_missing_locations(ast.Module(body=[node],type_ignores=[])),'actual-donor-method-frontdoor','exec'),ns)
  lane=ns['GE']();self.assertEqual(lane.run(['x']),'actual-super-path');self.assertEqual(lane.cleanup(),'actual-cleanup-path');self.assertIsNone(lane.cleanup_until)
 def device(self):
  cid='a'*64;plan={'sha256':'b'};argv=['python','-I'];p=dict(physical=5,namespace_pids=[99,1],start_ticks=88,cgroup='/docker/'+cid,argv=argv)
  fields=['R']+['0']*18+['88'];dv=dict(logical=0,physical_declared_by_plan=5,plan=plan,canary=[4.,5.],physical_proof_must_be_host_owned=True,cgroup='/docker/'+cid,pid=1,stat='1 (python) '+' '.join(fields))
  return dv,dict(owned_process_proofs=[p]),plan,cid,argv
 def test_real_handshake(self):
  a=self.device();self.assertEqual(O.device_proof(*a)['physical'],5)
  for key,value in [('physical',4),('namespace_pids',[99,2]),('start_ticks',89),('cgroup','foreign'),('argv',['wrong'])]:
   b=copy.deepcopy(a);b[1]['owned_process_proofs'][0][key]=value
   with self.assertRaises(ValueError):O.device_proof(*b)
  a=self.device();a[1]['owned_process_proofs']=[];self.assertIsNone(O.device_proof(*a))
 def test_actual_inspect(self):
  d=O.load(O.ref(DONOR/'host.py'),'donor');d.OWNER=O.OWNER
  a=type('A',(),dict(owner_ref={'sha256':'h'},guest_cpu=7,physical_device=5,current_mounts={'/out':('/out',True)},current_cmd=['p'],current_env={'ASCEND_RT_VISIBLE_DEVICES':'0'}))()
  h=dict(Privileged=False,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,IpcMode='private',ShmSize=2*2**30,PidsLimit=512,CpusetCpus='7',NetworkMode='none',PortBindings={},Devices=[dict(PathOnHost=x,PathInContainer=y)for x,y in [('/dev/davinci5','/dev/davinci0'),*[(p,p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc')]]])
  x=dict(Id='a'*64,Image=d.IMAGE,HostConfig=h,Config=dict(Labels={'qwen36.owner':O.OWNER,'qwen36.stage':'numeric','deltalog-fresh-bridge.owner-source-sha256':'h'},Cmd=['p'],Env=['ASCEND_RT_VISIBLE_DEVICES=0']),Mounts=[dict(Destination='/out',Source='/out',RW=True)],State=dict(OOMKilled=False))
  d.inspect_owned(x,'a'*64,'numeric',None,None,a)
  for mutate in [lambda z:z['HostConfig']['Devices'].pop(),lambda z:z['HostConfig'].update(Memory=9),lambda z:z.update(ExecIDs=['foreign']),lambda z:z['Mounts'][0].update(RW=False),lambda z:z['Config'].update(Env=['ASCEND_RT_VISIBLE_DEVICES=5'])]:
   y=copy.deepcopy(x);mutate(y)
   with self.assertRaises(ValueError):d.inspect_owned(y,'a'*64,'numeric',None,None,a)
 def test_scans_and_refs(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);(p/'x').write_bytes(b'a');self.assertEqual(O.scan(p),1);r=O.ref(p/'x');O.checked(r);r['sha256']='0'*64
   with self.assertRaises(ValueError):O.checked(r)
 def test_stage(self):
  v=dict(schema='deltalog.native-prefill-counterfactual-stage/v079',source={},authority={},plan={},primary=None,NPU=True,qualified=False,old160_failure_unchanged=True,result=dict(rows=[],raw_bytes=0,whole_correctness_qualified=False,native_baseline_postconv_inputs_were_captured=False))
  with self.assertRaises(ValueError):O.receive(v,{},{},{})
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'raw';p.write_bytes(b'real diagnostic bytes');v['result']['rows']=[dict(raw=O.ref(p))for _ in range(6)];O.receive(v,{},{},{})
   v['qualified']=True
   with self.assertRaises(ValueError):O.receive(v,{},{},{})
 def test_patch_inverse(self):
  patch=O.load(O.ref(DONOR/'patch_scope.py'),'patch');raw=(DONOR/'scope_adapter.py').read_bytes();changed=patch.transform(raw)
  self.assertEqual(changed.replace(patch.AFTER,patch.BEFORE),raw.decode())
if __name__=='__main__':unittest.main()
