import unittest
from dataclasses import replace
from independent_prefill_batch import plan_prefill_batch,stage_prefill_batch
from independent_request_map import freeze_request_slices
from independent_linear_map import freeze_prefill_linear_slices

class BatchTests(unittest.TestCase):
    def setup_batch(self,n=16):
        req=freeze_request_slices([str(i) for i in range(n)],[0]*n,[10]*n,
            list(range(0,10*n+1,10)),rank=2,step=4)
        prompts={r.request_id:(90,*range(8),91) for r in req}
        plans=plan_prefill_batch(req,prompts,tuple(range(8)),lambda r:r.rank,lambda i:True)
        assoc=freeze_prefill_linear_slices(req,list(range(0,10*n+1,10)),
            list(range(n)),[False]*n,state_capacity=n)
        return req,prompts,plans,assoc
    def test_c16_distinct_offsets_and_owners(self):
        req,prompts,plans,assoc=self.setup_batch();seen=[]
        out=stage_prefill_batch(plans,assoc,lambda p,a:(seen.append((p[0].token_start,a.state_slot)),p[0].request_id)[1])
        self.assertEqual(len(out),16);self.assertEqual(seen,[(10*i,i) for i in range(16)])
    def test_one_miss_falls_back_whole_batch(self):
        req,prompts,_,_=self.setup_batch();prompts['15']=(0,1)
        self.assertIsNone(plan_prefill_batch(req,prompts,tuple(range(8)),lambda r:r.rank,lambda i:True))
    def test_missing_material_falls_back(self):
        req,prompts,_,_=self.setup_batch()
        self.assertIsNone(plan_prefill_batch(req,prompts,tuple(range(8)),lambda r:r.rank,lambda i:False))
    def test_alias_rejected_before_prepare(self):
        _,_,plans,a=self.setup_batch();a=list(a);a[-1]=replace(a[-1],state_slot=0);seen=[]
        with self.assertRaises(ValueError):stage_prefill_batch(plans,a,lambda *x:seen.append(x))
        self.assertEqual(seen,[])
    def test_identity_rejected_before_prepare(self):
        _,_,plans,a=self.setup_batch();a=list(a);a[-1]=replace(a[-1],step=5);seen=[]
        with self.assertRaises(ValueError):stage_prefill_batch(plans,a,lambda *x:seen.append(x))
        self.assertEqual(seen,[])
    def test_late_failure_returns_no_prepared_batch(self):
        _,_,plans,a=self.setup_batch();seen=[]
        def prepare(p,a):
            seen.append(a.row)
            if a.row==15:raise RuntimeError('last request failure')
            return a.row
        with self.assertRaises(RuntimeError):stage_prefill_batch(plans,a,prepare)
        self.assertEqual(seen,list(range(16)))
if __name__=='__main__':unittest.main()
