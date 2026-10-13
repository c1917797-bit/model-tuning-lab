import unittest
from native_tp4_smoke import processes
HEADER="Process id"
class PhysicalProcessParserTests(unittest.TestCase):
    def test_real_combined_npu_chip_format(self):
        # Actual host display format retained in the orientation receipt.
        text=HEADER+"\n| 4       0                 | 570885        | python3                  | 271                     |\n"+"\n".join("| No running processes found in NPU "+str(i)+" |" for i in [0,1,2,3,5,6,7])
        self.assertEqual(processes(text),[(4,570885)])
    def test_combined_target_rows_cover_all_lanes(self):
        text=HEADER+"\n"+"\n".join("| "+str(i)+"       0 | "+str(10000+i)+" | python3 | 100 |" for i in range(4))
        self.assertEqual(processes(text),[(i,10000+i) for i in range(4)])
    def test_idle_physical_lanes(self):
        text=HEADER+"\n"+"\n".join("| No running processes found in NPU "+str(i)+" |" for i in range(8))
        self.assertEqual(processes(text),[])
    def test_target_and_neighbor_pid_preserved(self):
        text=HEADER+"\n| 0 | 0 | 123 | python3 | 1024 |\n| 4 | 0 | 777 | python3 | 100 |\n"+"\n".join("| No running processes found in NPU "+str(i)+" |" for i in [1,2,3,5,6,7])
        self.assertEqual(processes(text),[(0,123),(4,777)])
    def test_missing_table_fails(self):
        with self.assertRaises(ValueError):processes("NPU command error")
    def test_partial_lanes_fail(self):
        with self.assertRaises(ValueError):processes(HEADER+"\n| No running processes found in NPU 0 |")
if __name__=="__main__":unittest.main()
