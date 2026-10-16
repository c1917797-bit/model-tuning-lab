import copy,importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P));import owned_cpu as O
class Tests(unittest.TestCase):
 def test_docker_wrapper_exact_command_and_negative(self):
  for args in ([O.DOCKER,'ps','--no-trunc'],[O.DOCKER,'start','--attach','a'*64],[O.DOCKER,'stop','--time','10','a'*64]):
   self.assertEqual(O.docker_argv(args),['/usr/bin/prlimit','--as=unlimited','--',*args])
  for args in ([],['docker','ps'],['/usr/bin/python3','-c','pass'],['/usr/bin/prlimit','--as=unlimited','--',O.DOCKER,'ps']):
   with self.assertRaises(ValueError):O.docker_argv(args)
 def test_all_real_Docker_entries_wrapped_and_failure_retained(self):
  import ast
  tree=ast.parse((P/'owned_cpu.py').read_bytes());calls=[n for n in ast.walk(tree)if isinstance(n,ast.Call)and isinstance(n.func,ast.Attribute)and isinstance(n.func.value,ast.Name)and n.func.value.id=='subprocess'and n.func.attr in('run','Popen')]
  self.assertEqual(len(calls),2);self.assertEqual({n.args[0].id for n in calls},{'argv','attach_argv'})
  text=(P/'owned_cpu.py').read_text();self.assertIn('argv=docker_argv(args)',text);self.assertIn("attach_argv=docker_argv([DOCKER,'start','--attach',cid])",text);self.assertIn('MAIN_DOCKER_CLIENT_FAILURE',text);self.assertIn('stderr=x.stderr',text);self.assertIn('file=sys.stderr,flush=True',text)
 def test_cold_real_CLI(self):
  for n in('owned_cpu.py','diagnose.py','cpu_entry.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/n)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0);self.assertNotIn('Traceback',r.stderr)
  r=subprocess.run([sys.executable,'-I','-B',str(P/'owned_cpu.py'),'--execute','--unknown'],capture_output=True,text=True,timeout=10);self.assertNotEqual(r.returncode,0);self.assertIn('unrecognized',r.stderr)
 def test_actual_create_and_inspect_contract(self):
  mounts={'/sources/diagnose.py':('/sources/diagnose.py',False),'/new/output':('/adakv-results',True)};env={'ASCEND_RT_VISIBLE_DEVICES':'','TORCH_DEVICE_BACKEND_AUTOLOAD':'0'};child=['-I','-B','/sources/diagnose.py'];cid='a'*64;name='owned074-test'
  a=O.create_argv(7,mounts,env,name,child);self.assertIn(O.PY,a);self.assertNotIn('--device',a);self.assertEqual(a[a.index('--memory')+1],str(8*O.GIB));self.assertEqual(a[a.index('--network')+1],'none');self.assertIn('--read-only',a)
  x=dict(Id=cid,Image=O.IMAGE,Name='/'+name,ExecIDs=None,HostConfig=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*O.GIB,MemorySwap=8*O.GIB,NanoCpus=10**9,CpusetCpus='7',PidsLimit=256,IpcMode='private',NetworkMode='none',LogConfig={'Type':'none'},Devices=[],DeviceRequests=[],DeviceCgroupRules=[],PortBindings={}),Config=dict(Labels={'qwen36.owner':O.OWNER},Env=[k+'='+v for k,v in env.items()],Entrypoint=[O.PY],Cmd=child),Mounts=[dict(Source=s,Destination=d,RW=rw)for s,(d,rw)in mounts.items()],State={'OOMKilled':False})
  self.assertIs(O.inspect_owned(x,cid,mounts,env,7,name,child),x)
  for mutation in('device','swap','python','mount','oom','network'):
   y=copy.deepcopy(x)
   if mutation=='device':y['HostConfig']['Devices']=[{'PathOnHost':'/dev/davinci4'}]
   if mutation=='swap':y['HostConfig']['MemorySwap']=16*O.GIB
   if mutation=='python':y['Config']['Entrypoint']=['/usr/bin/python3']
   if mutation=='mount':y['Mounts'][0]['RW']=True
   if mutation=='oom':y['State']['OOMKilled']=True
   if mutation=='network':y['HostConfig']['NetworkMode']='host'
   with self.assertRaises(ValueError):O.inspect_owned(y,cid,mounts,env,7,name,child)
 def test_exact_input_and_no_source_mutation(self):
  self.assertEqual(O.SOURCE['bytes'],52969);self.assertEqual(O.PRODUCER['bytes'],100542)
  t=(P/'owned_cpu.py').read_text();self.assertNotIn('storage.reserve(',t);self.assertIn('seal.install(storage',t)
  self.assertIn("'committed_bytes']+CAP<=80*GIB",t);self.assertIn("'filesystem_free_bytes']>=101*GIB",t);self.assertIn("'prepared_template'",t)
  with tempfile.TemporaryDirectory()as td:
   q=Path(td)/'small';q.write_bytes(b'correct');r=O.ref(q);self.assertEqual(O.checked(r),q);q.write_bytes(b'wrong')
   with self.assertRaises(ValueError):O.checked(r)
if __name__=='__main__':unittest.main()
