"""Every long step must be consumed; final publication needs real retirement."""
import copy
from pathlib import Path
import sys
import unittest
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P))
import g2_coverage as COVER


class CoverageTests(unittest.TestCase):
 def fixture(self,accepted=False):
  events=[];rid='actual-fixture-request';stream=[7];length=131;steps=[];acks=[];ordinal=0
  def event(kind,coverage):
   value=dict(sequence=len(events),kind=kind,coverage=coverage);events.append(value);return value
  item=dict(request=dict(request=rid,generation=1,slot=0,length=131,version=0))
  item['open_event']=event('open',dict(generation=1,request=rid))
  while len(stream)<1024:
   count=min(2 if accepted else 1,1024-len(stream));emitted=[11+len(stream)+i for i in range(count)]
   nodes=[0,2]if count==2 else[0];owner=dict(request=rid,generation=1,slot=0,length=length,version=ordinal)
   se=event('step',dict(generation=1,request=rid,ordinal=ordinal,length=length,emitted_tokens=emitted,processed_nodes=nodes))
   stream+=emitted;length+=count;ack=None
   if len(stream)<1024:
    ack=dict(schema='bole.service-native-scheduler-ack/v1',request=rid,previous_version=ordinal,version=ordinal+1,
     computed_tokens=length,next_root=emitted[-1],scheduler_committed=True,whole_model_qualification=False,final_success=False);acks.append(ack)
   steps.append(dict(owner=owner,emitted_tokens=emitted,stream_event=se,next_ack=ack,
    publication=dict(next_length=length,next_version=ordinal+1,emitted_tokens=emitted)));ordinal+=1
  item.update(steps=steps,output_token_ids=stream,retirement=dict(schema='bole.service-owner-native-retirement/v1',request=rid,generation=1,
   steps=ordinal,next_counter_acknowledgements=acks,final_ack_by_retirement_pending=True,
   last_publication=dict(owner=owner,next_length=length,next_version=ordinal,emitted_tokens=emitted)))
  item['retire_event']=event('retire',dict(generation=1,request=rid,steps=ordinal,output_tokens=1024))
  completed=[dict(request=rid,generation=1,output_token_ids=stream,steps=ordinal,processed_tokens=1023)]
  event('close',dict(request_count=1,output_budget=1024));return events,completed,[item]
 def test_worst1023_steps_and_every_actual_counter_chain_reach_exact1024(self):
  result=COVER.audit(*self.fixture());self.assertEqual(result['target_step_count'],1023)
  self.assertTrue(result['all_coverage']);self.assertTrue(result['final_pending_by_retirement'])
 def test_child2_acceptance512_steps_and_final_root_only_keep_complete_coverage(self):
  e,c,r=self.fixture(True);result=COVER.audit(e,c,r)
  self.assertEqual(result['target_step_count'],512);self.assertEqual(e[-3]['coverage']['processed_nodes'],[0])
  self.assertEqual(len(c[0]['output_token_ids']),1024)
 def test_late_missing_or_replayed_segment_rejected_despite_first511_success(self):
  for kind in('omit','replay','version','computed'):
   e,c,r=copy.deepcopy(self.fixture())
   if kind=='omit':e.pop(900)
   elif kind=='replay':e[900]=copy.deepcopy(e[899])
   elif kind=='version':r[0]['steps'][899]['owner']['version']=898
   else:r[0]['steps'][899]['next_ack']['computed_tokens']+=1
   with self.subTest(kind=kind),self.assertRaises((ValueError,KeyError,IndexError)):COVER.audit(e,c,r)
 def test_output_truncation_fabricated_final_ack_or_missing_retirement_rejected(self):
  for kind in('truncate','counter','retire','future-growth'):
   e,c,r=copy.deepcopy(self.fixture(True))
   if kind=='truncate':c[0]['output_token_ids']=c[0]['output_token_ids'][:-1]
   elif kind=='counter':r[0]['steps'][-1]['next_ack']={'invented':True}
   elif kind=='retire':r[0]['retirement']['final_ack_by_retirement_pending']=False
   else:e[-3]['coverage']['length']=5199
   with self.subTest(kind=kind),self.assertRaises(ValueError):COVER.audit(e,c,r)


if __name__=='__main__':unittest.main()
