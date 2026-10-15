import copy,json,unittest
import provenance as P
from test_empty_top_exit import example,inspected
class Provenance(unittest.TestCase):
 def values(self):
  sr={'source':'fixture'};pr={'producer':'fixture'}
  failed=dict(schema='deltalog.diagnostic-owned-host/v035',target_source=sr,primary="ValueError(\"owned protected0-3 boundary or incomplete proof: ['protected ownership observation incomplete']\")",bridge_primitive_gate_pass=False,stopped_retained=True,secondary=[])
  producer=dict(source=sr,primary=None,steps=16,records=[{}]*40,NPU=True);stage=dict(actual_result=pr,producer_exit=0,observation_complete=True)
  cleanup=dict(resource_release_verified=True,stopped=True,retained=True,errors=[],secondary_guard_cleanup=[],unresolved_active_cid=None)
  verdict=example()[0][1];x=json.loads(verdict['exact_owned_inspect']['stdout'])[0];x['Id']=P.CID;verdict['exact_owned_inspect']['stdout']=json.dumps([x])
  devices=[dict(PathOnHost=a,PathInContainer=b)for a,b in[('/dev/davinci5','/dev/davinci0'),*((p,p)for p in('/dev/davinci_manager','/dev/devmm_svm','/dev/hisi_hdc'))]]
  terminal=inspected(False);terminal.update(Id=P.CID,Image='sha256:660ce23a83574fdcd28ba126b07615829c06770c06fbdf6533f03cc4d90acdb1',HostConfig=dict(Devices=devices))
  wire=dict(exit_code=0,stdout=json.dumps([terminal]));arm=dict(pid=1362378,start_ticks=21233724,cgroup='0::/'+P.CID)
  return[failed,producer,stage,cleanup,verdict,arm,wire,copy.deepcopy(wire),sr,pr]
 def test_actual_provenance_flow_and_original_failure_not_promoted(self):
  v=self.values();result=P.validate(*v);self.assertFalse(result['original_numerical_qualified']);self.assertFalse(result['NPU_reexecuted']);self.assertIsNotNone(v[0]['primary'])
  for index,key,bad in[(0,'primary',None),(1,'primary','numeric fail'),(2,'producer_exit',3),(3,'errors',['failed']),(5,'start_ticks',1)]:
   v=self.values();v[index][key]=bad
   with self.assertRaises(ValueError):P.validate(*v)
 def test_two_terminal_states_and_mapping_cannot_drift(self):
  for kind in('state','map','OOM'):
   v=self.values();x=json.loads(v[7]['stdout'])[0]
   if kind=='state':x['State']['FinishedAt']='different'
   if kind=='map':x['HostConfig']['Devices'][0]['PathOnHost']='/dev/davinci0'
   if kind=='OOM':x['State']['OOMKilled']=True
   v[7]['stdout']=json.dumps([x])
   with self.assertRaises(ValueError):P.validate(*v)
if __name__=='__main__':unittest.main()
