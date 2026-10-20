"""Complete segment coverage cannot be inferred from only a passing first frame."""
import copy
from pathlib import Path
import unittest
import sourceio as C
import g2_contract as G2
import g2_coverage as G
import g2_executor_proof as E
P=Path(__file__).resolve().parent


class CoverageTests(unittest.TestCase):
 def fixture(self):
  events=[];completed=[];requests=[]
  def event(kind,coverage):
   v=dict(sequence=len(events),kind=kind,coverage=coverage);events.append(v);return v
  for generation in(1,2):
   rid='request-%d'%generation;stream=[7];length=131
   item=dict(request=dict(request=rid,generation=generation,slot=0,length=131,version=0),steps=[])
   item['open_event']=event('open',dict(generation=generation,request=rid));acks=[]
   for ordinal in range(3):
    owner=dict(request=rid,generation=generation,slot=0,length=length,version=ordinal);emitted=[11+ordinal]
    se=event('step',dict(generation=generation,request=rid,ordinal=ordinal,length=length,emitted_tokens=emitted,processed_nodes=[0]))
    length+=1;stream+=emitted
    ack=None
    if ordinal<2:
     ack=dict(schema='bole.service-native-scheduler-ack/v1',request=rid,previous_version=ordinal,version=ordinal+1,computed_tokens=length,next_root=emitted[-1],scheduler_committed=True,whole_model_qualification=False,final_success=False);acks.append(ack)
    item['steps'].append(dict(owner=owner,emitted_tokens=emitted,stream_event=se,next_ack=ack,
        publication=dict(next_length=length,next_version=ordinal+1,emitted_tokens=emitted)))
   item.update(output_token_ids=stream,retirement=dict(schema='bole.service-owner-native-retirement/v1',request=rid,generation=generation,steps=3,next_counter_acknowledgements=acks,final_ack_by_retirement_pending=True,last_publication=dict(owner=owner,next_length=length,next_version=3,emitted_tokens=emitted)))
   item['retire_event']=event('retire',dict(generation=generation,request=rid,steps=3,output_tokens=4));requests.append(item)
   completed.append(dict(request=rid,generation=generation,output_token_ids=stream,steps=3,processed_tokens=3))
  event('close',dict(request_count=2,output_budget=4));return events,completed,requests
 def test_both_requests_entire_stream_covered_and_last_pending_retires(self):
  proof=G.audit(*self.fixture());self.assertEqual(proof['target_step_count'],6);self.assertTrue(proof['all_coverage'])
 def test_missing_later_step_fails_despite_first_step_pass(self):
  e,c,r=self.fixture();e.pop(2)
  with self.assertRaises((ValueError,KeyError,IndexError)):G.audit(e,c,r)
 def test_fabricated_final_counter_ACK_or_wrong_length_rejected(self):
  for mutate in('lastACK','length','emitted','version'):
   with self.subTest(mutate=mutate):
    e,c,r=copy.deepcopy(self.fixture())
    if mutate=='lastACK':r[0]['steps'][-1]['next_ack']={'invented':1}
    elif mutate=='length':e[2]['coverage']['length']+=1
    elif mutate=='emitted':c[0]['output_token_ids'][-1]+=1
    else:r[1]['steps'][1]['owner']['version']=0
    with self.assertRaises(ValueError):G.audit(e,c,r)
 def test_actual_executor_sources_prove_nonCPU_no_OMP_partition_and_supported_binding_OFF(self):
  local=P.parents[1]/'g1_review_v2/cpu3_runtime_sources'
  if local.is_dir():sources={k:C.ref(local/(k+'.py'))for k in E.INSTALLED}
  else:sources=C.obj(C.ref(P/'SOURCE_TEMPLATE.json'))['stream_executor_sources']
  proof=E.consume(sources)
  self.assertTrue(proof['four_workers_by_native_local_world_size']);self.assertTrue(proof['nonCPU_OMP_partition_bypassed'])
  self.assertFalse(proof['explicit_enable_cpu_binding']);self.assertFalse(proof['actual_runtime_launch_proven'])


if __name__=='__main__':unittest.main()
