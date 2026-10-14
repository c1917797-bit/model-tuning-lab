import unittest
import torch
from independent_compact_linear import execute_native_linear_plan
from independent_mixed_query_plan import NativeQueryPlan

class NativeLinearDispatchTests(unittest.TestCase):
    def test_decode_and_prefill_compute_all_live_rows_on_private_copies(self):
        for n in (1,9):
            plan=NativeQueryPlan('r',0,2,0,4,n,'decode' if n==1 else 'cold-material')
            state=torch.zeros(2,3,4);tail=torch.zeros(3,10);calls=[]
            def live(lo,hi,s,t):
                calls.append((lo,hi))
                s.add_(2);t.add_(3)
                return torch.ones(n,2,4),s,t
            out,final,conv=execute_native_linear_plan(plan,state,tail,run_live=live)
            self.assertEqual(calls,[(0,n)])
            self.assertEqual(out.shape,(n,2,4))
            self.assertTrue(torch.equal(state,torch.zeros_like(state)))
            self.assertTrue(torch.equal(tail,torch.zeros_like(tail)))
            self.assertTrue((final==2).all());self.assertTrue((conv==3).all())
    def test_failure_and_nonfinite_do_not_mutate_caller_slots(self):
        plan=NativeQueryPlan('r',0,2,0,4,1,'decode')
        for bad in ('raise','nan','shape'):
            state=torch.zeros(2,3,4);tail=torch.zeros(3,10)
            def live(lo,hi,s,t):
                s.add_(9);t.add_(9)
                if bad=='raise':raise RuntimeError('late native failure')
                out=torch.full((1,2,4),float('nan')) if bad=='nan' else torch.zeros(2,2,4)
                return out,s,t
            with self.assertRaises((ValueError,RuntimeError)):
                execute_native_linear_plan(plan,state,tail,run_live=live)
            self.assertEqual(state.sum().item(),0);self.assertEqual(tail.sum().item(),0)

if __name__=='__main__':unittest.main()
