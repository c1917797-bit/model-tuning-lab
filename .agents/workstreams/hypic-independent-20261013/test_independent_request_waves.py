import unittest,threading
from independent_request_waves import execute_waves,validate_waves

class WaveTests(unittest.TestCase):
    def test_public_finishes_before_two_private_requests_overlap(self):
        public=threading.Event();barrier=threading.Barrier(2);inside=set();lock=threading.Lock()
        def send(i):
            if i==0:public.set();return 'public'
            self.assertTrue(public.is_set())
            with lock:inside.add(i)
            barrier.wait(timeout=2)
            return 'private'
        records=list(execute_waves((0,1,2),((0,),(1,2)),send,check_guard=lambda:None))
        self.assertEqual(records[0]['index'],0)
        self.assertEqual(inside,{1,2})
        self.assertEqual({r['index'] for r in records},{0,1,2})
        a,b=records[1:]
        self.assertLess(max(a['client_start_monotonic'],b['client_start_monotonic']),
                        min(a['client_end_monotonic'],b['client_end_monotonic']))
    def test_duplicate_missing_and_excess_delay_rejected_before_send(self):
        for waves in (((0,),(1,1)),((0,),(2,)),((),(0,1,2))):
            with self.assertRaises(ValueError):validate_waves(waves,3)
        with self.assertRaises(ValueError):
            list(execute_waves((0,),((0,),),lambda p:self.fail(),check_guard=lambda:None,
                               start_delays={0:6}))
    def test_guard_failure_prevents_request(self):
        calls=[]
        def guard():raise RuntimeError('foreign')
        with self.assertRaises(RuntimeError):
            list(execute_waves((0,),((0,),),calls.append,check_guard=guard))
        self.assertEqual(calls,[])

if __name__=='__main__':unittest.main()
