import unittest,torch
from independent_public_chunk_plan import public_chunk
from independent_public_chunk_state import PublicChunkState
from independent_c1_reference import accumulate_segment,apply_segment,serial_dense_oracle
class ChunkStateTests(unittest.TestCase):
    def test_composed_chunks_match_independent_serial_oracle(self):
        torch.manual_seed(7);k=torch.randn(32,2,4,dtype=torch.float64)*.1
        v=torch.randn(32,2,3,dtype=torch.float64);b=torch.full((32,2),.2,dtype=torch.float64)
        g=torch.full((32,2),.99,dtype=torch.float64);state=torch.randn(2,4,3,dtype=torch.float64)
        first=public_chunk(0,16,32);second=public_chunk(16,20,32)
        acc=PublicChunkState("r","i")
        self.assertIsNone(acc.accept("r","i",first,accumulate_segment(k[8:16],v[8:16],b[8:16],g[8:16])))
        material=acc.accept("r","i",second,accumulate_segment(k[16:],v[16:],b[16:],g[16:]),torch.zeros(3,6))
        expected=serial_dense_oracle(k[8:],v[8:],b[8:],g[8:],state)
        self.assertTrue(torch.allclose(apply_segment(material.affine,state),expected,atol=1e-12))
        with self.assertRaises(ValueError):acc.accept("r","i",second)
    def test_missing_affine_and_bound_rejected(self):
        acc=PublicChunkState("r","i",max_bytes=1)
        with self.assertRaises(ValueError):acc.accept("r","i",public_chunk(0,16,32))
if __name__=="__main__":unittest.main()
