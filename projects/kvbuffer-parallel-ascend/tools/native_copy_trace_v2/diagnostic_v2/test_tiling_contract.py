"""Real source ABI tests; not device correctness evidence."""
import struct,unittest
from tiling_contract import FIELDS,FORMAT,audit_layout,decode_tiling
class Layout(unittest.TestCase):
    def fixture(self):
        return struct.pack(FORMAT,40,196608,50176,16,4,128,12,128,19,16,32,3,3,0.088388346,1,0,0)+b"\0"*4
    def test_actual_cpp_order(self):
        self.assertEqual(len(audit_layout()),17)
        self.assertEqual(FIELDS[13],"scale")
    def test_real_layout(self):
        d=decode_tiling(self.fixture())
        self.assertEqual([d[n] for n in ("t","nk","dk","nv","dv","sBlockNum","b")],[16,4,128,12,128,19,16])
        self.assertEqual([d[n] for n in FIELDS[14:]],[1,0,0])
    def test_old_wrong_format_exposes_known_seam(self):
        d=struct.unpack("<8If8I",self.fixture()[:68])
        self.assertNotEqual(list(d[1:8]),[16,4,128,12,128,19,16])
        self.assertNotEqual(d[8],struct.unpack(FORMAT,self.fixture()[:68])[13])
    def test_short_rejected(self):
        with self.assertRaises(ValueError):decode_tiling(self.fixture()[:-1])
    def test_nonzero_tail_rejected(self):
        with self.assertRaises(ValueError):decode_tiling(self.fixture()[:-1]+b"\1")
if __name__=="__main__":unittest.main()
