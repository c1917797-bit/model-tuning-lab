"""Actual controller cleanup path + real fresh imports; software only, no HAL."""
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
import scratch_environment as S

class Repair2(unittest.TestCase):
 def test_real_startup_CLI_default_OFF_and_wrong_source_before_Torch(self):
  entry=P/'startup_smoke.py'
  z=subprocess.run([sys.executable,'-I','-B',str(entry)],capture_output=True,text=True,timeout=10)
  self.assertEqual(z.returncode,0,z.stderr);self.assertIs(json.loads(z.stdout)['enabled'],False)
  z=subprocess.run([sys.executable,'-I','-B',str(entry),'--execute','--controlled-failure',
      '--source-ref','{}','--stage-root','/missing','--output','/missing/STARTUP.json'],capture_output=True,text=True,timeout=10)
  self.assertNotEqual(z.returncode,0);self.assertNotIn('unrecognized arguments',z.stderr)
  self.assertNotIn('BOLE_FACTOR_R2_CONTROLLED_FAILURE_AFTER_REAL',z.stderr)

 def test_actual_private_environment_fresh_stdlib_Torch_dill_and_failure(self):
  with tempfile.TemporaryDirectory(prefix='factor-scratch-') as root:
   env=dict(os.environ,**S.prepare(Path(root)));env['TORCH_DEVICE_BACKEND_AUTOLOAD']='0'
   # Actual fresh interpreter and real modules, not a helper import mock. This
   # local positive is not a same-image/readonly-root Linux proof.
   code="import sys;sys.path.insert(0,sys.argv[1]);import scratch_environment as s;s.validate(sys.argv[2]);import torch,dill;assert dill.loads(dill.dumps(torch.tensor([1,2]))).tolist()==[1,2];print('real-Torch-dill-startup')"
   z=subprocess.run([sys.executable,'-I','-B','-c',code,str(P),root],env=env,capture_output=True,text=True,timeout=30)
   self.assertEqual(z.returncode,0,z.stderr);self.assertIn('real-Torch-dill-startup',z.stdout)
   bad=dict(env,HOME=str(Path(root)/'foreign'))
   z=subprocess.run([sys.executable,'-I','-B','-c',code,str(P),root],env=bad,capture_output=True,text=True,timeout=15)
   self.assertNotEqual(z.returncode,0);self.assertIn('sole-RW TMPDIR/HOME',z.stderr)
   with self.assertRaises(ValueError):S.prepare(Path(root))

 def instance(self,GE,root):
  obj=object.__new__(GE);cid='a'*64
  obj.output=Path(root);obj.root=P;obj.stage='numeric';obj.active=cid;obj.cards=[4];obj.secondary=[]
  env={'software':'exact-inspect-fixture-not-actual-CID'}
  mounts={root:(root,True)}
  a=types.SimpleNamespace(owner_ref={'sha256':'b'*64},guest_cpu=0,physical_device=4,current_mounts=mounts,current_env=env,current_cmd=['exact-fixture-child'])
  obj.a=a
  fixture=dict(Id=cid,Image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',
    State=dict(Running=False,Pid=0,ExitCode=3,OOMKilled=False),ExecIDs=None,
    Config=dict(Labels={'qwen36.owner':'bole-saved-FA-factor-MAIN','qwen36.stage':'numeric','deltalog-fresh-bridge.owner-source-sha256':'b'*64},
      Cmd=['exact-fixture-child'],Env=['software=exact-inspect-fixture-not-actual-CID']),
    HostConfig=dict(Privileged=False,ReadonlyRootfs=True,PidMode='',CapDrop=['ALL'],SecurityOpt=['no-new-privileges'],Memory=8*2**30,MemorySwap=8*2**30,
      NanoCpus=10**9,IpcMode='private',ShmSize=2*2**30,PidsLimit=512,CpusetCpus='0',NetworkMode='none',PortBindings={},
      Devices=[dict(PathOnHost='/dev/davinci4',PathInContainer='/dev/davinci0')]+[dict(PathOnHost=p,PathInContainer=p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc')],DeviceRequests=None,DeviceCgroupRules=None),
    Mounts=[dict(Destination=root,Source=root,RW=True)])
  calls=[]
  def io(argv,*args,**kw):
   calls.append(argv)
   return dict(exit_code=0,stdout=json.dumps([fixture])if argv[1]=='inspect'else'',stderr='')
  obj.run=io;obj.call=io;obj.observe=lambda *a,**kw:{'software_only_resource_observer':True}
  return obj,fixture,calls

 def test_real_GE_cleanup_after_controlled_child_failure_passes_original_cleanup_flag(self):
  import controller_probe as K
  GE=K.construct(False)
  with tempfile.TemporaryDirectory(prefix='factor-cleanup-') as root:
   obj,fixture,calls=self.instance(GE,root)
   # Actual unchanged069 cleanup -> original Lane.cleanup -> NEW inspect ->
   # original Lane.inspect(cleanup=True), with only Docker IO replaced.
   GE.cleanup(obj)
   self.assertIsNone(obj.active)
   self.assertEqual([a[1]for a in calls],['inspect','logs','stop','inspect'])
   saved=json.loads((Path(root)/'cleanup-verdict.json').read_bytes())
   self.assertTrue(saved['resource_release_verified']);self.assertEqual(saved['errors'],[])

 def test_cleanup_preserves_actual_OOM_private_root_and_CID_rejections(self):
  import controller_probe as K
  GE=K.construct(False)
  with tempfile.TemporaryDirectory(prefix='factor-reject-') as root:
   obj,x,calls=self.instance(GE,root);x['State']['OOMKilled']=True
   # Original cleanup inspection may observe an OOM without losing ability
   # to stop it. Original final cleanup still rejects OOM as a stage failure.
   GE.inspect(obj,obj.active,cleanup=True)
   with self.assertRaises(ValueError):GE.inspect(obj,obj.active)
   with self.assertRaises(ValueError):GE.cleanup(obj)
  for field,value in [('ReadonlyRootfs',False),('PidMode','host')]:
   with tempfile.TemporaryDirectory(prefix='factor-isolation-') as root:
    obj,x,calls=self.instance(GE,root);x['HostConfig'][field]=value
    with self.assertRaises(ValueError):GE.inspect(obj,obj.active,cleanup=True)

 def test_entire_repair_inverse_and_exact_old_CPU_identity(self):
  import preflight_reuse as R
  e=json.loads((P/'REPAIR2_EDITS.json').read_bytes())
  for name,row in e['changed'].items():
   b=(P/name).read_bytes();self.assertEqual(hashlib.sha256(b).hexdigest(),row['after']['sha256'])
   self.assertEqual(hashlib.sha256(row['before_body'].encode()).hexdigest(),row['before']['sha256'])
  self.assertEqual(R.SOURCE['sha256'],'0c9cfef77f5ecb709731d0ac08302c9c75f80ba21accc25b10274bcf3cb4d3b8')
  import preflight_reuse,common116 as C
  with self.assertRaisesRegex(ValueError,'exact actual R1'):preflight_reuse.validate(C,dict(preflight_reuse={}))

if __name__=='__main__':unittest.main()
