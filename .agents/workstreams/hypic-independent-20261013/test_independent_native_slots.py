import unittest,torch
from independent_native_slots import install_linear_material
from independent_hybrid_material import MaterialIdentity
from independent_c1_reference import SegmentAffine
class SlotTests(unittest.TestCase):
    def setUp(self):
        self.id=MaterialIdentity('model','code','layer',0,'a'*64,12,8)
        self.aff=SegmentAffine(torch.eye(2)[None],torch.zeros(1,2,3))
        self.state=torch.arange(6.).reshape(1,2,3)
        self.ssm=torch.zeros(2,1,3,2);self.conv=torch.zeros(2,3,4)
    def test_transpose_and_neighbor_preserved(self):
        install_linear_material(self.id,self.id,self.aff,self.state,torch.ones(3,4),self.ssm,self.conv,1)
        torch.testing.assert_close(self.ssm[1],self.state.transpose(-1,-2))
        self.assertTrue(torch.equal(self.ssm[0],torch.zeros_like(self.ssm[0])))
        self.assertTrue(torch.equal(self.conv[0],torch.zeros_like(self.conv[0])))
    def test_bad_conv_layout_changes_neither_slot(self):
        with self.assertRaises(ValueError):install_linear_material(self.id,self.id,self.aff,self.state,torch.ones(4,3),self.ssm,self.conv,1)
        self.assertEqual(float(self.ssm.sum()),0);self.assertEqual(float(self.conv.sum()),0)
    def test_negative_slot_rejected(self):
        with self.assertRaises(ValueError):install_linear_material(self.id,self.id,self.aff,self.state,torch.ones(3,4),self.ssm,self.conv,-1)
if __name__=='__main__':unittest.main()
