import unittest,torch
from independent_private_linear import execute_private_linear
from independent_hybrid_material import MaterialIdentity
from independent_linear_reuse import LinearPublicBody
from independent_c1_reference import SegmentAffine
from independent_request_map import freeze_request_slices
from independent_segment_selection import select_segment
class PrivateLinearTests(unittest.TestCase):
    def test_prefix_boundary_body_tail_skip(self):
        public=list(range(8));prompt=[90,91,*public,92,93]
        selection=select_segment(prompt,public)
        request=freeze_request_slices(['a'],[0],[12],[0,12],rank=0,step=1)[0]
        identity=MaterialIdentity('m','c','l',0,selection.tokens_sha256,8,3)
        material=LinearPublicBody(identity,
            SegmentAffine(torch.ones(1,1,1),torch.full((1,1,1),5.)),
            torch.ones(5,1,1),torch.zeros(3,2))
        calls=[];initial=torch.zeros(1,1,1);conv=torch.zeros(3,2)
        def run(lo,hi,state,tail):
            calls.append((lo,hi))
            return torch.ones(hi-lo,1,1),state+hi-lo,tail.clone()
        output,state,tail=execute_private_linear(material,identity,selection,request,
                                                initial,conv,run_live=run)
        self.assertEqual(calls,[(0,2),(2,5),(10,12)])
        self.assertEqual(output.shape[0],12);self.assertEqual(state.item(),12)
        self.assertEqual(initial.item(),0)
    def test_failure_does_not_mutate_input_state(self):
        public=list(range(8));selection=select_segment([90,*public],public)
        req=freeze_request_slices(['a'],[0],[9],[0,9],rank=0,step=1)[0]
        identity=MaterialIdentity('m','c','l',0,selection.tokens_sha256,8,3)
        material=LinearPublicBody(identity,SegmentAffine(torch.ones(1,1,1),torch.ones(1,1,1)),
                                 torch.ones(5,1,1),torch.zeros(3,2))
        initial=torch.zeros(1,1,1)
        def fail(lo,hi,state,conv):
            state.fill_(99);raise RuntimeError('live failure')
        with self.assertRaises(RuntimeError):
            execute_private_linear(material,identity,selection,req,initial,torch.zeros(3,2),run_live=fail)
        self.assertEqual(initial.item(),0)
if __name__=='__main__':unittest.main()
