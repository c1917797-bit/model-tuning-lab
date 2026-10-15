import copy,importlib.util,json,pathlib,sys,tempfile,types,unittest
from unittest import mock
P=pathlib.Path(__file__).resolve().parent
S=importlib.util.spec_from_file_location('fence',P/'terminal_fence.py');F=importlib.util.module_from_spec(S);S.loader.exec_module(F)
class Fence(unittest.TestCase):
 def example(self):
  a=['R','1']+['0']*17+['99','0','0']
  stat='42 (python) '+' '.join(a)
  first=dict(status='present',pid=42,start_ticks=99,cgroup='0::/\n',proc_fields=dict(stat=dict(text=stat),stat_after=dict(text=stat),cmdline=dict(bytes=0)))
  return [({'path':'v'},dict(schema='deltalog-protected-ownership/v002',error=F.EXACT_ERROR,reasons=['protected ownership observation incomplete'])),({'path':'f'},dict(schema='deltalog.owned-top-child-first-observation/v031repair1',pid=42,first=first,classification='unresolved-not-retired',resource_release_authority=False))]
 def test_exact_bound_init_evidence(self):
  e=self.example();F.exiting_init(e,dict(pid=42,start_ticks=99),dict(State=dict(Running=True,Pid=42)))
  for mut in('unknown','reuse','live','cmd','foreignCG','othererror'):
   b=copy.deepcopy(e)
   if mut=='unknown':b[1][1]['first']['status']='missing'
   if mut=='reuse':b[1][1]['first']['start_ticks']=100
   if mut=='live':b[1][1]['first']['proc_fields']['stat']['text']=b[1][1]['first']['proc_fields']['stat']['text'].rsplit(' ',1)[0]+' 1'
   if mut=='cmd':b[1][1]['first']['proc_fields']['cmdline']['bytes']=10
   if mut=='foreignCG':b[1][1]['first']['cgroup']='0::/foreign'
   if mut=='othererror':b[0][1]['error']="PermissionError('denied')"
   with self.assertRaises(ValueError,msg=mut):F.exiting_init(b,dict(pid=42,start_ticks=99),dict(State=dict(Running=True,Pid=42)))
 def test_terminal_flags_and_live_refused(self):
  x=dict(Id='owned',ExecIDs=None,State=dict(Running=False,Pid=0,Status='exited',ExitCode=0,OOMKilled=False))
  F.state(x,'owned')
  for name in('nonzero','OOM','exec','live','foreignCID'):
   b=copy.deepcopy(x)
   if name=='nonzero':b['State']['ExitCode']=1
   if name=='OOM':b['State']['OOMKilled']=True
   if name=='exec':b['ExecIDs']=['foreignexec']
   if name=='live':b['State'].update(Running=True,Pid=42,Status='running')
   if name=='foreignCID':b['Id']='foreign'
   with self.assertRaises(ValueError,msg=name):F.state(b,'owned')
 def test_postexit_observer_failure_not_swallowed(self):
  def fail(*a,**kw):raise ValueError('foreign protected actual proof')
  x=dict(Id='owned',ExecIDs=None,State=dict(Running=False,Pid=0,Status='exited',ExitCode=0,OOMKilled=False))
  lane=types.SimpleNamespace(active='owned',observe=fail)
  import time
  with self.assertRaisesRegex(ValueError,'foreign protected'):F.postexit(lane,{},x,dict(pid=42),lambda x:None,time.monotonic()+2)
 def test_quiescent_refs_require_stable_bytes(self):
  with tempfile.TemporaryDirectory()as d:
   p=pathlib.Path(d)/'STAGE_RESULT.json';p.write_text('{}');calls=[]
   def r(path):
    calls.append(path);v=F.ref(path)
    if len(calls)==1:p.write_text('{"changed":1}')
    return v
   with self.assertRaises(ValueError):F.quiescent(pathlib.Path(d),False,r,lambda x:{})
 def test_actual_recovery_body_and_live_timeout(self):
  import time
  def snapshot(live):return dict(Id='owned',ExecIDs=None,State=dict(Running=live,Pid=42 if live else 0,Status='running'if live else'exited',ExitCode=0,OOMKilled=False))
  calls=[];frames=[]
  class Lane:
   active='owned';a=types.SimpleNamespace(run_root=P)
   def inspect(self,cid):
    calls.append(cid);return dict(actual_call=len(calls)),snapshot(len(calls)==1)
   def observe(self,*args,**kw):return dict(owned_process_proofs=[])
  original=ValueError("owned protected0-3 boundary or incomplete proof: ['protected ownership observation incomplete']")
  with mock.patch.object(F,'new_evidence',return_value=self.example()):
   _,x=F.recover(Lane(),original,dict(pid=42,start_ticks=99),snapshot(True),{},frames.append,time.monotonic()+2)
   self.assertFalse(x['State']['Running']);self.assertEqual(len(calls),3);self.assertTrue(frames)
  class Live(Lane):
   def inspect(self,cid):return {},snapshot(True)
  with mock.patch.object(F,'new_evidence',return_value=self.example()):
   with self.assertRaises(ValueError):F.recover(Live(),original,dict(pid=42,start_ticks=99),snapshot(True),{},frames.append,time.monotonic()+.01)
  class Reused(Lane):
   def inspect(self,cid):
    x=snapshot(True);x['State']['Pid']=99;return {},x
  with mock.patch.object(F,'new_evidence',return_value=self.example()):
   with self.assertRaises(ValueError):F.recover(Reused(),original,dict(pid=42,start_ticks=99),snapshot(True),{},frames.append,time.monotonic()+2)
if __name__=='__main__':unittest.main()
