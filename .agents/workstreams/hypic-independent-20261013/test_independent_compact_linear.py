import unittest
from types import SimpleNamespace
import torch
from independent_c1_reference import accumulate_segment,serial_dense_oracle
from independent_hybrid_material import MaterialIdentity
from independent_request_map import RequestSlice
from independent_segment_selection import SegmentSelection
from independent_c2_query_plan import plan_c2_queries
from independent_compact_linear import execute_compact_linear


class CompactLinearTests(unittest.TestCase):
    def fixture(self,length=16):
        generator=torch.Generator().manual_seed(31)
        keys=torch.randn(length,2,4,generator=generator,dtype=torch.float64)*.1
        values=torch.randn(length,2,3,generator=generator,dtype=torch.float64)
        beta=torch.full((length,2),.2,dtype=torch.float64)
        decay=torch.full((length,2),.9,dtype=torch.float64)
        state=torch.randn(2,4,3,generator=generator,dtype=torch.float64)
        req=RequestSlice('r',0,2,0,length,0,0,length)
        plan=plan_c2_queries(req,SegmentSelection(2,12,False,'a'*64),seam_tokens=3,public_length=10)
        identity=MaterialIdentity('m','c','l',0,'a'*64,10,3)
        material=SimpleNamespace(identity=identity,
            affine=accumulate_segment(keys[5:12],values[5:12],beta[5:12],decay[5:12]),
            conv_tail=torch.full((3,6),12.,dtype=torch.float64))
        calls=[]
        def live(lo,hi,initial,tail):
            calls.append((lo,hi,tail.clone()))
            outputs=[];s=initial
            for offset in plan.retained_offsets[lo:hi]:
                s=serial_dense_oracle(keys[offset:offset+1],values[offset:offset+1],
                                     beta[offset:offset+1],decay[offset:offset+1],s)
                outputs.append(s.sum(dim=-2))
            return torch.stack(outputs),s,torch.full_like(tail,float(plan.retained_offsets[hi-1]+1))
        return keys,values,beta,decay,state,plan,identity,material,calls,live

    def test_handoff_matches_dense_state_without_body_outputs(self):
        k,v,b,g,s,p,i,m,calls,live=self.fixture()
        original=s.clone();public=m.affine.zero_state.clone()
        out,final,tail=execute_compact_linear(m,i,p,s,torch.zeros(3,6,dtype=s.dtype),run_live=live)
        reference=serial_dense_oracle(k,v,b,g,s)
        torch.testing.assert_close(final,reference,rtol=1e-12,atol=1e-12)
        self.assertEqual(out.shape[0],9)
        self.assertEqual([(a,b) for a,b,_ in calls],[(0,5),(5,9)])
        self.assertEqual(float(calls[1][2][0,0]),12.)
        torch.testing.assert_close(s,original)
        torch.testing.assert_close(m.affine.zero_state,public)

    def test_no_suffix_still_commits_body_transition(self):
        k,v,b,g,s,p,i,m,calls,live=self.fixture(12)
        out,final,tail=execute_compact_linear(m,i,p,s,torch.zeros(3,6,dtype=s.dtype),run_live=live)
        torch.testing.assert_close(final,serial_dense_oracle(k,v,b,g,s),rtol=1e-12,atol=1e-12)
        self.assertEqual(len(calls),1)
        torch.testing.assert_close(tail,m.conv_tail)

    def test_live_failure_leaves_public_and_native_inputs_untouched(self):
        k,v,b,g,s,p,i,m,calls,live=self.fixture()
        original=s.clone();public=m.affine.zero_state.clone()
        def fail(lo,hi,state,tail):
            state.zero_();tail.zero_();raise RuntimeError('late kernel failure')
        with self.assertRaises(RuntimeError):
            execute_compact_linear(m,i,p,s,torch.ones(3,6,dtype=s.dtype),run_live=fail)
        torch.testing.assert_close(s,original)
        torch.testing.assert_close(m.affine.zero_state,public)


if __name__=='__main__':unittest.main()
