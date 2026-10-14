import json,hashlib,tempfile,unittest
from pathlib import Path
from independent_formal_workload import run_formal_workload
class FormalWorkloadTests(unittest.TestCase):
    def test_full_pipeline_and_separate_denominator(self):
        # Explicit fake counters/timings; not real model or performance evidence.
        a={"native_prefix":[1]*8192,"public_segment":[2]*16384,
           "requests":[{"index":i,"token_ids":[i]*32768,"segment_end":30000} for i in range(40)]}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"input.json";raw=json.dumps(a).encode();p.write_bytes(raw)
            events=[];checks=[]
            def measured(payload):
                i=payload["prompt"][0]
                return {"request_id":"fake-"+str(i),"completion_tokens":1024,
                    "usage":{"prompt_tokens":32768},"finish_reason":"length",
                    "tpot_denominator":"completion_tokens","ttft_ms":1000.,
                    "duration_ms":62440.,"tpot_ms":60.}
            r=run_formal_workload({"path":str(p),"sha256":hashlib.sha256(raw).hexdigest()},
                send_warmup=lambda p:{},send_measured=measured,guard=lambda:None,
                record=events.append,require_material_ready=lambda:checks.append(True))
            self.assertTrue(r["valid"]);self.assertEqual(r["summary"]["requests"],40)
            self.assertEqual(sum(x["scored"] for x in events),40)
            self.assertEqual(sum(not x["scored"] for x in events),4)
            self.assertEqual(checks,[True])
if __name__=="__main__":unittest.main()
