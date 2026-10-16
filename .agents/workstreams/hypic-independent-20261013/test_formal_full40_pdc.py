import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from audit_formal_full40_pdc import bind_full40_pic_starts,audit_full40_pdc

class Full40PDCTest(unittest.TestCase):
    def setUp(self):
        self.mapping={f"api{i}":f"req{i}" for i in range(40)}
        self.workers={r:r+100 for r in range(4)};self.sha="a"*64
        self.starts={v:9216 for v in self.mapping.values()}
        self.events=[dict(event="native_request_progress",request_id=rid,rank=r,pid=p,
            manifest_sha256=self.sha,computed_tokens=7680,scheduled_tokens=4096,
            first_observed=True,step=10) for rid in self.starts for r,p in self.workers.items()]
        self.caps=[dict(event="pic_scheduler_boundary_capped",request_id="req0",
            manifest_sha256=self.sha,native_block_size=1536,pic_start=9216,pic_end=25600)]
    def audit(self):
        return audit_full40_pdc(self.events,self.caps,self.mapping,self.workers,self.starts,manifest_sha256=self.sha)
    def test_full40_one_conditional_cap_is_sufficient(self):
        self.assertEqual(len(self.audit()["requests"]),40)
    def test_no_block_evidence(self):
        self.caps=[]
        with self.assertRaises(ValueError):self.audit()
    def test_missing_worker_request(self):
        self.events.pop()
        with self.assertRaises(ValueError):self.audit()
    def test_wrong_pid(self):
        self.events[0]["pid"]=999
        with self.assertRaises(ValueError):self.audit()
    def test_source_drift(self):
        self.events[0]["manifest_sha256"]="b"*64
        with self.assertRaises(ValueError):self.audit()
    def test_no_actual_hit(self):
        self.events[0]["computed_tokens"]=0
        with self.assertRaises(ValueError):self.audit()
    def test_earlier_contradiction(self):
        x=dict(self.events[0],first_observed=False,step=9);self.events.append(x)
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_first(self):
        self.events.append(copy.copy(self.events[0]))
        with self.assertRaises(ValueError):self.audit()
    def test_conflicting_cap(self):
        self.caps[0]["native_block_size"]=1024
        with self.assertRaises(ValueError):self.audit()
    def test_short_denominator(self):
        self.mapping.pop("api39")
        with self.assertRaises(ValueError):self.audit()
    def test_duplicate_runtime(self):
        self.mapping["api39"]="req0"
        with self.assertRaises(ValueError):self.audit()
    def test_geometry_conflict(self):
        self.caps[0]["pic_end"]+=1
        with self.assertRaises(ValueError):self.audit()
    def test_rank_bool_rejected(self):
        self.events[0]["rank"]=False
        with self.assertRaises(ValueError):self.audit()
    def test_input_binding(self):
        prefix=[1]*8192;public=[2]*16384;tokens=prefix+[3]*1024+public+[4]*7168
        a=dict(native_prefix=prefix,public_segment=public,requests=[
            dict(index=i,token_ids=tokens,segment_start=9216,segment_end=25600) for i in range(40)])
        results=[dict(index=i,ok=True,metrics={"request_id":f"api{i}"}) for i in range(40)]
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"tokens.json";p.write_text(json.dumps(a));h=hashlib.sha256(p.read_bytes()).hexdigest()
            self.assertEqual(bind_full40_pic_starts(p,h,results,self.mapping),self.starts)
            with self.assertRaises(ValueError):bind_full40_pic_starts(p,"b"*64,results,self.mapping)
            with self.assertRaises(ValueError):bind_full40_pic_starts(p,h,results[:-1],self.mapping)
            results[39]["metrics"]["request_id"]="api0"
            with self.assertRaises(ValueError):bind_full40_pic_starts(p,h,results,self.mapping)

if __name__=="__main__":unittest.main()
