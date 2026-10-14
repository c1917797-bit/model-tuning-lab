import unittest,torch
from types import SimpleNamespace
from independent_public_chunk_plan import public_chunk
from independent_public_chunk_kv import PublicChunkKV
class ChunkKVTests(unittest.TestCase):
    def test_exact_rows_positions_and_no_tail(self):
        identity=SimpleNamespace(length=32,boundary_tokens=8)
        keys=torch.arange(36*4,dtype=torch.float32).reshape(36,1,4);values=keys+1
        acc=PublicChunkKV("r",identity)
        self.assertIsNone(acc.accept("r",identity,public_chunk(0,16,32),keys[:16],values[:16]))
        data=acc.accept("r",identity,public_chunk(16,20,32),keys[16:],values[16:])
        self.assertTrue(torch.equal(data["keys"],keys[8:32]))
        self.assertTrue(torch.equal(data["values"],values[8:32]))
        self.assertEqual(data["positions"].tolist(),list(range(8,32)))
        with self.assertRaises(ValueError):acc.accept("r",identity,public_chunk(16,20,32),keys[16:],values[16:])
    def test_memory_and_foreign_identity_rejected(self):
        i=SimpleNamespace(length=32,boundary_tokens=8);keys=torch.zeros(16,1,4)
        acc=PublicChunkKV("r",i,max_bytes=1)
        with self.assertRaises(ValueError):acc.accept("r",i,public_chunk(0,16,32),keys,keys)
        with self.assertRaises(ValueError):acc.accept("other",i,public_chunk(0,16,32),keys,keys)
if __name__=="__main__":unittest.main()
