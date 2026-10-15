"""CPU protocol doubles only; no actual profiler or device evidence."""
import unittest,tempfile,json,hashlib
from pathlib import Path
from independent_profile_workload import validate_profile_spec,profiler_config,run_profile_workload

class ProfileTests(unittest.TestCase):
    def spec(self):
        return {"requests":16,"output_tokens":64,"max_iterations":12,"delay_iterations":0}
    def test_bounds_and_exclusivity(self):
        for change in ({"requests":1},{"output_tokens":1024},{"max_iterations":0},{"delay_iterations":129},{"requests":True}):
            s=self.spec();s.update(change)
            with self.assertRaises(ValueError):validate_profile_spec({"profile_diagnostic":s,"formal_token_artifact":{"path":"fixture"}})
        with self.assertRaises(ValueError):validate_profile_spec({"profile_diagnostic":self.spec(),"formal_token_artifact":{"path":"fixture"},"formal_performance":True})
        self.assertEqual(validate_profile_spec({"profile_diagnostic":self.spec(),"formal_token_artifact":{"path":"fixture"}}),self.spec())
    def test_native_profiler_config(self):
        c=profiler_config(self.spec())
        self.assertEqual(c["profiler"],"torch");self.assertFalse(c["torch_profiler_with_stack"])
        self.assertTrue(c["ignore_frontend"]);self.assertEqual(c["max_iterations"],12)
    def run_unit(self,bad=False,wrong_hash=False):
        artifact={"native_prefix":[1]*8192,"public_segment":[2]*16384,
                  "requests":[{"index":i,"segment_end":24576,"token_ids":[i+3]*32768} for i in range(40)]}
        events=[];controls=[];ready=[]
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"tokens.json";data=json.dumps(artifact).encode();p.write_bytes(data)
            def send(payload):
                n=payload["max_tokens"]
                return {"usage":{"prompt_tokens":len(payload["prompt"]),"completion_tokens":(1 if bad and n==64 else n)}}
            spec={"path":str(p),"sha256":("0"*64 if wrong_hash else hashlib.sha256(data).hexdigest())}
            unit=run_profile_workload(spec,self.spec(),send=send,
                control=lambda a:controls.append(a) or {"status":200},guard=lambda:None,
                record=events.append,require_material_ready=lambda:ready.append(True))
        return unit,events,controls,ready
    def test_warmup_before_profile_and_full16(self):
        u,e,c,r=self.run_unit()
        self.assertTrue(u["valid"]);self.assertEqual(len(u["results"]),16)
        self.assertEqual(c,["start_profile","stop_profile"]);self.assertEqual(r,[True])
        self.assertEqual([x["event"] for x in e[:5]],["warmup"]*4+["profile-start"])
        self.assertTrue(all(x.get("scored") is False for x in e))
    def test_failures_retained_and_stop(self):
        u,e,c,r=self.run_unit(bad=True)
        self.assertFalse(u["valid"]);self.assertEqual(len(u["results"]),16)
        self.assertTrue(all(not x["ok"] for x in u["results"]))
        self.assertEqual(c[-1],"stop_profile")
    def test_source_drift_rejected_before_work(self):
        with self.assertRaises(ValueError):self.run_unit(wrong_hash=True)

if __name__=="__main__":unittest.main()
