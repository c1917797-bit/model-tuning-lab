import inspect, os, unittest
from pathlib import Path
from unittest.mock import patch
import torch
import mtp_entry as M


class C:
 @staticmethod
 def ref(path): return str(Path(path).resolve())


class Model:
 def compute_logits(self, hidden): return hidden


class Proposer:
 method='mtp'
 def __init__(self): self.model=Model();self.original_calls=0
 def _propose(self,target_token_ids,target_positions,target_hidden_states,
              next_token_ids,common_attn_metadata,scheduler_output=None):
  self.original_calls+=1
  logits=self.model.compute_logits(target_hidden_states)
  result=logits.argmax(-1)
  self.model.compute_logits(torch.zeros_like(logits))
  self.result=result
  return result


def receive(*,proposer,record): proposer.received=record


class Tests(unittest.TestCase):
 def install(self,p):
  ref=C.ref(__file__)
  return M.install(p,torch,C,proposer_ref=ref,mtp_ref=ref,
                   receive=receive,receiver_ref=ref)
 def call(self,p):
  return p._propose(torch.tensor([4]),torch.tensor([127]),
                    torch.tensor([[0.,5.,3.,1.]]),torch.tensor([9]),object())
 def test_off(self):
  with patch.dict(os.environ,{'BOLE_MTP_TREE_CAPTURE_ENABLE':'0'}):
   self.assertIsNone(self.install(object()))
 def test_real_bound_hook_preserves_original_and_first_logits(self):
  with patch.dict(os.environ,{'BOLE_MTP_TREE_CAPTURE_ENABLE':'1'}):
   p=Proposer();restore=self.install(p);result=self.call(p)
   self.assertIs(result,p.result);self.assertEqual(p.original_calls,1)
   self.assertEqual(p.received['children'].tolist(),[[1,2]])
   self.assertEqual(p.received['root'].tolist(),[9])
   self.assertEqual(len(p.received['calls']),2)
   self.assertFalse(p.received['accepted_path_published'])
   restore();self.assertNotIn('_propose',p.__dict__)
   self.assertNotIn('compute_logits',p.model.__dict__)
 def test_wrong_source_before_install(self):
  with patch.dict(os.environ,{'BOLE_MTP_TREE_CAPTURE_ENABLE':'1'}):
   p=Proposer()
   with self.assertRaises(ValueError):
    M.install(p,torch,C,proposer_ref='wrong',mtp_ref=C.ref(__file__),
              receive=receive,receiver_ref=C.ref(__file__))
   self.assertNotIn('_propose',p.__dict__)
 def test_nonfinite_not_cleaned_into_valid_draft(self):
  with patch.dict(os.environ,{'BOLE_MTP_TREE_CAPTURE_ENABLE':'1'}):
   p=Proposer();restore=self.install(p)
   with self.assertRaises(ValueError):
    p._propose(torch.tensor([4]),torch.tensor([1]),
               torch.tensor([[float('nan'),0.]]),torch.tensor([9]),object())
   self.assertFalse(hasattr(p,'received'));restore()


if __name__=='__main__':unittest.main()
