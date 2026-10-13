import unittest
from independent_request_map import freeze_request_slices
from independent_cache_map import freeze_cache_slices
class CacheMapTests(unittest.TestCase):
    def inputs(self):
        reqs=freeze_request_slices(['a','b'],[3,0],[3,2],[0,3,5],rank=2,step=7)
        return reqs,[[[5,9],[8,0]]],[[23,36,37,32,33]]
    def run_map(self,inputs,**kwargs):
        return freeze_cache_slices(*inputs,block_sizes=[4],row_counts=[[2,1]],
                                   cp_world_sizes=kwargs.get('cp',[1]))
    def test_cross_block_and_immutable(self):
        x=self.inputs(); result=self.run_map(x)
        self.assertEqual(result[0].slots,(23,36,37))
        self.assertEqual(result[1].request_id,'b')
        x[1][0][0][0]=99
        self.assertEqual(result[0].block_ids,(5,9))
    def test_tampered_device(self):
        x=self.inputs();x[2][0][1]=999
        with self.assertRaises(ValueError):self.run_map(x)
    def test_cp_rejected(self):
        with self.assertRaises(ValueError):self.run_map(self.inputs(),cp=[2])
    def test_missing_allocated_block(self):
        x=self.inputs();x[1][0][0]=[5]
        with self.assertRaises(ValueError):self.run_map(x)
if __name__=='__main__':unittest.main()
