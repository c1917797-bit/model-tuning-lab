import types,unittest
from unittest.mock import patch
from independent_prompt_snapshot_probe import measure_prompt_snapshot
class Tests(unittest.TestCase):
    def states(self):return {"a":types.SimpleNamespace(prompt_token_ids=[1,2,3],mm_features=[]),
                             "b":types.SimpleNamespace(prompt_token_ids=[4,5,6],mm_features=[])}
    def test_same_metadata_decode_and_prefill(self):
        out,event=measure_prompt_snapshot(("a","b"),self.states(),(3,1),(1,2))
        self.assertEqual(dict(out),{"a":None,"b":(4,5,6)})
        self.assertEqual(event["omitted_decode_ids"],["a"])
        self.assertEqual(event["retained_prefill_ids"],["b"])
        self.assertEqual(event["omitted_prompt_tokens"],3)
        self.assertEqual(event["order"],["original","prefill_only"])
        for row in event["measurements"].values():
            self.assertGreaterEqual(row["wall_ns"],0);self.assertGreaterEqual(row["thread_cpu_ns"],0)
    def test_reverse_order(self):
        _,e=measure_prompt_snapshot(("a",),self.states(),(3,),(1,),reverse=True)
        self.assertEqual(e["order"],["prefill_only","original"])
    def test_required_prefill_mutation_fails(self):
        with patch("independent_prompt_snapshot_probe.freeze_prefill_prompt_tokens",return_value={"a":(9,)}):
            with self.assertRaises(ValueError):measure_prompt_snapshot(("a",),self.states(),(1,),(2,))
    def test_decode_not_omitted_fails(self):
        with patch("independent_prompt_snapshot_probe.freeze_prefill_prompt_tokens",return_value={"a":(1,2,3)}):
            with self.assertRaises(ValueError):measure_prompt_snapshot(("a",),self.states(),(3,),(1,))
    def test_invalid_count_coverage_fails(self):
        with self.assertRaises(ValueError):measure_prompt_snapshot(("a",),self.states(),(),(1,))
    def test_bound_and_switch(self):
        with self.assertRaises(ValueError):measure_prompt_snapshot((),{},(),())
        with self.assertRaises(ValueError):measure_prompt_snapshot(("a",),self.states(),(3,),(1,),reverse=1)
if __name__=="__main__":unittest.main()
