import unittest
from dataclasses import replace
from independent_request_map import RequestSlice
from independent_mixed_linear_map import freeze_mixed_linear_slices

class MixedLinearTests(unittest.TestCase):
    def test_first_token_prefill_is_not_stateful_decode(self):
        r=RequestSlice('first',0,1,0,1,0,0,1)
        result=freeze_mixed_linear_slices((r,),[0,1],[2],[False],
            state_capacity=4,num_decodes=0,num_prefills=1,num_decode_tokens=0,
            prefill_query_start=[0,1],prefill_state_indices=[2],
            prefill_has_initial=[False])
        self.assertFalse(result[0].has_initial_state)
        with self.assertRaises(ValueError):
            freeze_mixed_linear_slices((r,),[0,1],[2],[False],
                state_capacity=4,num_decodes=1,num_prefills=0,num_decode_tokens=1)

    def reqs(self):
        return (RequestSlice('d',1,7,100,1,0,0,1),
                RequestSlice('h',1,7,0,32,1,1,33),
                RequestSlice('p',1,7,8,4,2,33,37))
    def call(self,requests=None,**changes):
        kw=dict(state_capacity=20,num_decodes=1,num_prefills=2,
                num_decode_tokens=1,prefill_query_start=[0,32,36],
                prefill_state_indices=[9,12],prefill_has_initial=[False,True])
        kw.update(changes)
        return freeze_mixed_linear_slices(self.reqs() if requests is None else requests,
                  [0,1,33,37],[4,9,12],[True,False,True],**kw)
    def test_exact_mixed_slots_and_rebased_prefill(self):
        result=self.call()
        self.assertEqual([r.state_slot for r in result],[4,9,12])
        self.assertEqual([r.has_initial_state for r in result],[True,False,True])
        self.assertEqual([(r.token_start,r.token_end) for r in result],
                         [(0,1),(1,33),(33,37)])
    def test_native_tail_wrong_rebase_slot_or_initial_rejected(self):
        for kw in ({'prefill_query_start':[1,33,37]},
                   {'prefill_state_indices':[12,9]},
                   {'prefill_has_initial':[True,True]},
                   {'speculative':True}):
            with self.assertRaises(ValueError):self.call(**kw)
    def test_wrong_identity_and_decode_order_rejected(self):
        reqs=self.reqs()
        for r in (replace(reqs[1],step=8),replace(reqs[1],request_id='d'),
                  replace(reqs[1],scheduled_tokens=1)):
            with self.assertRaises(ValueError):self.call((reqs[0],r,reqs[2]))
    def test_decode_only_no_prefill(self):
        r=RequestSlice('d',0,1,3,1,0,0,1)
        result=freeze_mixed_linear_slices((r,),[0,1],[2],[True],
            state_capacity=4,num_decodes=1,num_prefills=0,num_decode_tokens=1)
        self.assertEqual(result[0].state_slot,2)

if __name__=='__main__':unittest.main()
