"""No framework import and no runtime/NPU execution."""
import unittest
from contract import (Row, plan, verify_native, LeaseBook, Unsupported,
                      block_accesses, verify_live_accesses)

def row(rid, slot, q, done, prompt=8, gen=1):
    return Row(rid, slot, q, done, prompt, gen)

def receipt(turn):
    return dict(spec_sequence_masks=None,num_actual_tokens=turn.starts[-1],
      num_decodes=turn.num_decodes,num_decode_tokens=turn.decode_tokens,
      num_prefills=len(turn.prefill_rows),
      non_spec_state_indices=[r.slot for r in turn.rows],
      conv_starts=list(turn.starts),conv_slots=[[r.slot] for r in turn.rows],
      conv_has_initial=[r.computed_tokens>0 for r in turn.rows],
      prefill_starts=list(turn.prefill_starts),prefill_slots=list(turn.prefill_slots),
      prefill_has_initial=list(turn.has_initial),
      decode_actual_seq_lengths=[0]+[1]*turn.num_decodes)

class Tests(unittest.TestCase):
    def test_mixed(self):
        t=plan([row("d",5,1,8),row("c",2,4,4),row("p",3,8,0)],[0,1,5,13],12)
        self.assertEqual((t.mode,t.num_decodes,t.decode_tokens,t.prefill_starts,t.has_initial),
                         ("mixed",1,1,(0,4,12),(True,False)))
        self.assertTrue(verify_native(t,receipt(t)))
    def test_single_continuation_decode(self):
        t=plan([row("d",5,1,8),row("c",2,1,7),row("p",3,8,0)],[0,1,2,10],12)
        self.assertEqual(t.num_decodes,2)
        self.assertTrue(verify_native(t,receipt(t)))
    def test_one_token_fresh_prefill(self):
        t=plan([row("p",3,1,0,1)],[0,1],12)
        self.assertEqual(t.mode,"prefill")
        self.assertEqual(t.has_initial,(False,))
    def test_short_and_long_chunks(self):
        t=plan([row("c",4,3,2)],[0,3],12)
        self.assertEqual(t.has_initial,(True,))
    def test_reorder_rejected(self):
        with self.assertRaises(Unsupported):
            plan([row("p",3,8,0),row("d",5,1,8)],[0,8,9],12)
    def test_zero_dummy(self):
        with self.assertRaises(Unsupported):plan([row("d",3,0,8)],[0,0],12)
    def test_duplicate_slots(self):
        with self.assertRaises(Unsupported):
            plan([row("d",3,1,8),row("p",3,8,0)],[0,1,9],12)
    def test_cross_prompt_boundary(self):
        with self.assertRaises(Unsupported):plan([row("c",3,2,7)],[0,2],12)
    def test_metadata_suffix_wrong(self):
        t=plan([row("d",5,1,8),row("p",3,8,0)],[0,1,9],12)
        d=receipt(t);d["prefill_starts"]=[1,9]
        with self.assertRaises(Unsupported):verify_native(t,d)
    def test_conv_not_sliced(self):
        t=plan([row("d",5,1,8),row("p",3,8,0)],[0,1,9],12)
        d=receipt(t);d["conv_starts"]=[0,8]
        with self.assertRaises(Unsupported):verify_native(t,d)
    def test_native_lengths_not_cumulative(self):
        t=plan([row("d",5,1,8),row("e",3,1,8)],[0,1,2],12)
        d=receipt(t);d["decode_actual_seq_lengths"]=[0,1,2]
        with self.assertRaises(Unsupported):verify_native(t,d)
    def test_bool_initial_required(self):
        t=plan([row("p",3,8,0)],[0,8],12)
        d=receipt(t);d["prefill_has_initial"]=[0]
        with self.assertRaises(Unsupported):verify_native(t,d)
    def test_pause_retains_and_batch_rows_can_move(self):
        b=LeaseBook();b.commit(plan([row("a",5,4,0),row("b",2,8,0)],[0,4,12],12))
        # b is unscheduled, not finished; a continues under same slot despite row move.
        b.commit(plan([row("a",5,4,4)],[0,4],12))
        self.assertEqual(b.records[2],("b",1,8))
        b.commit(plan([row("b",2,1,8),row("a",5,1,8)],[0,1,2],12))
    def test_finished_slot_reuse(self):
        b=LeaseBook();b.commit(plan([row("a",5,8,0)],[0,8],12))
        b.finish({"a"});b.commit(plan([row("z",5,8,0,8,2)],[0,8],12))
        self.assertEqual(b.records[5],("z",2,8))
    def test_generation_reuse_rejected(self):
        b=LeaseBook();b.commit(plan([row("a",5,8,0)],[0,8],12))
        with self.assertRaises(Unsupported):b.check(plan([row("a",5,1,8,8,2)],[0,1],12))
    def test_preempt_relocation_rejected(self):
        b=LeaseBook();b.commit(plan([row("a",5,8,0)],[0,8],12))
        with self.assertRaises(Unsupported):b.check(plan([row("a",6,1,8)],[0,1],12))
    def test_recompute_on_same_live_id_rejected(self):
        b=LeaseBook();b.commit(plan([row("a",5,8,0)],[0,8],12))
        with self.assertRaises(Unsupported):b.check(plan([row("a",6,8,0)],[0,8],12))
    def test_retire_whole_worker(self):
        b=LeaseBook();b.retire()
        with self.assertRaises(Unsupported):b.check(plan([row("a",5,8,0)],[0,8],12))
    def test_budget_view_bound(self):
        with self.assertRaises(Unsupported):
            block_accesses(1000,32,0,(2,4),(4,1),8,[0],"gdn",True)
    def test_disjoint_live_pool(self):
        g=block_accesses(1000,1024,0,(4,8),(8,1),4,[0,1],"gdn",True)
        fa=block_accesses(1000,1024,256,(4,8),(8,1),4,[0,1],"fa",True)
        self.assertTrue(verify_live_accesses(g+fa))
    def test_different_slot_does_not_prove_disjoint(self):
        g=block_accesses(1000,1024,0,(4,8),(8,1),4,[1],"gdn",True)
        fa=block_accesses(1000,1024,32,(4,8),(8,1),4,[0],"fa",True)
        with self.assertRaises(Unsupported):verify_live_accesses(g+fa)
    def test_paused_state_protected_from_fa(self):
        g=block_accesses(1000,1024,0,(4,8),(8,1),4,[1],"gdn",False)
        fa=block_accesses(1000,1024,32,(4,8),(8,1),4,[0],"fa",True)
        with self.assertRaises(Unsupported):verify_live_accesses(g+fa)
    def test_read_only_overlap(self):
        g=block_accesses(1000,1024,0,(4,8),(8,1),4,[1],"gdn",False)
        fa=block_accesses(1000,1024,32,(4,8),(8,1),4,[0],"fa",False)
        self.assertTrue(verify_live_accesses(g+fa))
    def test_noncontiguous_inner_view_rejected(self):
        with self.assertRaises(Unsupported):
            block_accesses(1000,1024,0,(4,4,4),(16,1,4),4,[0],"gdn",True)

if __name__=="__main__":
    unittest.main()
