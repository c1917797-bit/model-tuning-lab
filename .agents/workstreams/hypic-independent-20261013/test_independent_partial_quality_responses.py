import json,tempfile,unittest
from pathlib import Path
from independent_partial_quality_responses import recover_quality_responses

class PartialQualityTests(unittest.TestCase):
    def row(self,index=0,repetition=1,**changes):
        x=dict(event="quality-scored-response",scored=True,index=index,repetition=repetition,
               sample_id="sample",segment_sha256="a"*64,ok=True,request_id="req"+str(index)+str(repetition),
               finish_reason="length",completion_tokens=1024,response_text="partial",correct=False)
        x.update(changes);return x
    def recover(self,events):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"events.jsonl";p.write_text("".join(json.dumps(x)+"\n" for x in events))
            return recover_quality_responses(p)
    def test_success_failure_and_truncation_preserved(self):
        a=self.row();b=self.row(1,ok=False,request_id=None,error="deadline",finish_reason=None)
        r=self.recover([dict(event="quality-public-producer",scored=False),a,b])
        self.assertEqual(r,[{k:v for k,v in x.items() if k not in ("event","scored")} for x in [a,b]])
        self.assertFalse(r[0]["correct"]);self.assertEqual(r[0]["finish_reason"],"length")
    def test_empty_does_not_fabricate(self):self.assertEqual(self.recover([]),[])
    def test_duplicates_rejected(self):
        with self.assertRaises(ValueError):self.recover([self.row(),self.row()])
    def test_repeated_sample_different_round_retained(self):
        self.assertEqual(len(self.recover([self.row(),self.row(repetition=2)])),2)
    def test_bad_fields_rejected(self):
        for kw in [dict(index=127),dict(index=True),dict(repetition=0),dict(ok=1),
                   dict(sample_id=""),dict(segment_sha256="bad"),dict(scored=False),dict(request_id=None)]:
            with self.subTest(kw=kw),self.assertRaises(ValueError):self.recover([self.row(**kw)])
    def test_duplicate_success_request_rejected(self):
        with self.assertRaises(ValueError):self.recover([self.row(),self.row(1,request_id="req01")])
    def test_non_object_rejected(self):
        with self.assertRaises(ValueError):self.recover([[]])
    def test_malformed_journal_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"events.jsonl";p.write_text("{")
            with self.assertRaises(ValueError):recover_quality_responses(p)
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"events.jsonl";p.write_text("");q=Path(d)/"link";q.symlink_to(p)
            with self.assertRaises(ValueError):recover_quality_responses(q)

if __name__=="__main__":unittest.main()
