import ast
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest
from independent_pic_scheduler_hook import install_pic_scheduler,transform_schedule_source

class FixtureScheduler:
    def __init__(self):
        self.running=[SimpleNamespace(num_computed_tokens=0)]
        self.waiting=[SimpleNamespace(num_computed_tokens=0)]
        self.allocations=[]
    def schedule(self):
        req_index=0
        while req_index<len(self.running):
            request=self.running[req_index]
            num_new_tokens=5
            if num_new_tokens == 0:
                req_index+=1
                continue
            self.allocations.append(("running",num_new_tokens))
            request.num_computed_tokens+=num_new_tokens
            req_index+=1
        for request in self.waiting:
            num_computed_tokens=request.num_computed_tokens
            num_new_tokens=5
            load_kv_async=False
            limit_lookahead_tokens=load_kv_async
            self.allocations.append(("waiting",num_new_tokens))
            request.num_computed_tokens+=num_new_tokens
        return self.allocations

class Hook(unittest.TestCase):
    def digest(self):return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def test_disabled_and_exact_restore(self):
        original=FixtureScheduler.schedule
        stop=install_pic_scheduler(FixtureScheduler)
        self.assertIs(FixtureScheduler.schedule,original);stop()
        self.assertIs(FixtureScheduler.schedule,original)
    def test_before_allocation_and_waiting_zero(self):
        original=FixtureScheduler.schedule;calls=[]
        def cap(self,request,computed,n):
            calls.append(computed)
            return 2 if request in self.running else 0
        stop=install_pic_scheduler(FixtureScheduler,enabled=True,expected_source_sha256=self.digest(),cap=cap)
        try:
            obj=FixtureScheduler()
            self.assertEqual(obj.schedule(),[("running",2)])
            self.assertEqual(obj.running[0].num_computed_tokens,2)
            self.assertEqual(obj.waiting[0].num_computed_tokens,0)
            self.assertEqual(calls,[0,0])
        finally:stop()
        self.assertIs(FixtureScheduler.schedule,original)
    def test_source_drift(self):
        with self.assertRaises(ValueError):
            install_pic_scheduler(FixtureScheduler,enabled=True,expected_source_sha256="bad",cap=lambda *x:1)
    def test_increase_rejected(self):
        stop=install_pic_scheduler(FixtureScheduler,enabled=True,expected_source_sha256=self.digest(),cap=lambda *x:6)
        try:
            obj=FixtureScheduler()
            with self.assertRaises(ValueError):obj.schedule()
            self.assertEqual(obj.allocations,[])
        finally:stop()
    def test_anchor_drift(self):
        with self.assertRaises(ValueError):transform_schedule_source("def schedule(self): return 1")
if __name__=="__main__":unittest.main()
