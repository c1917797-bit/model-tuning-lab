import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from independent_quality_workload import run_quality_workload
from independent_quality_inputs import quality_generation
from independent_segment_selection import token_digest
class QualityWorkloadTests(unittest.TestCase):
    def test_full_input_bound_producers_and_scores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);segment=[2]*16;digest=token_digest(segment)
            rows=[{"index":i,"sample_id":str(i),"token_ids":[1]+segment+[3],
                "reference":"A","segment":{"start":1,"end":17,"tokens_sha256":digest}} for i in range(127)]
            def bound(name,obj):
                p=root/name;raw=json.dumps(obj).encode();p.write_bytes(raw)
                return {"path":str(p),"sha256":hashlib.sha256(raw).hexdigest()}
            spec={"inputs":bound("inputs.json",{"schema":"hypic-quality-inputs/v1",
                "requests":rows,"generation":quality_generation(),"repetitions":3}),
                "catalog":bound("catalog.json",{"schema":"hypic-public-catalog/v1","public_segments":[segment]}),
                "ruler_path":"unused-fixture","batch_samples":10}
            journal=[];ready=[]
            def send(payload):
                return {"id":"fixture","choices":[{"text":"A","finish_reason":"stop"}],
                    "usage":{"prompt_tokens":len(payload["prompt"]),"completion_tokens":1}}
            with patch("independent_quality_workload.load_ruler",return_value={"score_case":lambda *a:("A",True)}):
                result=run_quality_workload(spec,send=send,guard=lambda:None,
                    record=journal.append,require_material_ready=ready.append)
            self.assertEqual(result["requests"],381)
            self.assertEqual(len(ready),39)
            self.assertEqual(sum(x["scored"] for x in journal),381)
            self.assertEqual(sum(not x["scored"] for x in journal),39)
            self.assertEqual(set(ready),{digest})
if __name__=="__main__":unittest.main()
