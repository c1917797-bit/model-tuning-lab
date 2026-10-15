"""CPU-only ordering and failure controls; no runtime speed claim."""
import unittest,tempfile,json,hashlib
from pathlib import Path
from independent_warm_profile_workload import run_profile_workload

class WarmProfileTests(unittest.TestCase):
    def exercise(self,mode):
        spec={"requests":16,"output_tokens":64,"max_iterations":12,"delay_iterations":0}
        artifact={"native_prefix":[1]*8192,"public_segment":[2]*16384,
                  "requests":[{"index":i,"segment_end":24576,"token_ids":[i+3]*32768} for i in range(40)]}
        self.events=[];self.controls=[];active=[False]
        def control(a):
            self.controls.append(a);active[0]=(a=="start_profile");return {"status":200}
        def send(p):
            n=p["max_tokens"]
            wrong=n==64 and (mode=="warm-fail" or (mode=="measured-fail" and active[0]))
            return {"usage":{"prompt_tokens":len(p["prompt"]),"completion_tokens":1 if wrong else n}}
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"tokens.json";raw=json.dumps(artifact).encode();path.write_bytes(raw)
            return run_profile_workload({"path":str(path),"sha256":hashlib.sha256(raw).hexdigest()},spec,
                send=send,control=control,guard=lambda:None,record=self.events.append,
                require_material_ready=lambda:None)
    def test_exact_private_warmup_precedes_capture(self):
        u=self.exercise("ok");self.assertTrue(u["valid"])
        self.assertEqual(len(u["private_warmup_results"]),16)
        self.assertEqual(len(u["results"]),16)
        self.assertEqual([x["event"] for x in self.events[:20]],["warmup"]*4+["profile-private-warmup"]*16)
        self.assertEqual(self.events[20]["event"],"profile-start")
        self.assertEqual(self.controls,["start_profile","stop_profile"])
        self.assertTrue(all(x.get("scored") is False for x in self.events))
    def test_warmup_failure_retained_without_profile_start(self):
        with self.assertRaises(RuntimeError):self.exercise("warm-fail")
        self.assertEqual(self.controls,[])
        self.assertEqual(sum(x["event"]=="profile-private-warmup" for x in self.events),16)
    def test_measured_failures_preserved_and_stopped(self):
        u=self.exercise("measured-fail");self.assertFalse(u["valid"])
        self.assertEqual(len(u["results"]),16)
        self.assertTrue(all(not x["ok"] for x in u["results"]))
        self.assertEqual(self.controls[-1],"stop_profile")

if __name__=="__main__":unittest.main()
