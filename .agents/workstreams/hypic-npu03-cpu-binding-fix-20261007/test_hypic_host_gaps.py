import unittest
from correlate_hypic_host_gaps import correlate

def event(name, pid, ts, dur):
    return dict(ph="X", name=name, pid=pid, tid=1, ts=ts, dur=dur)
META = [dict(ph="M", name="process_name", pid=p, args={"name":n})
        for p,n in [(1,"Python"),(2,"CANN"),(3,"Overlap Analysis"),(4,"Ascend Hardware")]]

class CorrelationTests(unittest.TestCase):
    def test_synthetic_free_and_device_are_excluded(self):
        got=correlate((0,10000), META+[event("Free",3,0,10),event("kernel",4,0,10)])
        self.assertEqual(got["host_union_ms"],0)
    def test_nested_events_are_not_summed(self):
        got=correlate((0,10000),META+[event("outer",1,1,8),event("inner",2,2,4)])
        self.assertEqual(got["host_union_ms"],.008)
        self.assertFalse(got["causality_proven"])
    def test_clip_edges(self):
        got=correlate((2000,4000),META+[event("host",1,1,5)])
        self.assertEqual(got["host_union_ms"],.002)
    def test_touching_is_not_overlap(self):
        got=correlate((2000,4000),META+[event("left",1,0,2),event("right",2,4,2)])
        self.assertEqual(got["host_event_counts"],{})
    def test_missing_host_lanes_fails(self):
        with self.assertRaises(ValueError): correlate((0,1000),[])
    def test_negative_duration_fails(self):
        with self.assertRaises(ValueError): correlate((0,1000),META+[event("bad",1,0,-1)])

if __name__ == "__main__":
    unittest.main()
