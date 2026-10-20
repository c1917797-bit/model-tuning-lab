"""Real CPU tensor transaction checks. Group replicas are software fixtures."""
import unittest
from types import SimpleNamespace as NS
import torch
import transaction as T
import test_tp_consensus as F
Group=F.Group
from model_entry import Owner

class Tests(unittest.TestCase):
 def fixture(self):
  o,b,p=F.Tests().fixture()
  p['decision']=NS(processed_nodes=(0,2),terminal=2,accepted_draft_nodes=(2,),
    emitted_tokens=(6,7),bonus_token=7,cancelled=False)
  return o,b,p
 def call(self,o,b,p,group=None,current_owner=None):
  return T.publish(torch,b,p,group=Group()if group is None else group,
    tokens=(4,5,6),current_owner=(lambda:o)if current_owner is None else current_owner)
 def test_all128_destinations_persist_and_strided_padding_stays_untouched(self):
  o,b,p=self.fixture();r=self.call(o,b,p)
  self.assertEqual(len(r['actual_applied']),128);self.assertEqual(r['next_length'],133)
  self.assertTrue(r['cache_published']);self.assertFalse(r['scheduler_committed'])
  for row in p['writes']:
   if row['kind']in('state','conv'):
    self.assertTrue(torch.equal(row['arena'][row['slot']],row['after']))
   else:
    ids=row['indices'];self.assertTrue(torch.equal(row['arena'][ids//128,ids%128],row['after']))
    self.assertEqual(int(torch.count_nonzero(row['arena'])),row['after'].numel())
 def test_decision_mismatch_fails_before_any_write(self):
  o,b,p=self.fixture();p['decision'].emitted_tokens=(7,)
  with self.assertRaises(ValueError):self.call(o,b,p)
  self.assertTrue(all(not torch.count_nonzero(x['arena'])for x in p['writes']))
 def test_failure_after_all_writes_restores_all128_preimages(self):
  class DisagreeAfterPublication(Group):
   calls=0
   def all_gather(self,row,dim):
    self.calls+=1;out=super().all_gather(row,dim)
    if self.calls==2:out[3,-4]+=1
    return out
  o,b,p=self.fixture();group=DisagreeAfterPublication()
  with self.assertRaises(ValueError):self.call(o,b,p,group=group)
  self.assertEqual(group.calls,2)
  self.assertTrue(all(not torch.count_nonzero(x['arena'])for x in p['writes']))
 def test_stale_owner_after_consensus_never_publishes(self):
  o,b,p=self.fixture();calls=[]
  def owner():
   calls.append(1)
   return o if len(calls)==1 else Owner(o.request,o.generation,0,132,1)
  with self.assertRaises(ValueError):self.call(o,b,p,current_owner=owner)
  self.assertTrue(all(not torch.count_nonzero(x['arena'])for x in p['writes']))
 def test_ack_requires_native_length_root_identity_and_is_one_shot(self):
  o,b,p=self.fixture();r=self.call(o,b,p);request=object()
  kwargs=dict(request_id=o.request,request_object=request,expected_request=request,
    actual_computed_tokens=133,actual_tokens_without_spec=134,
    actual_next_root=7,actual_live_ids=[o.request])
  for key,bad in (('actual_computed_tokens',134),('actual_next_root',6),
                  ('request_object',object()),('actual_live_ids',[])):
   with self.assertRaises(ValueError):T.acknowledge(r,**dict(kwargs,**{key:bad}))
  proof=T.acknowledge(r,**kwargs);self.assertTrue(proof['scheduler_committed'])
  self.assertFalse(r['scheduler_ack_pending'])
  with self.assertRaises(ValueError):T.acknowledge(r,**kwargs)
if __name__=='__main__':unittest.main()
