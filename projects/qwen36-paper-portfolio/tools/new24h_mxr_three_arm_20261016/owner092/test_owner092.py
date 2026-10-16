import ast,copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent
def load(name,file):
 s=importlib.util.spec_from_file_location(name,P/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
O=load('o086','owner092.py');C=load('c086','owned_cpu092.py')
DONOR=P.parent/'deltalog-split-scale-numeric-new24h-20261016-069-repair1'
class Controls(unittest.TestCase):
 def test_cold_off_and_help(self):
  for leaf in('owner092.py','owned_cpu092.py'):
   for flag in([],['--help']):
    r=subprocess.run([sys.executable,'-I','-B',str(P/leaf),*flag],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
 def test_same_unchanged_methods(self):
  actual=O.exact_methods(O.ref(DONOR/'host.py'));tree=ast.parse((DONOR/'host.py').read_bytes());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='main');ge=next(n for n in main.body if isinstance(n,ast.ClassDef)and n.name=='GE')
  self.assertEqual({x.name for x in actual},{'run','cleanup','cpu_observe'})
  for x in actual:self.assertEqual(ast.dump(x),ast.dump(next(n for n in ge.body if getattr(n,'name',None)==x.name)))
 def test_device_join_actual_path(self):
  cid='a'*64;plan={'sha256':'b'};argv=['python','-I'];p=dict(physical=5,namespace_pids=[99,1],start_ticks=88,cgroup='/docker/'+cid,argv=argv)
  fields=['R']+['0']*18+['88'];dv=dict(logical=0,physical_declared_by_plan=5,plan=plan,canary=[4.,5.],physical_proof_must_be_host_owned=True,cgroup='/docker/'+cid,pid=1,stat='1 (python) '+' '.join(fields));a=(dv,dict(owned_process_proofs=[p]),plan,cid,argv)
  self.assertEqual(O.device_proof(*a)['physical'],5)
  for k,v in(('physical',4),('start_ticks',89),('namespace_pids',[99,2]),('cgroup','foreign'),('argv',['foreign'])):
   z=copy.deepcopy(a);z[1]['owned_process_proofs'][0][k]=v
   with self.assertRaises(ValueError):O.device_proof(*z)
 def test_NPU_stage_exact_084_abi(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td)/'r';p.write_bytes(b'actual bytes');r=O.ref(p)
   v=dict(schema='mxr.prefill-three-arm-stage/v084',source={},authority={},plan={},primary=None,NPU=True,qualified=False,old_failures_unchanged=True,result=dict(rows=[dict(arm=a,raw=r)for a in('saved_candidate','native','cpu64_cast')],raw_bytes=3*r['bytes'],whole_correctness_qualified=False,candidate_anchor_bitwise=True,same_actual_A_G=True,intermediate_Hend_FP32_API_available=False))
   O.receive(v,{},{},{})
   for mutation in(lambda x:x['result'].update(candidate_anchor_bitwise=False),lambda x:x['result']['rows'].reverse(),lambda x:x.update(qualified=True),lambda x:x.update(schema='deltalog.native-prefill-counterfactual-stage/v079'),lambda x:x['result'].update(raw_bytes=0)):
    y=copy.deepcopy(v);mutation(y)
    with self.assertRaises(ValueError):O.receive(y,{},{},{})
 def test_CPU_stage_exact_084_abi(self):
  v=dict(schema='mxr.prefill-three-arm-stage/v084',source={},primary=None,NPU=False,qualified=False,old_failures_unchanged=True,result=dict(actual_saved_frame_extracted=True));C.receive_preflight(v,None,{},None)
  for key,value in(('NPU',True),('primary','failed'),('qualified',True),('schema','deltalog.native-prefill-cpu-preflight/v083')):
   z=copy.deepcopy(v);z[key]=value
   with self.assertRaises(ValueError):C.receive_preflight(z,None,{},None)
 def test_CPU_create_no_devices_8GiB_RO(self):
  v=C.create_argv(7,{'/source':('/source',False),'/out':('/adakv-results',True)},dict(ASCEND_RT_VISIBLE_DEVICES=''),'mxr-test',['-I','x.py'])
  self.assertNotIn('--device',v);self.assertIn('--read-only',v);self.assertEqual(v[v.index('--memory')+1],str(8*2**30));self.assertIn('type=bind,src=/source,dst=/source,readonly',v)
  self.assertEqual(C.docker_argv(['/usr/bin/docker','ps'])[:3],['/usr/bin/prlimit','--as=unlimited','--'])
  with self.assertRaises(ValueError):C.docker_argv(['/bin/sh','-c','docker ps'])
 def test_ref_and_output_failclosed(self):
  with tempfile.TemporaryDirectory()as td:
   p=Path(td);(p/'x').write_bytes(b'a');self.assertEqual(O.scan(p),1);self.assertEqual(C.output_scan(p),1);r=O.ref(p/'x');O.checked(r);r['sha256']='0'*64
   with self.assertRaises(ValueError):O.checked(r)
 def test_storage_not_DL_and_new_scope(self):
  for leaf in('owner092.py','owned_cpu092.py'):
   s=(P/leaf).read_text();self.assertNotIn('storage061.lock',s);self.assertNotIn('sealed_storage069.py',s);self.assertNotIn('committed_bytes',s);self.assertIn("OUTROOT=Path('/opt/host/vnf/austinov')",s);self.assertIn('>=32*GIB',s);self.assertIn('>=8.5*GIB',s)
 def test_CPUclosure_actual_stageRefs(self):
  s=(P/'owned_cpu092.py').read_text();self.assertIn("refs+=[stage_ref,*[r['raw']for r in stage['result']['rows']]]",s)
 def test_NPU_inspect_exact_original(self):
  d=O.load(O.ref(DONOR/'host.py'),'donor086');d.OWNER=O.OWNER
  a=type('A',(),dict(owner_ref={'sha256':'h'},guest_cpu=7,physical_device=5,current_mounts={'/out':('/out',True)},current_cmd=['p'],current_env={'ASCEND_RT_VISIBLE_DEVICES':'0'}))()
  h=dict(Privileged=False,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,IpcMode='private',ShmSize=2*2**30,PidsLimit=512,CpusetCpus='7',NetworkMode='none',PortBindings={},Devices=[dict(PathOnHost=x,PathInContainer=y)for x,y in [('/dev/davinci5','/dev/davinci0'),*[(p,p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc')]]])
  x=dict(Id='a'*64,Image=d.IMAGE,HostConfig=h,Config=dict(Labels={'qwen36.owner':O.OWNER,'qwen36.stage':'numeric','deltalog-fresh-bridge.owner-source-sha256':'h'},Cmd=['p'],Env=['ASCEND_RT_VISIBLE_DEVICES=0']),Mounts=[dict(Destination='/out',Source='/out',RW=True)],State=dict(OOMKilled=False))
  d.inspect_owned(x,'a'*64,'numeric',None,None,a)
  for mutate in(lambda z:z['HostConfig']['Devices'].pop(),lambda z:z['HostConfig'].update(Memory=9),lambda z:z.update(ExecIDs=['foreign']),lambda z:z['Mounts'][0].update(RW=False)):
   y=copy.deepcopy(x);mutate(y)
   with self.assertRaises(ValueError):d.inspect_owned(y,'a'*64,'numeric',None,None,a)
if __name__=='__main__':unittest.main()
