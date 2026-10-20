"""Selection oracle/partial-schedule checks; no device or model execution."""
import unittest
from model_entry import Owner
from acceptance import select
from tree_metadata111 import Tree
import eligibility as E
class Tests(unittest.TestCase):
 def test_three_admitted_rows_choose_root_and_both_children(self):
  o=Owner('r',1,0,131,0);tokens=(4,5,6)
  for targets,terminal,emitted in(((9,10,11),0,(9,)),((5,10,11),1,(5,10)),((6,10,11),2,(6,11))):
   d=E.decide(o,tokens,targets,3,remaining_output_tokens=3)
   self.assertEqual(d.terminal,terminal);self.assertEqual(d.emitted_tokens,emitted)
   self.assertEqual(len(d.processed_nodes),len(d.emitted_tokens))
 def test_truncated_schedule_never_accepts_unadmitted_child(self):
  o=Owner('r',1,0,131,0)
  self.assertEqual(E.decide(o,(4,5,6),(5,),1,remaining_output_tokens=3).processed_nodes,(0,))
  self.assertEqual(E.decide(o,(4,5,6),(6,9),2,remaining_output_tokens=3).processed_nodes,(0,))
  self.assertEqual(E.decide(o,(4,5,6),(5,9),2,remaining_output_tokens=3).processed_nodes,(0,1))
 def test_native_compaction_preserves_root_and_reorders_only_second_child(self):
  self.assertEqual(E.native_compaction_order(3,2),(0,2,1))
  self.assertEqual(E.native_compaction_order(3,1),(0,1,2))
  self.assertEqual(E.native_compaction_order(1,0),(0,))
  with self.assertRaises(ValueError):E.native_compaction_order(2,2)
 def test_final_native_output_budget_requires_root_only(self):
  o=Owner('r',1,0,131,0)
  for targets in((5,10,11),(6,10,11)):
   d=E.decide(o,(4,5,6),targets,3,remaining_output_tokens=1)
   self.assertEqual(d.processed_nodes,(0,));self.assertEqual(d.emitted_tokens,(targets[0],))
  for bad in(0,-1,True):
   with self.assertRaises(ValueError):E.decide(o,(4,5,6),(5,10,11),3,remaining_output_tokens=bad)
 def test_duplicate_children_bad_counts_and_noninteger_ids_rejected(self):
  o=Owner('r',1,0,131,0)
  for tokens,nexts,count in(((4,5,5),(5,),1),((4,5,6),(5,),0),((4,5,6),(5,),2),((4,5,6),(True,),1)):
   with self.assertRaises(ValueError):E.decide(o,tokens,nexts,count,remaining_output_tokens=3)
if __name__=='__main__':unittest.main()
