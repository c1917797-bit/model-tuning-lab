"""Actual 0909 failure shape; no actual remote/container evidence fabricated."""
import copy,json,time,types,unittest
from unittest.mock import patch
import terminal_fence as F
def inspected(live):return dict(Id='79ed',ExecIDs=None,State=dict(Running=live,Pid=1362378 if live else 0,Status='running'if live else'exited',ExitCode=0,OOMKilled=False,FinishedAt=''if live else'2026-10-15T20:13:51.63161752Z'))
def example():
 return [({'path':'original-verdict'},dict(schema='deltalog-protected-ownership/v002',error="ValueError('actual container init included in top')",reasons=['protected ownership observation incomplete'],owned=[],protected=[dict(pid=123,present=True)],actual_owned_top=dict(exit_code=0,stdout='PID PPID COMMAND\n'),exact_owned_inspect=dict(stdout=json.dumps([inspected(True)]))))]
class EmptyTop(unittest.TestCase):
 def test_exact_failure_and_all_negative_branches(self):
  b=dict(pid=1362378,start_ticks=21233724);F.empty_top_exit(example(),b,inspected(True),'79ed')
  for name in('wrongerror','topfail','pidpresent','nonheader','owned','wrongCID','wronginit','exec','OOM','unrelatedfirst'):
   e=example();v=e[0][1]
   if name=='wrongerror':v['error']="PermissionError('denied')"
   if name=='topfail':v['actual_owned_top']['exit_code']=1
   if name=='pidpresent':v['actual_owned_top']['stdout']+='1362378 1 python\n'
   if name=='nonheader':v['actual_owned_top']['stdout']=''
   if name=='owned':v['owned']=[dict(pid=1362378)]
   if name in('wrongCID','wronginit','exec','OOM'):
    x=inspected(True)
    if name=='wrongCID':x['Id']='foreign'
    if name=='wronginit':x['State']['Pid']=999
    if name=='exec':x['ExecIDs']=['other']
    if name=='OOM':x['State']['OOMKilled']=True
    v['exact_owned_inspect']['stdout']=json.dumps([x])
   if name=='unrelatedfirst':e.append(({},dict(schema='deltalog.owned-top-child-first-observation/v031repair1')))
   with self.assertRaises(ValueError,msg=name):F.empty_top_exit(e,b,inspected(True),'79ed')
 def test_actual_recover_calls_postexit_protected_and_two_terminal_states(self):
  class Lane:
   active='79ed';a=types.SimpleNamespace(run_root='not-read')
   def __init__(self):self.inspects=0;self.observed=0
   def inspect(self,cid):self.inspects+=1;return dict(actual=self.inspects),inspected(False)
   def observe(self,*args,**kw):self.observed+=1;return dict(owned_process_proofs=[])
  lane=Lane();error=ValueError("owned protected0-3 boundary or incomplete proof: ['protected ownership observation incomplete']")
  with patch.object(F,'new_evidence',return_value=example()):
   F.recover(lane,error,dict(pid=1362378,start_ticks=21233724),inspected(True),{},lambda v:None,time.monotonic()+2)
  self.assertEqual((lane.inspects,lane.observed),(2,1))
  lane.observe=lambda *a,**kw:(_ for _ in()).throw(ValueError('protected boundary failed'))
  with patch.object(F,'new_evidence',return_value=example()):
   with self.assertRaisesRegex(ValueError,'protected boundary'):F.recover(lane,error,dict(pid=1362378,start_ticks=21233724),inspected(True),{},lambda v:None,time.monotonic()+2)
if __name__=='__main__':unittest.main()
