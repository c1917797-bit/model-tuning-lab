import unittest
from types import SimpleNamespace as NS
import torch
import tp_consensus as P
from model_entry import Owner,tensor_id
from native_seams import bits

class Group:
 world_size=4;rank_in_group=0
 def all_gather(self,row,dim):return row.repeat(4,1)

class Tests(unittest.TestCase):
 def fixture(self):
  o=Owner('actual',1,0,131,0);rows=[];bindings=[]
  for i in range(64):
   if i%4!=3:
    b=dict(index=i,kind='gdn',conv=torch.zeros(1,3,2),state=torch.zeros(1,2,2))
    for name in('conv','state'):
     a=b[name];rows.append(dict(layer=i,kind=name,arena=a,arena_identity=tensor_id(a),slot=0,before=a[0].clone(),after=torch.ones_like(a[0])))
   else:
    # A genuine strided ND page view: reshape would silently copy and would
    # not update the real backing storage. Test actual indexed writeback.
    backing=torch.zeros(3,129,1,256)
    key=backing[:,:128];value=torch.zeros_like(backing)[:,:128]
    b=dict(index=i,kind='fa',key=key,value=value,table=(2,0))
    for name in('key','value'):
     a=b[name];ids=torch.tensor([3,4]);before=a[ids//128,ids%128].clone()
     rows.append(dict(layer=i,kind=name,arena=a,arena_identity=tensor_id(a),indices=ids,before=before,after=torch.ones_like(before)))
   bindings.append(b)
  bridge=NS(bindings=bindings,N=NS(bits=bits))
  proposal=dict(schema='bole.actual-model-selected-path-staging/v1',owner=o,processed_nodes=(0,2),writes=rows,published=False,model_ready=False)
  return o,bridge,proposal
 def test_all128_real_destinations_written_then_restored_with_padding(self):
  o,b,p=self.fixture();r=P.temporary_writeback(torch,b,p,group=Group(),tokens=(4,5,6),current_owner=lambda:o)
  self.assertEqual(len(r['actual_applied']),128);self.assertFalse(r['scheduler_committed'])
  self.assertTrue(all(torch.equal(x,torch.ones_like(x))for x in r['actual_applied']))
  self.assertTrue(all(torch.equal(x,torch.zeros_like(x))for x in r['actual_restored']))
  self.assertTrue(all(not torch.count_nonzero(row['arena'])for row in p['writes']))
 def test_wrongrank_path_and_substitute_destination_rejected(self):
  o,b,p=self.fixture()
  class Bad(Group):
   def all_gather(self,row,dim):
    x=row.repeat(4,1);x[3,-4]+=1;return x
  with self.assertRaises(ValueError):P.temporary_writeback(torch,b,p,group=Bad(),tokens=(4,5,6),current_owner=lambda:o)
  row=p['writes'][0];row['arena']=row['arena'].clone();row['arena_identity']=tensor_id(row['arena'])
  with self.assertRaises(ValueError):P.temporary_writeback(torch,b,p,group=Group(),tokens=(4,5,6),current_owner=lambda:o)

if __name__=='__main__':unittest.main()
