import csv,tempfile,unittest
from pathlib import Path
from independent_profile_timeline import union_us,kernel_timeline


class TimelineTests(unittest.TestCase):
    def test_union_overlap_adjacent_and_duplicate(self):
        self.assertEqual(union_us([(0,10),(5,12),(12,20),(1,2),(0,10)]),20)
        with self.assertRaises(ValueError):union_us([(2,1)])
        with self.assertRaises(ValueError):union_us([(0,float("nan"))])
    def write(self,root,rows):
        p=Path(root)/"kernel.csv"
        with p.open("w",newline="") as f:
            w=csv.DictWriter(f,fieldnames=["Start Time(us)","Duration(us)","Name","Type"])
            w.writeheader();w.writerows(rows)
        return p
    def row(self,start,duration,name="mm",kind="MatMul"):
        return {"Start Time(us)":start,"Duration(us)":duration,"Name":name,"Type":kind}
    def test_large_epoch_precision_and_overlap(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.write(root,[self.row("1792052268378336.001",10),
                self.row("1792052268378341.001",10,"HcclAllReduce","HCCL"),
                self.row("1792052268378356.001",5)])
            r=kernel_timeline(p)
        self.assertEqual(r["kernel_envelope_us"],25)
        self.assertEqual(r["all_kernel_union_us"],20)
        self.assertEqual(r["communication_exclusive_us"],5)
        self.assertEqual(r["uncovered_envelope_us"],5)
    def test_invalid_row_not_silently_dropped(self):
        for duration in ("bad","nan","-1"):
            with tempfile.TemporaryDirectory() as root:
                p=self.write(root,[self.row("1",duration)])
                with self.assertRaises(ValueError):kernel_timeline(p)
    def test_row_ceiling(self):
        with tempfile.TemporaryDirectory() as root:
            p=self.write(root,[self.row("1",1),self.row("2",1)])
            with self.assertRaises(ValueError):kernel_timeline(p,max_rows=1)


if __name__=="__main__":unittest.main()
