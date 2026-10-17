import ast,hashlib,importlib.util,json,os,subprocess,sys,tempfile,types,unittest
from pathlib import Path
import recovery_io as C,plan as R,owner
P=Path(__file__).resolve().parent
class Tests(unittest.TestCase):
 def test_actual_path_bytes_fault_adapter_full_IO_wrongbytes_outside_no_mutation(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory()as td:
   root=Path(td);full=C.write(root/'HOST-FIRST-FAULT.json',dict(schema='software_ref_shape_control_not_actual_owner'));legacy=dict(path=full['path'],bytes=full['bytes']);original=dict(legacy)
   with patch.object(R,'ROOT',root):
    self.assertEqual(R.first_fault_ref(C,legacy),full);self.assertEqual(legacy,original)
    for bad in(dict(legacy,bytes=legacy['bytes']+1),dict(legacy,path=str(root/'elsewhere.json')),dict(legacy,sha256=full['sha256'])):
     with self.assertRaises(ValueError):R.first_fault_ref(C,bad)
   self.assertEqual(legacy,original)
 def test_actual_saved_terminal_failed_not_success_unknown_hash_source(self):
  r=C.ref(P/'evidence/BOLE_R17_TERMINAL_OPERATION_FINAL.json');v=R.terminal(C,r)
  self.assertEqual(v['operation']['result']['record']['exitCode'],3)
  with self.assertRaises(ValueError):R.terminal(C,dict(r,sha256='0'*64))
  with tempfile.TemporaryDirectory()as td:
   for change in('exit','found','stdout'):
    copy=json.loads(json.dumps(v));s=copy;record=s['operation']['result']['record']
    if change=='exit':record['exitCode']=0
    elif change=='found':s['found']=False
    else:record['stdout']=''
    ref=C.write(Path(td)/(change+'.json'),copy)
    with self.assertRaises(ValueError):R.terminal(C,ref)
 def test_actual_typed_command_full_cold_parse_missing_ref_and_no_output(self):
  cmd=json.loads((P/'COMMANDS.json').read_bytes())['bind']
  with tempfile.TemporaryDirectory()as td:
   absent=dict(path=str(Path(td)/'ACTUAL_TERMINAL_MISSING.json'),bytes=0,sha256='0'*64)
   argv=[sys.executable,'-I','-B',str(P/'bind.py'),*cmd[4:]];argv[argv.index('--template-ref')+1]=json.dumps(C.ref(P/'SOURCE_TEMPLATE.json'));argv[argv.index('--terminal-ref')+1]=json.dumps(absent)
   r=subprocess.run(argv,capture_output=True,text=True,timeout=10);self.assertNotEqual(r.returncode,0);self.assertIn('ordinary exact evidence bytes',r.stderr);self.assertNotIn('unrecognized arguments',r.stderr)
  self.assertFalse((P/'SOURCE_BOUND.json').exists());self.assertFalse((P/'RECOVERY_PLAN.json').exists())
 def test_owner_original_whole_inverse_safety_create_Devices_none_and_memory8(self):
  row=json.loads((P/'DIAGNOSTIC_OWNER_EDITS.json').read_bytes());actual=(P/'owner.py').read_text();self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(),row['after']['sha256'])
  for e in reversed(row['edits']):self.assertEqual(actual.count(e['after']),1);actual=actual.replace(e['after'],e['before'])
  self.assertEqual(actual.encode(),(P/'historical/owner.py').read_bytes());self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(),row['donor']['sha256'])
  args=owner.create_argv(144,{'/own/output':('/own/output',True)},{'ASCEND_RT_VISIBLE_DEVICES':''},'software', ['-I','-B','recover.py'])
  self.assertNotIn('--device',args);self.assertNotIn('--gpus',args);self.assertEqual(args[args.index('--memory')+1],str(8*2**30));self.assertEqual(args[args.index('--memory-swap')+1],str(8*2**30));self.assertIn('--read-only',args)
  requested=owner.docker_argv(['/usr/bin/docker','ps']);self.assertEqual(requested[:4],['/usr/bin/prlimit','--as=unlimited','--','/usr/bin/docker'])
  with self.assertRaises(ValueError):owner.docker_argv(['/bin/sh','-c','true'])
  cid='a'*64;mounts={'/own/output':('/own/output',True),'/source/leaf':('/source/leaf',False)};env={'ASCEND_RT_VISIBLE_DEVICES':''};child=['-I','-B','/source/recover.py','--output','/own/output']
  x=dict(Id=cid,Image=owner.IMAGE,Name='/software',ExecIDs=None,Config=dict(Labels={'qwen36.owner':owner.OWNER},Env=['ASCEND_RT_VISIBLE_DEVICES='],Entrypoint=['/bin/bash'],Cmd=['-c',owner.CANN_WRAPPER,'boletree116',owner.PY,*child]),HostConfig=dict(Privileged=False,ReadonlyRootfs=True,CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],PidMode='private',Memory=8*2**30,MemorySwap=8*2**30,NanoCpus=10**9,CpusetCpus='144',PidsLimit=256,IpcMode='private',NetworkMode='none',LogConfig={'Type':'none'},Devices=[],DeviceRequests=[],DeviceCgroupRules=[],PortBindings={}),Mounts=[dict(Source=k,Destination=v[0],RW=v[1])for k,v in mounts.items()],State=dict(OOMKilled=False))
  self.assertIs(owner.inspect_owned(x,cid,mounts,env,144,'software',child),x)
  for key,value in(('Devices',[{'PathOnHost':'/dev/davinci4'}]),('PidMode','host'),('Memory',16*2**30),('MemorySwap',16*2**30)):
   bad=json.loads(json.dumps(x));bad['HostConfig'][key]=value
   with self.assertRaises(ValueError):owner.inspect_owned(bad,cid,mounts,env,144,'software',child)
 def test_diagnostic_ABI_never_promotes_original_numeric_failure(self):
  s=(P/'recover.py').read_text();self.assertIn("D.diagnose(t,raw)",s);self.assertIn("ranks_completed=4",s)
  for v in('qualified=False','original_owner_pass=False','original_numeric_failures_unchanged=True','whole_numerical_qualified=False','model_ready=False'):self.assertIn(v,s)
  self.assertNotIn('set_device',s);self.assertNotIn('t.ops',s)
 def test_all_actual_cold_defaultOFF_entries_source_layout(self):
  for name in('entry.py','bind.py','owner.py','recover.py'):
   r=subprocess.run([sys.executable,'-I','-B',str(P/name)],capture_output=True,text=True,timeout=10);self.assertEqual(r.returncode,0,(name,r.stderr));self.assertIs(json.loads(r.stdout)['enabled'],False)
  tree=ast.parse((P/'owner.py').read_bytes());self.assertNotIn('--device',(P/'owner.py').read_text());self.assertIn('label=model-tuning-lab.owner',(P/'owner.py').read_text());self.assertIn("mounts[str(a.output)]=(str(a.output),True)",(P/'owner.py').read_text())
if __name__=='__main__':unittest.main()
