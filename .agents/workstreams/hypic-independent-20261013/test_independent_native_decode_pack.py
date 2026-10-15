import unittest
import torch
from independent_native_decode_pack import DecodeRow,pack_native_decode,unpack_native_decode

class PackingTests(unittest.TestCase):
    def setUp(self):
        self.p=torch.arange(30,dtype=torch.float32).reshape(5,6)
        self.b=torch.arange(10,dtype=torch.float32).reshape(5,2)
        self.a=self.b+100
        self.conv=torch.arange(72,dtype=torch.float32).reshape(4,3,6)
        # Unequal key/value dimensions catch accidental transpose symmetry.
        self.state=torch.arange(120,dtype=torch.float32).reshape(4,2,3,5)
        self.rows=(DecodeRow("b",4,3,True),DecodeRow("a",1,0,False))
    def pack(self,rows=None):
        return pack_native_decode(self.rows if rows is None else rows,self.p,self.b,self.a,self.conv,self.state)
    def test_permutation_and_metadata(self):
        x=self.pack()
        self.assertTrue(torch.equal(x.projected,self.p[[4,1]]))
        self.assertTrue(torch.equal(x.a,self.a[[4,1]]))
        self.assertTrue(torch.equal(x.conv_starts,torch.tensor([0,1,2],dtype=torch.int32)))
        self.assertTrue(torch.equal(x.actual_seq_lengths,torch.tensor([0,1,1],dtype=torch.int32)))
        self.assertTrue(torch.equal(x.state[0],self.state[3]))
        self.assertEqual(x.state[1].count_nonzero().item(),0)
        self.assertEqual(x.conv[1].count_nonzero().item(),0)
    def test_private_mutation(self):
        before=[v.clone() for v in (self.p,self.b,self.a,self.conv,self.state)]
        x=self.pack()
        for v in (x.projected,x.b,x.a,x.conv,x.state):v.zero_()
        self.assertTrue(all(torch.equal(v,w) for v,w in zip(before,(self.p,self.b,self.a,self.conv,self.state))))
    def test_unpack_key_major_and_ownership(self):
        x=self.pack();out=torch.arange(12,dtype=torch.float32).reshape(2,2,3)
        result=unpack_native_decode(x,out,x.state,x.conv)
        self.assertEqual(tuple(result["b"][1].shape),(2,5,3))
        self.assertTrue(torch.equal(result["b"][1],self.state[3].transpose(-1,-2)))
        for v in result["b"]:v.zero_()
        self.assertTrue(torch.equal(x.state[0],self.state[3]))
    def test_reject_duplicate_or_outside(self):
        for rows in ((),(self.rows[0],self.rows[0]),(DecodeRow("x",5,0,True),),
                     (DecodeRow("x",0,4,True),),(DecodeRow("x",0,0,1),),
                     (DecodeRow("x",0,0,True),DecodeRow("y",1,0,True))):
            with self.subTest(rows=rows),self.assertRaises(ValueError):self.pack(rows)
    def test_reject_nonfinite_or_bad_final_shape(self):
        x=self.pack();out=torch.zeros(2,2,3);out[0,0,0]=float("nan")
        with self.assertRaises(ValueError):unpack_native_decode(x,out,x.state,x.conv)
        with self.assertRaises(ValueError):unpack_native_decode(x,torch.zeros(2,2,5),x.state,x.conv)

if __name__=="__main__":unittest.main()
